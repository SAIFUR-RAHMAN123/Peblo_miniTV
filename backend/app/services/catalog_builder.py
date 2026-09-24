"""
Builds the published catalogue JSON from the DB. Two things this file owns
that the rest of the app doesn't need to know about:

1. content_group collapsing: episodes sharing a content_group are language
   variants of ONE episode. They collapse into a single catalogue entry
   with a `languages` list. Season 0 rows collapse the same way -- they
   just land in `trailers` instead of `seasons`.
2. Deterministic ordering: shows within a section are ordered by slug,
   seasons by season_number, episodes by episode_number. Two publish runs
   over unchanged data produce byte-identical JSON (see services/publish.py
   for how that's used for idempotency).

Only called after validation.build_validation_report() reports no blocking
issues -- this module assumes the data it's given is already clean, and
does NOT re-validate.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.reference_data import allowed_sections
from app.models import Show, Episode, Artwork
from app.storage import get_storage

PREFERRED_LANGUAGE_ORDER = ["en", "hi"]  # 'en' wins ties when picking a representative variant; documented decision


def _collapse_content_groups(episodes: list[Episode]) -> list[list[Episode]]:
    groups: dict[str, list[Episode]] = {}
    order: list[str] = []
    for ep in episodes:
        if ep.content_group not in groups:
            groups[ep.content_group] = []
            order.append(ep.content_group)
        groups[ep.content_group].append(ep)
    return [groups[cg] for cg in order]


def _artwork_url(artwork_by_episode: dict[int, dict[str, Artwork]], episode_pk: int, kind: str) -> str | None:
    storage = get_storage()
    art = artwork_by_episode.get(episode_pk, {}).get(kind)
    if not art:
        return None
    return storage.public_url(art.storage_key)


def _build_episode_entry(variants: list[Episode], show: Show, artwork_by_episode: dict[int, dict[str, Artwork]]) -> dict:
    variants_sorted = sorted(variants, key=lambda e: (
        PREFERRED_LANGUAGE_ORDER.index(e.language) if e.language in PREFERRED_LANGUAGE_ORDER else 999,
        e.language,
    ))
    representative = variants_sorted[0]

    languages = []
    for ep in variants_sorted:
        languages.append({
            "language": ep.language,
            "episode_id": ep.episode_id,
            "duration_seconds": ep.duration_seconds,
            "thumbnail_url": _artwork_url(artwork_by_episode, ep.id, "thumbnail"),
        })

    return {
        "content_group": representative.content_group,
        "show_id": show.id,
        "show_slug": show.slug,
        "show_title": show.title,
        "section": show.section,
        "categories": show.categories,
        "season_number": representative.season_number,
        "episode_number": representative.episode_number,
        "episode_title": representative.episode_title,
        "languages": languages,
        "poster_url": _artwork_url(artwork_by_episode, representative.id, "poster"),
        "banner_url": _artwork_url(artwork_by_episode, representative.id, "banner"),
        "thumbnail_url": _artwork_url(artwork_by_episode, representative.id, "thumbnail"),
    }


def build_catalog(db: Session) -> dict:
    published_episodes = (
        db.query(Episode)
        .filter(Episode.status == "published")
        .all()
    )
    show_ids = {e.show_id for e in published_episodes}
    shows = {s.id: s for s in db.query(Show).filter(Show.id.in_(show_ids)).all()} if show_ids else {}

    artwork_rows = (
        db.query(Artwork)
        .join(Episode, Episode.id == Artwork.episode_id)
        .filter(Episode.status == "published")
        .all()
    )
    artwork_by_episode: dict[int, dict[str, Artwork]] = {}
    for art in artwork_rows:
        artwork_by_episode.setdefault(art.episode_id, {})[art.kind] = art

    episodes_by_show: dict[int, list[Episode]] = {}
    for ep in published_episodes:
        episodes_by_show.setdefault(ep.show_id, []).append(ep)

    section_map: dict[str, list[dict]] = {s: [] for s in allowed_sections()}

    for show_id, eps in episodes_by_show.items():
        show = shows[show_id]
        if show.section is None:
            # Should never reach here if validation ran first; skip defensively.
            continue

        normal_eps = [e for e in eps if e.season_number != 0]
        trailer_eps = [e for e in eps if e.season_number == 0]

        normal_groups = _collapse_content_groups(
            sorted(normal_eps, key=lambda e: (e.season_number, e.episode_number, e.language))
        )
        trailer_groups = _collapse_content_groups(
            sorted(trailer_eps, key=lambda e: (e.episode_number, e.language))
        )

        seasons_map: dict[int, list[dict]] = {}
        for group in normal_groups:
            entry = _build_episode_entry(group, show, artwork_by_episode)
            seasons_map.setdefault(entry["season_number"], []).append(entry)

        seasons = [
            {"season_number": sn, "episodes": sorted(eps_list, key=lambda e: e["episode_number"])}
            for sn, eps_list in sorted(seasons_map.items())
        ]

        trailers = [_build_episode_entry(g, show, artwork_by_episode) for g in trailer_groups]
        trailers.sort(key=lambda e: e["episode_number"])

        # representative poster/banner for the show tile: first episode of
        # the first season (documented decision -- shows have no artwork of
        # their own in this schema, only episodes do)
        show_poster_url = None
        show_banner_url = None
        if seasons and seasons[0]["episodes"]:
            first_ep = seasons[0]["episodes"][0]
            show_poster_url = first_ep["poster_url"]
            show_banner_url = first_ep["banner_url"]

        show_entry = {
            "id": show.id,
            "slug": show.slug,
            "title": show.title,
            "synopsis": show.synopsis,
            "categories": show.categories,
            "section": show.section,
            "poster_url": show_poster_url,
            "banner_url": show_banner_url,
            "seasons": seasons,
            "trailers": trailers,
        }
        section_map[show.section].append(show_entry)

    sections_out = []
    flat_entries: list[dict] = []
    for section in allowed_sections():
        shows_list = sorted(section_map[section], key=lambda s: s["slug"])
        if not shows_list:
            continue
        sections_out.append({"section": section, "shows": shows_list})
        for show_entry in shows_list:
            for season in show_entry["seasons"]:
                flat_entries.extend(season["episodes"])
            flat_entries.extend(show_entry["trailers"])

    hero = None
    for sec in sections_out:
        if sec["shows"]:
            hero = sec["shows"][0]
            break

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "hero": hero,
        "sections": sections_out,
        "entries": flat_entries,
    }