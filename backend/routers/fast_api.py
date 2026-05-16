from fastapi import FastAPI, Form, UploadFile, File, HTTPException, Depends,Response
from pydantic import BaseModel
from enum import Enum
from fastapi.middleware.cors import CORSMiddleware
from db_models import get_db, engine
from sqlalchemy.orm import Session
import db_models
import urllib.parse
import json
from fpdf import FPDF # pdf 다운로드 형식

db_models.Base.metadata.create_all(engine)

app = FastAPI()

#cors 문제 해결
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], #모든 도메인 허용
    allow_methods=["*"], #모든 메서드 허용
    allow_headers=["*"],  #모든 헤더 허용
    expose_headers = ["X-Extra-Info", "Content-Disposition"]
)


# return 값
# file, length, style

# 1. Enum 정의
class LengthEnum(str, Enum):
    SHORT= "SHORT" 
    MIDDLE= "MIDDLE"
    LONG= "LONG"

class styleEnum(str, Enum):
    STYLE1='1'
    STYLE2='2'

# Response 스키마
class SummaryResponse(BaseModel):
    fileId: str
    fileName: str
    summary: str
    fileSize: int
    create_at: str

#


@app.post("/upload", response_model=SummaryResponse)
async def upload_pdf(
    file:UploadFile = File(...),
    length: LengthEnum = Form(LengthEnum.MIDDLE), #기본값 설정
    style: styleEnum = Form(styleEnum.STYLE1),
    db: Session=Depends(get_db) # db 세션 주입
    ):

    # 파일 검증
    if not file.filename.endswith('.pdf'):
        # raise : 에러 발생시키는 것
        raise HTTPException(status_code=422, detail='파일 형식 다름')
    print(f"파일 이름: {file.filename}")
    print(f"선택된 길이: {length}")
    
    try:
    
        # 비즈니스 로직 불러오기 (llm,ocr 작업)
        # ocr,llm 함수 가져오기 

        # llm을 돌려서 받아온 summary을 txt 파일로 만들기
        summary_text = '요약 본 입니당~'

        summary_filename = f"summary_{file.filename}.txt"

        content = await file.read()
        file_size = len(content)

        # response로 보내줄 다른 info
        extra_info ={
            "fileId": "test_id",
            "fileName": file.filename,
            "summary": "요약 내용입니다!!",
            "fileSize": file_size,
            "extracted_text":"pdf에서 추출된 텍스트입니당",
            "create_at": "2024-05-22",
            "category": "카데고리입니당"
        }


        # PostgreSQL에 정보 저장
        filetask = db_models.FileTask(
            file_name = file.filename,
            file_size = file_size,
            extracted_text = "", # 추후 ocr작업 후 업데이트
            status = "PENDING", 
            summary = "", # 추후 llm 작업 후 업데이트
            category= ""
        )

        db.add(filetask)
        db.commit()
        db.refresh(filetask) # 생성된 정보 다z시 읽어오기 

        # 작업 큐 등록


        # 임시 응답 데이터 리턴
        return Response(
            content=summary_text,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={urllib.parse.quote(summary_filename)}.txt",
                "X-Extra-Info":json.dumps(extra_info),
                "Access-Control-Expose-Headers": "X-Extra-Info, Content-Disposition"
            }
        )
    except Exception as e:
        print(f"발생한 에러 원인:{e}")
        raise HTTPException(status_code=422, detail='파일 요청 실패')

