# services/ai/ringkasan_ai.py
import json
import logging
import asyncio
from typing import Dict, Any

from google.genai import types
from services.ai.client import get_gemini_client
from services.ai.prompt import SYSTEM_PROMPT, ringkasan_prompt
from services.ai.schema import RingkasanAIResult

logger = logging.getLogger("ai_ringkasan")


def _normalize_status(status: str) -> str:
    if status not in {"Stabil", "Waspada", "Berisiko"}:
        return "Tidak Diketahui"
    return status


def _sanitize_ai_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    kolam_data = []
    for k in raw_data["pengeluaran_per_kolam"]:
        kolam_data.append(
            {
                "nama": k["nama_kolam"],
                "status": k["status_label"],
                "total_pengeluaran": k["total_pengeluaran"],
                "bibit": k["bibit"]["total_harga"],
                "pakan": k["pakan"]["total_harga"],
                "operasional": k["operasional"]["total_harga"],
                "kematian": k["kematian"]["total_ekor"],
            }
        )

    return {
        "total_pengeluaran": raw_data["total_pengeluaran_semua_kolam"][
            "total_pengeluaran"
        ],
        "total_kematian": raw_data["total_kematian"],
        "jumlah_kolam": len(raw_data["pengeluaran_per_kolam"]),
        "kolam": kolam_data,
    }


# services/ai/ringkasan_ai.py
async def generate_ringkasan_ai(raw_data: Dict[str, Any]) -> RingkasanAIResult:
    logger.info("Generate AI ringkasan dimulai")

    client = get_gemini_client()
    data_for_ai = _sanitize_ai_data(raw_data)
    user_prompt = ringkasan_prompt(data_for_ai)

    loop = asyncio.get_event_loop()

    def _call_ai():
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        return response.text

    try:
        result_text = await loop.run_in_executor(None, _call_ai)
        result_json = json.loads(result_text)

        status = _normalize_status(result_json.get("status", ""))

        warnings = result_json.get("warnings")
        recommendations = result_json.get("recommendations")

        # normalisasi warnings
        if not isinstance(warnings, list):
            warnings = [str(warnings)] if warnings else []

        # normalisasi & PAKSA recommendations
        if not isinstance(recommendations, list) or len(recommendations) == 0:
            recommendations = [
                "Lakukan evaluasi biaya bibit dengan membandingkan tingkat kematian dan performa pertumbuhan untuk menekan risiko kerugian pada siklus berikutnya."
            ]


        logger.info("AI ringkasan berhasil dibuat")

        return {
            "status": status,
            "summary": result_json.get("summary", ""),
            "warnings": warnings,
            "recommendations": recommendations,
        }

    except Exception as e:
        logger.error(f"AI ringkasan gagal: {e}")

        return {
            "status": "Tidak Diketahui",
            "summary": "Analisis gagal dibuat karena kendala pemrosesan data atau respon AI.",
            "warnings": ["Respon AI tidak valid atau tidak dapat diproses."],
            "recommendations": [
                "Coba ulangi proses analisis atau periksa kelengkapan data input."
            ],
        }
