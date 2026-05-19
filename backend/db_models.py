import enum
from sqlalchemy import create_engine,Column, String, DateTime, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import sessionmaker,declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
from dotenv import load_dotenv
import os
import uuid
from enum import Enum as PyEnum


load_dotenv()

# 도커용
DATABASE_URL = "postgresql://admin:1234@postgres:5432/ai_db"

# 로컬용
# DATABASE_URL = "postgresql://admin:1234@localhost:5432/ai_db"

engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine)
# DB_URL = os.getenv("DATABASE_URL")
# engine = create_engine(DB_URL, echo=True)
# Session = sessionmaker(bind=engine)

Base = declarative_base()

def get_db():
    db = Session() # db 세션 생헝
    try:
        yield db # 함수의 실행을 일시중지하고 값을 호출자에게 반환하는 키워드, api 컨트롤러에 세션 전달 및 대기
    finally:
        db.close() # api 요청 처리 완료 후 세션 종류 

# 1. 카테고리 Enum 정의
class DocCategory(enum.Enum):
    TECH = "기술/개발문서"
    LEGAL = "법률/판례"
    PROPOSAL = "기획안/제안서"
    BUSINESS = "경영/비즈니스"
    ACADEMIC = "교육/학술"
    ADMIN = "행정/공공문서"
    LIFE = "생활/가정"
    FINANCE = "금융/회계"
    MEDICAL = "의료/건강"
    ETC = "기타/미분류"

class DocLength(str, Enum):
    SHORT= "SHORT" 
    MIDDLE= "MIDDLE"
    LONG= "LONG"

class styleEnum(str, Enum):
    STYLE1='1'
    STYLE2='2'    

# 2. 사용자 정보 테이블 모델
class UserInfo(Base):
    __tablename__ = "USER_INFO"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="User")
    create_at = Column(DateTime(timezone=True), server_default=func.now())
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # 관계 설정 컬럼 : 한 사용자는 여러 문서 기록을 가질 수 있고, 사용자 삭제시 관련 문서도 모두 삭제
    documents = relationship("DocumentRecord", back_populates="owner", cascade="all, delete-orphan")

# 3. 문서 요약 기록 테이블 모델
class DocumentRecord(Base):
    __tablename__ = "DOCUMENT_RECORDS"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER_INFO.user_id", ondelete="CASCADE"), nullable=False)
    file_id = Column(UUID(as_uuid=True), nullable=False)
    file_name = Column(String(255), nullable=False)
    category = Column(Enum(DocCategory, name="doc_category_enum"),nullable=True)
    summary = Column(Text, nullable=True)
    upload_at = Column(DateTime(timezone=True), server_default=func.now())
    process_at = Column(DateTime(timezone=True), nullable=True)
    task_status = Column(String(20), default="PENDING")

    # 관계 설정: 이 문서는 특정 사용자에게 속함
    owner = relationship("UserInfo", back_populates="documents")



