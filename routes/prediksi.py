# routes/dashboard/prediksi.py
# Lokasi file: routes/dashboard/prediksi.py

import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
logger = logging.getLogger("router_prediksi")
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard/prediksi", response_class=HTMLResponse)
async def prediksi_page(request: Request):
    logger.info("Render halaman prediksi tanpa ambil data")
    return templates.TemplateResponse(
        "dashboard/prediksi.html",
        {"request": request},
    )
