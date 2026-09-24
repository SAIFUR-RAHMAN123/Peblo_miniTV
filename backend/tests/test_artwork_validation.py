"""Artwork validation against the real challenge sample images."""
from pathlib import Path

from app.services.artwork_validation import validate_artwork

ASSETS = Path(__file__).resolve().parent.parent.parent / "assets_seed"


def _read(name):
    return (ASSETS / name).read_bytes()


def test_good_poster_passes():
    r = validate_artwork("poster", _read("poster_good.jpg"))
    assert r.ok, r.errors


def test_wrong_ratio_poster_rejected():
    r = validate_artwork("poster", _read("poster_wrong_ratio.jpg"))
    assert not r.ok
    assert "landscape" in r.errors[0] or "portrait" in r.errors[0]


def test_good_banner_passes():
    r = validate_artwork("banner", _read("banner_good.jpg"))
    assert r.ok, r.errors


def test_oversized_banner_rejected():
    r = validate_artwork("banner", _read("banner_too_big.png"))
    assert not r.ok
    assert "too large" in r.errors[0]


def test_good_thumbnail_passes():
    r = validate_artwork("thumbnail", _read("thumb_good.jpg"))
    assert r.ok, r.errors


def test_tiny_thumbnail_rejected():
    r = validate_artwork("thumbnail", _read("thumb_tiny.jpg"))
    assert not r.ok
    assert "too small" in r.errors[0]


def test_oversized_file_kb_rejected():
    from io import BytesIO
    from PIL import Image
    img = Image.new("RGB", (600, 900), color=(10, 20, 30))
    buf = BytesIO()
    img.save(buf, format="BMP")  # uncompressed -> large
    data = buf.getvalue()
    assert len(data) > 200 * 1024
    r = validate_artwork("poster", data)
    assert not r.ok
    assert any("KB" in e for e in r.errors)


def test_garbage_bytes_rejected():
    r = validate_artwork("poster", b"not an image")
    assert not r.ok