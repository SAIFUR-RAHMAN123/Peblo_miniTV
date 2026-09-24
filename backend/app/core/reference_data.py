"""
Loads reference.json once and exposes its contents as the single source of
truth for allowed sections/categories/languages and artwork specs. Nothing
else in the app hardcodes these lists.
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

REFERENCE_PATH = Path(__file__).resolve().parent.parent / "reference_data" / "reference.json"


@lru_cache
def get_reference() -> dict[str, Any]:
    with open(REFERENCE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def allowed_sections() -> list[str]:
    return get_reference()["sections"]


def allowed_categories() -> list[str]:
    return get_reference()["categories"]


def allowed_languages() -> list[str]:
    return get_reference()["languages"]


def artwork_specs() -> dict[str, Any]:
    return get_reference()["artwork_specs"]