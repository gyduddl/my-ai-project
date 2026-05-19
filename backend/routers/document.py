import os
import uuid
import json
from fastapi import APIRouter, WebSocketDisconnect, WebSocket, UploadFile, File, Form, Response, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime
import urllib.parse
from db import get_db, engine, styleEnum, DocLength, Base, Session, DocumentRecord
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import asyncio
from websocket import process_document, manager
import pymupdf
from ollama_client import subtract_text
from util.file_reader2 import process_pdf
from starlette.concurrency import run_in_threadpool


# 파일 임시 저장소 
temp_files: dict ={}


Base.metadata.create_all(bind=engine)

router= APIRouter()

# 인증 로직
def get_current_user(request:Request):
    user_id = request.session.get("user_id")
    print(request.session.items())

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
    print("뭔지 모르겠지만 뭐가 나와야 하지...")
    somting ="""
        너는 문서 분류 및 요약 엔진이다.

        반드시 아래 규칙을 지켜라.

        [작업]
        INPUT 문서를 읽고 category와 summary를 생성한다.

        [category 선택 규칙]
        category는 반드시 CATEGORY_LIST 중 정확히 하나를 그대로 복사한다.
        CATEGORY_LIST에 없는 값은 절대 출력하지 않는다.
        category를 번역하거나, 줄이거나, 띄어쓰기를 바꾸거나, 새로 만들지 않는다.
        판단이 애매하면 "기타/미분류"를 선택한다.

        [CATEGORY_LIST]

        [summary 작성 규칙]
        summary는 INPUT에 있는 내용만 근거로 작성한다.
        INPUT에 없는 정보, 추측, 외부 지식은 절대 추가하지 않는다.
        summary는 한국어로 작성한다.
        summary는 2문장 이상 5문장 이하로 작성한다.
        문서의 핵심 주제, 목적, 주요 내용을 포함한다.
        원문 의미를 과장하거나 바꾸지 않는다.

        [출력 규칙]
        반드시 JSON 객체만 출력한다.
        JSON 밖에 설명, 문장, 코드블록, 마크다운을 출력하지 않는다.
        키는 반드시 category와 summary만 사용한다.

        [출력 예시]
        

        [INPUT]
        """
    print(f"llm에 들어가는 거 어떤 타입? ${type(somting)}")
    llm_text = await run_in_threadpool(subtract_text,somting)
    print(f"llm 잘 나아아아아오냐${llm_text}")
    # print("ocr 시작")
    # print(f"들어온 파일 ${file}, 타입 확인 1. ${type(file)}")
    # #ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
    # file_send :bytes= await file.read()
    # print(f"바이트인지 확인 2. ${len(file_send)}")
    # print(f"타입 확인 2. ${type(file_send)}")
    # extracted_text = await run_in_threadpool(
    #     process_pdf,
    #     file_send
    # )
    # print(f"추출된 데이터 :${extracted_text}")
    # #ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
    
    # print(f"출력결과 가져오기 : ${llm_text}")
    # check_file = await file.read()
    # doc = pymupdf.open(stream =check_file, filetype="pdf")
    # print(f"파일 확인${doc},타입 ${type(check_file)}")    

    ALLOWED_EXTENSIONS = ('.pdf', '.docx', '.doc', '.hwp', '.ppt', '.pptx', '.jpg', '.jpeg', '.png', '.gif', '.webp')

    #허용할 확장자 목록 
    if not file.filename.endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=422, detail=f"허용된 파일 형식:{ALLOWED_EXTENSIONS}")

    # 용량 체크
    MAX_SIZE = 10*1024*1024

    file_id = uuid.uuid4()
    file_bytes :bytes= await file.read()
    print(f"웹소켓 들어가기지전에 바이트 확인 . 1 ${type(file_bytes)} ")

     # 파일 바이트를 메모리에 임시저장 => 파일 자체를 저장해야 할듯
    temp_files[str(file_id)] = file_bytes

    print("잘들어가지나1")
    # 파일 검증
    if len(file_bytes)> MAX_SIZE:
        raise HTTPException(status_code=422, detail="파일 용량이 10MB를 초과했습니다.")
    
    await file.seek(0)
    print("잘들어가지나2")
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
    print("잘들어가지나3")
    if file.content_type not in ALLOWED_MIME_TYPES.values():
        raise HTTPException(status_code=422, detail='파일 내영이 확장자와 일치하지 않습니다.')
    

    try:
        print("잘들어가지나4")
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
    print("잘들어가지나6")
    await manager.connect(file_id, websocket)
    with Session() as db:
        try:
            print("잘들어가지나7")
            file_bytes = temp_files.get(str(file_id), None) # 임시 저장된 파일 바이트 꺼내오기
            print(f"웹소켓 들어가기지전에 바이트 확인 . 2 타입 확인 : ${type(file_bytes)}")

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
    print(request.session.items())
    print(f"로그인 정보 : {user_id, DocumentRecord.user_id}")

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


