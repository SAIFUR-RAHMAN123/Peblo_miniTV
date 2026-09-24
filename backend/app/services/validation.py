"""
Everything currently blocking (or worth flagging before) publish, grouped
so an editor can act without an engineer. Built directly against the issues
found in the actual seed data:
  - ep_0004 / ep_9001 share (content_group='motis-many-lives-s01e02',
    language='hi') while both are 'published'
  - ep_0036 is 'published' with zero artwork rows
  - ep_0093 / ep_0094 (season-0 trailers) are 'published' with only a
    thumbnail, missing poster + banner
  - 'Rhyme Rangers' has section=None (currently all-draft, so not blocking
    yet, but flagged so an editor can fix it before it becomes one)
"""
from dataclasses import dataclass, field

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Show, Episode, Artwork

REQUIRED_ARTWORK_KINDS = {"poster", "banner", "thumbnail"}


@dataclass
class ValidationIssue:
    code: str
    message: str
    episode_ids: list[str] = field(default_factory=list)
    show_slug: str | None = None


@dataclass
class ValidationReport:
    blocking: bool
    issues: list[ValidationIssue]
    informational: list[ValidationIssue]
    published_episode_count: int
    published_show_count: int


def build_validation_report(db: Session) -> ValidationReport:
    issues: list[ValidationIssue] = []
    informational: list[ValidationIssue] = []

    published_episodes = (
        db.query(Episode).filter(Episode.status == "published").all()
    )
    published_show_ids = {e.show_id for e in published_episodes}
    shows_by_id = {s.id: s for s in db.query(Show).filter(Show.id.in_(published_show_ids)).all()} if published_show_ids else {}

    # 1. duplicate (content_group, language) among published episodes
    groups: dict[tuple[str, str], list[Episode]] = {}
    for ep in published_episodes:
        groups.setdefault((ep.content_group, ep.language), []).append(ep)
    for (cg, lang), eps in groups.items():
        if len(eps) > 1:
            issues.append(ValidationIssue(
                code="duplicate_content_group_language",
                message=(
                    f"{len(eps)} published episodes share content_group '{cg}' and language '{lang}' "
                    f"({', '.join(e.episode_id for e in eps)}). Only one episode per language may exist "
                    f"per content_group -- unpublish or fix all but one before publishing."
                ),
                episode_ids=[e.episode_id for e in eps],
            ))

    # 2. published episode missing required artwork
    artwork_rows = (
        db.query(Artwork.episode_id, Artwork.kind)
        .join(Episode, Episode.id == Artwork.episode_id)
        .filter(Episode.status == "published")
        .all()
    )
    artwork_by_episode: dict[int, set[str]] = {}
    for episode_pk, kind in artwork_rows:
        artwork_by_episode.setdefault(episode_pk, set()).add(kind)

    for ep in published_episodes:
        have = artwork_by_episode.get(ep.id, set())
        missing = REQUIRED_ARTWORK_KINDS - have
        if missing:
            show = shows_by_id.get(ep.show_id)
            issues.append(ValidationIssue(
                code="missing_artwork",
                message=(
                    f"Episode '{ep.episode_title}' ({ep.episode_id}) in "
                    f"'{show.title if show else ep.show_id}' is published but missing "
                    f"{', '.join(sorted(missing))} artwork. Upload it or unpublish the episode."
                ),
                episode_ids=[ep.episode_id],
                show_slug=show.slug if show else None,
            ))

    # 3. published episode with no/invalid duration
    for ep in published_episodes:
        if not ep.duration_seconds or ep.duration_seconds <= 0:
            show = shows_by_id.get(ep.show_id)
            issues.append(ValidationIssue(
                code="missing_duration",
                message=(
                    f"Episode '{ep.episode_title}' ({ep.episode_id}) in "
                    f"'{show.title if show else ep.show_id}' is published but has no valid duration."
                ),
                episode_ids=[ep.episode_id],
                show_slug=show.slug if show else None,
            ))

    # 4. published show with no section
    seen_show_ids = set()
    for ep in published_episodes:
        show = shows_by_id.get(ep.show_id)
        if show and show.section is None and show.id not in seen_show_ids:
            seen_show_ids.add(show.id)
            issues.append(ValidationIssue(
                code="published_show_missing_section",
                message=(
                    f"Show '{show.title}' has published episodes but no section assigned. "
                    f"Set a section before publishing."
                ),
                show_slug=show.slug,
            ))

    # 5. informational: shows with no section that have no published episodes yet
    # (not blocking today, but will block the moment an editor publishes one)
    all_shows_no_section = db.query(Show).filter(Show.section.is_(None)).all()
    for show in all_shows_no_section:
        if show.id not in seen_show_ids:
            informational.append(ValidationIssue(
                code="show_missing_section",
                message=(
                    f"Show '{show.title}' has no section set. It won't block publish until "
                    f"an episode under it is marked published, but should be fixed proactively."
                ),
                show_slug=show.slug,
            ))

    return ValidationReport(
        blocking=len(issues) > 0,
        issues=issues,
        informational=informational,
        published_episode_count=len(published_episodes),
        published_show_count=len(published_show_ids),
    )