import re

from pydantic import BaseModel, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(value: str) -> str:
    if not _EMAIL_RE.match(value):
        raise ValueError("Email không hợp lệ")
    return value


class RegisterRequest(BaseModel):
    email: str
    password: str

    _check_email = field_validator("email")(_validate_email)


class LoginRequest(BaseModel):
    email: str
    password: str

    _check_email = field_validator("email")(_validate_email)


class AuthResponse(BaseModel):
    token: str
    email: str
    is_pro: bool


class MeResponse(BaseModel):
    email: str
    is_pro: bool
