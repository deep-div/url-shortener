from fastapi import FastAPI

from app.api.router import router

app = FastAPI(title="URL Shortener")
app.include_router(router)


# py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000