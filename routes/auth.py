# routes/auth.py
# Router untuk registrasi, login, dan logout user

import logging
from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from passlib.hash import bcrypt
import re

from lib.supabase_client import get_db

router = APIRouter()
logger = logging.getLogger("router_auth")


# =========================
# FORM REGISTER (GET)
# =========================
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    logger.info("Mengakses halaman register...")
    return request.app.templates.TemplateResponse("register.html", {"request": request})


# =========================
# AKSI REGISTER (POST)
# =========================
@router.post("/register")
async def register_action(
    request: Request,
    username: str = Form(...),
    fullname: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    db = get_db()

    logger.info(f"Proses register user: {username}")

    # =========================
    # VALIDASI INPUT
    # =========================

    # Bersihkan input
    username = username.strip()
    fullname = fullname.strip()
    email = email.strip()

    if len(fullname) < 3:
        raise HTTPException(status_code=400, detail="Nama lengkap minimal 3 karakter")

    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username minimal 3 karakter")

    if " " in username:
        raise HTTPException(
            status_code=400, detail="Username tidak boleh mengandung spasi"
        )

    # Validasi email simple
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(status_code=400, detail="Format email tidak valid")

    # Validasi password
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password minimal 6 karakter")

    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Konfirmasi password tidak cocok")

    # =========================
    # CEK USERNAME / EMAIL SUDAH ADA
    # =========================
    exists_username = db.table("Users").select("*").eq("username", username).execute()
    if exists_username.data:
        raise HTTPException(status_code=400, detail="Username sudah dipakai.")

    exists_email = db.table("Users").select("*").eq("email", email).execute()
    if exists_email.data:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar.")

    # Hash password
    hashed = bcrypt.hash(password)

    # Insert user baru
    db.table("Users").insert(
        {"fullname": fullname, "email": email, "username": username, "password": hashed}
    ).execute()

    logger.info(f"User berhasil dibuat: {username}")

    return RedirectResponse(url="/login", status_code=303)


# =========================
# FORM LOGIN (GET)
# =========================
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    logger.info("Mengakses halaman login...")
    return request.app.templates.TemplateResponse("login.html", {"request": request})


# =========================
# AKSI LOGIN (POST)
# =========================
@router.post("/login")
async def login_action(
    request: Request,
    username: str = Form(...),  # email atau username
    password: str = Form(...),
):
    db = get_db()
    logger.info(f"Proses login user: {username}")

    error_message = None

    # =========================
    # DETEKSI EMAIL / USERNAME
    # =========================
    is_email = "@" in username

    if is_email:
        logger.info("Login menggunakan email")
        result = db.table("Users").select("*").eq("email", username).single().execute()
    else:
        logger.info("Login menggunakan username")
        result = (
            db.table("Users").select("*").eq("username", username).single().execute()
        )

    # =========================
    # USER TIDAK DITEMUKAN
    # =========================
    if not result.data:
        logger.warning("Login gagal: akun tidak ditemukan")
        error_message = "Akun tidak ditemukan"
        return request.app.templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": error_message,
                "username": username,  # biar input gak kosong
            },
        )

    user = result.data

    # =========================
    # PASSWORD SALAH
    # =========================
    if not bcrypt.verify(password, user["password"]):
        logger.warning("Login gagal: password salah")
        error_message = "Password salah"
        return request.app.templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": error_message,
                "username": username,
            },
        )

    logger.info(f"User login berhasil: {user['username']}")

    # =========================
    # SET COOKIE & REDIRECT
    # =========================
    response = RedirectResponse(url="/dashboard", status_code=303)

    response.set_cookie(
        "user_id",
        str(user["id"]),
        httponly=True,
        max_age=86400,
        samesite="Strict",
    )

    return response


# =========================
# LOGOUT
# =========================
@router.get("/logout")
async def logout(request: Request):
    logger.info("User melakukan logout...")

    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("user_id")

    return response
