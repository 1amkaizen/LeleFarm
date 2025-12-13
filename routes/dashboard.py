# routes/dashboard.py
# Dashboard user (filter wajib: user_id)

import logging
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime, timezone, timedelta

from services.user import get_user_by_id
from services.kolam import get_all_kolam, get_kolam_status
from services.kematian import get_all_kematian
from services.bibit import get_all_bibit
from services.pengeluaran import get_all_pengeluaran
from services.pakan import get_all_pakan
from services.pakan_stok import get_all_pakan_stok  # import service pakan stok

router = APIRouter()
logger = logging.getLogger("router_dashboard")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Ambil user_id dari cookie
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Akses dashboard ditolak: user belum login.")
        return RedirectResponse(url="/login", status_code=303)

    user_id = int(user_id)
    user = await get_user_by_id(user_id)
    username = user["username"] if user else "User"

    logger.info(f"User {username} mengakses dashboard.")

    # ============================
    # AMBIL DATA (WAJIB FILTER USER)
    # ============================

    kolam_list_raw = await get_all_kolam(user_id)
    kolam_list = [dict(k) for k in kolam_list_raw]

    kematian_list = await get_all_kematian(user_id)
    bibit_list = await get_all_bibit(user_id)
    pengeluaran_list = await get_all_pengeluaran(user_id)
    pakan_list = await get_all_pakan(user_id)
    pakan_stok_list = await get_all_pakan_stok(user_id)  # ambil stok pakan

    # --- Tambah status panen ke tiap kolam ---
    for k in kolam_list:
        k["status"] = get_kolam_status(k)

    # ============================
    # HITUNG DATA KOLAM
    # ============================

    total_kolam = len(kolam_list)
    kolam_belum = len([k for k in kolam_list if k.get("status") == "belum"])
    kolam_sudah = len([k for k in kolam_list if k.get("status") == "sudah"])

    # ============================
    # HITUNG BIBIT & KEMATIAN
    # ============================

    total_bibit = sum(b.get("jumlah", 0) for b in bibit_list)
    total_kematian = sum(k.get("jumlah", 0) for k in kematian_list)

    bibit_per_kolam = {}
    for k in kolam_list:
        kolam_id = k.get("id")

        bibit_per_kolam[kolam_id] = sum(
            b.get("jumlah", 0) for b in bibit_list if b.get("kolam_id") == kolam_id
        )

        kematian_kolam = sum(
            km.get("jumlah", 0)
            for km in kematian_list
            if km.get("kolam_id") == kolam_id
        )

        total_b = bibit_per_kolam[kolam_id]
        k["persentase_kematian"] = (kematian_kolam / total_b * 100) if total_b else 0

    # ============================
    # TABEL BIBIT & PAKAN ENTRY PER KOLAM
    # ============================

    bibit_entries = []
    for b in bibit_list:
        kolam_id = b.get("kolam_id")
        nama_kolam = next(
            (k.get("nama_kolam") for k in kolam_list if k.get("id") == kolam_id), "-"
        )

        # Hitung umur bibit
        tanggal_tebar = b.get("tanggal_tebar")
        umur_hari = 0
        if tanggal_tebar:
            try:
                # Pastikan start_date selalu date object
                if isinstance(tanggal_tebar, str):
                    start_date = datetime.fromisoformat(tanggal_tebar.split("T")[0]).date()
                elif isinstance(tanggal_tebar, datetime):
                    start_date = tanggal_tebar.date()
                else:
                    start_date = tanggal_tebar  # kalau memang date object

                # Pakai timezone WIB untuk sekarang
                now_wib = datetime.now(timezone.utc) + timedelta(hours=7)
                umur_hari = (now_wib.date() - start_date).days
                if umur_hari < 0:
                    umur_hari = 0

                logger.info(
                    f"{nama_kolam} - tanggal_tebar={tanggal_tebar} -> umur_hari={umur_hari}"
                )
            except Exception as e:
                logger.error(
                    f"Gagal hitung umur bibit kolam {nama_kolam}, tanggal_tebar={tanggal_tebar}: {e}"
                )
                umur_hari = 0

        kematian_kolam = sum(
            km.get("jumlah", 0) for km in kematian_list if km.get("kolam_id") == kolam_id
        )

        pakan_total = sum(
            p.get("jumlah_gram", 0) for p in pakan_list if p.get("kolam_id") == kolam_id
        )
        stok_pakan_total = sum(
            s.get("jumlah", 0) for s in pakan_stok_list if s.get("kolam_id") == kolam_id
        )

        logger.info(
            f"{nama_kolam} - tanggal_tebar={tanggal_tebar} -> umur_hari={umur_hari}"
        )

        bibit_entries.append(
            {
                "kolam_id": kolam_id,
                "nama_kolam": nama_kolam,
                "jumlah": b.get("jumlah", 0),
                "harga": b.get("total_harga", 0),
                "ukuran_bibit": b.get("ukuran_bibit", "-"),
                "tanggal_tebar": tanggal_tebar,
                "umur_hari": umur_hari,
                "status": next(
                    (k.get("status") for k in kolam_list if k.get("id") == kolam_id), "-"
                ),
                "kematian": kematian_kolam,
                "pakan_total": pakan_total,
                "stok_pakan_total": stok_pakan_total,
            }
        )

    # ============================
    # PENGELUARAN + BIBIT + PAKAN STOK
    # ============================

    pengeluaran_detail = [
        {
            "nama": p.get("nama_pengeluaran") or (p.get("catatan") or "Pengeluaran"),
            "jumlah": p.get("jumlah", 1),
            "harga": p.get("harga", 0),
            "total": p.get("harga", 0) * p.get("jumlah", 1),
        }
        for p in pengeluaran_list
    ]

    bibit_detail = [
        {
            "nama": f"Bibit ({b.get('ukuran_bibit', '-')})",
            "jumlah": b.get("jumlah", 0),
            "harga": b.get("total_harga", 0),
            "total": b.get("total_harga", 0),
        }
        for b in bibit_list
    ]

    pakan_stok_detail = [
        {
            "nama": f"Stok Pakan ({s.get('nama_pakan', '-')})",
            "jumlah": s.get("jumlah", 0),
            "harga": s.get("harga", 0),
            "total": s.get("harga", 0),
        }
        for s in pakan_stok_list
    ]

    # Gabung semua ke pengeluaran_detail
    pengeluaran_detail += bibit_detail + pakan_stok_detail
    pengeluaran_total = sum(item["total"] for item in pengeluaran_detail)
    pengeluaran_total_formatted = "{:,}".format(int(pengeluaran_total)).replace(
        ",", "."
    )

    # ============================
    # PAKAN TOTAL
    # ============================

    # total pakan dari pakan_list (gram) → konversi ke kg
    total_pakan_gram = sum(p.get("jumlah_gram", 0) for p in pakan_list)
    total_pakan_kg = total_pakan_gram / 1000

    # total stok pakan (sudah kg di DB)
    total_stok_pakan_kg = sum(s.get("jumlah", 0) for s in pakan_stok_list)

    # total semua pakan + stok
    total_pakan_semua_kg = total_pakan_kg + total_stok_pakan_kg

    # Tampilkan
    total_pakan = f"{int(total_pakan_semua_kg)} kg"



    total_bibit = "{:,}".format(total_bibit).replace(",", ".")
    total_kematian = "{:,}".format(total_kematian).replace(",", ".")
    total_kolam = "{:,}".format(total_kolam).replace(",", ".")

    # ============================
    # RENDER DASHBOARD
    # ============================

    return request.app.templates.TemplateResponse(
        "dashboard/dashboard.html",
        {
            "request": request,
            "username": username,
            "kolam_list": kolam_list,
            "total_bibit": total_bibit,
            "total_kematian": total_kematian,
            "bibit_entries": bibit_entries,
            "pengeluaran_total": pengeluaran_total_formatted,
            "pengeluaran_detail": pengeluaran_detail,
            "total_pakan": total_pakan,
            "total_kolam": total_kolam,
            "kolam_belum": kolam_belum,
            "kolam_sudah": kolam_sudah,
            "bibit_per_kolam": bibit_per_kolam,
            "kematian_list": kematian_list,
        },
    )
