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


# Kept for callers that still want a cheap enlarge, but the native resolution
# tier below made it unnecessary for the chapter frames: real pixels from the
# model beat interpolated ones.
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


# `size` selects the ASPECT RATIO only. The gateway maps requests onto its own
# supported set rather than honouring arbitrary dimensions, and "1792x1024" is
# the only value that actually yields a landscape frame. Every other value
# tested, including literal 16:9 sizes like "1365x768" and "1920x1080",
# silently returns a square.
LANDSCAPE_SIZE = "1792x1024"

# Anchor portraits stay square: they are head-and-shoulders identity references,
# never published, and a square crop wastes nothing on empty sides.
PORTRAIT_SIZE = "1024x1024"

# `image_size` selects the RESOLUTION TIER, and is what actually lifts the
# output off the old 1376x768 frame — the model renders up to 4K natively, the
# OpenAI-compatible `size` field just has no way to ask for it. Measured
# through this gateway, for both images.generate and images.edit:
#
#   tier   16:9          1:1
#   1K     1376x768      1024x1024   (the old default)
#   2K     2752x1536     2048x2048
#   4K     5504x3072     4096x4096
#
# Chapter frames run at 4K: ~17MB and slower per frame, but they are the
# published artefact and the headroom is there, so spend it. Anchors override
# to 2K (see character_bible) — they are re-uploaded as references on every
# chapter call, where a 17MB multipart body costs latency on every request for
# identity detail the model does not read back at that resolution.
#
# Passed via extra_body as a flat field. The nested Vertex form
# (generationConfig.imageConfig.imageSize) works on generate but 400s on edit,
# where the SDK flattens it into multipart keys Vertex won't parse — this flat
# spelling is the one the gateway translates correctly on BOTH endpoints.
IMAGE_SIZE_TIER = "4K"


def render_image(
    model: str,
    prompt: str,
    references: list[Path] | None = None,
    metadata: dict | None = None,
    size: str = LANDSCAPE_SIZE,
    image_size: str = IMAGE_SIZE_TIER,
    upscale: bool = False,
) -> bytes:
    """Generate one image. If `references` are given, they're attached as
    reference images via the edit endpoint (the gateway accepts several).
    `metadata` is tagged onto the gateway request for tracing. `size` picks the
    aspect ratio, `image_size` the resolution tier ("1K"/"2K"/"4K"). `upscale`
    interpolates on top of that, and should stay off now that the tier is
    doing the work."""
    client = get_tfy_client(metadata)
    existing = [p for p in (references or []) if p.exists()]
    tier = {"image_size": image_size}

    if existing:
        raw = _extract_image_bytes(
            client.images.edit(
                model=model,
                image=[(p.name, p.read_bytes(), "image/png") for p in existing],
                prompt=prompt,
                n=1,
                size=size,
                extra_body=tier,
            )
        )
    else:
        raw = _extract_image_bytes(
            client.images.generate(
                model=model, prompt=prompt, n=1, size=size, extra_body=tier
            )
        )

    return _upscale(raw) if upscale else raw
