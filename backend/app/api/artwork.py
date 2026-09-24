import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import Role, require_editor
from app.models import Episode, Artwork
from app.services.artwork_validation import validate_artwork, VALID_KINDS
from app.storage import get_storage

router = APIRouter(prefix="/admin/episodes/{episode_pk}/artwork", tags=["artwork"])


@router.get("")
def list_artwork(episode_pk: int, db: Session = Depends(get_db), _: Role = Depends(require_editor)):
    episode = db.get(Episode, episode_pk)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found.")
    storage = get_storage()
    rows = db.query(Artwork).filter(Artwork.episode_id == episode_pk).all()
    return [
        {
            "id": a.id, "kind": a.kind, "width": a.width, "height": a.height,
            "size_bytes": a.size_bytes, "url": storage.public_url(a.storage_key),
        }
        for a in rows
    ]


@router.post("", status_code=201)
async def upload_artwork(
    episode_pk: int,
    kind: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: Role = Depends(require_editor),
):
    episode = db.get(Episode, episode_pk)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found.")
    if kind not in VALID_KINDS:
        raise HTTPException(status_code=400, detail=f"'{kind}' is not a valid artwork type. Must be one of: {', '.join(sorted(VALID_KINDS))}.")

    data = await file.read()
    result = validate_artwork(kind, data)
    if not result.ok:
        raise HTTPException(status_code=422, detail=result.errors)

    ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    key = f"artwork/{episode.episode_id}/{kind}{ext}"
    storage = get_storage()
    storage.write(key, data, file.content_type or "application/octet-stream")

    existing = db.query(Artwork).filter(Artwork.episode_id == episode_pk, Artwork.kind == kind).first()
    if existing:
        existing.storage_key = key
        existing.width = result.width
        existing.height = result.height
        existing.size_bytes = result.size_bytes
    else:
        existing = Artwork(
            episode_id=episode_pk, kind=kind, storage_key=key,
            width=result.width, height=result.height, size_bytes=result.size_bytes,
        )
        db.add(existing)
    db.commit()
    db.refresh(existing)

    return {
        "id": existing.id, "kind": existing.kind, "width": existing.width,
        "height": existing.height, "size_bytes": existing.size_bytes,
        "url": storage.public_url(existing.storage_key),
    }


@router.delete("/{kind}", status_code=204)
def delete_artwork(episode_pk: int, kind: str, db: Session = Depends(get_db), _: Role = Depends(require_editor)):
    row = db.query(Artwork).filter(Artwork.episode_id == episode_pk, Artwork.kind == kind).first()
    if not row:
        raise HTTPException(status_code=404, detail="Artwork not found.")
    db.delete(row)
    db.commit()
    return None