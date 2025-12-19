# routes/dashboard/panen.py
import logging
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from services.panen import get_all_panen, edit_panen
from services.kolam import get_all_kolam
from services.kematian import get_all_kematian
from services.bibit import get_all_bibit
from services.pengeluaran import get_all_pengeluaran
from services.pakan_stok import get_all_pakan_stok

router = APIRouter()
logger = logging.getLogger("router__panen")


def fmt(x: float | int) -> str:
    """Format angka ribuan tanpa desimal"""
    return "{:,}".format(int(x)).replace(",", ".")


def fmt_berat(x: float | int) -> str:
    """Format berat ikan, kuintal jika >=100kg"""
    if x >= 100:
        kuintal = x / 100
        return (
            f"{int(kuintal)} kuintal"
            if kuintal.is_integer()
            else f"{kuintal:g} kuintal"
        )
    return f"{int(x)} kg" if float(x).is_integer() else f"{x:g} kg"


@router.get("/dashboard/panen")
async def panen_page(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Akses panen ditolak: user belum login")
        return RedirectResponse(url="/login", status_code=303)
    user_id = int(user_id)

    # Ambil semua data
    kolam_list = await get_all_kolam(user_id)
    panen_list = await get_all_panen(user_id)
    kematian_list = await get_all_kematian(user_id)
    bibit_list = await get_all_bibit(user_id)
    pengeluaran_list = await get_all_pengeluaran(user_id)
    pakan_stok_list = await get_all_pakan_stok(user_id)

    ringkasan_per_kolam = {}

    for k in kolam_list:
        kolam_id = k["id"]
        panen_kolam = [p for p in panen_list if p["kolam_id"] == kolam_id]
        if not panen_kolam:
            continue

        # Hitung total panen per kolam
        total_berat_kolam = sum(p.get("total_berat", 0) for p in panen_kolam)
        total_jual_kolam = sum(p.get("total_jual", 0) for p in panen_kolam)

        # Bibit
        bibit_kolam = [b for b in bibit_list if b["kolam_id"] == kolam_id]
        total_berat_bibit = sum(b.get("total_berat", 0) for b in bibit_kolam)
        total_ekor_bibit = sum(b.get("jumlah", 0) for b in bibit_kolam)
        total_pengeluaran_bibit = sum(
            Decimal(b.get("total_harga", 0)) for b in bibit_kolam
        )

        # ===== TANGGAL TEBAR (DARI BIBIT) =====
        tanggal_tebar = (
            min(
                datetime.strptime(b["tanggal_tebar"], "%Y-%m-%d")
                for b in bibit_kolam
                if b.get("tanggal_tebar")
            )
            if bibit_kolam
            else None
        )

        # Pakan
        pakan_kolam = [p for p in pakan_stok_list if p.get("kolam_id") == kolam_id]
        total_pengeluaran_pakan = sum(
            Decimal(p.get("harga", 0)) for p in pakan_kolam
        )

        # Operasional
        pengeluaran_operasional_kolam = [
            pe for pe in pengeluaran_list if pe.get("kolam_id") == kolam_id
        ]

        total_pengeluaran_operasional = sum(
            Decimal(pe.get("harga", 0)) * Decimal(pe.get("jumlah", 1))
            for pe in pengeluaran_operasional_kolam
        )

        # Total pengeluaran
        total_pengeluaran = total_pengeluaran_bibit + total_pengeluaran_pakan + total_pengeluaran_operasional

        # ===== TANGGAL PANEN TERAKHIR =====
        tanggal_terakhir_panen = max(
            datetime.strptime(p["tanggal_panen"], "%Y-%m-%d")
            for p in panen_kolam
        )

        # Hari aktif
        # ===== HARI AKTIF (DARI TANGGAL TEBAR) =====
        hari_aktif = (
            (tanggal_terakhir_panen - tanggal_tebar).days
            if tanggal_tebar
            else 0
        )

        # Total kematian
        total_kematian = sum(
            km.get("jumlah", 0)
            for km in kematian_list
            if km.get("kolam_id") == kolam_id
        )

        # =====================================================
        # RINGKASAN PANEN (UNTUK TABEL RINCIAN)
        # =====================================================

        # Total pakan (kg)
        total_pakan_kg = sum(
            Decimal(p.get("jumlah", 0)) for p in pakan_kolam
        )

        # Total biaya produksi
        total_biaya_produksi = (
            total_pengeluaran_bibit
            + total_pengeluaran_pakan
            + total_pengeluaran_operasional
        )

        # Laba
        total_keuntungan = Decimal(total_jual_kolam) - total_biaya_produksi
  
        # Simpan ringkasan per kolam
        ringkasan_per_kolam[kolam_id] = {
            "nama_kolam": k.get("nama_kolam", "-"),
            "status_panen": "sudah",
            "tanggal_tebar": (
                tanggal_tebar.strftime("%Y-%m-%d") if tanggal_tebar else "-"
            ),
            "tanggal_panen": tanggal_terakhir_panen.strftime("%Y-%m-%d"),
            "total_panen": len(panen_kolam),
            # ===== PANEN =====
            "total_berat": total_berat_kolam,
            "total_berat_fmt": fmt_berat(total_berat_kolam),
            "total_jual": total_jual_kolam,
            "total_jual_fmt": fmt(total_jual_kolam),
            # ===== BIBIT =====
            "total_ekor_bibit": total_ekor_bibit,
            "total_ekor_bibit_fmt": fmt(total_ekor_bibit),
            "total_berat_bibit": total_berat_bibit,
            "total_berat_bibit_fmt": fmt_berat(total_berat_bibit),
            # ===== KEMATIAN =====
            "total_kematian": total_kematian,
            "total_kematian_fmt": fmt(total_kematian),
            # ===== PENGELUARAN =====
            "total_pengeluaran": total_pengeluaran,
            "total_pengeluaran_fmt": fmt(total_pengeluaran),
            "total_pengeluaran_bibit": total_pengeluaran_bibit,
            "total_pengeluaran_bibit_fmt": fmt(total_pengeluaran_bibit),
            "total_pengeluaran_pakan": total_pengeluaran_pakan,
            "total_pengeluaran_pakan_fmt": fmt(total_pengeluaran_pakan),
            "total_pengeluaran_operasional": total_pengeluaran_operasional,
            "total_pengeluaran_operasional_fmt": fmt(total_pengeluaran_operasional),
            "hari_aktif": hari_aktif,
            # ===== RINGKASAN BIAYA =====
            "total_biaya_bibit": total_pengeluaran_bibit,
            "total_biaya_bibit_fmt": fmt(total_pengeluaran_bibit),
            "total_pakan_kg": total_pakan_kg,
            "total_pakan_kg_fmt": fmt_berat(float(total_pakan_kg)),
            "total_biaya_pakan": total_pengeluaran_pakan,
            "total_biaya_pakan_fmt": fmt(total_pengeluaran_pakan),
            "total_operasional": total_pengeluaran_operasional,
            "total_operasional_fmt": fmt(total_pengeluaran_operasional),
            "total_biaya_produksi": total_biaya_produksi,
            "total_biaya_produksi_fmt": fmt(total_biaya_produksi),
            # ===== LABA =====
            "total_keuntungan": total_keuntungan,
            "total_keuntungan_fmt": fmt(total_keuntungan),
            "panen_detail": [
                {
                    "id": p["id"],
                    "tanggal_panen": p["tanggal_panen"],
                    "total_berat": fmt_berat(p.get("total_berat", 0)),
                    "total_jual": fmt(p.get("total_jual", 0)),
                    "catatan": p.get("catatan", "-"),
                }
                for p in panen_kolam
            ],
        }

    kolam_sudah_panen = list(ringkasan_per_kolam.values())

    # Hitung global
    total_berat_global = sum(r["total_berat"] for r in kolam_sudah_panen)
    total_panen_global = sum(r["total_panen"] for r in kolam_sudah_panen)
    total_jual_global = sum(r["total_jual"] for r in kolam_sudah_panen)
    # ===============================
    # TOTAL PENGELUARAN GLOBAL (BENAR)
    # ===============================

    total_pengeluaran_bibit_global = sum(
        Decimal(b.get("total_harga", 0)) for b in bibit_list
    )

    total_pengeluaran_pakan_global = sum(
        Decimal(p.get("total_harga", 0)) for p in pakan_stok_list
    )

    total_pengeluaran_operasional_global = sum(
        Decimal(pe.get("harga", 0)) * Decimal(pe.get("jumlah", 1))
        for pe in pengeluaran_list
    )

    total_pengeluaran_global = (
        total_pengeluaran_bibit_global
        + total_pengeluaran_pakan_global
        + total_pengeluaran_operasional_global
    )

    total_kolam_panen = len(kolam_sudah_panen)

    return request.app.templates.TemplateResponse(
        "dashboard/panen.html",
        {
            "request": request,
            "ringkasan_per_kolam": kolam_sudah_panen,
            "total_berat_global": fmt_berat(total_berat_global),
            "total_panen_global": fmt(total_panen_global),
            "total_jual_global": fmt(total_jual_global),
            "total_pengeluaran_global": fmt(total_pengeluaran_global),
            "total_pengeluaran_global": fmt(int(total_pengeluaran_global)),
            "total_pengeluaran_bibit_global": fmt(int(total_pengeluaran_bibit_global)),
            "total_pengeluaran_pakan_global": fmt(int(total_pengeluaran_pakan_global)),
            "total_pengeluaran_operasional_global": fmt(
                int(total_pengeluaran_operasional_global)
            ),
            "total_kolam_panen": total_kolam_panen,
        },
    )


# ============================================================
# EDIT PANEN
# ============================================================
@router.post("/dashboard/panen/edit")
async def edit_panen_route(
    request: Request,
    panen_id: int = Form(...),
    total_berat: float = Form(...),
    total_jual: float = Form(...),
    tanggal_panen: str = Form(...),
    catatan: str = Form(None),
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Edit panen ditolak: user belum login")
        return RedirectResponse(url="/login", status_code=303)

    user_id = int(user_id)

    logger.info(f"Request edit panen: panen_id={panen_id}, user_id={user_id}")

    success = await edit_panen(
        panen_id=panen_id,
        user_id=user_id,
        total_berat=total_berat,
        total_jual=total_jual,
        tanggal_panen=tanggal_panen,
        catatan=catatan,
    )

    if not success:
        logger.error(f"Gagal edit panen panen_id={panen_id}")
    else:
        logger.info(f"Berhasil edit panen panen_id={panen_id}")

    return RedirectResponse(
        url="/dashboard/panen",
        status_code=303,
    )
