import requests
import re
import json
import os
from dotenv import load_dotenv
from google import genai
from fastapi import FastAPI, UploadFile, File,HTTPException
import base64
import json
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_ollama import OllamaLLM

load_dotenv()

app = FastAPI()

llm = OllamaLLM(model='gemma4')

class DiaryRequest(BaseModel):
    content: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 실제 서비스 시에는 React 주소(http://localhost:3000)만 넣으세요
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/counseling")
async def get_counseling(request: DiaryRequest):
    user_text=request.content
    prompt=f"""당신은 심리 상담사입니다. 사용자의 일기를 읽고 위로의 한 문장으로 대답해주세요.
    
    일기 내용:{user_text}"""

    response=llm.invoke(prompt)
    return {"reply":response}

API_KEY = os.getenv("YOUR_OPENAI_API_KEY")
client = genai.Client(api_key= API_KEY)

@app.post("/extract-document")
async def extract_document(file:UploadFile = File(...)):
    contents = await file.read()
    base64_image = base64.b64encode(contents).decode('utf-8')

    response = client.models.generate_content(
        model ="gemini-flash-latest",
        contents = [
                "내일 시험 보는 사람이여서 해당 자료를 가지고 요약본을 추출한다고 생각하고 이 파일에서 요약본 추출해줘.",
                {
                    "inline_data": {
                        "mime_type": file.content_type,
                        "data": base64_image
                    }
                }
            ]
    )
    extracted_text = response.text

    clean_json = extracted_text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_json)

# @app.post("/extract-document")
# async def extract_document(file: UploadFile = File(...)):
#     try:
#         contents = await file.read()
#         base64_image = base64.b64encode(contents).decode('utf-8')

#         # 1. 프롬프트 강화: JSON 형식을 엄격히 요구
#         prompt = (
#             "내일 시험 공부를 위한 요약본을 만들어줘. "
#             "반드시 다른 설명 없이 오직 JSON 형식으로만 응답해. "
#             "형식: {'title': '제목', 'summary': ['요약1', '요약2'], 'keywords': ['키워드1']}"
#         )

#         response = client.models.generate_content(
#             model="gemini-flash-latest", 
#             contents=[
#                 prompt,
#                 {
#                     "inline_data": {
#                         "mime_type": file.content_type,
#                         "data": base64_image
#                     }
#                 }
#             ]
#         )
        
#         extracted_text = response.text
#         if not extracted_text:
#             raise ValueError("모델 응답이 비어있습니다.")

#         # 2. 정규표현식으로 JSON 블록({ ... })만 추출
#         # (설명이 섞여 들어오는 경우를 대비한 가장 확실한 방법)
#         json_match = re.search(r'\{.*\}', extracted_text, re.DOTALL)
#         if json_match:
#             clean_json = json_match.group(0)
#         else:
#             # 정규표현식 실패 시 기존 방식(마크다운 제거) 사용
#             clean_json = extracted_text.replace("```json", "").replace("```", "").strip()
        
#         return json.loads(clean_json)

#     except json.JSONDecodeError as je:
#         print(f"JSON 파싱 에러: {extracted_text}")
#         raise HTTPException(status_code=500, detail="JSON 형식이 올바르지 않습니다.")
#     except Exception as e:
#         print(f"서버 에러: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/unrest-check")
async def unrest_check(diary: DiaryRequest):
    prompt = f"""
    당신은 심리 분석 전문가입니다. 다음 일기를 읽고 사용자의 '불안도'를 0부터 100 사이의 수치로 분석하세요.
    결과는 반드시 아래의 JSON 형식으로만 응답하세요. 다른 설명은 생략하세요.

    {{
        "anxiety_score": (수치),
        "reason": "한 줄 분석 내용",
        "keywords": ["감정키워드1", "감정키워드2"]
    }}

    일기 내용:
    {diary.content}
    """

    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=[prompt]
        )
        raw_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(raw_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
