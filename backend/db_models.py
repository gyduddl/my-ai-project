import enum
from sqlalchemy import create_engine,Column, Integer, String, DateTime, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import sessionmaker,declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
# from database import Base
from datetime import datetime
from dotenv import load_dotenv
import os
import uuid
from enum import Enum as PyEnum


load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL, echo=True)
Session = sessionmaker(bind=engine)

Base = declarative_base()

def get_db():
    db = Session()
    try:
        yield db # 함수의 실행을 일시중지하고 값을 호출자에게 반환하는 키워드
    finally:
        db.close()

# 1. 카테고리 Enum 정의
class DocCategory(enum.Enum):
    REPORT = "REPORT"
    BUSINESS = "BUSINESS"
    ACADEMIC = "ACADEMIC"
    LEGAL = "LEGAL"
    ETC = "ETC"

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
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER_INFO.user_id", ondelete="CASCADE"), nullable=True)
    file_id = Column(UUID(as_uuid=True), nullable=False)
    file_name = Column(String(255), nullable=False)
    category = Column(Enum(DocCategory, name="doc_category_enum"),nullable=True)
    summary = Column(Text, nullable=True)
    upload_at = Column(DateTime(timezone=True), server_default=func.now())
    process_at = Column(DateTime(timezone=True), nullable=True)

    # 관계 설정: 이 문서는 특정 사용자에게 속함
    owner = relationship("UserInfo", back_populates="documents")

# class FileTask(Base):
#     __tablename__ ='filetask'

#     id= Column(Integer, primary_key=True, default = uuid.uuid4)
#     file_name = Column(String, nullable=False)
#     extracted_text = Column(Text, nullable=False)
#     status = Column(String, default="PENDING")
#     summary = Column(Text, nullable=True)
#     file_size = Column(Integer)
#     created_at = Column(DateTime, default=datetime.now)
#     category = Column(String, default=False)




