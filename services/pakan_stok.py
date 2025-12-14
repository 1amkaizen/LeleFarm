# services/pakan_stok.py
import logging
import asyncio
from lib.supabase_client import get_db

logger = logging.getLogger("service_pakan_stok")


async def get_all_pakan_stok(user_id: int, kolam_id: int = None):
    """
    Ambil semua stok pakan milik user
    Bisa difilter berdasarkan kolam_id jika disediakan
    """
    db = get_db()

    def db_call():
        query = db.table("PakanStok").select("*").eq("user_id", user_id)
        if kolam_id:
            query = query.eq("kolam_id", kolam_id)
        return query.execute()

    result = await asyncio.to_thread(db_call)

    if not hasattr(result, "data") or result.data is None:
        logger.error(
            f"[PAKANSTOK] Gagal ambil data user_id={user_id}, kolam_id={kolam_id}: {result}"
        )
        return []

    return result.data


async def add_pakan_stok(
    user_id: int,
    nama_pakan: str,
    jumlah: float,
    harga: float,
    kolam_id: int = None,
    tanggal_masuk: str = None,
    satuan: str = "g",
):
    """
    Tambah stok pakan baru dengan opsional kolam_id
    """
    db = get_db()
    payload = {
        "user_id": user_id,
        "nama_pakan": nama_pakan,
        "jumlah": jumlah,
        "harga": harga,
        "kolam_id": kolam_id,
        "tanggal_masuk": tanggal_masuk,
        "satuan": satuan,
    }

    result = await asyncio.to_thread(
        lambda: db.table("PakanStok").insert(payload).execute()
    )

    if not hasattr(result, "data") or result.data is None:
        logger.error(
            f"[PAKANSTOK] Gagal tambah stok user_id={user_id}, kolam_id={kolam_id}: {result}"
        )
        return None

    logger.info(
        f"[PAKANSTOK] Stok ditambahkan user_id={user_id}, kolam_id={kolam_id}: {result.data}"
    )
    return result.data


async def edit_pakan_stok(
    user_id: int,
    pakan_stok_id: int,
    nama_pakan: str,
    jumlah: float,
    harga: float,
    kolam_id: int = None,
    tanggal_masuk: str = None,
    satuan: str = "g",
):
    """
    Update stok pakan milik user
    """
    db = get_db()
    payload = {
        "nama_pakan": nama_pakan,
        "jumlah": jumlah,
        "harga": harga,
        "kolam_id": kolam_id,
        "tanggal_masuk": tanggal_masuk,
        "satuan": satuan,
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
            f"[PAKANSTOK] Gagal edit id={pakan_stok_id} user_id={user_id}, kolam_id={kolam_id}: {result}"
        )
        return None

    logger.info(
        f"[PAKANSTOK] Stok {pakan_stok_id} berhasil diedit user_id={user_id}, kolam_id={kolam_id}"
    )
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
