from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import Role, require_editor
from app.models import Show, Episode, Artwork
from app.schemas.episode import EpisodeCreate, EpisodeOut, EpisodeUpdate

router = APIRouter(prefix="/admin/episodes", tags=["episodes"])

REQUIRED_ARTWORK_KINDS = {"poster", "banner", "thumbnail"}


def _check_publish_preconditions(db: Session, episode: Episode, show: Show, exclude_pk: int | None = None) -> list[str]:
    """
    Rules enforced at write time (not just reported after the fact):
      - a published episode needs a section on its show
      - a published episode needs duration_seconds
      - a published episode needs all 3 artwork kinds
      - (content_group, language) must be unique among published episodes
    Returns a list of human-readable problems; empty list means OK to publish.
    """
    problems = []
    if show.section is None:
        problems.append(
            f"Show '{show.title}' has no section set. Set a section before publishing an episode under it."
        )
    if not episode.duration_seconds or episode.duration_seconds <= 0:
        problems.append("This episode has no valid duration. Set duration_seconds before publishing.")

    have_kinds = {
        a.kind for a in db.query(Artwork).filter(Artwork.episode_id == episode.id).all()
    }
    missing = REQUIRED_ARTWORK_KINDS - have_kinds
    if missing:
        problems.append(f"Missing artwork: {', '.join(sorted(missing))}. Upload it before publishing.")

    conflict_q = db.query(Episode).filter(
        Episode.content_group == episode.content_group,
        Episode.language == episode.language,
        Episode.status == "published",
        Episode.id != (exclude_pk or episode.id),
    )
    conflict = conflict_q.first()
    if conflict:
        problems.append(
            f"Another published episode ('{conflict.episode_id}') already uses content_group "
            f"'{episode.content_group}' + language '{episode.language}'. Only one is allowed."
        )
    return problems


@router.get("")
def list_episodes(
    show_id: int | None = None,
    status_: str | None = Query(default=None, alias="status"),
    language: str | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Role = Depends(require_editor),
):
    q = db.query(Episode)
    if show_id:
        q = q.filter(Episode.show_id == show_id)
    if status_:
        q = q.filter(Episode.status == status_)
    if language:
        q = q.filter(Episode.language == language)
    if search:
        q = q.filter(Episode.episode_title.ilike(f"%{search}%"))
    total = q.count()
    episodes = (
        q.order_by(Episode.show_id, Episode.season_number, Episode.episode_number)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [EpisodeOut.model_validate(e).model_dump() for e in episodes],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=EpisodeOut, status_code=201)
def create_episode(payload: EpisodeCreate, db: Session = Depends(get_db), _: Role = Depends(require_editor)):
    show = db.get(Show, payload.show_id)
    if not show:
        raise HTTPException(status_code=404, detail="Show not found.")
    if db.query(Episode).filter(Episode.episode_id == payload.episode_id).first():
        raise HTTPException(status_code=409, detail=f"episode_id '{payload.episode_id}' already exists.")

    episode = Episode(**payload.model_dump())

    if episode.status == "published":
        problems = _check_publish_preconditions(db, episode, show)
        if problems:
            raise HTTPException(status_code=409, detail=problems)

    db.add(episode)
    db.commit()
    db.refresh(episode)
    return episode


@router.get("/{episode_pk}", response_model=EpisodeOut)
def get_episode(episode_pk: int, db: Session = Depends(get_db), _: Role = Depends(require_editor)):
    episode = db.get(Episode, episode_pk)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found.")
    return episode


@router.patch("/{episode_pk}", response_model=EpisodeOut)
def update_episode(episode_pk: int, payload: EpisodeUpdate, db: Session = Depends(get_db), _: Role = Depends(require_editor)):
    episode = db.get(Episode, episode_pk)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found.")
    show = db.get(Show, episode.show_id)

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(episode, field, value)

    if episode.status == "published":
        problems = _check_publish_preconditions(db, episode, show, exclude_pk=episode.id)
        if problems:
            db.rollback()
            raise HTTPException(status_code=409, detail=problems)

    db.commit()
    db.refresh(episode)
    return episode


@router.delete("/{episode_pk}", status_code=204)
def delete_episode(episode_pk: int, db: Session = Depends(get_db), _: Role = Depends(require_editor)):
    episode = db.get(Episode, episode_pk)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found.")
    db.delete(episode)
    db.commit()
    return None