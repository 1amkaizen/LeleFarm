# services/bibit.py
import logging
import asyncio
from lib.supabase_client import get_db

logger = logging.getLogger("service_bibit")


# ============================================================
# AMBIL SEMUA BIBIT (FILTER BERDASARKAN USER)
# ============================================================
async def get_all_bibit(user_id: int):
    """
    Ambil semua data bibit milik user tertentu,
    urut berdasarkan tanggal_tebar descending.
    """
    db = get_db()

    def db_call():
        return (
            db.table("Bibit")
            .select("*")
            .eq("user_id", user_id)
            .order("tanggal_tebar", desc=True)
            .execute()
        )

    try:
        result = await asyncio.to_thread(db_call)

        if not getattr(result, "data", None):
            logger.warning(f"Tidak ada bibit untuk user_id={user_id}")
            return []

        logger.info(f"Ambil {len(result.data)} data bibit untuk user_id={user_id}")
        return result.data

    except Exception as e:
        logger.error(f"Gagal ambil bibit untuk user_id={user_id}: {e}")
        return []


# ============================================================
# BUAT BIBIT BARU (DENGAN USER_ID)
# ============================================================
async def create_bibit(
    kolam_id: int,
    ukuran_bibit: str,
    jumlah: int,
    total_harga: float = 0,
    catatan: str = None,
    tanggal_tebar: str = None,
    user_id: int = None,
):
    """
    Tambah data bibit ke kolam tertentu untuk user tertentu.
    """
    db = get_db()

    payload = {
        "user_id": user_id,
        "kolam_id": kolam_id,
        "ukuran_bibit": ukuran_bibit,
        "jumlah": jumlah,
        "total_harga": total_harga,
        "catatan": catatan,
    }

    if tanggal_tebar:
        payload["tanggal_tebar"] = tanggal_tebar

    def db_call():
        return db.table("Bibit").insert(payload).execute()

    try:
        result = await asyncio.to_thread(db_call)

        if not getattr(result, "data", None):
            logger.error(f"Gagal input bibit untuk user_id={user_id}: {result}")
            return None

        logger.info(
            f"Bibit ditambahkan user_id={user_id} kolam_id={kolam_id} jumlah={jumlah}"
        )
        return result.data[0]

    except Exception as e:
        logger.error(f"Error create_bibit user_id={user_id}: {e}")
        return None
