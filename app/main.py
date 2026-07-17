from fastapi import FastAPI
from app.routers import songs, sync

app = FastAPI(
    title="API Mogz"
)

app.include_router(songs.router)
app.include_router(sync.router)