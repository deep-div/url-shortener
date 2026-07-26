from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router

app = FastAPI(title="URL Shortener")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


# py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000