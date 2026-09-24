"""
Orchestrates a publish run: validate -> build catalogue -> atomic write ->
record outcome. This is the one place all three come together.

Atomicity: the actual atomic write happens in the storage backend
(write_atomic -> temp file + os.replace on local disk; a plain PutObject on
R2/S3, which is atomic by nature there). This module's job is to make sure
we NEVER call write_atomic with a catalogue built from invalid data, and to
always record what happened -- success, blocked, or crashed -- as a
PublishRun row.

If the process dies mid-publish:
  - before write_atomic returns: readers still see the previous catalog.json,
    untouched. Nothing is corrupted.
  - the PublishRun row for that attempt is stuck at outcome='running' with
    no finished_at. That's the signal an operator/alert should watch for
    (see README Part D) -- a run 'running' for longer than a publish should
    ever take means the process died and needs re-triggering.

Idempotency: re-running publish with no data changes produces a catalogue
with the same sections/shows/episodes/entries (only `generated_at` and
`publish_run_id` differ) and creates a new PublishRun row rather than
mutating history -- publish is safe to retry or schedule repeatedly.
"""
import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import PublishRun
from app.services.catalog_builder import build_catalog
from app.services.validation import ValidationReport, build_validation_report
from app.storage import get_storage


class PublishBlockedError(Exception):
    def __init__(self, report: ValidationReport):
        self.report = report
        super().__init__(f"Publish blocked by {len(report.issues)} validation issue(s).")


def _catalog_key() -> str:
    settings = get_settings()
    return f"{settings.catalog_publish_dir}/catalog.json"


def run_publish(db: Session, triggered_by: str) -> PublishRun:
    report = build_validation_report(db)

    run = PublishRun(triggered_by=triggered_by, outcome="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    if report.blocking:
        run.outcome = "failed"
        run.finished_at = datetime.now(timezone.utc)
        run.error = " | ".join(i.message for i in report.issues)
        db.commit()
        raise PublishBlockedError(report)

    try:
        catalog = build_catalog(db)
        catalog["publish_run_id"] = run.id
        data = json.dumps(catalog, indent=2).encode("utf-8")

        storage = get_storage()
        key = _catalog_key()
        storage.write_atomic(key, data, "application/json")

        show_count = sum(len(sec["shows"]) for sec in catalog["sections"])
        run.outcome = "success"
        run.shows_count = show_count
        run.episodes_count = len(catalog["entries"])
        run.catalog_storage_key = key
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
        return run
    except Exception as exc:
        run.outcome = "failed"
        run.error = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise


def get_published_catalog() -> dict:
    storage = get_storage()
    key = _catalog_key()
    if not storage.exists(key):
        return {"generated_at": None, "hero": None, "sections": [], "entries": []}
    return json.loads(storage.read(key))