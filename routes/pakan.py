# routes/dashboard/pakan.py
# Lokasi file: routes/dashboard/pakan.py

import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from services.kolam import get_all_kolam
from services import pakan
from services import pakan_stok

router = APIRouter()
logger = logging.getLogger("router_pakan")
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard/pakan", response_class=HTMLResponse)
async def pakan_page(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Akses /dashboard/pakan ditolak: user belum login.")
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)

    kolam_list = await get_all_kolam(user_id=user_id)
    pakan_list = await pakan.get_all_pakan(user_id=user_id)
    pakan_stok_list = await pakan_stok.get_all_pakan_stok(user_id=user_id)

    kolam_dict = {k["id"]: k["nama_kolam"] for k in kolam_list}
    for p in pakan_list:
        p["kolam_nama"] = kolam_dict.get(p["kolam_id"], "Unknown")

    logger.info(f"[USER {user_id}] Render pakan_page: {len(pakan_list)} data ditemukan")

    return templates.TemplateResponse(
        "dashboard/pakan.html",
        {
            "request": request,
            "kolam_list": kolam_list,
            "pakan_list": pakan_list,
            "pakan_stok_list": pakan_stok_list,
        },
    )


@router.post("/dashboard/pakan/add")
async def pakan_add(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    user_id = int(user_id)

    form = await request.form()
    kolam_id = int(form.get("kolam_id"))
    tanggal = form.get("tanggal")
    pakan_stok_id = int(form.get("pakan_stok_id"))
    jumlah = float(form.get("jumlah") or 0)
    satuan = form.get("satuan")
    catatan = form.get("catatan")

    # Ambil nama pakan dari stok
    stok_list = await pakan_stok.get_all_pakan_stok(user_id=user_id)
    stok_dict = {s["id"]: s["nama_pakan"] for s in stok_list}
    jenis_pakan = stok_dict.get(pakan_stok_id, "Unknown")

    jumlah_gram = jumlah * 1000 if satuan == "kg" else jumlah

    logger.info(
        f"[USER {user_id}] Tambah pakan kolam={kolam_id}, pakan='{jenis_pakan}', jumlah={jumlah_gram}g"
    )

    added = await pakan.add_pakan(
        kolam_id=kolam_id,
        tanggal=tanggal,
        jenis_pakan=jenis_pakan,
        jumlah_gram=jumlah_gram,
        catatan=catatan,
        user_id=user_id,
    )

    if not added:
        logger.error(f"[USER {user_id}] Gagal tambah pakan")
    return RedirectResponse("/dashboard/pakan", status_code=303)


@router.post("/dashboard/pakan/edit")
async def pakan_edit(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    user_id = int(user_id)

    form = await request.form()
    pakan_id = int(form.get("pakan_id"))
    kolam_id = int(form.get("kolam_id"))
    tanggal = form.get("tanggal")

    # Validasi pakan_stok_id
    pakan_stok_id_str = form.get("pakan_stok_id")
    if pakan_stok_id_str is None or pakan_stok_id_str == "":
        logger.error(f"[USER {user_id}] PemberianPakan Stok ID tidak ditemukan atau kosong")
        return RedirectResponse("/dashboard/pakan", status_code=303)

    pakan_stok_id = int(pakan_stok_id_str)  # Sekarang aman untuk di-convert

    jumlah = float(form.get("jumlah") or 0)
    satuan = form.get("satuan")
    catatan = form.get("catatan")

    # Ambil nama pakan dari stok
    stok_list = await pakan_stok.get_all_pakan_stok(user_id=user_id)
    stok_dict = {s["id"]: s["nama_pakan"] for s in stok_list}
    jenis_pakan = stok_dict.get(pakan_stok_id, "Unknown")

    jumlah_gram = jumlah * 1000 if satuan == "kg" else jumlah

    updated = await pakan.edit_pakan(
        pakan_id=pakan_id,
        kolam_id=kolam_id,
        tanggal=tanggal,
        jenis_pakan=jenis_pakan,
        jumlah_gram=jumlah_gram,
        catatan=catatan,
        user_id=user_id,
    )

    if updated:
        logger.info(
            f"[USER {user_id}] PemberianPakan {pakan_id} diedit: pakan='{jenis_pakan}', jumlah={jumlah_gram}g"
        )
    else:
        logger.error(f"[USER {user_id}] Gagal edit pakan {pakan_id}")

    # Ambil ulang data setelah edit
    kolam_list = await get_all_kolam(user_id=user_id)
    pakan_list = await pakan.get_all_pakan(user_id=user_id)
    pakan_stok_list = await pakan_stok.get_all_pakan_stok(user_id=user_id)

    kolam_dict = {k["id"]: k["nama_kolam"] for k in kolam_list}
    for p in pakan_list:
        p["kolam_nama"] = kolam_dict.get(p["kolam_id"], "Unknown")

    return templates.TemplateResponse(
        "dashboard/pakan.html",
        {
            "request": request,
            "kolam_list": kolam_list,
            "pakan_list": pakan_list,
            "pakan_stok_list": pakan_stok_list,
        },
    )


@router.post("/dashboard/pakan/delete")
async def pakan_delete(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    user_id = int(user_id)

    form = await request.form()
    pakan_id = int(form.get("pakan_id"))

    # Panggil delete_pakan tanpa mengirimkan user_id lagi, karena sudah ada di cookies
    success = await pakan.delete_pakan(pakan_id, user_id)

    if success:
        logger.info(f"[USER {user_id}] PemberianPakan {pakan_id} dihapus")
    else:
        logger.error(f"[USER {user_id}] Gagal hapus pakan {pakan_id}")

    return RedirectResponse("/dashboard/pakan", status_code=303)
