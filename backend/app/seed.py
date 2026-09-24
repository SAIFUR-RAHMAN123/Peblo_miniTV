"""
Loads seed_shows.json as-is into the database -- including its
deliberate imperfections (the ep_0004/ep_9001 duplicate, ep_0036's missing
artwork, the two trailers missing poster/banner, Rhyme Rangers' null
section). This script does NOT run the create/update validation the API
enforces -- it's a raw bulk import representing "the current, occasionally
dirty state of the world" per the challenge brief. Run the validation
report afterwards to see exactly what it flags.

Per-episode source images weren't provided (only an `artwork_available`
list of which kinds exist per row), so this script generates placeholder
JPGs at the correct target dimensions for whichever kinds each row claims,
through the same storage abstraction the real upload endpoint uses. This
is a stand-in for real assets -- noted in the README.

Usage:
    python -m app.seed
"""
import json
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from app.core.database import Base, SessionLocal, engine
from app.core.reference_data import artwork_specs
from app.models import Artwork, Episode, Show
from app.storage import get_storage

SEED_DIR = Path(__file__).resolve().parent.parent / "seed_source"
SEED_SHOWS_PATH = SEED_DIR / "seed_shows.json"


def _placeholder_image_bytes(kind: str, label: str) -> bytes:
    spec = artwork_specs()[kind]
    w, h = spec["target_px"]
    img = Image.new("RGB", (w, h), color=(90, 90, 160))
    draw = ImageDraw.Draw(img)
    text = f"{kind}\n{label}\n{w}x{h}"
    draw.text((20, 20), text, fill=(255, 255, 255))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return buf.getvalue()


def seed():
    Base.metadata.create_all(bind=engine)  # no-op if migrations already ran; safe either way
    db = SessionLocal()
    storage = get_storage()

    if db.query(Show).count() > 0:
        print("Database already has shows -- skipping seed. Delete rows or drop the DB first to reseed.")
        return

    rows = json.loads(SEED_SHOWS_PATH.read_text(encoding="utf-8"))

    shows_by_slug: dict[str, Show] = {}
    for row in rows:
        slug = row["slug"]
        if slug not in shows_by_slug:
            show = Show(
                slug=slug,
                title=row["show_title"],
                section=row["section"],
                synopsis=row["synopsis"],
                categories=row["categories"],
            )
            db.add(show)
            db.flush()
            shows_by_slug[slug] = show

        show = shows_by_slug[slug]
        episode = Episode(
            episode_id=row["episode_id"],
            show_id=show.id,
            season_number=row["season_number"],
            episode_number=row["episode_number"],
            episode_title=row["episode_title"],
            duration_seconds=row["duration_seconds"],
            language=row["language"],
            content_group=row["content_group"],
            status=row["status"],
        )
        db.add(episode)
        db.flush()

        for kind in row["artwork_available"]:
            data = _placeholder_image_bytes(kind, row["episode_id"])
            key = f"artwork/{episode.episode_id}/{kind}.jpg"
            storage.write(key, data, "image/jpeg")
            img = Image.open(BytesIO(data))
            db.add(Artwork(
                episode_id=episode.id, kind=kind, storage_key=key,
                width=img.width, height=img.height, size_bytes=len(data),
            ))

    db.commit()
    print(f"Seeded {len(shows_by_slug)} shows, {len(rows)} episodes.")


if __name__ == "__main__":
    seed()