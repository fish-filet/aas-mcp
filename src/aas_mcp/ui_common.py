"""Reusable Gradio UI building blocks (heading, engine inputs).

These helpers allow non-MCP specific UI parts to be reused across apps.
"""

from __future__ import annotations

import os
from typing import List, Tuple

# Ensure Gradio analytics are disabled consistently when this is imported
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

try:  # optional dependency at runtime
    import gradio as gr
except Exception:  # pragma: no cover
    gr = None  # type: ignore[assignment]


def add_heading(title: str, bullets: List[str] | None = None) -> None:
    """Insert a Markdown heading with optional bullets into the current Blocks.

    Must be called within a `gr.Blocks` context. Does nothing if Gradio is absent.
    """
    if gr is None:  # type: ignore[truthy-bool]
        return
    bullets = bullets or []
    bullet_md = "\n".join(f"- {b}" for b in bullets if b.strip())
    md = f"# {title}\n"
    if bullet_md:
        md += bullet_md
    gr.Markdown(md)


def build_engine_inputs(
    default_endpoint_placeholder: str = "https://aaa.ariadneanyerse.de",
) -> Tuple["gr.Textbox", "gr.Textbox", "gr.Checkbox", "gr.Textbox"]:
    """Create and return engine inputs: API key, endpoint URL, toggle and optional MCP token.

    Returns a tuple:
      (api_key_textbox, endpoint_url_textbox, require_mcp_auth_checkbox, mcp_bearer_token_textbox)
    Call this inside a `gr.Blocks` (optionally within a Row for layout).
    """
    if gr is None:  # type: no cover
        raise RuntimeError("Gradio not available")

    api_key = gr.Textbox(label="Engine API Key (Bearer)", type="password")
    endpoint_url = gr.Textbox(
        label=(
            "Engine Endpoint URL (if running in Docker, use "
            "docker.host.internal to reach host)"
        ),
        placeholder=default_endpoint_placeholder,
    )
    require_mcp_auth = gr.Checkbox(label="Requires MCP authentication", value=False)
    mcp_bearer_token = gr.Textbox(
        label="MCP Bearer Token",
        type="password",
        placeholder="",
        visible=False,
    )
    return api_key, endpoint_url, require_mcp_auth, mcp_bearer_token
