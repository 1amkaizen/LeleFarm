# routes/dashboard/bibit.py
# Lokasi file: routes/dashboard/bibit.py

import logging
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from services.bibit import get_all_bibit, create_bibit
from services.kolam import get_all_kolam

router = APIRouter()
logger = logging.getLogger("router_bibit")
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard/bibit", response_class=HTMLResponse)
async def bibit_page(request: Request):
    """Halaman input bibit & daftar riwayat bibit."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Akses halaman bibit ditolak: user belum login.")
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)

    # WAJIB await kalau service async
    kolam_list = await get_all_kolam(user_id)
    bibit_list = await get_all_bibit(user_id)

    kolam_list = [dict(k) for k in kolam_list]
    bibit_list = [dict(b) for b in bibit_list]

    kolam_dict = {k["id"]: k["nama_kolam"] for k in kolam_list}

    for b in bibit_list:
        b["nama_kolam"] = kolam_dict.get(b["kolam_id"], f"ID {b['kolam_id']}")

    total_bibit = sum(int(b.get("jumlah", 0)) for b in bibit_list)

    return templates.TemplateResponse(
        "dashboard/bibit.html",
        {
            "request": request,
            "kolam_list": kolam_list,
            "bibit_list": bibit_list,
            "total_bibit": total_bibit,
        },
    )


@router.post("/dashboard/bibit")
async def bibit_submit(
    request: Request,
    kolam_id: int = Form(...),
    ukuran_bibit: str = Form(...),
    jumlah: int = Form(...),
    total_harga: float = Form(0),
    catatan: str = Form(None),
    tanggal_tebar: str = Form(None),
):
    """Submit data bibit per user."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Submit bibit ditolak: user belum login.")
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)

    result = await create_bibit(
        kolam_id=kolam_id,
        ukuran_bibit=ukuran_bibit,
        jumlah=jumlah,
        total_harga=total_harga,
        catatan=catatan,
        tanggal_tebar=tanggal_tebar,
        user_id=user_id,
    )


    if result:
        logger.info(f"[BIBIT] Bibit berhasil ditambahkan user_id={user_id}: {result}")
    else:
        logger.error("[BIBIT] Gagal menambahkan data bibit")

    return RedirectResponse("/dashboard/bibit", status_code=303)
