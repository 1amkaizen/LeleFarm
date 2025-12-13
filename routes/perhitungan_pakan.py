# routes/dashboard/perhitungan_pakan.py
# Lokasi file: routes/dashboard/perhitungan_pakan.py

import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import date

from services import perhitungan_pakan
from services.perhitungan_pakan import get_persen_pakan

router = APIRouter()
logger = logging.getLogger("router_perhitungan_pakan")
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard/perhitungan_pakan", response_class=HTMLResponse)
async def perhitungan_pakan_page(request: Request):
    # ambil user_id dari cookie
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Akses /dashboard/perhitungan_pakan ditolak: user belum login.")
        return RedirectResponse("/login", status_code=303)

    user_id = int(user_id)

    try:
        kolam_list = await perhitungan_pakan.get_kolam_data(user_id=user_id)
    except Exception as e:
        logger.error(f"[USER {user_id}] Gagal ambil data kolam: {e}")
        kolam_list = []

    total_kebutuhan_gram = 0
    total_ikan = 0
    total_stok_pakan = 0
    total_berat_bibit = 0

    hasil_perhitungan = []

    for kolam in kolam_list:
        kolam_id = kolam["id"]
        nama_kolam = kolam["nama_kolam"]
        jumlah_ikan = kolam["jumlah_ikan_hidup"]
        total_berat = kolam["total_berat_kg"]  # kg
        ukuran_bibit = kolam.get("ukuran_bibit", "7-9 cm")
        stok_pakan = kolam.get("stok_pakan", 0)

        # ambil persen pakan harian sesuai ukuran bibit
        persen_pakan_harian = get_persen_pakan(ukuran_bibit)

        # ============================================================
        # HITUNG KEBUTUHAN PAKAN HARIAN
        # Rumus: Biomassa (kg) × Persentase Pakan Harian
        # ============================================================
        kebutuhan_harian_kg = total_berat * (persen_pakan_harian / 100)
        kebutuhan_harian_gram = kebutuhan_harian_kg * 1000

        sisa_stok = stok_pakan - kebutuhan_harian_gram
        if sisa_stok < 0:
            logger.warning(f"[USER {user_id}] Stok pakan kurang di kolam {nama_kolam}")

        # ============================================================
        # SIMPAN OTOMATIS PEMBERIAN PAKAN HARI INI
        # ============================================================
        try:
            await perhitungan_pakan.create_pemberian_pakan(
                user_id=user_id,
                kolam_id=kolam_id,
                tanggal=date.today(),
                jenis_pakan="pakan standar",
                jumlah_gram=kebutuhan_harian_gram,
                catatan=f"Auto generate perhitungan {date.today()}",
            )
            await perhitungan_pakan.update_pakan_stok(
                user_id=user_id,
                jumlah_keluar=kebutuhan_harian_gram,
            )
        except Exception as e:
            logger.error(
                f"[USER {user_id}] Gagal simpan PemberianPakan kolam {nama_kolam}: {e}"
            )

        hasil_perhitungan.append(
            {
                "nama_kolam": nama_kolam,
                "jumlah_ikan": jumlah_ikan,
                "total_berat": total_berat,
                "persen_pakan_harian": persen_pakan_harian,
                "kebutuhan_harian_kg": kebutuhan_harian_kg,
                "kebutuhan_harian_gram": kebutuhan_harian_gram,
                "stok_tersisa": sisa_stok,
            }
        )

        # total global
        total_kebutuhan_gram += kebutuhan_harian_gram
        total_ikan += jumlah_ikan
        total_stok_pakan += stok_pakan
        total_berat_bibit += total_berat

    return templates.TemplateResponse(
        "dashboard/perhitungan_pakan.html",
        {
            "request": request,
            "hasil_perhitungan": hasil_perhitungan,
            "total_kebutuhan_gram": total_kebutuhan_gram,
            "total_ikan": total_ikan,
            "total_stok_pakan": total_stok_pakan,
            "total_berat_bibit": total_berat_bibit,
        },
    )
