# routes/dashboard/ringkasan.py
# Lokasi file: routes/dashboard/ringkasan.py

import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from services.user import get_user_by_id
from services.kolam import get_all_kolam
from services.kematian import get_all_kematian
from services.bibit import get_all_bibit
from services.pengeluaran import get_all_pengeluaran
from services.pakan import get_all_pakan
from services.pakan_stok import get_all_pakan_stok

router = APIRouter()
logger = logging.getLogger("router_ringkasan")


def fmt(x: float | int) -> str:
    """Format angka ribuan tanpa desimal"""
    return "{:,}".format(int(x)).replace(",", ".")


def fmt_pakan(gram: int | float) -> str:
    """Format pakan dengan satuan jelas"""
    gram = int(gram)
    if gram >= 1000:
        return f"{gram // 1000} kg"
    return f"{gram} g"


@router.get("/dashboard/ringkasan", response_class=HTMLResponse)
async def ringkasan_page(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Akses ringkasan ditolak: user belum login")
        return RedirectResponse(url="/login", status_code=303)

    user_id = int(user_id)
    user = await get_user_by_id(user_id)
    username = user["username"] if user else "User"
    logger.info(f"[RINGKASAN] User {username} membuka halaman ringkasan")

    kolam_list = [dict(k) for k in await get_all_kolam(user_id)]
    kematian_list = await get_all_kematian(user_id)
    bibit_list = await get_all_bibit(user_id)
    pengeluaran_list = await get_all_pengeluaran(user_id)
    pakan_list = await get_all_pakan(user_id)
    pakan_stok_list = await get_all_pakan_stok(user_id)

    pengeluaran_per_kolam = {}
    kolam_aktif = 0
    kolam_nonaktif = 0

    # ===========================
    # Inisialisasi per kolam
    # ===========================
    for k in kolam_list:
        # Ambil status langsung dari kolam dan normalisasi
        status_raw = (
            (k.get("status_panen") or "").strip().lower()
        )  # 'belum' atau 'sudah'
        if status_raw == "belum":
            kolam_aktif += 1
            k["status_label"] = "Belum Panen"
        else:
            kolam_nonaktif += 1
            k["status_label"] = "Sudah Panen"

        kolam_id = k["id"]
        pengeluaran_per_kolam[kolam_id] = {
            "nama_kolam": k.get("nama_kolam", "-"),
            "status_label": k["status_label"],
            "tanggal_mulai": k.get("tanggal_mulai", "-"),
            "operasional": {
                "detail": [],
                "total_item": 0,
                "total_transaksi": 0,
                "total_harga": 0,
            },
            "bibit": {
                "detail": [],
                "total_item": 0,
                "total_transaksi": 0,
                "total_harga": 0,
            },
            "pakan": {
                "detail": [],
                "total_item": 0,
                "total_transaksi": 0,
                "total_harga": 0,
            },
        }

    # ===========================
    # Detail Operasional
    # ===========================
    for p in pengeluaran_list:
        kolam_id = p.get("kolam_id") or 0
        total = p.get("harga", 0) * p.get("jumlah", 1)
        data = {
            "nama": p.get("nama_pengeluaran") or p.get("catatan") or "Operasional",
            "jumlah": fmt(p.get("jumlah", 1)),
            "harga": fmt(p.get("harga", 0)),
            "total": fmt(total),
            "tanggal": p.get("tanggal") or "-",  # tambahkan tanggal
        }
        if kolam_id in pengeluaran_per_kolam:
            kolam_data = pengeluaran_per_kolam[kolam_id]["operasional"]
            kolam_data["detail"].append(data)
            kolam_data["total_item"] += p.get("jumlah", 1)
            kolam_data["total_transaksi"] += 1
            kolam_data["total_harga"] += total

    # ===========================
    # Detail Bibit
    # ===========================
    for b in bibit_list:
        kolam_id = b.get("kolam_id") or 0
        total_harga = b.get("total_harga", 0)
        data = {
            "nama": f"Bibit ({b.get('ukuran_bibit', '-')})",
            "jumlah": fmt(b.get("jumlah", 0)),
            "harga": fmt(total_harga),
            "total": fmt(total_harga),
            "tanggal": b.get("tanggal_tebar") or "-",  # tambahkan tanggal
        }
        if kolam_id in pengeluaran_per_kolam:
            kolam_data = pengeluaran_per_kolam[kolam_id]["bibit"]
            kolam_data["detail"].append(data)
            kolam_data["total_item"] += b.get("jumlah", 0)
            kolam_data["total_transaksi"] += 1
            kolam_data["total_harga"] += total_harga

    # ===========================
    # Detail Pakan
    # ===========================
    for s in pakan_stok_list:
        kolam_id = s.get("kolam_id") or 0
        harga = s.get("harga", 0)
        jumlah = s.get("jumlah", 0)
        data = {
            "nama": f"Pakan ({s.get('nama_pakan', '-')})",
            "jumlah": fmt(jumlah),
            "harga": fmt(harga),
            "total": fmt(harga),
            "tanggal": s.get("tanggal_masuk") or "-",  # tambahkan tanggal
        }
        if kolam_id in pengeluaran_per_kolam:
            kolam_data = pengeluaran_per_kolam[kolam_id]["pakan"]
            kolam_data["detail"].append(data)
            kolam_data["total_item"] += jumlah
            kolam_data["total_transaksi"] += 1
            kolam_data["total_harga"] += harga

    # ===========================
    # Hitung Total Pengeluaran Per Kolam & Format
    # ===========================
    for k_id, k_data in pengeluaran_per_kolam.items():
        # Total pengeluaran
        total_pengeluaran = (
            k_data["operasional"]["total_harga"]
            + k_data["bibit"]["total_harga"]
            + k_data["pakan"]["total_harga"]
        )
        k_data["total_pengeluaran"] = total_pengeluaran
        k_data["total_pengeluaran_fmt"] = fmt(total_pengeluaran)

        # Format per kategori
        for cat in ["operasional", "bibit", "pakan"]:
            k_data[cat]["total_item_fmt"] = fmt(k_data[cat]["total_item"])
            k_data[cat]["total_harga_fmt"] = fmt(k_data[cat]["total_harga"])

    # ===========================
    # Total Global
    # ===========================
    total_bibit = sum(b.get("jumlah", 0) for b in bibit_list)
    total_kematian = sum(k.get("jumlah", 0) for k in kematian_list)
    total_pakan_gram = sum(p.get("jumlah_gram", 0) for p in pakan_list)
    total_stok_pakan_gram = sum(s.get("jumlah", 0) for s in pakan_stok_list)
    total_pakan_semua = total_pakan_gram + total_stok_pakan_gram

    # ===========================
    # Hitung Persentase Kategori & Perbandingan Kolam
    # ===========================
    # Cari kolam dengan total pengeluaran terbesar untuk perbandingan
    max_total = max(
        (k_data["total_pengeluaran"] for k_data in pengeluaran_per_kolam.values()),
        default=1,
    )

    for k_id, k_data in pengeluaran_per_kolam.items():
        # Persentase per kategori
        for cat in ["operasional", "bibit", "pakan"]:
            total_harga = k_data[cat]["total_harga"]
            if k_data["total_pengeluaran"] > 0:
                k_data[cat]["persentase_kolam"] = round(
                    (total_harga / k_data["total_pengeluaran"]) * 100, 1
                )
            else:
                k_data[cat]["persentase_kolam"] = 0.0
            k_data[cat][
                "total_harga_fmt_with_pct"
            ] = f"Rp {fmt(total_harga)} ({k_data[cat]['persentase_kolam']}%)"

        # Selisih terhadap kolam terbesar
        k_data["selisih_total"] = k_data["total_pengeluaran"] - max_total
        k_data["selisih_fmt"] = (
            f"+Rp {fmt(k_data['selisih_total'])}"
            if k_data["selisih_total"] > 0
            else (
                f"-Rp {fmt(abs(k_data['selisih_total']))}"
                if k_data["selisih_total"] < 0
                else "-"
            )
        )

        # Proporsi terhadap kolam terbesar (untuk progress bar)
        k_data["proporsi_max"] = round((k_data["total_pengeluaran"] / max_total) * 100, 1)

    # ===========================
    # Total Keseluruhan Semua Kolam
    # ===========================
    total_operasional = sum(k["operasional"]["total_harga"] for k in pengeluaran_per_kolam.values())
    total_bibit = sum(k["bibit"]["total_harga"] for k in pengeluaran_per_kolam.values())
    total_pakan = sum(k["pakan"]["total_harga"] for k in pengeluaran_per_kolam.values())
    total_pengeluaran_global = total_operasional + total_bibit + total_pakan

    total_pengeluaran_semua_kolam = {
        "operasional": {
            "total_harga": total_operasional,
            "total_item": sum(k["operasional"]["total_item"] for k in pengeluaran_per_kolam.values()),
            "total_harga_fmt": fmt(total_operasional),
            "total_item_fmt": fmt(sum(k["operasional"]["total_item"] for k in pengeluaran_per_kolam.values())),
        },
        "bibit": {
            "total_harga": total_bibit,
            "total_item": sum(k["bibit"]["total_item"] for k in pengeluaran_per_kolam.values()),
            "total_harga_fmt": fmt(total_bibit),
            "total_item_fmt": fmt(sum(k["bibit"]["total_item"] for k in pengeluaran_per_kolam.values())),
        },
        "pakan": {
            "total_harga": total_pakan,
            "total_item": sum(k["pakan"]["total_item"] for k in pengeluaran_per_kolam.values()),
            "total_harga_fmt": fmt(total_pakan),
            "total_item_fmt": fmt(sum(k["pakan"]["total_item"] for k in pengeluaran_per_kolam.values())),
        },
        "total_pengeluaran": total_pengeluaran_global,
        "total_pengeluaran_fmt": fmt(total_pengeluaran_global),
    }

    # ===========================
    # Render Template
    # ===========================
    return request.app.templates.TemplateResponse(
        "dashboard/ringkasan.html",
        {
            "request": request,
            "username": username,
            "total_kolam": fmt(len(kolam_list)),
            "kolam_aktif": fmt(kolam_aktif),
            "kolam_nonaktif": fmt(kolam_nonaktif),
            "total_bibit": fmt(total_bibit),
            "total_kematian": fmt(total_kematian),
            "total_pakan": fmt_pakan(total_pakan_semua),
            "pengeluaran_per_kolam": [
                {"id": k_id, **k_data} for k_id, k_data in pengeluaran_per_kolam.items()
            ],
            "total_pengeluaran_semua_kolam": total_pengeluaran_semua_kolam,
        },
    )
