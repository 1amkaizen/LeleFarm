# services/ai/client.py
import os
import logging
from google import genai

logger = logging.getLogger("ai_client")


def get_gemini_client():
    """
    Membuat client Gemini menggunakan SDK resmi google-genai.
    API key diambil dari ENV: GEMINI_API_KEY
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY belum diset")

    client = genai.Client(api_key=api_key)
    logger.info("Gemini GenAI client initialized")
    return client
