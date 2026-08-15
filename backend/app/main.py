from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import db
from app.routers.auth import router as auth_router
from app.routers.pattern import router as pattern_router

app = FastAPI(title="Crochet Chart Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pattern_router)
app.include_router(auth_router)


@app.on_event("startup")
async def on_startup() -> None:
    db.init_db()


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


# Serve frontend tinh (index.html) tu cung 1 service khi deploy - tranh phai
# quan ly CORS/2 domain rieng biet. Neu thu muc frontend khong ton tai (vd
# khi chi chay unit test backend) thi bo qua, khong loi.
_frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
if _frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
