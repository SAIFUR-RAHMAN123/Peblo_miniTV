from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import Role, require_admin, require_editor
from app.models import PublishRun
from app.services.publish import PublishBlockedError, run_publish
from app.services.validation import build_validation_report

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/validation-report")
def validation_report(db: Session = Depends(get_db), _: Role = Depends(require_editor)):
    report = build_validation_report(db)
    return {
        "blocking": report.blocking,
        "published_episode_count": report.published_episode_count,
        "published_show_count": report.published_show_count,
        "issues": [
            {"code": i.code, "message": i.message, "episode_ids": i.episode_ids, "show_slug": i.show_slug}
            for i in report.issues
        ],
        "informational": [
            {"code": i.code, "message": i.message, "episode_ids": i.episode_ids, "show_slug": i.show_slug}
            for i in report.informational
        ],
    }


@router.post("/catalog/publish", status_code=201)
def publish_catalog(db: Session = Depends(get_db), role: Role = Depends(require_admin)):
    try:
        run = run_publish(db, triggered_by=role.value)
    except PublishBlockedError as exc:
        return {
            "outcome": "failed",
            "reason": "blocked_by_validation",
            "issues": [{"code": i.code, "message": i.message} for i in exc.report.issues],
        }
    return {
        "outcome": run.outcome,
        "publish_run_id": run.id,
        "shows_count": run.shows_count,
        "episodes_count": run.episodes_count,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


@router.get("/catalog/publish-runs")
def publish_runs(db: Session = Depends(get_db), _: Role = Depends(require_editor)):
    runs = db.query(PublishRun).order_by(PublishRun.id.desc()).limit(50).all()
    return [
        {
            "id": r.id, "triggered_by": r.triggered_by, "outcome": r.outcome,
            "shows_count": r.shows_count, "episodes_count": r.episodes_count,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "error": r.error,
        }
        for r in runs
    ]

@router.get("/whoami")
def whoami(role: Role = Depends(require_editor)):
    return {"role": role.value}