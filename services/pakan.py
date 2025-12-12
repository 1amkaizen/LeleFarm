# services/pakan.py
# Lokasi file: services/pakan.py

import logging
from lib.supabase_client import get_db
import asyncio

logger = logging.getLogger("service_pakan")


async def get_all_pakan(user_id: int, kolam_id: int = None):
    """
    Ambil semua pakan milik user tertentu.
    Jika kolam_id diberikan, ambil hanya untuk kolam tersebut.
    """
    db = get_db()
    query = db.table("Pakan").select("*").eq("user_id", user_id)

    if kolam_id:
        query = query.eq("kolam_id", kolam_id)

    result = await asyncio.to_thread(query.execute)

    if not hasattr(result, "data") or result.data is None:
        logger.error(f"[PAKAN] Error ambil data user_id={user_id}: {result}")
        return []

    return result.data


async def add_pakan(
    user_id: int,
    kolam_id: int,
    tanggal: str,
    jenis_pakan: str,
    jumlah_gram: float,
    catatan: str = None,
):
    """
    Tambah pakan untuk user tertentu
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

    result = await asyncio.to_thread(
        lambda: db.table("Pakan").insert(payload).execute()
    )

    if not hasattr(result, "data") or result.data is None:
        logger.error(f"[PAKAN] Gagal tambah pakan user_id={user_id}: {result}")
        return None

    logger.info(f"[PAKAN] Pakan ditambahkan user_id={user_id}: {result.data}")
    return result.data


async def edit_pakan(
    user_id: int,
    pakan_id: int,
    kolam_id: int,
    tanggal: str,
    jenis_pakan: str,
    jumlah_gram: float,
    catatan: str = None,
):
    """
    Update pakan milik user tertentu
    """
    db = get_db()

    payload = {
        "kolam_id": kolam_id,
        "tanggal": tanggal,
        "jenis_pakan": jenis_pakan,
        "jumlah_gram": jumlah_gram,
        "catatan": catatan,
    }

    result = await asyncio.to_thread(
        lambda: db.table("Pakan")
        .update(payload)
        .eq("id", pakan_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not hasattr(result, "data") or result.data is None:
        logger.error(
            f"[PAKAN] Gagal edit pakan id={pakan_id} user_id={user_id}: {result}"
        )
        return None

    logger.info(f"[PAKAN] Pakan {pakan_id} berhasil diedit user_id={user_id}")
    return result.data


async def delete_pakan(user_id: int, pakan_id: int):
    """
    Hapus pakan milik user tertentu
    """
    db = get_db()

    result = await asyncio.to_thread(
        lambda: db.table("Pakan")
        .delete()
        .eq("id", pakan_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not hasattr(result, "data") or result.data is None:
        logger.error(
            f"[PAKAN] Gagal hapus pakan id={pakan_id} user_id={user_id}: {result}"
        )
        return False

    logger.info(f"[PAKAN] Pakan {pakan_id} berhasil dihapus user_id={user_id}")
    return True
