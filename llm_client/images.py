"""Image-generation plumbing shared by the character bible and the chapter pipeline."""

import base64
from pathlib import Path

from llm_client.tfy_client import get_tfy_client

# Per-chapter workhorse: cheap, run once per chapter.
CHAPTER_IMAGE_MODEL = "google-vertex-marketing/google-gemini-3.1-flash-image"

# Character anchor portraits: rendered once per character per book and then
# attached to every later chapter, so a face flaw here propagates everywhere.
# Worth the higher-tier model at this very low call volume.
ANCHOR_IMAGE_MODEL = "google-vertex-marketing/google-gemini-3.1-flash-image"


# The model tops out around 1376x768. That is fine on a desktop but soft on a
# phone, where a 2-3x pixel-density screen asks for far more physical pixels
# than the frame has — which is what reads as blur in an app. Upscaling can't
# invent detail, but it does stop the display layer doing a cruder job of the
# same resize, and it keeps text and edges cleaner.
UPSCALE_FACTOR = 2


def _upscale(png_bytes: bytes, factor: int = UPSCALE_FACTOR) -> bytes:
    from io import BytesIO

    from PIL import Image, ImageFilter

    with Image.open(BytesIO(png_bytes)) as image:
        image = image.convert("RGB")
        enlarged = image.resize(
            (image.width * factor, image.height * factor), Image.LANCZOS
        )
        # Any interpolation softens edges. A restrained unsharp mask puts back
        # the acutance it costs — kept mild, since over-sharpening a generated
        # image produces halos around faces that look worse than the softness.
        # threshold skips flat areas so grain and skin don't get crunchy.
        enlarged = enlarged.filter(
            ImageFilter.UnsharpMask(radius=2, percent=55, threshold=3)
        )
        buffer = BytesIO()
        # PNG keeps it lossless; the app can re-encode as it likes.
        enlarged.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()


class ImageBlockedError(RuntimeError):
    """The image model returned no image data. Observed to mean the safety
    filter rejected the prompt silently — not a code or transport error."""


def _extract_image_bytes(images_response) -> bytes:
    if not images_response.data:
        raise ImageBlockedError(
            "Image response had no data (likely filtered/rejected silently). "
            f"Full response:\n{images_response.model_dump()!r}"
        )
    item = images_response.data[0]
    if getattr(item, "b64_json", None):
        return base64.b64decode(item.b64_json)
    if getattr(item, "url", None):
        import requests

        resp = requests.get(item.url, timeout=60)
        resp.raise_for_status()
        return resp.content
    raise RuntimeError(f"Image response had neither b64_json nor url: {item!r}")


# Chapter frames are 16:9 landscape. The gateway maps requests onto its own
# supported set rather than honouring arbitrary dimensions, and "1792x1024" is
# the only value that actually yields a landscape frame — it comes back as
# 1376x768, i.e. 16:9. Every other value tested, including literal 16:9 sizes
# like "1365x768" and "1920x1080", silently returns a 1024x1024 square.
LANDSCAPE_SIZE = "1792x1024"

# Anchor portraits stay square: they are head-and-shoulders identity references,
# never published, and a square crop wastes nothing on empty sides.
PORTRAIT_SIZE = "1024x1024"


def render_image(
    model: str,
    prompt: str,
    references: list[Path] | None = None,
    metadata: dict | None = None,
    size: str = LANDSCAPE_SIZE,
    upscale: bool = False,
) -> bytes:
    """Generate one image. If `references` are given, they're attached as
    reference images via the edit endpoint (the gateway accepts several).
    `metadata` is tagged onto the gateway request for tracing. `upscale`
    enlarges the result for display on high pixel-density screens."""
    client = get_tfy_client(metadata)
    existing = [p for p in (references or []) if p.exists()]

    if existing:
        raw = _extract_image_bytes(
            client.images.edit(
                model=model,
                image=[(p.name, p.read_bytes(), "image/png") for p in existing],
                prompt=prompt,
                n=1,
                size=size,
            )
        )
    else:
        raw = _extract_image_bytes(
            client.images.generate(model=model, prompt=prompt, n=1, size=size)
        )

    return _upscale(raw) if upscale else raw
