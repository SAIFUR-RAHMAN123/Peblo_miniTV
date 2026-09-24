"""
Validates an uploaded artwork file against reference.json's artwork_specs.
Two independent checks, because the sample assets prove aspect alone isn't
enough:
  - aspect ratio must match within tolerance
  - both dimensions must be within tolerance of the target_px (catches
    banner_too_big.png: correct 16:9 aspect but 2x the target resolution,
    and thumb_tiny.jpg: correct 16:9 aspect but far under target)
Plus the flat 200KB file-size ceiling.

Errors are returned as a list of plain-English strings a non-technical
content editor can act on directly (e.g. "Image is 900x600 (landscape) but
poster artwork must be portrait, ~600x900 (2:3)."), not schema/type errors.
"""
from dataclasses import dataclass
from io import BytesIO

from PIL import Image

from app.core.config import get_settings

ARTWORK_SPECS = {
    "poster": {"aspect": (2, 3), "target_px": (600, 900)},
    "banner": {"aspect": (16, 9), "target_px": (1280, 720)},
    "thumbnail": {"aspect": (16, 9), "target_px": (640, 360)},
}

VALID_KINDS = set(ARTWORK_SPECS.keys())


@dataclass
class ArtworkValidationResult:
    ok: bool
    errors: list[str]
    width: int = 0
    height: int = 0
    size_bytes: int = 0


def validate_artwork(kind: str, data: bytes) -> ArtworkValidationResult:
    settings = get_settings()
    errors: list[str] = []

    if kind not in VALID_KINDS:
        return ArtworkValidationResult(ok=False, errors=[f"Unknown artwork type '{kind}'. Must be one of: poster, banner, thumbnail."])

    size_bytes = len(data)
    max_bytes = settings.artwork_max_kb * 1024
    if size_bytes > max_bytes:
        errors.append(
            f"File is {size_bytes / 1024:.1f} KB, which is over the {settings.artwork_max_kb} KB limit. "
            f"Please compress the image and try again."
        )

    try:
        img = Image.open(BytesIO(data))
        img.verify()
        img = Image.open(BytesIO(data))  # verify() consumes the file handle; reopen to read size
        width, height = img.size
    except Exception:
        errors.append("This file isn't a readable image. Please upload a JPG or PNG.")
        return ArtworkValidationResult(ok=False, errors=errors, size_bytes=size_bytes)

    spec = ARTWORK_SPECS[kind]
    target_w, target_h = spec["target_px"]
    aspect_w, aspect_h = spec["aspect"]
    expected_ratio = aspect_w / aspect_h
    actual_ratio = width / height if height else 0

    aspect_tol = settings.artwork_aspect_tolerance_pct / 100
    if abs(actual_ratio - expected_ratio) / expected_ratio > aspect_tol:
        orientation = "landscape" if width > height else "portrait" if height > width else "square"
        expected_orientation = "portrait" if aspect_h > aspect_w else "landscape" if aspect_w > aspect_h else "square"
        errors.append(
            f"Image is {width}x{height} ({orientation}) but {kind} artwork must be "
            f"{expected_orientation}, ~{target_w}x{target_h} ({aspect_w}:{aspect_h})."
        )
    else:
        dim_tol = settings.artwork_dimension_tolerance_pct / 100
        w_low, w_high = target_w * (1 - dim_tol), target_w * (1 + dim_tol)
        h_low, h_high = target_h * (1 - dim_tol), target_h * (1 + dim_tol)
        if not (w_low <= width <= w_high and h_low <= height <= h_high):
            if width < w_low or height < h_low:
                errors.append(
                    f"Image is {width}x{height}, which is too small for {kind} artwork. "
                    f"Please upload closer to {target_w}x{target_h}."
                )
            else:
                errors.append(
                    f"Image is {width}x{height}, which is too large for {kind} artwork. "
                    f"Please resize closer to {target_w}x{target_h}."
                )

    return ArtworkValidationResult(ok=len(errors) == 0, errors=errors, width=width, height=height, size_bytes=size_bytes)