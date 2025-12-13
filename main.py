# main.py
# File utama menjalankan FastAPI + Template

import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from routes.home import router as home_router
from routes.auth import router as auth_router
from routes.dashboard import router as dashboard_router
from routes.kolam import router as kolam_router
from routes.pengeluaran import router as pengeluaran_router
from routes.kematian import router as kematian_router
from routes .pakan import router as pakan_router
from routes.bibit import router as bibit_router
from routes.pakan_stok import router as pakan_stok_router
from routes.prediksi import router as prediksi_router
from routes.ringkasan import router as ringkasan_router
from routes.perhitungan_pakan import router as perhitungan_pakan_router


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main_app")

app = FastAPI(title="Kolam Lele Dashboard")
logger.info("Inisialisasi aplikasi FastAPI...")

# =============================
# Session Middleware
# =============================
# Untuk session (penyimpanan user login)
app.add_middleware(
    SessionMiddleware,
    secret_key="kolam_lele_super_secret_key_123",  # bebas, jangan kosong
)

# =============================
# Static folder
# =============================
app.mount("/static", StaticFiles(directory="static"), name="static")

# =============================
# Template folder
# =============================
app.templates = Jinja2Templates(directory="templates")

# =============================
# Router
# =============================
app.include_router(home_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(kolam_router)
app.include_router(pengeluaran_router)
app.include_router(kematian_router)
app.include_router(pakan_router)
app.include_router(bibit_router)
app.include_router(pakan_stok_router)
app.include_router(prediksi_router)
app.include_router(ringkasan_router)
app.include_router(perhitungan_pakan_router)


# Handler untuk 404
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        # Render template 404.html
        return app.templates.TemplateResponse(
            "404.html", {"request": request}, status_code=404
        )
    # kalau error lain, bisa return default
    return HTMLResponse(content=str(exc.detail), status_code=exc.status_code)
