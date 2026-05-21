import os
import uuid
import json
from typing import List, Optional
from fastapi import APIRouter, WebSocketDisconnect, WebSocket, UploadFile, File, Form, Response, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from datetime import datetime
import urllib.parse
from db import get_db, engine, styleEnum, DocLength, Base, Session, DocumentRecord, ItemSearch
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit
import asyncio
from websocket import process_document, manager
import unicodedata 


# 파일 임시 저장소 
temp_files: dict ={}


Base.metadata.create_all(bind=engine)

router= APIRouter()

# 인증 로직
def get_current_user(request:Request):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    return uuid.UUID(user_id)


# 파일 업로드 및 분석 결과 저장 API
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

    file_id = uuid.uuid4()
    file_bytes :bytes= await file.read()

     # 파일 바이트를 메모리에 임시저장
    temp_files[str(file_id)] = file_bytes

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
        # 2. DOCUMENT_RECORDS 테이블에 저장
        new_record = DocumentRecord(
            id=str(uuid.uuid4()),
            user_id=current_user_id,
            file_id=file_id,
            file_name=file.filename,
            category=None,
            summary=None,
            upload_at=datetime.now(),
            process_at=None,
            task_status="PENDING"
        )
        db.add(new_record)
        db.commit()      

        # 3. 규격에 맞춘 JSON 응답
        return {
            "fileId": str(file_id),
            "fileName": file.filename,
            "fileSize": len(file_bytes),
            "status": "PENDING",
            "create_at": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error Detail: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    
# websocket 엔드 포인트
@router.websocket("/ws/{file_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    file_id:str
):
    await manager.connect(file_id, websocket)
    with Session() as db:
        try:
            file_bytes = temp_files.get(str(file_id), None) # 임시 저장된 파일 바이트 꺼내오기

            if not file_bytes:
                await manager.send(file_id, {"state":"FAILURE", "error": "파일을 찾을 수 없습니당!"})
                await websocket.close()
                return
            #process_document로 바로 전달
            asyncio.create_task(process_document(file_id, file_bytes, db))
            
            
            while True:
                    await websocket.receive_text() # 클라가 메시지 보낼때까지 대기 하겠다.
        except WebSocketDisconnect: # 루프를 빠져나오고 맨 밑에 있는 file_id 연결목록에서 해당 유저를 지우고 종료
            pass
        finally:
            manager.disconnect(file_id)
            db.close() 


# 사용자의 업로드 이력 조회 API
@router.get("/history")
async def get_user_history(
    request:Request,
    db: Session = Depends(get_db)
):
    user_id =request.session.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    history =db.query(DocumentRecord).filter(DocumentRecord.user_id==user_id).all()
    return history

# 결과 파일 다운로드 API (PDF/TXT 선택)
@router.get("/download/{file_id}")
async def download_file(file_id:str, format:str, db: Session = Depends(get_db)):
    record = db.query(DocumentRecord).filter(DocumentRecord.file_id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    
    content = record.summary

    if format == 'txt':
        file_content=content.encode("utf-8")
        media_type= "text/plain"
        file_name =f"{urllib.parse.quote(record.file_name)}.txt"
    elif format == 'pdf':
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        text_object = p.beginText(40,750)
        # 한글 폰트 설정 필수
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        FONT_PATH = os.path.join(BASE_DIR, "fonts","NanumGothic.ttf")
        pdfmetrics.registerFont(TTFont("NanumGothic", FONT_PATH))
        text_object.setFont("NanumGothic",10)


        usable_width = 594 - 80 # A4 너비 - 양옆 너비


        for line in content.split('\n'):
            # 자동 줄바꿈
            text_line = simpleSplit(line, "NanumGothic",10, usable_width)
            for text in text_line:
                text_object.textLine(text) 
        
        p.drawText(text_object) 
        p.showPage() 
        p.save() 

        file_content = buffer.getvalue()
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


@router.get('/search', response_model = List[ItemSearch])
async def search_file(
    request : Request,
    keyword: Optional[str] = Query(None, min_length=2), # 아무것도 없어도 되며, 최소 2글자는 적어야 한다.
    db:Session = Depends(get_db)
):
    
    if not hasattr(request, "session") or request.session is None:
        print("에러: 세션 미들웨어가 설정되지 않았거나 세션이 없습니다.")
        raise HTTPException(status_code=401, detail="세션 정보가 없습니다. 다시 로그인 해주세요.")

    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="로그인이 필요한 서비스입니다.")
    
    clean_text = unicodedata.normalize('NFC', keyword)
    results = []
    all_records = db.query(DocumentRecord).filter(DocumentRecord.user_id == uuid.UUID(user_id)).all()
    if not keyword:
        return all_records
    for doc in all_records:
        normalized_file_name = unicodedata.normalize('NFC', doc.file_name)
        if clean_text in normalized_file_name:
            results.append(doc)
    return results