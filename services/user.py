# services/user.py
import logging
from lib.supabase_client import get_db

logger = logging.getLogger("service_user")


async def get_user_by_id(user_id: int):
    """
    Ambil user dari Supabase berdasarkan ID
    """
    db = get_db()
    try:
        result = db.table("Users").select("*").eq("id", user_id).single().execute()
    except Exception as e:
        logger.error(f"Gagal ambil user {user_id}: {e}")
        return None

    if not result.data:
        logger.warning(f"User {user_id} tidak ditemukan")
        return None

    return result.data
