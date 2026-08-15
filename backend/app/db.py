"""SQLite don gian de luu tai khoan + trang thai goi Pro - du chi la demo
nhung du lieu duoc luu that vao file (khong phai localStorage phia frontend),
song sot qua cac lan restart server."""
from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from pathlib import Path
from typing import Optional

_DB_PATH = Path(__file__).resolve().parent.parent / "data.db"

# Tai khoan demo da duoc kich hoat san goi Pro - de nguoi dung xem tinh nang
# "khong can xem quang cao" ma khong phai tu dang ky truoc.
DEMO_PRO_EMAIL = "pro@lenly.vn"
DEMO_PRO_PASSWORD = "demo123"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def init_db() -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                is_pro INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id)
            )
            """
        )
        conn.commit()

        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?", (DEMO_PRO_EMAIL,)
        ).fetchone()
        if existing is None:
            salt = secrets.token_hex(16)
            conn.execute(
                "INSERT INTO users (email, salt, password_hash, is_pro) VALUES (?, ?, ?, 1)",
                (DEMO_PRO_EMAIL, salt, _hash_password(DEMO_PRO_PASSWORD, salt)),
            )
            conn.commit()
    finally:
        conn.close()


def create_user(email: str, password: str) -> Optional[dict]:
    conn = _connect()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing is not None:
            return None
        salt = secrets.token_hex(16)
        password_hash = _hash_password(password, salt)
        cur = conn.execute(
            "INSERT INTO users (email, salt, password_hash, is_pro) VALUES (?, ?, ?, 0)",
            (email, salt, password_hash),
        )
        conn.commit()
        return {"id": cur.lastrowid, "email": email, "is_pro": False}
    finally:
        conn.close()


def verify_user(email: str, password: str) -> Optional[dict]:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT id, email, salt, password_hash, is_pro FROM users WHERE email = ?", (email,)
        ).fetchone()
        if row is None:
            return None
        if _hash_password(password, row["salt"]) != row["password_hash"]:
            return None
        return {"id": row["id"], "email": row["email"], "is_pro": bool(row["is_pro"])}
    finally:
        conn.close()


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    conn = _connect()
    try:
        conn.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user_id))
        conn.commit()
    finally:
        conn.close()
    return token


def get_user_by_token(token: str) -> Optional[dict]:
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT users.id AS id, users.email AS email, users.is_pro AS is_pro
            FROM sessions JOIN users ON sessions.user_id = users.id
            WHERE sessions.token = ?
            """,
            (token,),
        ).fetchone()
        if row is None:
            return None
        return {"id": row["id"], "email": row["email"], "is_pro": bool(row["is_pro"])}
    finally:
        conn.close()


def delete_session(token: str) -> None:
    conn = _connect()
    try:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
    finally:
        conn.close()


def set_pro(user_id: int, is_pro: bool) -> None:
    conn = _connect()
    try:
        conn.execute("UPDATE users SET is_pro = ? WHERE id = ?", (1 if is_pro else 0, user_id))
        conn.commit()
    finally:
        conn.close()
