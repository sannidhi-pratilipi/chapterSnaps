"""TFY (internal model gateway) client for ChapterSnap.

Talks to the gateway through the raw `openai` SDK, which it exposes an
OpenAI-compatible surface for. No langchain dependency.

Every gateway setting comes from the environment, with no fallbacks: a missing
value fails immediately and says which one, rather than silently sending a
wrong endpoint or metadata the gateway will reject. See .env.example.
"""

import json
import os
import uuid

from openai import OpenAI

REQUIRED_ENV = ("TFY_API_KEY", "TFY_BASE_URL", "TFY_SERVICE", "TFY_TEAM", "ENV")


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"{name} is not set. Copy .env.example to .env and fill in "
            f"{', '.join(REQUIRED_ENV)}."
        )
    return value


def get_tfy_client(extra_metadata: dict | None = None) -> OpenAI:
    """Build an OpenAI-compatible client pointed at the TFY gateway, with a
    fresh request id in the metadata headers for this call."""
    metadata = {
        "env": _required("ENV"),
        "service": _required("TFY_SERVICE"),
        # The gateway's mandatory-metadata guardrail rejects requests whose
        # team is empty or outside its allowed set.
        "team": _required("TFY_TEAM"),
        "request_id": str(uuid.uuid4()),
        **(extra_metadata or {}),
    }
    return OpenAI(
        api_key=_required("TFY_API_KEY"),
        base_url=_required("TFY_BASE_URL"),
        default_headers={
            "X-TFY-METADATA": json.dumps(metadata),
            "X-TFY-LOGGING-CONFIG": json.dumps({"enabled": True}),
        },
    )
