from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine_music
from app.routers import albums, downloads, songs


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

app.include_router(songs.router)
app.include_router(albums.router)
app.include_router(downloads.router)
