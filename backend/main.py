import requests
import json
import os
from dotenv import load_dotenv
from google import genai
from fastapi import FastAPI, UploadFile, File
import base64
import json
from fastapi.middleware.cors import CORSMiddleware

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
