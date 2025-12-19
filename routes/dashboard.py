# routes/dashboard.py
# Dashboard user (filter wajib: user_id)

import logging
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime, timezone, timedelta

from services.user import get_user_by_id
from services.kolam import get_all_kolam
from services.kematian import get_all_kematian
from services.bibit import get_all_bibit
from services.pengeluaran import get_all_pengeluaran
from services.pemberian_pakan import get_all_pakan
from services.pakan_stok import get_all_pakan_stok

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
    pakan_stok_list = await get_all_pakan_stok(user_id)

    # --- Tetapkan status langsung dari status_panen ---
    for k in kolam_list:
        status_panen = k.get("status_panen")
        k["status"] = status_panen if status_panen in ("belum", "sudah") else "belum"

    # ============================
    # HITUNG DATA KOLAM
    # ============================
    total_kolam = len(kolam_list)
    kolam_belum = len([k for k in kolam_list if k["status"] == "belum"])
    kolam_sudah = len([k for k in kolam_list if k["status"] == "sudah"])

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
    for k in kolam_list:
        kolam_id = k.get("id")
        nama_kolam = k.get("nama_kolam")
        bibit_kolam = [b for b in bibit_list if b.get("kolam_id") == kolam_id]

        if bibit_kolam:
            for b in bibit_kolam:
                tanggal_tebar = b.get("tanggal_tebar")
                umur_hari = 0
                if tanggal_tebar:
                    try:
                        start_date = (
                            datetime.fromisoformat(tanggal_tebar.split("T")[0]).date()
                            if isinstance(tanggal_tebar, str)
                            else (
                                tanggal_tebar.date()
                                if isinstance(tanggal_tebar, datetime)
                                else tanggal_tebar
                            )
                        )
                        now_wib = datetime.now(timezone.utc) + timedelta(hours=7)
                        umur_hari = max((now_wib.date() - start_date).days, 0)
                    except Exception as e:
                        logger.error(
                            f"Gagal hitung umur bibit kolam {nama_kolam}, tanggal_tebar={tanggal_tebar}: {e}"
                        )

                kematian_kolam = sum(
                    km.get("jumlah", 0)
                    for km in kematian_list
                    if km.get("kolam_id") == kolam_id
                )
                pakan_total = sum(
                    p.get("jumlah_gram", 0)
                    for p in pakan_list
                    if p.get("kolam_id") == kolam_id
                )
                stok_pakan_total = sum(
                    s.get("jumlah", 0)
                    for s in pakan_stok_list
                    if s.get("kolam_id") == kolam_id
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
                        "status": k["status"],
                        "kematian": kematian_kolam,
                        "pakan_total": pakan_total,
                        "stok_pakan_total": stok_pakan_total,
                    }
                )
        else:
            # Kolam tanpa bibit → tetap tampil
            bibit_entries.append(
                {
                    "kolam_id": kolam_id,
                    "nama_kolam": nama_kolam,
                    "jumlah": 0,
                    "harga": 0,
                    "ukuran_bibit": "-",
                    "tanggal_tebar": None,
                    "umur_hari": 0,
                    "status": k["status"],
                    "kematian": 0,
                    "pakan_total": sum(
                        p.get("jumlah_gram", 0)
                        for p in pakan_list
                        if p.get("kolam_id") == kolam_id
                    ),
                    "stok_pakan_total": sum(
                        s.get("jumlah", 0)
                        for s in pakan_stok_list
                        if s.get("kolam_id") == kolam_id
                    ),
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

    pengeluaran_detail += bibit_detail + pakan_stok_detail
    pengeluaran_total_formatted = "{:,}".format(
        int(sum(item["total"] for item in pengeluaran_detail))
    ).replace(",", ".")

    total_pakan_semua_kg = sum(
        p.get("jumlah_gram", 0) for p in pakan_list
    ) / 1000 + sum(s.get("jumlah", 0) for s in pakan_stok_list)
    total_pakan = f"{int(total_pakan_semua_kg)} kg"

    return request.app.templates.TemplateResponse(
        "dashboard/dashboard.html",
        {
            "request": request,
            "username": username,
            "kolam_list": kolam_list,
            "total_bibit": "{:,}".format(total_bibit).replace(",", "."),
            "total_kematian": "{:,}".format(total_kematian).replace(",", "."),
            "bibit_entries": bibit_entries,
            "pengeluaran_total": pengeluaran_total_formatted,
            "pengeluaran_detail": pengeluaran_detail,
            "total_pakan": total_pakan,
            "total_kolam": "{:,}".format(total_kolam).replace(",", "."),
            "kolam_belum": kolam_belum,
            "kolam_sudah": kolam_sudah,
            "bibit_per_kolam": bibit_per_kolam,
            "kematian_list": kematian_list,
            "tanggal_bibit": sorted(
                {str(b["tanggal_tebar"]) for b in bibit_list if b.get("tanggal_tebar")}
            ),
            "tanggal_kematian": sorted(
                {str(k["tanggal"]) for k in kematian_list if k.get("tanggal")}
            ),
            "tanggal_pengeluaran": sorted(
                {str(p["tanggal"]) for p in pengeluaran_list if p.get("tanggal")}
            ),
            "tanggal_pemberian_pakan": sorted(
                {str(pp["tanggal"]) for pp in pakan_list if pp.get("tanggal")}
            ),
            "tanggal_pakan_stok": sorted(
                {
                    str(s["tanggal_masuk"])
                    for s in pakan_stok_list
                    if s.get("tanggal_masuk")
                }
            ),
        },
    )
