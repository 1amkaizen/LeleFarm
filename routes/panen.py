# routes/dashboard/panen.py
import logging
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from services.panen import get_all_panen, edit_panen
from services.kolam import get_all_kolam

router = APIRouter()
logger = logging.getLogger("router__panen")


def fmt(x: float | int) -> str:
    """Format angka ribuan tanpa desimal"""
    return "{:,}".format(int(x)).replace(",", ".")


@router.get("/dashboard/panen")
async def panen_page(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Akses panen ditolak: user belum login")
        return RedirectResponse(url="/login", status_code=303)
    user_id = int(user_id)

    kolam_list = await get_all_kolam(user_id)
    panen_list = await get_all_panen(user_id)

    ringkasan_per_kolam = {}
    for k in kolam_list:
        panen_kolam = [p for p in panen_list if p["kolam_id"] == k["id"]]
        if not panen_kolam:
            continue

        total_berat_kolam = sum(p.get("total_berat", 0) for p in panen_kolam)
        total_ikan_kolam = sum(p.get("jumlah_ikan", 0) for p in panen_kolam)
        total_jual_kolam = sum(p.get("total_jual", 0) for p in panen_kolam)

        ringkasan_per_kolam[k["id"]] = {
            "nama_kolam": k["nama_kolam"],
            "status_panen": "sudah",
            "tanggal_mulai": k["tanggal_mulai"],
            "tanggal_panen": max(p["tanggal_panen"] for p in panen_kolam),
            "total_panen": len(panen_kolam),
            "total_ikan": total_ikan_kolam,
            "total_berat": total_berat_kolam,  # tetap angka
            "total_jual": total_jual_kolam,
            "total_berat_fmt": fmt(total_berat_kolam),  # untuk template
            "total_ikan_fmt": fmt(total_ikan_kolam),  # opsional, biar konsisten
            "total_jual_fmt": fmt(total_jual_kolam),
            "panen_detail": [
                {
                    "id": p["id"],
                    "tanggal_panen": p["tanggal_panen"],
                    "jumlah_ikan": fmt(p.get("jumlah_ikan", 0)),
                    "total_berat": fmt(p.get("total_berat", 0)),
                    "total_jual": fmt(p.get("total_jual", 0)),
                    "catatan": p.get("catatan", "-"),
                }
                for p in panen_kolam
            ],
        }

    total_ikan_global = sum(r["total_ikan"] for r in ringkasan_per_kolam.values())
    total_berat_global = sum(r["total_berat"] for r in ringkasan_per_kolam.values())
    total_panen_global = sum(r["total_panen"] for r in ringkasan_per_kolam.values())
    total_jual_global = sum(r["total_jual"] for r in ringkasan_per_kolam.values())

    return request.app.templates.TemplateResponse(
        "dashboard/panen.html",
        {
            "request": request,
            "ringkasan_per_kolam": list(ringkasan_per_kolam.values()),
            "total_ikan_global": fmt(total_ikan_global),
            "total_berat_global": fmt(total_berat_global),
            "total_panen_global": fmt(total_panen_global),
            "total_jual_global": fmt(total_jual_global),
        },
    )


@router.post("/dashboard/panen/edit")
async def panen_edit(
    request: Request,
    panen_id: int = Form(...),
    jumlah_ikan: int = Form(None),
    total_berat: float = Form(None),
    total_jual: int = Form(None),
    tanggal_panen: str = Form(None),
    catatan: str = Form(None),
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    user_id = int(user_id)

    res = await edit_panen(
        panen_id=panen_id,
        user_id=user_id,
        jumlah_ikan=jumlah_ikan,
        total_berat=total_berat,
        total_jual=total_jual,
        tanggal_panen=tanggal_panen,
        catatan=catatan,
    )
    if res:
        logger.info(f"Panen {panen_id} berhasil diupdate")
    else:
        logger.warning(f"Gagal update panen {panen_id}")

    return RedirectResponse(url="/dashboard/panen", status_code=303)
