from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import Role, require_editor
from app.models import Show, Episode
from app.schemas.show import ShowCreate, ShowOut, ShowUpdate

router = APIRouter(prefix="/admin/shows", tags=["shows"])


@router.get("")
def list_shows(
    search: str | None = None,
    section: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Role = Depends(require_editor),
):
    q = db.query(Show)
    if search:
        q = q.filter(Show.title.ilike(f"%{search}%"))
    if section:
        q = q.filter(Show.section == section)
    total = q.count()
    shows = q.order_by(Show.title).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for s in shows:
        ep_count = db.query(Episode).filter(Episode.show_id == s.id).count()
        pub_count = db.query(Episode).filter(Episode.show_id == s.id, Episode.status == "published").count()
        items.append({
            **ShowOut.model_validate(s).model_dump(),
            "episode_count": ep_count,
            "published_episode_count": pub_count,
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=ShowOut, status_code=201)
def create_show(payload: ShowCreate, db: Session = Depends(get_db), _: Role = Depends(require_editor)):
    if db.query(Show).filter(Show.slug == payload.slug).first():
        raise HTTPException(status_code=409, detail=f"A show with slug '{payload.slug}' already exists.")
    show = Show(**payload.model_dump())
    db.add(show)
    db.commit()
    db.refresh(show)
    return show


@router.get("/{show_id}", response_model=ShowOut)
def get_show(show_id: int, db: Session = Depends(get_db), _: Role = Depends(require_editor)):
    show = db.get(Show, show_id)
    if not show:
        raise HTTPException(status_code=404, detail="Show not found.")
    return show


@router.patch("/{show_id}", response_model=ShowOut)
def update_show(show_id: int, payload: ShowUpdate, db: Session = Depends(get_db), _: Role = Depends(require_editor)):
    show = db.get(Show, show_id)
    if not show:
        raise HTTPException(status_code=404, detail="Show not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(show, field, value)
    db.commit()
    db.refresh(show)
    return show


@router.delete("/{show_id}", status_code=204)
def delete_show(show_id: int, db: Session = Depends(get_db), _: Role = Depends(require_editor)):
    show = db.get(Show, show_id)
    if not show:
        raise HTTPException(status_code=404, detail="Show not found.")
    db.delete(show)
    db.commit()
    return None