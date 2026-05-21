from fastapi import WebSocket
from starlette.concurrency import run_in_threadpool
from db import DocumentRecord,Session, DocCategory
import asyncio # async/await 사용하는 라이브러리
from datetime import datetime
from util.file_reader2 import process_pdf
from ollama_client import subtract_text
import json

# websocket 연결 관리
class ConnectionManager:
    def __init__(self):
        self.connections:dict={} # fille_id : websocket 저장
    
    async def connect(self, file_id: str, websocket: WebSocket): # 웹소켓 연결
        await websocket.accept() # websocket 연결 수락
        self.connections[file_id] = websocket
        
    def disconnect(self, file_id: str,): # 웹소켓 제거
        if file_id in self.connections:
            del self.connections[file_id] 

    async def send(self, file_id:str, data:dict):
        if file_id in self.connections:
            await self.connections[file_id].send_json(data) # 딕셔너리를 자동으로 json 문자열로 반환


manager = ConnectionManager()
# 앱 전체에서 하나의 manager 공유 

# 진행상태 전달 함수
async def process_document(file_id, file_bytes ,db:Session):
    record = None
    record = db.query(DocumentRecord).filter(DocumentRecord.file_id == file_id).first()
    try:
        # ocr 시작 (10%)
        await manager.send(file_id,{
            "percent": 10,
            "state" : "PROGRESS"
        })
        # ocr 
        extracted_text = await run_in_threadpool(
            process_pdf,
            file_bytes
        )

        await manager.send(file_id,{
            "percent": 40,
            "state" : "PROGRESS",
            "extracted_text" :  extracted_text
        })

        await manager.send(file_id,{
            "percent": 50,
            "state" : "PROGRESS",
        })


        # llm 
        llm_result= await run_in_threadpool(subtract_text,extracted_text[0]) # 문자열로 들어옴
        llm_result = json.loads(llm_result)
        category=llm_result["category"]
        summary = llm_result["summary"]

        await manager.send(file_id,{
            "percent": 90,
            "state" : "PROGRESS",
        })
        
        now = datetime.now()

        if record:
            record.summary =summary
            record.category = DocCategory(llm_result["category"])
            record.task_status = "SUCCESS"
            record.process_at = now
            db.commit()

        await manager.send(file_id,{
            "percent": 100,
            "state" : "SUCCESS",
            "summary" : summary,
            "category" : category,
            "process_at":now.isoformat() # .isoformat()을 확실하게 붙여서 문자열로 만들어줍니다!
        })
        

    except Exception as e:
        record = db.query(DocumentRecord).filter(DocumentRecord.file_id == file_id).first()
        if record:
            record.task_status = "FAILURE"
            db.commit()
        
        await manager.send(file_id,{
            "percent" : 0,
            "state" : "FAILURE",
            "error": str(e)
        })

