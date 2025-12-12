# lib/supabase_client.py
# Koneksi Supabase + helper fungsi untuk query
import logging
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Muat env
load_dotenv()

logger = logging.getLogger("supabase_client")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("SUPABASE_URL atau SUPABASE_KEY tidak ditemukan di .env")

_supabase: Client | None = None


def get_db() -> Client:
    """
    Mengembalikan client Supabase.
    Koneksi dibuat sekali, lalu dipakai ulang.
    """
    global _supabase

    if _supabase is None:
        try:
            logger.info("Membuat koneksi Supabase...")
            _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Koneksi Supabase berhasil dibuat.")
        except Exception as e:
            logger.error(f"Gagal membuat koneksi Supabase: {e}")
            raise e

    return _supabase
