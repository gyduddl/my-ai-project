from celery import Celery
import os
from dotenv import load_dotenv
from db_models import DocumentRecord, Session
import time
from datetime import datetime

load_dotenv()

celery_app = Celery(
    "worker", # 워커 이름

    # broker = os.getenv("REDIS_URL"), # 작업을 전달하는 메시지 큐
    # backend = os.getenv("REDIS_URL") # 작업 결과 저장하는 곳

    broker = "redis://localhost:6379/0",
    backend = "redis://localhost:6379/0"
)

# celery 작업으로 등록
@celery_app.task(bind=True) # bind = True -> self로 현재 task에 접근 가능, task상태를 중간에 업데이트할 수 있음
def process_document(self, file_id:str):
    db=Session() 

    try:
        # ----1단게: 시작(0%) -----
        self.update_state(
            state="PROGRESS", # celery 작업 상태
            meta = {"percent": 0} # meta 추가정보(퍼센트, 현재 단계)
        )

        record = db.query(DocumentRecord).filter(DocumentRecord.file_id == file_id).first()

        # 처리중
        record.task_status = "PROCESSING"
        db.commit()

        # -- 2. OCR 단계 --
        self.update_state(
            state="PROGRESS", 
            meta = {"percent": 10} 
        )
        time.sleep(3) # ocr 작업 중....ing
        extracted_text = "추출된 텍스트 입니당!"

        self.update_state(
            state="PROGRESS", 
            meta = {"percent": 40} 
        )        

        # -- 3. LLM 단계 ---
        self.update_state(
            state="PROGRESS", 
            meta = {"percent": 50} 
        )
        time.sleep(3) # LLM 작업 중....ing
        summary = "AI가 요약한 내용입니당!"
        category="REPORT"

        self.update_state(
            state="PROGRESS", 
            meta = {"percent": 90} 
        )

        record.summary =summary
        record.category = category
        record.task_status = "SUCCESS"
        record.process_at = datetime.now()
        db.commit()

        return summary, category, extracted_text

    except Exception as e:
        print(f"celery 처리 실패: {e}")
        if record:
            record.task_status = "FAILURE"
            db.commit()
        raise e
    finally:
        db.close()