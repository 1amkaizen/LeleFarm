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


# ============================================================
# HALAMAN KEMATIAN
# ============================================================
@router.get("/dashboard/kematian", response_class=HTMLResponse)
async def kematian_page(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Akses kematian ditolak: user belum login")
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)

    kolam_list = [dict(k) for k in await get_all_kolam(user_id)]
    kematian_list = [dict(k) for k in await get_all_kematian(user_id)]

    kolam_dict = {k["id"]: k["nama_kolam"] for k in kolam_list}

    for k in kematian_list:
        k["nama_kolam"] = kolam_dict.get(k["kolam_id"], "-")

    total_kematian = sum(int(k.get("jumlah", 0)) for k in kematian_list)

    logger.info(f"[USER {user_id}] Render kematian_page ({len(kematian_list)} data)")

    return templates.TemplateResponse(
        "dashboard/kematian.html",
        {
            "request": request,
            "kolam_list": kolam_list,
            "kematian_list": kematian_list,
            "total_kematian": total_kematian,
        },
    )


# ============================================================
# TAMBAH KEMATIAN
# ============================================================
@router.post("/dashboard/kematian")
async def kematian_submit(
    request: Request,
    kolam_id: int | None = Form(None),
    tanggal: str = Form(...),
    jumlah: int = Form(...),
    catatan: str = Form(None),
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Submit kematian ditolak: user belum login")
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)

    # ================= VALIDASI WAJIB: KOLAM DIPILIH =================
    if not kolam_id:
        logger.warning(f"[USER {user_id}] Submit kematian gagal: kolam belum dipilih")
        return RedirectResponse(
            "/dashboard/kematian?error=kolam_kosong",
            status_code=303,
        )

    # ================= VALIDASI: KOLAM MILIK USER =================
    kolam_list = await get_all_kolam(user_id)
    kolam_ids = {k["id"] for k in kolam_list}
    if kolam_id not in kolam_ids:
        logger.warning(f"[USER {user_id}] Kolam_id tidak valid saat submit kematian")
        return RedirectResponse("/dashboard/kematian", status_code=303)

    logger.info(
        f"[USER {user_id}] Tambah kematian | kolam_id={kolam_id} | jumlah={jumlah}"
    )

    await create_kematian(
        kolam_id=kolam_id,
        tanggal=tanggal,
        jumlah=jumlah,
        catatan=catatan,
        user_id=user_id,
    )

    return RedirectResponse("/dashboard/kematian", status_code=303)


# ============================================================
# EDIT KEMATIAN
# ============================================================
@router.post("/dashboard/kematian/edit")
async def kematian_edit(
    request: Request,
    kematian_id: int = Form(...),
    kolam_id: int | None = Form(None),
    tanggal: str = Form(None),
    jumlah: int = Form(None),
    catatan: str = Form(None),
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Edit kematian ditolak: user belum login")
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)

    # ================= VALIDASI KOLAM (JIKA DIUBAH) =================
    if kolam_id:
        kolam_list = await get_all_kolam(user_id)
        kolam_ids = {k["id"] for k in kolam_list}
        if kolam_id not in kolam_ids:
            logger.warning(f"[USER {user_id}] Kolam_id tidak valid saat edit kematian")
            return RedirectResponse("/dashboard/kematian", status_code=303)
    else:
        kolam_id = None

    logger.info(f"[USER {user_id}] Edit kematian_id={kematian_id}, kolam_id={kolam_id}")

    await update_kematian(
        kematian_id=kematian_id,
        user_id=user_id,
        kolam_id=kolam_id,
        tanggal=tanggal,
        jumlah=jumlah,
        catatan=catatan,
    )

    return RedirectResponse("/dashboard/kematian", status_code=303)


# ============================================================
# DELETE KEMATIAN
# ============================================================
@router.post("/dashboard/kematian/delete")
async def kematian_delete(
    request: Request,
    kematian_id: int = Form(...),
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Hapus kematian ditolak: user belum login")
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)

    logger.info(f"[USER {user_id}] Hapus kematian_id={kematian_id}")

    await delete_kematian(
        kematian_id=kematian_id,
        user_id=user_id,
    )

    return RedirectResponse("/dashboard/kematian", status_code=303)
