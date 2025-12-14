# routes/dashboard/pengeluaran.py
# Lokasi file: routes/dashboard/pengeluaran.py

import logging
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from services.pengeluaran import (
    get_all_pengeluaran,
    create_pengeluaran,
    update_pengeluaran,
    delete_pengeluaran,
)
from services.kolam import get_all_kolam  # ambil list kolam user

router = APIRouter()
logger = logging.getLogger("router_pengeluaran")
templates = Jinja2Templates(directory="templates")


# ============================================================
# HALAMAN DAFTAR PENGELUARAN
# ============================================================
@router.get("/dashboard/pengeluaran", response_class=HTMLResponse)
async def pengeluaran_page(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Akses halaman pengeluaran ditolak: user belum login.")
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)
    pengeluaran_list = [dict(p) for p in await get_all_pengeluaran(user_id)]
    kolam_list = await get_all_kolam(user_id)

    for p in pengeluaran_list:
        p["harga"] = float(p.get("harga", 0))
        p["jumlah"] = int(p.get("jumlah", 0))
        p["total"] = p["harga"] * p["jumlah"]

    grand_total = sum(p["total"] for p in pengeluaran_list)

    logger.info(
        f"[USER {user_id}] Render pengeluaran_page: {len(pengeluaran_list)} item"
    )

    return templates.TemplateResponse(
        "dashboard/pengeluaran.html",
        {
            "request": request,
            "pengeluaran_list": pengeluaran_list,
            "grand_total": grand_total,
            "kolam_list": kolam_list,  # untuk dropdown kolam
        },
    )


# ============================================================
# TAMBAH PENGELUARAN
# ============================================================
@router.post("/dashboard/pengeluaran")
async def pengeluaran_submit(
    request: Request,
    nama: str = Form(...),
    harga: float = Form(...),
    jumlah: int = Form(1),
    tanggal: str = Form(...),
    catatan: str = Form(None),
    kolam_id: int = Form(None),  # baru
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Submit pengeluaran ditolak: user belum login.")
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)
    logger.info(
        f"[USER {user_id}] Tambah pengeluaran: nama={nama}, harga={harga}, jumlah={jumlah}, kolam_id={kolam_id}"
    )

    result = await create_pengeluaran(
        user_id=user_id,
        nama_pengeluaran=nama,
        harga=harga,
        jumlah=jumlah,
        tanggal=tanggal,
        catatan=catatan,
        kolam_id=kolam_id,
    )

    if result:
        logger.info(f"[USER {user_id}] Pengeluaran berhasil ditambahkan")
    else:
        logger.error(f"[USER {user_id}] Gagal tambah pengeluaran")

    return RedirectResponse("/dashboard/pengeluaran", status_code=303)


# ============================================================
# EDIT PENGELUARAN
# ============================================================
@router.post("/dashboard/pengeluaran/edit")
async def pengeluaran_edit(
    request: Request,
    pengeluaran_id: int = Form(...),
    nama: str = Form(None),
    harga: float = Form(None),
    jumlah: int = Form(None),
    tanggal: str = Form(None),
    catatan: str = Form(None),
    kolam_id: int = Form(None),  # baru
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Edit pengeluaran ditolak: user belum login.")
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)
    logger.info(f"[USER {user_id}] Edit pengeluaran_id={pengeluaran_id}")

    result = await update_pengeluaran(
        pengeluaran_id=pengeluaran_id,
        user_id=user_id,
        nama_pengeluaran=nama,
        harga=harga,
        jumlah=jumlah,
        tanggal=tanggal,
        catatan=catatan,
        kolam_id=kolam_id,
    )

    if result:
        logger.info(
            f"[USER {user_id}] Pengeluaran_id={pengeluaran_id} berhasil diupdate"
        )
    else:
        logger.warning(f"[USER {user_id}] Gagal update pengeluaran_id={pengeluaran_id}")

    return RedirectResponse("/dashboard/pengeluaran", status_code=303)


# ============================================================
# HAPUS PENGELUARAN
# ============================================================
@router.post("/dashboard/pengeluaran/delete")
async def pengeluaran_delete(request: Request, pengeluaran_id: int = Form(...)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Hapus pengeluaran ditolak: user belum login.")
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)
    logger.info(f"[USER {user_id}] Hapus pengeluaran_id={pengeluaran_id}")

    success = await delete_pengeluaran(pengeluaran_id=pengeluaran_id, user_id=user_id)
    if success:
        logger.info(
            f"[USER {user_id}] Pengeluaran_id={pengeluaran_id} berhasil dihapus"
        )
    else:
        logger.warning(f"[USER {user_id}] Gagal hapus pengeluaran_id={pengeluaran_id}")

    return RedirectResponse("/dashboard/pengeluaran", status_code=303)
