# routes/dashboard/kolam.py
# Lokasi file: routes/dashboard/kolam.py

import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from services.kolam import (
    get_all_kolam,
    create_kolam,
    edit_kolam,
    delete_kolam,
    update_status_kolam,  # <-- TAMBAHAN
)

router = APIRouter()
logger = logging.getLogger("router_kolam")
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard/kolam", response_class=HTMLResponse)
async def kolam_page(request: Request):
    # --- Ambil user_id dari cookies ---
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Akses /dashboard/kolam ditolak: user belum login.")
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)

    # --- Ambil kolam sesuai user ---
    kolam_list = await get_all_kolam(user_id=user_id)

    # Status sudah dari database, tidak dihitung lagi
    logger.info(f"[KOLAM] Render kolam_page user_id={user_id}, total={len(kolam_list)}")

    return templates.TemplateResponse(
        "dashboard/kolam.html",
        {
            "request": request,
            "kolam_list": kolam_list,
        },
    )


@router.post("/dashboard/kolam")
async def kolam_submit(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)
    form = await request.form()

    kolam_baru = form.get("kolam_baru")
    kapasitas_bibit = int(form.get("kapasitas_bibit") or 0)
    tanggal_mulai = form.get("tanggal_mulai")
    catatan = form.get("catatan")

    logger.info(f"[USER {user_id}] Submit kolam baru: {kolam_baru}")

    if kolam_baru:
        kolam = await create_kolam(
            user_id=user_id,
            nama_kolam=kolam_baru,
            kapasitas_bibit=kapasitas_bibit,
            tanggal_mulai=tanggal_mulai,
            catatan=catatan,
        )

        if not kolam:
            logger.error(f"[USER {user_id}] Gagal buat kolam baru")
            return HTMLResponse("Gagal buat kolam baru", status_code=400)

        logger.info(f"[USER {user_id}] Kolam dibuat id={kolam['id']}")

    return RedirectResponse("/dashboard/kolam", status_code=303)


@router.post("/dashboard/kolam/edit")
async def kolam_edit(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)
    form = await request.form()

    kolam_id = int(form.get("kolam_id"))
    nama_kolam = form.get("nama_kolam")
    kapasitas_bibit = form.get("kapasitas_bibit")
    tanggal_mulai = form.get("tanggal_mulai")
    catatan = form.get("catatan")

    if kapasitas_bibit:
        kapasitas_bibit = int(kapasitas_bibit)

    updated = await edit_kolam(
        user_id=user_id,
        kolam_id=kolam_id,
        nama_kolam=nama_kolam,
        kapasitas_bibit=kapasitas_bibit,
        tanggal_mulai=tanggal_mulai,
        catatan=catatan,
    )

    if updated:
        logger.info(f"[USER {user_id}] Kolam {kolam_id} berhasil diedit")
    else:
        logger.error(f"[USER {user_id}] Gagal edit kolam {kolam_id}")

    return RedirectResponse("/dashboard/kolam", status_code=303)


@router.post("/dashboard/kolam/status")
async def kolam_update_status(request: Request):
    """
    Update status kolam: belum / sudah
    """
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)
    form = await request.form()

    kolam_id = int(form.get("kolam_id"))
    status = form.get("status")

    logger.info(f"[USER {user_id}] Update status kolam id={kolam_id} -> {status}")

    updated = await update_status_kolam(
        user_id=user_id,
        kolam_id=kolam_id,
        status=status,
    )

    if not updated:
        logger.error(f"[USER {user_id}] Gagal update status kolam id={kolam_id}")

    return RedirectResponse("/dashboard/kolam", status_code=303)


@router.post("/dashboard/kolam/delete")
async def kolam_delete(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)
    form = await request.form()

    kolam_id = int(form.get("kolam_id"))

    success = await delete_kolam(kolam_id, user_id=user_id)

    if success:
        logger.info(f"[USER {user_id}] Kolam {kolam_id} dihapus")
    else:
        logger.error(f"[USER {user_id}] Gagal hapus kolam {kolam_id}")

    return RedirectResponse("/dashboard/kolam", status_code=303)
