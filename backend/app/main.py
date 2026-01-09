from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import chat, presentation
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Analytics Chatbot API",
    description="AI-powered analytics chatbot with chart and presentation generation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(presentation.router)


@app.get("/")
async def root():
    return {"message": "Analytics Chatbot API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
