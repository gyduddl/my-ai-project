import os
import uuid
import json
from fastapi import BackgroundTasks, APIRouter, FastAPI, UploadFile, File, Form, Response, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime
import urllib.parse
import db_models
from db_models import get_db, engine, DocCategory, styleEnum,DocLength, Base
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

Base.metadata.create_all(bind=engine)

router= APIRouter()

# 인증 로직 가정
def get_current_user(request:Request):
    user_id = request.session.get("user_id")
    print(request.session.items())

    if not user_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    return uuid.UUID(user_id)


# [POST] 파일 업로드 및 분석 결과 저장 API
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    length: str = Form(DocLength.MIDDLE), # SHORT, MIDDLE, LONG
    style: str = Form(styleEnum.STYLE1),
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user) # 인증 로직 가정
    ):

    ALLOWED_EXTENSIONS = ('.pdf', '.docx', '.doc', '.hwp', '.ppt', '.pptx', '.jpg', '.jpeg', '.png', '.gif', '.webp')

    #허용할 확장자 목록 
    if not file.filename.endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=422, detail=f"허용된 파일 형식:{ALLOWED_EXTENSIONS}")

    # 용량 체크
    MAX_SIZE = 10*1024*1024

    file_bytes=await file.read()

    # 파일 검증
    if len(file_bytes)> MAX_SIZE:
        raise HTTPException(status_code=422, detail="파일 용량이 10MB를 초과했습니다.")
    
    await file.seek(0)

    ALLOWED_MIME_TYPES = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc': 'application/msword',
    '.hwp': 'application/x-hwp',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    }

    if file.content_type not in ALLOWED_MIME_TYPES.values():
        raise HTTPException(status_code=422, detail='파일 내영이 확장자와 일치하지 않습니다.')
    

    try:
        # 1. AI 분석 및 요약 로직 수행 (가정)
        extracted_text = "추출된 텍스트 내용..."
        summary_result = "요약된 문서 내용입니다."
        # category_result = DocCategory.LEGAL
        category_result = "LEGAL"
        file_id = uuid.uuid4()

        # 2. DOCUMENT_RECORDS 테이블에 저장
        new_record = db_models.DocumentRecord(
            id=str(uuid.uuid4()),
            user_id=current_user_id,
            file_id=file_id,
            file_name=file.filename,
            category=category_result,
            summary=summary_result,
            upload_at=datetime.now(),
            process_at=datetime.now()
        )
        db.add(new_record)
        db.commit()

        # 3. 규격에 맞춘 JSON 응답
        return {
            "fileId": str(file_id),
            "extracted_text": extracted_text,
            "fileName": file.filename,
            "summary": summary_result,
            "category": category_result,
            "fileSize": len(file_bytes),
            "create_at": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error Detail: {e}")
        raise HTTPException(status_code=422, detail=str(e))

# [GET] 사용자의 업로드 이력 조회 API
@router.get("/history")
async def get_user_history(
    request:Request,
    db: Session = Depends(get_db)
):
    user_id =request.session.get("user_id")
    print(request.session.items())
    print(f"로그인 정보 : {user_id, db_models.DocumentRecord.user_id}")

    if not user_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    history =db.query(db_models.DocumentRecord).filter(db_models.DocumentRecord.user_id==user_id).all()
    
    return history

# [GET] 결과 파일 다운로드 API (PDF/TXT 선택)
@router.get("/download/{file_id}")
async def download_file(file_id:str, format:str, db: Session = Depends(get_db)):
    # 디비에서 데이터 가져오기 
    record = db.query(db_models.DocumentRecord).filter(db_models.DocumentRecord.file_id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    
    content = record.summary

    if format == 'txt':
        file_content=content.encode("utf-8")
        media_type= "text/plain"
        file_name =f"{urllib.parse.quote(record.file_name)}.txt"
    elif format == 'pdf':
        buffer = BytesIO() # 바구니 만들기
        p = canvas.Canvas(buffer)
        text_object = p.beginText(40,750)
        # 한글 폰트 설정 필수
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        FONT_PATH = os.path.join(BASE_DIR, "fonts","NanumGothic.ttf")
        pdfmetrics.registerFont(TTFont("NanumGothic", FONT_PATH))
        text_object.setFont("NanumGothic",10)

        for line in content.split('\n'):
            text_object.textLine(line) # textLine 한줄 쓰고 다음줄로 가자
        
        p.drawText(text_object) # 텍스트를 도화지에 인쇄
        p.showPage() # 현재 페이지 끝
        p.save() # 파일 저장

        file_content = buffer.getvalue() #바구니를 복사, 데이터 가져옴
        buffer.close()
        media_type = "application/pdf"
        file_name = f"{urllib.parse.quote(record.file_name)}.pdf"

    return Response(
        content = file_content,
        media_type = media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{file_name}",
            "Access-Control-Expose-Headers" : "Content-Disposition"
        }
    )


