import requests
import json
import os
from dotenv import load_dotenv
from google import genai
from fastapi import FastAPI, UploadFile, File,HTTPException
import base64
import json
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 실제 서비스 시에는 React 주소(http://localhost:3000)만 넣으세요
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("YOUR_OPENAI_API_KEY")
client = genai.Client(api_key= API_KEY)

@app.post("/extract-document")
async def extract_document(file:UploadFile = File(...)):
    contents = await file.read()
    base64_image = base64.b64encode(contents).decode('utf-8')

    response = client.models.generate_content(
        model ="gemini-flash-latest",
        contents = [
                "이 이미지에서 텍스트를 추출해서 JSON 형식으로 정리해줘. 결과는 반드시 순수 JSON 데이터만 출력해.",
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
    return json.loads(extracted_text)

class DiaryRequest(BaseModel):
    content: str

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
