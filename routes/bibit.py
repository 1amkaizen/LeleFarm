# routes/dashboard/bibit.py
import logging
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from services.bibit import get_all_bibit, create_bibit, edit_bibit, delete_bibit
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

    kolam_list = await get_all_kolam(user_id)
    bibit_list = await get_all_bibit(user_id)

    kolam_list = [dict(k) for k in kolam_list]
    bibit_list = [dict(b) for b in bibit_list]

    kolam_dict = {k["id"]: k["nama_kolam"] for k in kolam_list}

    # Menambahkan nama kolam dan total_berat ke dalam data bibit
    for b in bibit_list:
        b["nama_kolam"] = kolam_dict.get(b["kolam_id"], f"ID {b['kolam_id']}")
        b["total_berat"] = b.get("total_berat", 0)

    total_bibit = sum(int(b.get("jumlah", 0)) for b in bibit_list)
    total_berat = sum(float(b.get("total_berat", 0)) for b in bibit_list)

    # List ukuran bibit untuk mapping di template
    ukuran_list = [
        "2-3 cm",
        "3-4 cm",
        "3-5 cm",
        "4-6 cm",
        "4-7 cm",
        "5-7 cm",
        "6-8 cm",
        "7-9 cm",
        "9-12 cm",
    ]

    return templates.TemplateResponse(
        "dashboard/bibit.html",
        {
            "request": request,
            "kolam_list": kolam_list,
            "bibit_list": bibit_list,
            "total_bibit": total_bibit,
            "total_berat": total_berat,
            "ukuran_list": ukuran_list,  # <-- kirim ke template
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
    total_berat: float = Form(0),  # Terima parameter total_berat
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
        total_berat=total_berat,  # Sertakan total_berat saat menambahkan bibit
    )

    if result:
        logger.info(f"[BIBIT] Bibit berhasil ditambahkan user_id={user_id}: {result}")
    else:
        logger.error("[BIBIT] Gagal menambahkan data bibit")

    return RedirectResponse("/dashboard/bibit", status_code=303)


@router.post("/dashboard/bibit/edit")
async def bibit_edit(request: Request):
    """Edit data bibit."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)
    form = await request.form()
    bibit_id = int(form.get("bibit_id"))
    kolam_id = int(form.get("kolam_id"))
    ukuran_bibit = form.get("ukuran_bibit")
    jumlah = int(form.get("jumlah") or 0)
    total_harga = float(form.get("total_harga") or 0)
    catatan = form.get("catatan")
    tanggal_tebar = form.get("tanggal_tebar")
    total_berat = float(form.get("total_berat") or 0)  # Ambil total_berat

    updated = await edit_bibit(
        bibit_id=bibit_id,
        kolam_id=kolam_id,
        ukuran_bibit=ukuran_bibit,
        jumlah=jumlah,
        total_harga=total_harga,
        catatan=catatan,
        tanggal_tebar=tanggal_tebar,
        user_id=user_id,
        total_berat=total_berat,  # Sertakan total_berat saat mengedit bibit
    )

    if updated:
        logger.info(f"[USER {user_id}] Bibit {bibit_id} berhasil diedit")
    else:
        logger.error(f"[USER {user_id}] Gagal edit bibit {bibit_id}")

    return RedirectResponse("/dashboard/bibit", status_code=303)


@router.post("/dashboard/bibit/delete")
async def bibit_delete(request: Request):
    """Hapus data bibit."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)
    form = await request.form()
    bibit_id = int(form.get("bibit_id"))

    success = await delete_bibit(bibit_id, user_id=user_id)

    if success:
        logger.info(f"[USER {user_id}] Bibit {bibit_id} dihapus")
    else:
        logger.error(f"[USER {user_id}] Gagal hapus bibit {bibit_id}")

    return RedirectResponse("/dashboard/bibit", status_code=303)
