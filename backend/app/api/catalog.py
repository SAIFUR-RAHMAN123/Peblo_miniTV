"""
Viewer-facing, unauthenticated. Serves the already-published catalogue file
(or the empty shell if nothing has ever been published) -- never touches the
database directly. See services/publish.get_published_catalog and README
Part E for why we serve a file instead of querying live, and where that
choice stops scaling.
"""
from fastapi import APIRouter

from app.services.publish import get_published_catalog

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("")
def get_catalog():
    return get_published_catalog()


@router.get("/search")
def search_catalog(
    q: str | None = None,
    category: str | None = None,
    language: str | None = None,
    section: str | None = None,
):
    catalog = get_published_catalog()
    entries = catalog.get("entries", [])

    def matches(entry: dict) -> bool:
        if section and entry.get("section") != section:
            return False
        if category and category not in entry.get("categories", []):
            return False
        if language and not any(l["language"] == language for l in entry.get("languages", [])):
            return False
        if q:
            needle = q.lower()
            haystacks = [entry.get("show_title", ""), entry.get("episode_title", "")] + entry.get("categories", [])
            if not any(needle in h.lower() for h in haystacks):
                return False
        return True

    results = [e for e in entries if matches(e)]
    return {"query": q, "filters": {"category": category, "language": language, "section": section}, "count": len(results), "results": results}