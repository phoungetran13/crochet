from fastapi import APIRouter, Header, HTTPException
from typing import Optional

from app import db
from app.schemas.auth import AuthResponse, LoginRequest, MeResponse, RegisterRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _require_user(authorization: Optional[str]) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    token = authorization.removeprefix("Bearer ").strip()
    user = db.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập không hợp lệ")
    return user


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest) -> AuthResponse:
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu cần ít nhất 6 ký tự")
    user = db.create_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=409, detail="Email đã được đăng ký")
    token = db.create_session(user["id"])
    return AuthResponse(token=token, email=user["email"], is_pro=user["is_pro"])


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest) -> AuthResponse:
    user = db.verify_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
    token = db.create_session(user["id"])
    return AuthResponse(token=token, email=user["email"], is_pro=user["is_pro"])


@router.post("/logout")
async def logout(authorization: Optional[str] = Header(default=None)) -> dict:
    if authorization and authorization.startswith("Bearer "):
        db.delete_session(authorization.removeprefix("Bearer ").strip())
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
async def me(authorization: Optional[str] = Header(default=None)) -> MeResponse:
    user = _require_user(authorization)
    return MeResponse(email=user["email"], is_pro=user["is_pro"])


@router.post("/subscribe-pro", response_model=MeResponse)
async def subscribe_pro(authorization: Optional[str] = Header(default=None)) -> MeResponse:
    """Demo: kich hoat goi Pro ngay lap tuc, khong qua buoc thanh toan that."""
    user = _require_user(authorization)
    db.set_pro(user["id"], True)
    return MeResponse(email=user["email"], is_pro=True)


@router.post("/cancel-pro", response_model=MeResponse)
async def cancel_pro(authorization: Optional[str] = Header(default=None)) -> MeResponse:
    user = _require_user(authorization)
    db.set_pro(user["id"], False)
    return MeResponse(email=user["email"], is_pro=False)
