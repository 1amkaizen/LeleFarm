# services/kematian.py
import logging
import asyncio
from lib.supabase_client import get_db

logger = logging.getLogger("service_kematian")


# ============================================================
# AMBIL SEMUA KEMATIAN (FILTER USER)
# ============================================================
async def get_all_kematian(user_id: int):
    """
    Ambil semua data kematian untuk user tertentu
    """
    db = get_db()

    def db_call():
        return (
            db.table("Kematian")
            .select("*")
            .eq("user_id", user_id)
            .order("tanggal", desc=True)
            .execute()
        )

    try:
        result = await asyncio.to_thread(db_call)

        if not getattr(result, "data", None):
            logger.warning(f"Tidak ada data kematian untuk user_id={user_id}")
            return []

        logger.info(f"Ambil {len(result.data)} data kematian untuk user_id={user_id}")
        return result.data

    except Exception as e:
        logger.error(f"Gagal ambil kematian untuk user_id={user_id}: {e}")
        return []


# ============================================================
# BUAT KEMATIAN BARU
# ============================================================
async def create_kematian(
    user_id: int, kolam_id: int, tanggal: str, jumlah: int, catatan: str = None
):
    """
    Tambah data kematian lele untuk user tertentu
    """
    db = get_db()
    payload = {
        "user_id": user_id,
        "kolam_id": kolam_id,
        "tanggal": tanggal,
        "jumlah": jumlah,
        "catatan": catatan,
    }

    def db_call():
        return db.table("Kematian").insert(payload).execute()

    try:
        result = await asyncio.to_thread(db_call)

        if not getattr(result, "data", None):
            logger.error(f"Gagal input data kematian untuk user_id={user_id}: {result}")
            return None

        logger.info(
            f"Kematian ditambahkan user_id={user_id} kolam_id={kolam_id} jumlah={jumlah}"
        )
        return result.data[0]

    except Exception as e:
        logger.error(f"Error create_kematian user_id={user_id}: {e}")
        return None
