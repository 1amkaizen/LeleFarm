# services/kolam.py
import logging
import asyncio
from lib.supabase_client import get_db

logger = logging.getLogger("service_kolam")


async def get_all_kolam(user_id: int):
    """
    Ambil semua kolam milik user tertentu
    """
    db = get_db()

    def db_call():
        result = (
            db.table("Kolam")
            .select("*")
            .eq("user_id", user_id)
            .order("id", desc=True)
            .execute()
        )
        return result

    result = await asyncio.to_thread(db_call)

    if not hasattr(result, "data") or result.data is None:
        logger.error(f"[KOLAM] Error ambil data user_id={user_id}: {result}")
        return []

    return result.data


async def create_kolam(
    user_id: int,
    nama_kolam: str,
    kapasitas_bibit: int,
    tanggal_mulai: str,
    catatan: str = None,
):
    """
    Buat kolam untuk user tertentu
    """
    db = get_db()
    payload = {
        "user_id": user_id,
        "nama_kolam": nama_kolam,
        "kapasitas_bibit": kapasitas_bibit,
        "tanggal_mulai": tanggal_mulai,
        "catatan": catatan,
    }

    def db_call():
        return db.table("Kolam").insert(payload).execute()

    result = await asyncio.to_thread(db_call)

    if not hasattr(result, "data") or result.data is None:
        logger.error(f"[KOLAM] Gagal buat kolam user_id={user_id}: {result}")
        return None

    return result.data[0]


async def get_kolam_by_id(kolam_id: int, user_id: int):
    """
    Ambil 1 kolam berdasarkan id & user_id
    """
    db = get_db()

    def db_call():
        return (
            db.table("Kolam")
            .select("*")
            .eq("id", kolam_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )

    result = await asyncio.to_thread(db_call)

    if not hasattr(result, "data") or result.data is None:
        logger.error(
            f"[KOLAM] Kolam id={kolam_id} tidak ditemukan untuk user_id={user_id}"
        )
        return None

    return result.data


async def edit_kolam(
    user_id: int,
    kolam_id: int,
    nama_kolam: str = None,
    kapasitas_bibit: int = None,
    tanggal_mulai: str = None,
    catatan: str = None,
):
    """
    Update data kolam (hanya milik user terkait)
    """
    kolam = await get_kolam_by_id(kolam_id, user_id)
    if not kolam:
        logger.error(
            f"[KOLAM] Gagal edit kolam id={kolam_id}: tidak ditemukan untuk user_id={user_id}"
        )
        return None

    update_data = {}
    if nama_kolam is not None:
        update_data["nama_kolam"] = nama_kolam
    if kapasitas_bibit is not None:
        update_data["kapasitas_bibit"] = kapasitas_bibit
    if tanggal_mulai is not None:
        update_data["tanggal_mulai"] = tanggal_mulai
    if catatan is not None:
        update_data["catatan"] = catatan

    if not update_data:
        logger.warning(f"[KOLAM] Tidak ada perubahan untuk kolam id={kolam_id}")
        return kolam

    db = get_db()

    def db_call():
        return (
            db.table("Kolam")
            .update(update_data)
            .eq("id", kolam_id)
            .eq("user_id", user_id)
            .execute()
        )

    result = await asyncio.to_thread(db_call)

    if not hasattr(result, "data") or result.data is None:
        logger.error(
            f"[KOLAM] Gagal update kolam id={kolam_id} untuk user_id={user_id}: {result}"
        )
        return None

    logger.info(f"[KOLAM] Kolam id={kolam_id} berhasil diperbarui user_id={user_id}")
    return result.data[0]


async def delete_kolam(kolam_id: int, user_id: int):
    """
    Hapus kolam milik user tertentu
    """
    kolam = await get_kolam_by_id(kolam_id, user_id)
    if not kolam:
        logger.error(
            f"[KOLAM] Gagal hapus kolam id={kolam_id}: tidak ditemukan untuk user_id={user_id}"
        )
        return False

    db = get_db()

    def db_call():
        return (
            db.table("Kolam")
            .delete()
            .eq("id", kolam_id)
            .eq("user_id", user_id)
            .execute()
        )

    result = await asyncio.to_thread(db_call)

    if hasattr(result, "data") and result.data is not None:
        logger.info(f"[KOLAM] Kolam id={kolam_id} berhasil dihapus user_id={user_id}")
        return True

    logger.error(
        f"[KOLAM] Gagal hapus kolam id={kolam_id} untuk user_id={user_id}: {result}"
    )
    return False


def get_kolam_status(kolam_entry):
    """
    Tentukan status kolam: 'Sudah Panen' jika kolam punya data panen > 0
    'Belum Panen' jika belum ada panen
    """
    try:
        if kolam_entry.get("jumlah_panen", 0) > 0:
            return "Sudah Panen"
        return "Belum Panen"
    except Exception as e:
        logger.error(f"Gagal hitung status kolam id={kolam_entry.get('id')}: {e}")
        return "Belum Panen"
