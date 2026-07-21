from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import songs, sync

app = FastAPI(
    title="API Mogz"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://192.168.1.XXX:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(songs.router)
app.include_router(sync.router)