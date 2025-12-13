# routes/dashboard/ringkasan.py
# Lokasi file: routes/dashboard/ringkasan.py

import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from services.user import get_user_by_id
from services.kolam import get_all_kolam, get_kolam_status
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
    # ============================
    # VALIDASI LOGIN
    # ============================
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Akses ringkasan ditolak: user belum login")
        return RedirectResponse(url="/login", status_code=303)

    user_id = int(user_id)
    user = await get_user_by_id(user_id)
    username = user["username"] if user else "User"

    logger.info(f"[RINGKASAN] User {username} membuka halaman ringkasan")

    # ============================
    # AMBIL DATA
    # ============================
    kolam_list = [dict(k) for k in await get_all_kolam(user_id)]
    kematian_list = await get_all_kematian(user_id)
    bibit_list = await get_all_bibit(user_id)
    pengeluaran_list = await get_all_pengeluaran(user_id)
    pakan_list = await get_all_pakan(user_id)
    pakan_stok_list = await get_all_pakan_stok(user_id)

    # ============================
    # STATUS KOLAM
    # ============================
    kolam_aktif = 0
    kolam_nonaktif = 0

    for k in kolam_list:
        status_raw = get_kolam_status(k)
        if status_raw == "belum":
            kolam_aktif += 1
            k["status_label"] = "Belum Panen"
        else:
            kolam_nonaktif += 1
            k["status_label"] = "Sudah Panen"

    total_kolam = len(kolam_list)

    # ============================
    # BIBIT & KEMATIAN
    # ============================
    total_bibit = sum(b.get("jumlah", 0) for b in bibit_list)
    total_kematian = sum(k.get("jumlah", 0) for k in kematian_list)

    # ============================
    # DETAIL PER KATEGORI (SUDAH DI-FORMAT)
    # ============================
    pengeluaran_operasional_detail = []
    pengeluaran_bibit_detail = []
    pengeluaran_pakan_detail = []

    # Operasional
    for p in pengeluaran_list:
        total = p.get("harga", 0) * p.get("jumlah", 1)
        pengeluaran_operasional_detail.append(
            {
                "nama": p.get("nama_pengeluaran") or p.get("catatan") or "Operasional",
                "jumlah": fmt(p.get("jumlah", 1)),
                "harga": fmt(p.get("harga", 0)),
                "total": fmt(total),
            }
        )

    # Bibit
    for b in bibit_list:
        pengeluaran_bibit_detail.append(
            {
                "nama": f"Bibit ({b.get('ukuran_bibit', '-')})",
                "jumlah": fmt(b.get("jumlah", 0)),
                "harga": fmt(b.get("total_harga", 0)),
                "total": fmt(b.get("total_harga", 0)),
            }
        )

    # Pakan
    for s in pakan_stok_list:
        pengeluaran_pakan_detail.append(
            {
                "nama": f"Pakan ({s.get('nama_pakan', '-')})",
                "jumlah": fmt(s.get("jumlah", 0)),
                "harga": fmt(s.get("harga", 0)),
                "total": fmt(s.get("harga", 0)),
            }
        )

    # ============================
    # TOTAL ITEM & TRANSAKSI PER KATEGORI
    # ============================

    # Bibit
    total_item_bibit = sum(b.get("jumlah", 0) for b in bibit_list)
    total_transaksi_bibit = len(pengeluaran_bibit_detail)

    # Pakan
    total_item_pakan = sum(s.get("jumlah", 0) for s in pakan_stok_list)
    total_transaksi_pakan = len(pengeluaran_pakan_detail)

    # Operasional  ✅ INI YANG KAMU MAU
    total_item_operasional = sum(
        p.get("jumlah", 1) for p in pengeluaran_list
    )
    total_transaksi_operasional = len(pengeluaran_operasional_detail)

    logger.info(
        "[RINGKASAN] "
        f"Operasional item={total_item_operasional}, "
        f"transaksi={total_transaksi_operasional}"
    )

    # ============================
    # TOTAL PER KATEGORI
    # ============================
    pengeluaran_operasional = sum(
        int(p["total"].replace(".", "")) for p in pengeluaran_operasional_detail
    )
    pengeluaran_bibit = sum(
        int(p["total"].replace(".", "")) for p in pengeluaran_bibit_detail
    )
    pengeluaran_pakan = sum(
        int(p["total"].replace(".", "")) for p in pengeluaran_pakan_detail
    )

    pengeluaran_total = pengeluaran_operasional + pengeluaran_bibit + pengeluaran_pakan

    # ============================
    # PAKAN
    # ============================
    total_pakan_gram = sum(p.get("jumlah_gram", 0) for p in pakan_list)
    total_stok_pakan_gram = sum(s.get("jumlah", 0) for s in pakan_stok_list)
    total_pakan_semua = total_pakan_gram + total_stok_pakan_gram

    # ============================
    # RENDER
    # ============================
    return request.app.templates.TemplateResponse(
        "dashboard/ringkasan.html",
        {
            "request": request,
            "username": username,
            "total_kolam": total_kolam,
            "kolam_aktif": fmt(kolam_aktif),
            "kolam_nonaktif": fmt(kolam_nonaktif),
            "total_bibit": fmt(total_bibit),
            "total_kematian": fmt(total_kematian),
            "pengeluaran_operasional": fmt(pengeluaran_operasional),
            "pengeluaran_bibit": fmt(pengeluaran_bibit),
            "pengeluaran_pakan": fmt(pengeluaran_pakan),
            "pengeluaran_total": fmt(pengeluaran_total),
            "total_pakan": fmt_pakan(total_pakan_semua),
            "pengeluaran_operasional_detail": pengeluaran_operasional_detail,
            "pengeluaran_bibit_detail": pengeluaran_bibit_detail,
            "pengeluaran_pakan_detail": pengeluaran_pakan_detail,
            "total_item_bibit": fmt(total_item_bibit),
            "total_item_pakan": fmt(total_item_pakan),
            "total_item_operasional": fmt(total_item_operasional),
            "total_transaksi_bibit": fmt(total_transaksi_bibit),
            "total_transaksi_pakan": fmt(total_transaksi_pakan),
            "total_transaksi_operasional": fmt(total_transaksi_operasional),
        },
    )
