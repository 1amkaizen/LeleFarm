# routes/dashboard/pakan_stok.py
# Lokasi file: routes/dashboard/pakan_stok.py

import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from services import pakan_stok, kolam  # kolam service untuk ambil list kolam

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

    # ambil daftar kolam untuk dropdown
    kolam_list = await kolam.get_all_kolam(user_id)

    # ambil stok pakan, bisa difilter kolam jika query param ada
    kolam_id = request.query_params.get("kolam_id")
    kolam_id = int(kolam_id) if kolam_id else None

    stok_list = await pakan_stok.get_all_pakan_stok(user_id=user_id, kolam_id=kolam_id)

    total_jumlah_g = 0
    total_harga = 0
    for p in stok_list:
        satuan = p.get("satuan") or "g"
        jumlah_g = float(p["jumlah"]) * 1000 if satuan == "kg" else float(p["jumlah"])
        total_jumlah_g += jumlah_g
        total_harga += float(p["harga"])

    total_jumlah_kg = int(total_jumlah_g / 1000)  # buang desimal

    logger.info(
        f"[USER {user_id}] Render pakan_stok_page: {len(stok_list)} data ditemukan"
    )

    return templates.TemplateResponse(
        "dashboard/pakan_stok.html",
        {
            "request": request,
            "stok_list": stok_list,
            "total_jumlah_kg": total_jumlah_kg,
            "total_harga": total_harga,
            "kolam_list": kolam_list,  # untuk dropdown
            "selected_kolam_id": kolam_id,
        },
    )


# routes/dashboard/pakan_stok.py


@router.post("/dashboard/pakan_stok/add")
async def pakan_stok_add(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Submit pakan_stok ditolak: user belum login.")
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)
    form = await request.form()

    nama_pakan = form.get("nama_pakan")
    jumlah_str = (form.get("jumlah") or "0").strip()
    satuan = form.get("satuan", "g")

    kolam_id = form.get("kolam_id")
    kolam_id = int(kolam_id) if kolam_id else None

    # ===============================
    # VALIDASI WAJIB: KOLAM HARUS ADA
    # ===============================
    if not kolam_id:
        logger.warning(
            f"[PAKAN_STOK] Gagal submit: kolam belum dipilih user_id={user_id}"
        )
        return RedirectResponse(
            "/dashboard/pakan_stok?error=kolam_kosong",
            status_code=303,
        )

    try:
        jumlah = float(jumlah_str)
    except ValueError:
        jumlah = 0

    harga = float(form.get("harga") or 0)
    tanggal_masuk = form.get("tanggal_masuk")

    added = await pakan_stok.add_pakan_stok(
        user_id=user_id,
        nama_pakan=nama_pakan,
        jumlah=jumlah,
        harga=harga,
        kolam_id=kolam_id,
        tanggal_masuk=tanggal_masuk,
        satuan=satuan,
    )

    if added:
        logger.info(f"[USER {user_id}] Stok pakan ditambahkan: {nama_pakan}")
    else:
        logger.error(f"[USER {user_id}] Gagal tambah stok pakan: {nama_pakan}")

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
    kolam_id = form.get("kolam_id")
    kolam_id = int(kolam_id) if kolam_id else None
    try:
        jumlah = float(jumlah_str)
    except ValueError:
        jumlah = 0
    harga = float(form.get("harga", 0))
    tanggal_masuk = form.get("tanggal_masuk")

    updated = await pakan_stok.edit_pakan_stok(
        user_id,
        pakan_stok_id,
        nama_pakan,
        jumlah,
        harga,
        kolam_id,
        tanggal_masuk,
        satuan,
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
