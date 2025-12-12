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


# ============================================================
# UPDATE KEMATIAN
# ============================================================
async def update_kematian(
    kematian_id: int,
    user_id: int,
    kolam_id: int = None,
    tanggal: str = None,
    jumlah: int = None,
    catatan: str = None,
):
    """
    Update data kematian tertentu milik user
    """
    db = get_db()
    payload = {}
    if kolam_id is not None:
        payload["kolam_id"] = kolam_id
    if tanggal is not None:
        payload["tanggal"] = tanggal
    if jumlah is not None:
        payload["jumlah"] = jumlah
    if catatan is not None:
        payload["catatan"] = catatan

    if not payload:
        logger.warning(
            f"[USER {user_id}] Tidak ada data yang diupdate untuk kematian_id={kematian_id}"
        )
        return None

    def db_call():
        return (
            db.table("Kematian")
            .update(payload)
            .eq("id", kematian_id)
            .eq("user_id", user_id)
            .execute()
        )

    try:
        result = await asyncio.to_thread(db_call)
        if not getattr(result, "data", None):
            logger.warning(f"[USER {user_id}] Gagal update kematian_id={kematian_id}")
            return None

        logger.info(f"[USER {user_id}] Kematian_id={kematian_id} berhasil diupdate")
        return result.data[0]

    except Exception as e:
        logger.error(
            f"Error update_kematian user_id={user_id} kematian_id={kematian_id}: {e}"
        )
        return None


# ============================================================
# DELETE KEMATIAN
# ============================================================
async def delete_kematian(kematian_id: int, user_id: int):
    """
    Hapus data kematian milik user
    """
    db = get_db()

    def db_call():
        return (
            db.table("Kematian")
            .delete()
            .eq("id", kematian_id)
            .eq("user_id", user_id)
            .execute()
        )

    try:
        result = await asyncio.to_thread(db_call)
        if not getattr(result, "data", None):
            logger.warning(f"[USER {user_id}] Gagal hapus kematian_id={kematian_id}")
            return False

        logger.info(f"[USER {user_id}] Kematian_id={kematian_id} berhasil dihapus")
        return True

    except Exception as e:
        logger.error(
            f"Error delete_kematian user_id={user_id} kematian_id={kematian_id}: {e}"
        )
        return False
