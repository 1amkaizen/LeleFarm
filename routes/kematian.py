# routes/dashboard/kematian.py
# Lokasi file: routes/dashboard/kematian.py

import logging
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from services.kematian import (
    get_all_kematian,
    create_kematian,
    update_kematian,
    delete_kematian,
)
from services.kolam import get_all_kolam

router = APIRouter()
logger = logging.getLogger("router_kematian")
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard/kematian", response_class=HTMLResponse)
async def kematian_page(request: Request):
    """
    Halaman riwayat kematian, filter berdasarkan user melalui cookies.
    """
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Akses halaman kematian ditolak: user belum login.")
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)

    # --- Ambil data kolam & kematian berdasarkan user ---
    kolam_list = [dict(k) for k in await get_all_kolam(user_id)]
    kematian_list = [dict(k) for k in await get_all_kematian(user_id)]

    # Mapping kolam_id → nama
    kolam_dict = {k["id"]: k["nama_kolam"] for k in kolam_list}

    for k in kematian_list:
        k["kolam_nama"] = kolam_dict.get(k["kolam_id"], f"ID {k['kolam_id']}")

    total_kematian = sum(int(k.get("jumlah", 0)) for k in kematian_list)

    logger.info(f"[USER {user_id}] Render kematian_page: {len(kematian_list)} data")

    return templates.TemplateResponse(
        "dashboard/kematian.html",
        {
            "request": request,
            "kolam_list": kolam_list,
            "kematian_list": kematian_list,
            "total_kematian": total_kematian,
        },
    )


@router.post("/dashboard/kematian")
async def kematian_submit(
    request: Request,
    kolam_id: int = Form(...),
    tanggal: str = Form(...),
    jumlah: int = Form(...),
    catatan: str = Form(None),
):
    """
    Submit data kematian berbasis user_id dari cookies.
    """
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Submit kematian ditolak: user belum login.")
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)

    logger.info(f"[USER {user_id}] Tambah kematian: kolam={kolam_id}, jumlah={jumlah}")

    result = await create_kematian(
        kolam_id=kolam_id,
        tanggal=tanggal,
        jumlah=jumlah,
        catatan=catatan,
        user_id=user_id,
    )

    if not result:
        logger.error(f"[USER {user_id}] Gagal tambah kematian")
    else:
        logger.info(f"[USER {user_id}] Kematian berhasil ditambahkan")

    return RedirectResponse("/dashboard/kematian", status_code=303)


# ============================================================
# EDIT KEMATIAN
# ============================================================
@router.post("/dashboard/kematian/edit")
async def kematian_edit(
    request: Request,
    kematian_id: int = Form(...),
    kolam_id: int = Form(None),
    tanggal: str = Form(None),
    jumlah: int = Form(None),
    catatan: str = Form(None),
):
    """
    Edit data kematian berdasarkan user_id dari cookies
    """
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Edit kematian ditolak: user belum login.")
        return RedirectResponse("/login", status_code=303)
    user_id = int(user_id)

    result = await update_kematian(
        kematian_id=kematian_id,
        user_id=user_id,
        kolam_id=kolam_id,
        tanggal=tanggal,
        jumlah=jumlah,
        catatan=catatan,
    )

    if result:
        logger.info(f"[USER {user_id}] Kematian_id={kematian_id} berhasil diupdate")
    else:
        logger.error(f"[USER {user_id}] Gagal update kematian_id={kematian_id}")

    return RedirectResponse("/dashboard/kematian", status_code=303)


# ============================================================
# DELETE KEMATIAN
# ============================================================
@router.post("/dashboard/kematian/delete")
async def kematian_delete(request: Request, kematian_id: int = Form(...)):
    """
    Hapus data kematian berdasarkan user_id dari cookies
    """
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Hapus kematian ditolak: user belum login.")
        return RedirectResponse("/login", status_code=303)
    user_id = int(user_id)

    success = await delete_kematian(kematian_id=kematian_id, user_id=user_id)

    if success:
        logger.info(f"[USER {user_id}] Kematian_id={kematian_id} berhasil dihapus")
    else:
        logger.error(f"[USER {user_id}] Gagal hapus kematian_id={kematian_id}")

    return RedirectResponse("/dashboard/kematian", status_code=303)
