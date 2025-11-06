"""Gradio UI for configuring the MCP server and ShellSmith host.

This module runs a small Gradio app in a background thread, offering:
- Configure Engine (POST to engine endpoint with API key)
- Set ShellSmith BaSyx Host (updates env/config)
"""

from __future__ import annotations

import logging
import os
import threading
from urllib.parse import urlparse

import httpx
from shellsmith.config import config

try:  # optional dependency at runtime
    import gradio as gr
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

    def configure_engine(api_key: str, engine_host: str) -> str:
        api_key_s = (api_key or "").strip()
        engine_host_s = (engine_host or "").strip()
        if not api_key_s:
            return "API key is required."
        if not engine_host_s or not _is_valid_url(engine_host_s):
            return "Engine host must be a valid URL (http/https)."

        mcp_url = f"http://{mcp_host}:{mcp_port}"
        endpoint = engine_host_s.rstrip("/") + "/api/mcp/register"
        headers = {"Authorization": f"Bearer {api_key_s}", "Content-Type": "application/json"}
        payload = {"name": "aas-mcp", "mcp_url": mcp_url}

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(endpoint, headers=headers, json=payload)
                if 200 <= resp.status_code < 300:
                    return f"Engine configured successfully at {endpoint}"
                return f"Engine config failed ({resp.status_code}): {resp.text[:200]}"
        except Exception as e:  # pragma: no cover - network errors
            return f"Error contacting engine: {e}"

    # UI components
    with gr.Blocks(title="AAS-MCP Control") as demo:
        gr.Markdown(
            """
            # AAS-MCP Control Panel
            - Configure your AI Engine with this MCP HTTP endpoint.
            - Optionally set a new ShellSmith BaSyx host for MCP tools.
            """
        )

        with gr.Row():
            api_key = gr.Textbox(label="AI Engine API Key", type="password")
            engine_host = gr.Textbox(label="AI Engine Host (http[s]://...)")
        engine_status = gr.Textbox(label="Engine Status", interactive=False)
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
            inputs=[api_key, engine_host],
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

