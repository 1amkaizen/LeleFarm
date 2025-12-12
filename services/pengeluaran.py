# services/pengeluaran.py
import logging
import asyncio
from lib.supabase_client import get_db

logger = logging.getLogger("service_pengeluaran")


# ============================================================
# AMBIL SEMUA PENGELUARAN (FILTER USER)
# ============================================================
async def get_all_pengeluaran(user_id: int):
    """
    Ambil semua pengeluaran milik user tertentu, urut dari tanggal terbaru.
    """
    db = get_db()

    def db_call():
        return (
            db.table("Pengeluaran")
            .select("*")
            .eq("user_id", user_id)
            .order("tanggal", desc=True)
            .execute()
        )

    try:
        result = await asyncio.to_thread(db_call)

        if not getattr(result, "data", None):
            logger.warning(f"Tidak ada pengeluaran untuk user_id={user_id}")
            return []

        logger.info(f"Ambil {len(result.data)} pengeluaran untuk user_id={user_id}")
        return result.data

    except Exception as e:
        logger.error(f"Gagal ambil pengeluaran untuk user_id={user_id}: {e}")
        return []


# ============================================================
# BUAT PENGELUARAN BARU
# ============================================================
async def create_pengeluaran(
    user_id: int,
    nama_pengeluaran: str,
    harga: float,
    tanggal: str,
    jumlah: int = 1,
    catatan: str = None,
):
    """
    Buat entry pengeluaran baru untuk user tertentu
    """
    db = get_db()
    payload = {
        "user_id": user_id,
        "nama_pengeluaran": nama_pengeluaran,
        "harga": harga,
        "tanggal": tanggal,
        "jumlah": jumlah,
        "catatan": catatan,
    }

    def db_call():
        return db.table("Pengeluaran").insert(payload).execute()

    try:
        result = await asyncio.to_thread(db_call)

        if not getattr(result, "data", None):
            logger.error(f"Gagal buat pengeluaran user_id={user_id}: {result}")
            return None

        logger.info(f"Pengeluaran baru ditambahkan user_id={user_id}: {result.data}")
        return result.data[0]

    except Exception as e:
        logger.error(f"Error create_pengeluaran user_id={user_id}: {e}")
        return None
