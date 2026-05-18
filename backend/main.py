from fastapi import FastAPI
from routers import auth, document
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv

load_dotenv()



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175"], #모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"], #모든 메서드 허용
    allow_headers=["*"],  #모든 헤더 허용
    expose_headers = ["Content-Disposition"]
)

app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("SESSION_SECRET_KEY"),
    same_site="lax",
    https_only=False, 
    
    )

app.include_router(auth.router)
app.include_router(document.router)