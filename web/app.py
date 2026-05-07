"""Flask web application for the Chicago Zoning Assistant."""

from __future__ import annotations

import logging
import os
from typing import Any

from flask import Flask, jsonify, render_template, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates", static_folder="static")
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
MAX_QUESTION_LENGTH = 4000  # characters; rejects oversized payloads early

# Lazily initialized Gemini client (avoids cold-start API key check)
_gemini_client = None


def _get_client():
    global _gemini_client
    if _gemini_client is None:
        from web.gemini_client import GeminiZoningClient

        _gemini_client = GeminiZoningClient()
    return _gemini_client


def _gemini_error_payload(exc: Exception) -> dict[str, Any] | None:
    """Return a sanitized payload for Google GenAI SDK errors."""
    if exc.__class__.__module__ != "google.genai.errors":
        return None

    status_code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    response_json = getattr(exc, "details", None) or getattr(exc, "response_json", None) or {}
    error = response_json.get("error", {}) if isinstance(response_json, dict) else {}
    message = getattr(exc, "message", None) or error.get("message")
    if not message or message == getattr(exc, "status", None):
        message = str(exc)
    status = getattr(exc, "status", None) or error.get("status")

    payload: dict[str, Any] = {
        "error": "Gemini API request failed.",
        "detail": message,
    }
    if status_code:
        payload["status_code"] = status_code
    if status:
        payload["status"] = status
    return payload


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.post("/api/chat")
def chat() -> tuple[Any, int]:
    data: dict[str, Any] = request.get_json(force=True, silent=True) or {}
    question: str = (data.get("question") or "").strip()

    if not question:
        return jsonify({"error": "Question is required."}), 400

    if len(question) > MAX_QUESTION_LENGTH:
        return (
            jsonify(
                {
                    "error": (
                        f"Question is too long ({len(question)} chars). "
                        f"Maximum is {MAX_QUESTION_LENGTH}."
                    )
                }
            ),
            413,
        )

    try:
        client = _get_client()
        answer, trace = client.ask(question)
        tool_calls = trace.get("tool_calls", [])
        return (
            jsonify(
                {
                    "answer": answer,
                    "used_tools": bool(tool_calls),
                    "tool_calls": [
                        {"name": tc["name"], "args": tc["args"]} for tc in tool_calls
                    ],
                    "trace": trace,
                }
            ),
            200,
        )
    except RuntimeError as exc:
        # e.g. missing GOOGLE_API_KEY
        logger.error("Configuration error: %s", exc)
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        gemini_payload = _gemini_error_payload(exc)
        if gemini_payload is not None:
            logger.exception("Gemini API error handling chat request")
            return jsonify(gemini_payload), 502

        logger.exception("Unexpected error handling chat request")
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500


@app.get("/api/health")
def health() -> tuple[Any, int]:
    api_key_set = bool(os.environ.get("GOOGLE_API_KEY"))
    return (
        jsonify(
            {
                "status": "ok",
                "api_key_configured": api_key_set,
                "gemini_model": os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
                "tools_count": 10,
            }
        ),
        200,
    )


@app.get("/api/tools")
def list_tools() -> tuple[Any, int]:
    from web.gemini_client import GeminiZoningClient

    return jsonify({"tools": GeminiZoningClient.tool_names()}), 200


# ---------------------------------------------------------------------------
# Entry point (dev only — production uses gunicorn)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
