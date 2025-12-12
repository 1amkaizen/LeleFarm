# services/pakan_stok.py
import logging
import asyncio
from lib.supabase_client import get_db

logger = logging.getLogger("service_pakan_stok")


async def get_all_pakan_stok(user_id: int):
    """
    Ambil semua stok pakan milik user
    """
    db = get_db()
    result = await asyncio.to_thread(
        lambda: db.table("PakanStok").select("*").eq("user_id", user_id).execute()
    )

    if not hasattr(result, "data") or result.data is None:
        logger.error(f"[PAKANSTOK] Gagal ambil data user_id={user_id}: {result}")
        return []

    return result.data


async def add_pakan_stok(
    user_id: int,
    nama_pakan: str,
    jumlah: float,
    harga: float,
    tanggal_masuk: str = None,
    satuan: str = "g",  # baru
):
    """
    Tambah stok pakan baru
    """
    db = get_db()
    payload = {
        "user_id": user_id,
        "nama_pakan": nama_pakan,
        "jumlah": jumlah,
        "harga": harga,
        "tanggal_masuk": tanggal_masuk,
        "satuan": satuan,  # baru
    }

    result = await asyncio.to_thread(
        lambda: db.table("PakanStok").insert(payload).execute()
    )

    if not hasattr(result, "data") or result.data is None:
        logger.error(f"[PAKANSTOK] Gagal tambah stok user_id={user_id}: {result}")
        return None

    logger.info(f"[PAKANSTOK] Stok ditambahkan user_id={user_id}: {result.data}")
    return result.data


async def edit_pakan_stok(
    user_id: int,
    pakan_stok_id: int,
    nama_pakan: str,
    jumlah: float,
    harga: float,
    tanggal_masuk: str = None,
    satuan: str = "g",  # baru
):
    """
    Update stok pakan milik user
    """
    db = get_db()
    payload = {
        "nama_pakan": nama_pakan,
        "jumlah": jumlah,
        "harga": harga,
        "tanggal_masuk": tanggal_masuk,
        "satuan": satuan,  # baru
    }

    result = await asyncio.to_thread(
        lambda: db.table("PakanStok")
        .update(payload)
        .eq("id", pakan_stok_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not hasattr(result, "data") or result.data is None:
        logger.error(
            f"[PAKANSTOK] Gagal edit id={pakan_stok_id} user_id={user_id}: {result}"
        )
        return None

    logger.info(f"[PAKANSTOK] Stok {pakan_stok_id} berhasil diedit user_id={user_id}")
    return result.data


async def delete_pakan_stok(user_id: int, pakan_stok_id: int):
    """
    Hapus stok pakan milik user
    """
    db = get_db()
    result = await asyncio.to_thread(
        lambda: db.table("PakanStok")
        .delete()
        .eq("id", pakan_stok_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not hasattr(result, "data") or result.data is None:
        logger.error(
            f"[PAKANSTOK] Gagal hapus id={pakan_stok_id} user_id={user_id}: {result}"
        )
        return False

    logger.info(f"[PAKANSTOK] Stok {pakan_stok_id} berhasil dihapus user_id={user_id}")
    return True
