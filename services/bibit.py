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
    total_berat: float = 0,  # Tambahkan parameter total_berat
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
        "total_berat": total_berat,  # Sertakan total_berat
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
            f"Bibit ditambahkan user_id={user_id} kolam_id={kolam_id} jumlah={jumlah} total_berat={total_berat}"
        )
        return result.data[0]

    except Exception as e:
        logger.error(f"Error create_bibit user_id={user_id}: {e}")
        return None


# ============================================================
# EDIT BIBIT
# ============================================================
async def edit_bibit(
    bibit_id: int,
    kolam_id: int = None,
    ukuran_bibit: str = None,
    jumlah: int = None,
    total_harga: float = None,
    catatan: str = None,
    tanggal_tebar: str = None,
    user_id: int = None,
    total_berat: float = None,  # Tambahkan parameter total_berat
):
    """
    Update data bibit berdasarkan bibit_id dan user_id
    """
    db = get_db()
    payload = {}

    if kolam_id is not None:
        payload["kolam_id"] = kolam_id
    if ukuran_bibit is not None:
        payload["ukuran_bibit"] = ukuran_bibit
    if jumlah is not None:
        payload["jumlah"] = jumlah
    if total_harga is not None:
        payload["total_harga"] = total_harga
    if catatan is not None:
        payload["catatan"] = catatan
    if tanggal_tebar is not None:
        payload["tanggal_tebar"] = tanggal_tebar
    if total_berat is not None:
        payload["total_berat"] = total_berat  # Sertakan total_berat

    if not payload:
        logger.warning(f"Tidak ada field untuk update bibit_id={bibit_id}")
        return False

    def db_call():
        return (
            db.table("Bibit")
            .update(payload)
            .eq("id", bibit_id)
            .eq("user_id", user_id)
            .execute()
        )

    try:
        result = await asyncio.to_thread(db_call)
        if getattr(result, "data", None):
            logger.info(f"Bibit {bibit_id} berhasil diupdate user_id={user_id}")
            return True
        else:
            logger.warning(f"Gagal update bibit {bibit_id} user_id={user_id}")
            return False
    except Exception as e:
        logger.error(f"Error edit_bibit bibit_id={bibit_id} user_id={user_id}: {e}")
        return False


# ============================================================
# DELETE BIBIT
# ============================================================
async def delete_bibit(bibit_id: int, user_id: int = None):
    """
    Hapus bibit berdasarkan bibit_id dan user_id
    """
    db = get_db()

    def db_call():
        return (
            db.table("Bibit")
            .delete()
            .eq("id", bibit_id)
            .eq("user_id", user_id)
            .execute()
        )

    try:
        result = await asyncio.to_thread(db_call)
        if getattr(result, "data", None):
            logger.info(f"Bibit {bibit_id} berhasil dihapus user_id={user_id}")
            return True
        else:
            logger.warning(f"Gagal hapus bibit {bibit_id} user_id={user_id}")
            return False
    except Exception as e:
        logger.error(f"Error delete_bibit bibit_id={bibit_id} user_id={user_id}: {e}")
        return False
