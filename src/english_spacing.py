"""Restore spaces in concatenated English ASR output using wordninja."""
import re
import sys
from pathlib import Path


_WORD_RUN = re.compile(r"[A-Za-z]{7,}")


def add_english_spaces(text):
    if not _WORD_RUN.search(text):
        return text

    vendor_dir = str(Path(__file__).resolve().parent / "vendor")
    if vendor_dir not in sys.path:
        sys.path.insert(0, vendor_dir)
    import wordninja

    def split(match):
        parts = wordninja.split(match.group())
        return " ".join(parts) if len(parts) > 1 else match.group()

    text = _WORD_RUN.sub(split, text)
    text = re.sub(r"(?i)\biam\b", "I am", text)
    return re.sub(r"(?i)\bi\b", "I", text)
