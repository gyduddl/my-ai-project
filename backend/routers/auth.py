from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
from db import UserInfo, get_db,Base,engine
import bcrypt


router = APIRouter()

Base.metadata.create_all(bind=engine)

# 스키마
class UserCreate(BaseModel):
    email:str
    password:str

# 유틸
def hash_password(password:str): # 암호화된 문자열을 반환, db에 암호화 값만 저장
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain, hashed): # 로그인시 입력한 비밀번호(plain)과 db 해시값과 같은지 비교
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    

@router.post("/register")
def register(user_data: UserCreate, db:Session = Depends(get_db)):
    # 이미 같은 이메일로 가입한 유저가 있는지 확인
    existing = db.query(UserInfo).filter(UserInfo.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
    
    new_user = UserInfo(
        email = user_data.email,
        password_hash = hash_password(user_data.password) # 암호화해서 저장
    )

    db.add(new_user)
    db.commit()

    return {"message": "회원가입 완료"}

@router.post("/login") # request: Request => 세션 접근할떄 필요
def login(user_data:UserCreate, request:Request, db:Session=Depends(get_db)):
    user =db.query(UserInfo).filter(UserInfo.email == user_data.email).first()

    if not user or not verify_password(user_data.password,user.password_hash):
        raise  HTTPException(status_code=401, detail="이메일 또는 비밀번호가 틀렸습니다.")
        # HTTPException : 오류 발생시 클라이언트에게 상태코드랑 메시지 전달, 
        # 401 : 인증 요구시 유효하지 않는 유저

    # 서버 세션에 유저 정보 저장
    # 브라우저 쿠키에 세션 ID가 자동으로 담겨서 이후 요청마다 자동 첨부됨
    request.session["user_id"] = str(user.user_id)
    request.session["email"] = user.email
    print(f"로그인할때 세션 :{request}{request.session.items()}")
    return {"message": "로그인 성공"}

@router.post("/logout")
def logout(request:Request):
    request.session.cleare()
    return {"message":"로그아웃 완료"}