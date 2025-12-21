# services/ai/schema.py
from typing import TypedDict, List


class RingkasanAIResult(TypedDict):
    summary: str
    warnings: List[str]
