from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import app.models
from app.config import DOWNLOADS_FOLDER
from app.database import Base, engine_music
from app.routers import downloads, music


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine_music)
    yield

app = FastAPI(
    title="API ZTools",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://192.168.1.42:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=DOWNLOADS_FOLDER), name="static")

app.include_router(music.router)
app.include_router(downloads.router)
