# services/kolam.py
import logging
import asyncio
from datetime import date
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
    Tentukan status kolam sesuai database: 'belum' atau 'sudah'
    """
    try:
        if kolam_entry.get("jumlah_panen", 0) > 0:
            return "sudah"
        return "belum"
    except Exception as e:
        logger.error(f"Gagal hitung status kolam id={kolam_entry.get('id')}: {e}")
        return "belum"


async def update_status_kolam(user_id: int, kolam_id: int, status: str):
    """
    Update status panen kolam (belum / sudah) milik user terkait.
    Jika status menjadi 'sudah', catat panen ke tabel Panen tanpa duplikat.
    """
    logger.info(
        f"[KOLAM] Request update status_panen kolam id={kolam_id} "
        f"user_id={user_id} status={status}"
    )

    if status not in ("belum", "sudah"):
        logger.error(f"[KOLAM] Status panen tidak valid: {status}")
        return None

    db = get_db()

    # Ambil data kolam dulu
    kolam = await asyncio.to_thread(
        lambda: db.table("Kolam")
        .select("*")
        .eq("id", kolam_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not hasattr(kolam, "data") or not kolam.data:
        logger.error(
            f"[KOLAM] Kolam id={kolam_id} tidak ditemukan untuk user_id={user_id}"
        )
        return None

    kolam_data = kolam.data

    # Kalau status sama, skip
    if kolam_data.get("status_panen") == status:
        logger.info(
            f"[KOLAM] Status panen kolam id={kolam_id} sudah '{status}', skip update"
        )
        return kolam_data

    # Update status kolam
    update_res = await asyncio.to_thread(
        lambda: db.table("Kolam")
        .update({"status_panen": status})
        .eq("id", kolam_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not hasattr(update_res, "data") or not update_res.data:
        logger.error(
            f"[KOLAM] Gagal update status_panen kolam id={kolam_id} user_id={user_id}"
        )
        return None

    logger.info(
        f"[KOLAM] Status panen kolam id={kolam_id} berhasil diubah ke '{status}'"
    )

    # Jika sudah panen, catat ke tabel Panen, tapi cek dulu jangan duplikat hari ini
    if status == "sudah":
        today = date.today().isoformat()

        # cek apakah panen hari ini sudah ada
        exists_res = await asyncio.to_thread(
            lambda: db.table("Panen")
            .select("*")
            .eq("kolam_id", kolam_id)
            .eq("user_id", user_id)
            .eq("tanggal_panen", today)
            .execute()
        )

        if exists_res.data:
            logger.info(
                f"Panen kolam id={kolam_id} hari ini sudah tercatat, skip insert"
            )
        else:
            panen_payload = {
                "user_id": user_id,
                "kolam_id": kolam_id,
                "nama_kolam": kolam_data.get("nama_kolam"),
                "tanggal_panen": today,
                "jumlah_ikan": kolam_data.get("jumlah_ikan", 0),
                "total_berat": kolam_data.get("total_berat", 0),
                "catatan": f"Panen otomatis pada {today}",
            }

            panen_res = await asyncio.to_thread(
                lambda: db.table("Panen").insert(panen_payload).execute()
            )

            if hasattr(panen_res, "error") and panen_res.error:
                logger.error(
                    f"Gagal catat panen kolam id={kolam_id}: {panen_res.error}"
                )
            else:
                logger.info(
                    f"Panen kolam id={kolam_id} tercatat di tabel Panen tanggal={today}"
                )

    return update_res.data[0]
