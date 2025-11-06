"""Gradio UI for configuring the MCP server and ShellSmith host.

This module composes a reusable heading and engine input section with
MCP-specific controls. The generic pieces live in `ui_common` so they can be
reused by other apps.
"""

from datetime import datetime
import json
import logging
import os
import threading
from urllib.parse import urlparse

import httpx
from shellsmith.config import config
from .ui_common import add_heading, build_engine_inputs

# Disable Gradio telemetry/analytics via env before importing
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

try:  # optional dependency at runtime
    import gradio as gr
    # Extra safety: disable via runtime flag if present
    try:  # pragma: no cover - runtime feature gate
        if hasattr(gr, "utils") and hasattr(gr.utils, "analytics_enabled"):
            gr.utils.analytics_enabled = False  # type: ignore[attr-defined]
    except Exception:
        pass
except Exception:  # pragma: no cover
    gr = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def _is_valid_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in {"http", "https"} and bool(p.netloc)
    except Exception:
        return False


def maybe_start_ui(ui_host: str, ui_port: int, mcp_host: str, mcp_port: int) -> None:
    """Start the Gradio UI in a background thread if Gradio is available."""
    if gr is None:  # type: ignore[truthy-bool]
        logger.warning("Gradio not installed; skipping UI startup")
        return

    # Handlers
    def set_shellsmith_host(new_host: str) -> str:
        new_host = (new_host or "").strip()
        if not new_host:
            return "No host provided; keeping existing configuration."
        if not _is_valid_url(new_host):
            return "Invalid ShellSmith host URL. Please include http(s)://"
        # Persist for current process and child clients
        os.environ["SHELLSMITH_BASYX_ENV_HOST"] = new_host
        try:
            # Update runtime config for new requests
            config.host = new_host  # type: ignore[attr-defined]
        except Exception:
            pass
        return f"ShellSmith host set to: {new_host}"

    def _post_thread(endpoint_url: str, api_key_val: str, thread_name: str, payload: dict) -> httpx.Response:
        headers = {
            "Authorization": f"Bearer {api_key_val}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        body = {"thread_name": thread_name, "payload": payload}
        with httpx.Client(timeout=15.0) as client:
            return client.post(endpoint_url, headers=headers, json=body)

    def _get_spec_by_name(endpoint_url: str, api_key_val: str, name: str):
        try:
            resp = _post_thread(
                endpoint_url,
                api_key_val,
                "get-mcp-server-spec-by-name",
                {"path_params": {"name": name}, "query_params": None, "body_params_serialized": None},
            )
        except Exception as e:  # pragma: no cover - network errors
            return {"error": f"Network error while checking name: {e}"}

        if resp.status_code == 404:
            return {"data": None}
        if not (200 <= resp.status_code < 300):
            return {"error": f"Lookup failed ({resp.status_code}): {resp.text[:200]}"}
        try:
            return {"data": resp.json()}
        except Exception:
            return {"error": f"Invalid JSON from lookup ({resp.status_code})"}

    def configure_engine(
        api_key: str,
        endpoint_url: str,
        spec_name: str,
        mcp_reachable_url: str,
        tags_raw: str,
        description: str | None = None,
        mcp_bearer_token: str | None = None,
    ) -> str:
        # Validate inputs
        api_key_s = (api_key or "").strip()
        endpoint_s = (endpoint_url or "").strip()
        name_s = (spec_name or "").strip()
        mcp_url_in = (mcp_reachable_url or "").strip()
        tags_s = (tags_raw or "").strip()
        desc_s = (description or "").strip() if description is not None else ""
        mcp_bearer_s = (mcp_bearer_token or "").strip() if mcp_bearer_token is not None else ""

        if not api_key_s:
            return "API key is required."
        if not endpoint_s or not _is_valid_url(endpoint_s):
            return "Engine endpoint URL must be a valid URL (http/https)."
        if not name_s:
            return "Name is required."
        if not mcp_url_in or not _is_valid_url(mcp_url_in):
            return "MCP URL must be a valid URL (http/https) reachable by the engine."

        # Parse tags
        tags = [t.strip() for t in tags_s.split(",") if t.strip()] if tags_s else []

        # Build DTO according to spec
        dto = {
            "key": "",
            "name": name_s,
            "description": desc_s,
            "transport": "http",
            "command": None,
            "url": mcp_url_in,
            "bearer_token": (mcp_bearer_s or None),
            "env": None,
            "tags": tags,
            "is_standard": False,
            "created_at": datetime.now().isoformat()
        }

        # First, check uniqueness by name
        lookup = _get_spec_by_name(endpoint_s, api_key_s, name_s)
        if "error" in lookup:
            return f"Name check failed: {lookup['error']}"

        existing = lookup.get("data")

        # Create or update
        try:
            if existing is None:
                # Create flow
                resp = _post_thread(
                    endpoint_s,
                    api_key_s,
                    "create-mcp-server-spec",
                    {
                        "path_params": None,
                        "query_params": None,
                        "body_params_serialized": json.dumps(dto),
                    },
                )
                if resp.status_code != 201:
                    return f"Create failed ({resp.status_code}): {resp.text[:300]}"
                try:
                    data = resp.json().get("data")
                except Exception:
                    data = None
                key = (data or {}).get("key") if isinstance(data, dict) else None
                return f"Created MCP Server Spec '{name_s}' (key={key or '?'})."
            else:
                # Update flow
                key = existing.get("key") if isinstance(existing, dict) else None
                if not key:
                    return "Update failed: existing spec has no key."
                resp = _post_thread(
                    endpoint_s,
                    api_key_s,
                    "update-mcp-server-spec",
                    {
                        "path_params": {"key": key},
                        "query_params": None,
                        "body_params_serialized": json.dumps(dto),
                    },
                )
                if resp.status_code != 200:
                    return f"Update failed ({resp.status_code}): {resp.text[:300]}"
                return f"Updated MCP Server Spec '{name_s}' (key={key})."
        except Exception as e:  # pragma: no cover - network errors
            return f"Error contacting engine: {e}"

    # UI components
    with gr.Blocks(title="AAS-MCP Control") as demo:
        # Reusable heading section
        add_heading(
            title="AAS-MCP Control Panel",
            bullets=[
                "Configure your AI Engine with this MCP HTTP endpoint.",
                "Optionally set a new ShellSmith BaSyx host for MCP tools.",
            ],
        )

        # Reusable engine inputs
        with gr.Row():
            api_key, endpoint_url, require_mcp_auth, mcp_bearer_token = build_engine_inputs()
        # Toggle visibility of MCP bearer token based on checkbox
        def _toggle_token_vis(enabled: bool):  # pragma: no cover - UI binding
            return gr.update(visible=bool(enabled))
        require_mcp_auth.change(fn=_toggle_token_vis, inputs=require_mcp_auth, outputs=mcp_bearer_token)
        with gr.Row():
            spec_name = gr.Textbox(label="Spec Name (unique)", placeholder="aas-mcp")
            mcp_public_url = gr.Textbox(
                label="MCP URL (reachable by engine)",
                value=f"http://{mcp_host}:{mcp_port}",
            )
        tags_input = gr.Textbox(label="Tags (comma-separated)", placeholder="prod, http, aas")
        description_input = gr.Textbox(label="Description (optional)", lines=3)
        engine_status = gr.Textbox(label="Configure Status", interactive=False)
        configure_btn = gr.Button("Configure Engine")

        gr.Markdown("---")
        shellsmith_host = gr.Textbox(
            label="ShellSmith BaSyx Host (optional)",
            placeholder="http://localhost:8081",
        )
        shellsmith_status = gr.Textbox(label="ShellSmith Status", interactive=False)
        set_host_btn = gr.Button("Set ShellSmith Host")

        configure_btn.click(
            fn=configure_engine,
            inputs=[api_key, endpoint_url, spec_name, mcp_public_url, tags_input, description_input, mcp_bearer_token],
            outputs=engine_status,
        )
        set_host_btn.click(
            fn=set_shellsmith_host,
            inputs=[shellsmith_host],
            outputs=shellsmith_status,
        )

    def _launch():
        try:
            demo.launch(
                server_name=ui_host,
                server_port=ui_port,
                share=False,
                inbrowser=False,
                prevent_thread_lock=True,
            )
            logger.info("Gradio UI available at http://%s:%s", ui_host, ui_port)
        except Exception as e:  # pragma: no cover
            logger.error("Failed to launch Gradio UI: %s", e)

    t = threading.Thread(target=_launch, name="gradio-ui", daemon=True)
    t.start()
