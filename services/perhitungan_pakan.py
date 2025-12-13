# services/perhitungan_pakan.py
# Lokasi file: services/perhitungan_pakan.py

import logging
import asyncio
from datetime import date
from lib.supabase_client import get_db

logger = logging.getLogger("service_perhitungan_pakan")


# ============================================================
# AMBIL DATA KOLAM AKTIF BESERTA BIBIT & KEMATIAN
# ============================================================
async def get_kolam_data(user_id: int):
    """
    Ambil data kolam aktif user beserta jumlah ikan hidup,
    total berat bibit, kebutuhan pakan harian, dan stok pakan.
    """
    db = get_db()

    def db_call_kolam():
        return (
            db.table("Kolam")
            .select("*")
            .eq("user_id", user_id)
            .eq("status_panen", "belum")
            .execute()
        )

    kolam_result = await asyncio.to_thread(db_call_kolam)
    kolam_list = getattr(kolam_result, "data", []) or []

    result_list = []

    for kolam in kolam_list:
        kolam_id = kolam["id"]

        # ambil bibit per kolam
        def db_call_bibit():
            return (
                db.table("Bibit")
                .select("*")
                .eq("kolam_id", kolam_id)
                .eq("user_id", user_id)
                .execute()
            )

        bibit_result = await asyncio.to_thread(db_call_bibit)
        bibit_list = getattr(bibit_result, "data", []) or []

        total_ikan = sum(b["jumlah"] for b in bibit_list)
        total_berat = sum(b.get("total_berat", 0) for b in bibit_list)  # kg

        # ambil kematian per kolam
        def db_call_kematian():
            return (
                db.table("Kematian")
                .select("*")
                .eq("kolam_id", kolam_id)
                .eq("user_id", user_id)
                .execute()
            )

        kematian_result = await asyncio.to_thread(db_call_kematian)
        kematian_list = getattr(kematian_result, "data", []) or []

        total_mati = sum(k["jumlah"] for k in kematian_list)
        total_ikan_hidup = max(total_ikan - total_mati, 0)

        # hitung kebutuhan pakan (misal 5% dari total berat)
        kebutuhan_pakan_gram = total_berat * 1000 * 0.05  # kg -> gram

        # ambil stok pakan
        def db_call_stok():
            return (
                db.table("PakanStok")
                .select("jumlah, satuan")
                .eq("user_id", user_id)
                .execute()
            )

        stok_result = await asyncio.to_thread(db_call_stok)
        stok_list = getattr(stok_result, "data", []) or []

        total_stok_gram = 0
        for s in stok_list:
            jumlah = float(s["jumlah"])
            if (s.get("satuan") or "g") == "kg":
                jumlah *= 1000
            total_stok_gram += jumlah

        result_list.append(
            {
                "id": kolam_id,
                "nama_kolam": kolam["nama_kolam"],
                "jumlah_ikan_hidup": total_ikan_hidup,
                "total_berat_kg": total_berat,
                "kebutuhan_pakan_gram": kebutuhan_pakan_gram,
                "stok_pakan": total_stok_gram,
            }
        )

    logger.info(f"[USER {user_id}] Ambil data kolam & pakan: {len(result_list)} kolam")
    return result_list


# ============================================================
# BUAT PEMBERIAN PAKAN OTOMATIS
# ============================================================
async def create_pemberian_pakan(
    user_id: int,
    kolam_id: int,
    tanggal: date,
    jenis_pakan: str,
    jumlah_gram: float,
    catatan: str = None,
):
    """
    Buat record PemberianPakan otomatis
    """
    db = get_db()
    payload = {
        "user_id": user_id,
        "kolam_id": kolam_id,
        "tanggal": tanggal,
        "jenis_pakan": jenis_pakan,
        "jumlah_gram": jumlah_gram,
        "catatan": catatan,
    }

    def db_call():
        return db.table("PemberianPakan").insert(payload).execute()

    try:
        result = await asyncio.to_thread(db_call)
        if getattr(result, "data", None):
            logger.info(
                f"[USER {user_id}] PemberianPakan kolam {kolam_id} {jumlah_gram}g berhasil dibuat"
            )
            return True
        else:
            logger.warning(
                f"[USER {user_id}] Gagal buat PemberianPakan kolam {kolam_id}"
            )
            return False
    except Exception as e:
        logger.error(f"[USER {user_id}] Error create_pemberian_pakan: {e}")
        return False


# ============================================================
# UPDATE PAKAN STOK SETELAH PEMBERIAN
# ============================================================
async def update_pakan_stok(user_id: int, jumlah_keluar: float):
    """
    Kurangi jumlah pakan dari PakanStok user secara proporsional
    """
    db = get_db()

    # ambil semua stok urut tanggal masuk
    def db_call():
        return (
            db.table("PakanStok")
            .select("*")
            .eq("user_id", user_id)
            .order("tanggal_masuk", "asc")
            .execute()
        )

    stok_result = await asyncio.to_thread(db_call)
    stok_list = getattr(stok_result, "data", []) or []

    sisa_keluar = jumlah_keluar
    for stok in stok_list:
        jumlah = float(stok["jumlah"])
        if (stok.get("satuan") or "g") == "kg":
            jumlah *= 1000

        if sisa_keluar <= 0:
            break

        if jumlah >= sisa_keluar:
            new_jumlah = jumlah - sisa_keluar
            if stok.get("satuan") == "kg":
                new_jumlah /= 1000  # balik ke kg

            def db_update():
                return (
                    db.table("PakanStok")
                    .update({"jumlah": new_jumlah})
                    .eq("id", stok["id"])
                    .execute()
                )

            await asyncio.to_thread(db_update)
            sisa_keluar = 0
        else:
            sisa_keluar -= jumlah

            # hapus stok habis
            def db_delete():
                return db.table("PakanStok").delete().eq("id", stok["id"]).execute()

            await asyncio.to_thread(db_delete)

    logger.info(f"[USER {user_id}] Update PakanStok, dikurangi {jumlah_keluar}g")
    return True


def get_persen_pakan(ukuran_bibit: str) -> float:
    """
    Tentuin persentase pakan harian berdasarkan ukuran bibit.
    ukuran_bibit contoh: '5-7 cm', '7-9 cm', '8-12 cm', '>13 cm'
    """
    if "5-7" in ukuran_bibit:
        return 6  # 5-7% rata-rata
    elif "7-9" in ukuran_bibit:
        return 6  # sama kayak benih kecil
    elif "8-12" in ukuran_bibit:
        return 4  # 3-5% rata-rata
    elif "13" in ukuran_bibit or ">" in ukuran_bibit:
        return 2.5  # 2-3% rata-rata
    else:
        return 3  # default kalau unknown
