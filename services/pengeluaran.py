# services/pengeluaran.py
import logging
import asyncio
from lib.supabase_client import get_db

logger = logging.getLogger("service_pengeluaran")


# ============================================================
# AMBIL SEMUA PENGELUARAN (FILTER USER)
# ============================================================
async def get_all_pengeluaran(user_id: int):
    db = get_db()

    def db_call():
        # ambil pengeluaran beserta nama kolam
        return (
            db.table("Pengeluaran")
            .select("*, Kolam(nama_kolam)")
            .eq("user_id", user_id)
            .order("tanggal", desc=True)
            .execute()
        )

    result = await asyncio.to_thread(db_call)
    if not getattr(result, "data", None):
        return []

    # gabung nama kolam ke dict pengeluaran
    pengeluaran_list = []
    for p in result.data:
        p["nama_kolam"] = p.get("Kolam", {}).get("nama_kolam", "-")
        pengeluaran_list.append(p)
    return pengeluaran_list


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
    kolam_id: int = None,  # baru
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
        "kolam_id": kolam_id,  # baru
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


# ============================================================
# UPDATE PENGELUARAN
# ============================================================
async def update_pengeluaran(
    pengeluaran_id: int,
    user_id: int,
    nama_pengeluaran: str = None,
    harga: float = None,
    tanggal: str = None,
    jumlah: int = None,
    catatan: str = None,
    kolam_id: int = None,  # baru
):
    """
    Update pengeluaran tertentu milik user
    """
    db = get_db()
    payload = {}
    if nama_pengeluaran is not None:
        payload["nama_pengeluaran"] = nama_pengeluaran
    if harga is not None:
        payload["harga"] = harga
    if tanggal is not None:
        payload["tanggal"] = tanggal
    if jumlah is not None:
        payload["jumlah"] = jumlah
    if catatan is not None:
        payload["catatan"] = catatan
    if kolam_id is not None:
        payload["kolam_id"] = kolam_id  # baru

    if not payload:
        logger.warning(
            f"Tidak ada data yang diupdate untuk pengeluaran_id={pengeluaran_id}"
        )
        return None

    def db_call():
        return (
            db.table("Pengeluaran")
            .update(payload)
            .eq("id", pengeluaran_id)
            .eq("user_id", user_id)
            .execute()
        )

    try:
        result = await asyncio.to_thread(db_call)

        if not getattr(result, "data", None):
            logger.warning(
                f"Gagal update pengeluaran_id={pengeluaran_id} atau tidak ditemukan"
            )
            return None

        logger.info(f"Pengeluaran_id={pengeluaran_id} berhasil diupdate: {result.data}")
        return result.data[0]

    except Exception as e:
        logger.error(f"Error update_pengeluaran pengeluaran_id={pengeluaran_id}: {e}")
        return None


# ============================================================
# HAPUS PENGELUARAN
# ============================================================
async def delete_pengeluaran(pengeluaran_id: int, user_id: int):
    """
    Hapus pengeluaran tertentu milik user
    """
    db = get_db()

    def db_call():
        return (
            db.table("Pengeluaran")
            .delete()
            .eq("id", pengeluaran_id)
            .eq("user_id", user_id)
            .execute()
        )

    try:
        result = await asyncio.to_thread(db_call)

        if not getattr(result, "data", None):
            logger.warning(
                f"Gagal hapus pengeluaran_id={pengeluaran_id} atau tidak ditemukan"
            )
            return False

        logger.info(f"Pengeluaran_id={pengeluaran_id} berhasil dihapus")
        return True

    except Exception as e:
        logger.error(f"Error delete_pengeluaran pengeluaran_id={pengeluaran_id}: {e}")
        return False
