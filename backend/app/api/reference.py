from fastapi import APIRouter

from app.core.reference_data import allowed_categories, allowed_languages, allowed_sections, artwork_specs

router = APIRouter(tags=["reference"])


@router.get("/reference")
def get_reference_data():
    return {
        "sections": allowed_sections(),
        "categories": allowed_categories(),
        "languages": allowed_languages(),
        "artwork_specs": artwork_specs(),
    }