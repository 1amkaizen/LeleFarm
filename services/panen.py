# services/panen.py
import logging
import asyncio
from lib.supabase_client import get_db

logger = logging.getLogger("service_panen")


# ============================================================
# AMBIL SEMUA PANEN PER USER / PER KOLAM
# ============================================================
async def get_all_panen(user_id: int = None, kolam_id: int = None):
    """
    Ambil data panen. Bisa filter per user_id dan/atau kolam_id.
    """
    db = get_db()

    def db_call():
        query = db.table("Panen").select("*").order("tanggal_panen", desc=True)
        if user_id:
            query = query.eq("user_id", user_id)
        if kolam_id:
            query = query.eq("kolam_id", kolam_id)
        return query.execute()

    try:
        result = await asyncio.to_thread(db_call)
        if not getattr(result, "data", None):
            logger.info(f"Tidak ada panen untuk user_id={user_id} kolam_id={kolam_id}")
            return []
        return result.data
    except Exception as e:
        logger.error(f"Gagal ambil panen user_id={user_id} kolam_id={kolam_id}: {e}")
        return []


# ============================================================
# TAMBAH PANEN BARU
# ============================================================
async def create_panen(
    kolam_id: int,
    
    total_berat: float,
    total_jual: float = 0,
    catatan: str = None,
    tanggal_panen: str = None,
    user_id: int = None,
):
    """
    Tambah panen baru. Cek dulu apakah sudah ada panen sama di kolam untuk tanggal sama.
    """
    db = get_db()
    if not tanggal_panen:
        from datetime import date

        tanggal_panen = date.today().isoformat()

    # --- Cek duplikat ---
    existing = await get_all_panen(user_id=user_id, kolam_id=kolam_id)
    for p in existing:
        if p.get("tanggal_panen") == tanggal_panen:
            logger.warning(
                f"Panen sudah tercatat untuk kolam {kolam_id} tanggal {tanggal_panen}"
            )
            return None

    payload = {
        "user_id": user_id,
        "kolam_id": kolam_id,
      
        "total_berat": total_berat,
        "total_jual": total_jual,  # <- tambahan field
        "catatan": catatan or f"Panen otomatis pada {tanggal_panen}",
        "tanggal_panen": tanggal_panen,
    }

    def db_call():
        return db.table("Panen").insert(payload).execute()

    try:
        result = await asyncio.to_thread(db_call)
        if not getattr(result, "data", None):
            logger.error(f"Gagal input panen user_id={user_id} kolam_id={kolam_id}")
            return None

        logger.info(f"Panen ditambahkan user_id={user_id} kolam_id={kolam_id}")
        # update status kolam
        await update_status_kolam(kolam_id, user_id)
        return result.data[0]
    except Exception as e:
        logger.error(f"Error create_panen user_id={user_id} kolam_id={kolam_id}: {e}")
        return None


# ============================================================
# UPDATE STATUS KOLAM
# ============================================================
async def update_status_kolam(kolam_id: int, user_id: int):
    db = get_db()

    def db_call():
        return (
            db.table("Kolam")
            .update({"status_panen": "sudah"})
            .eq("id", kolam_id)
            .eq("user_id", user_id)
            .execute()
        )

    try:
        result = await asyncio.to_thread(db_call)
        if getattr(result, "data", None):
            logger.info(f"Kolam {kolam_id} status_panen diupdate jadi 'sudah'")
            return True
        return False
    except Exception as e:
        logger.error(f"Error update status kolam {kolam_id}: {e}")
        return False


# ============================================================
# EDIT PANEN
# ============================================================
async def edit_panen(
    panen_id: int,
    user_id: int,
    
    total_berat: float = None,
    total_jual: float = None,
    catatan: str = None,
    tanggal_panen: str = None,
):
    db = get_db()
    payload = {}
    if total_berat is not None:
        payload["total_berat"] = total_berat
    if total_jual is not None:
        payload["total_jual"] = total_jual  # <- tambahan field
    if catatan is not None:
        payload["catatan"] = catatan
    if tanggal_panen is not None:
        payload["tanggal_panen"] = tanggal_panen

    if not payload:
        logger.warning(f"Tidak ada field untuk update panen_id={panen_id}")
        return False

    def db_call():
        return (
            db.table("Panen")
            .update(payload)
            .eq("id", panen_id)
            .eq("user_id", user_id)
            .execute()
        )

    try:
        result = await asyncio.to_thread(db_call)
        if getattr(result, "data", None):
            logger.info(f"Panen {panen_id} berhasil diupdate")
            return True
        return False
    except Exception as e:
        logger.error(f"Error edit_panen panen_id={panen_id}: {e}")
        return False


