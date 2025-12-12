# routes/home.py


import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()
logger = logging.getLogger("router_home")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Log akses halaman utama
    logger.info("Mengakses halaman landing ...")

    # Render template index.html
    return request.app.templates.TemplateResponse("index.html", {"request": request})
