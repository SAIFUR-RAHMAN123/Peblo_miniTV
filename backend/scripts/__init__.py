"""
CI/demo helper: after seeding the intentionally-imperfect seed data, put
the DB into a publishable state so CI can exercise a real publish and the
CMS/viewer integration tests have real, representative published content
(including a real trailer) to check against.

This does NOT touch the pytest suite's fixtures -- those run against a
separate, isolated test database (peblo_tv_test) and specifically assert
on the raw, unresolved validation report. This script only patches the
shared dev/demo database seeded by `python -m app.seed`, mirroring what an
editor would actually do after reading the validation report:
  - upload the missing artwork for ep_0036, ep_0093, ep_0094 (they're
    otherwise fine episodes -- the fix is adding artwork, not hiding them)
  - unpublish ep_9001, the one member of the genuine duplicate pair
    (ep_0004 / ep_9001 share a content_group+language) that can't be
    auto-resolved -- an editor has to make a judgment call on which one
    is canonical, so this script picks ep_0004 and drafts the other
"""
from io import BytesIO

from PIL import Image, ImageDraw

from app.core.database import SessionLocal
from app.core.reference_data import artwork_specs
from app.models import Artwork, Episode
from app.storage import get_storage

EPISODES_MISSING_ARTWORK = {
    "ep_0036": ["poster", "banner", "thumbnail"],
    "ep_0093": ["poster", "banner"],
    "ep_0094": ["poster", "banner"],
}
DUPLICATE_TO_UNPUBLISH = "ep_9001"


def _placeholder_image_bytes(kind: str, label: str) -> bytes:
    spec = artwork_specs()[kind]
    w, h = spec["target_px"]
    img = Image.new("RGB", (w, h), color=(90, 90, 160))
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), f"{kind}\n{label}\n{w}x{h}", fill=(255, 255, 255))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return buf.getvalue()


def main():
    db = SessionLocal()
    storage = get_storage()

    added = 0
    for episode_id, kinds in EPISODES_MISSING_ARTWORK.items():
        episode = db.query(Episode).filter(Episode.episode_id == episode_id).first()
        if not episode:
            continue
        for kind in kinds:
            exists = db.query(Artwork).filter(Artwork.episode_id == episode.id, Artwork.kind == kind).first()
            if exists:
                continue
            data = _placeholder_image_bytes(kind, episode_id)
            key = f"artwork/{episode_id}/{kind}.jpg"
            storage.write(key, data, "image/jpeg")
            img = Image.open(BytesIO(data))
            db.add(Artwork(episode_id=episode.id, kind=kind, storage_key=key, width=img.width, height=img.height, size_bytes=len(data)))
            added += 1
    db.commit()

    updated = (
        db.query(Episode)
        .filter(Episode.episode_id == DUPLICATE_TO_UNPUBLISH)
        .update({"status": "draft"}, synchronize_session=False)
    )
    db.commit()

    print(f"Added {added} missing artwork file(s); unpublished {updated} duplicate episode(s).")


if __name__ == "__main__":
    main()