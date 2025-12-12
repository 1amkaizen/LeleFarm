# routes/dashboard/pakan_stok.py
# Lokasi file: routes/dashboard/pakan_stok.py

import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from services import pakan_stok

router = APIRouter()
logger = logging.getLogger("router_pakan_stok")
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard/pakan_stok", response_class=HTMLResponse)
async def pakan_stok_page(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Akses /dashboard/pakan_stok ditolak: user belum login.")
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)
    stok_list = await pakan_stok.get_all_pakan_stok(user_id=user_id)

    total_jumlah_g = 0
    total_harga = 0
    for p in stok_list:
        satuan = p.get("satuan") or "g"
        jumlah_g = float(p["jumlah"]) * 1000 if satuan == "kg" else float(p["jumlah"])
        total_jumlah_g += jumlah_g
        total_harga += float(p["harga"])

    logger.info(
        f"[USER {user_id}] Render pakan_stok_page: {len(stok_list)} data ditemukan"
    )

    return templates.TemplateResponse(
        "dashboard/pakan_stok.html",
        {
            "request": request,
            "stok_list": stok_list,
            "total_jumlah_g": total_jumlah_g,
            "total_harga": total_harga,
        },
    )


@router.post("/dashboard/pakan_stok/add")
async def pakan_stok_add(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)
    form = await request.form()
    nama_pakan = form.get("nama_pakan")
    jumlah_str = form.get("jumlah", "0").strip()
    satuan = form.get("satuan", "g")
    try:
        jumlah = float(jumlah_str)
    except ValueError:
        jumlah = 0
    harga = float(form.get("harga", 0))
    tanggal_masuk = form.get("tanggal_masuk")

    added = await pakan_stok.add_pakan_stok(
        user_id, nama_pakan, jumlah, harga, tanggal_masuk, satuan
    )
    if not added:
        logger.error(f"[USER {user_id}] Gagal tambah stok pakan {nama_pakan}")

    return RedirectResponse("/dashboard/pakan_stok", status_code=303)


@router.post("/dashboard/pakan_stok/edit")
async def pakan_stok_edit(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)
    form = await request.form()
    pakan_stok_id = int(form.get("pakan_stok_id"))
    nama_pakan = form.get("nama_pakan")
    jumlah_str = form.get("jumlah", "0").strip()
    satuan = form.get("satuan", "g")
    try:
        jumlah = float(jumlah_str)
    except ValueError:
        jumlah = 0
    harga = float(form.get("harga", 0))
    tanggal_masuk = form.get("tanggal_masuk")

    updated = await pakan_stok.edit_pakan_stok(
        user_id, pakan_stok_id, nama_pakan, jumlah, harga, tanggal_masuk, satuan
    )
    if updated:
        logger.info(f"[USER {user_id}] Stok {pakan_stok_id} diedit")
    else:
        logger.error(f"[USER {user_id}] Gagal edit stok {pakan_stok_id}")

    return RedirectResponse("/dashboard/pakan_stok", status_code=303)


@router.post("/dashboard/pakan_stok/delete")
async def pakan_stok_delete(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)
    form = await request.form()
    pakan_stok_id = int(form.get("pakan_stok_id"))

    success = await pakan_stok.delete_pakan_stok(user_id, pakan_stok_id)
    if success:
        logger.info(f"[USER {user_id}] Stok {pakan_stok_id} dihapus")
    else:
        logger.error(f"[USER {user_id}] Gagal hapus stok {pakan_stok_id}")

    return RedirectResponse("/dashboard/pakan_stok", status_code=303)
