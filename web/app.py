"""Flask web application for the Chicago Zoning Assistant."""

from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from collections import deque
from typing import Any, Deque

from flask import Flask, jsonify, render_template, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates", static_folder="static")
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
MAX_QUESTION_LENGTH = 4000  # characters; rejects oversized payloads early

# Lazily initialized Gemini client (avoids cold-start API key check)
_gemini_client = None

# ---------------------------------------------------------------------------
# In-memory conversation sessions
# ---------------------------------------------------------------------------
# Each session keeps a small rolling transcript and a dict of resolved
# entities (last address / district / lot area / etc). This is intentionally
# in-process — sessions are best-effort and reset when the worker restarts.

_SESSION_TTL_SECONDS = 60 * 60  # 1 hour
_SESSION_MAX = 500
_SESSION_HISTORY_TURNS = 8  # 4 Q/A pairs

_sessions: dict[str, dict[str, Any]] = {}
_sessions_lock = threading.Lock()


def _prune_sessions_locked() -> None:
    """Drop expired or oldest sessions. Caller holds ``_sessions_lock``."""
    now = time.monotonic()
    expired = [sid for sid, s in _sessions.items() if now - s["updated"] > _SESSION_TTL_SECONDS]
    for sid in expired:
        _sessions.pop(sid, None)
    while len(_sessions) > _SESSION_MAX:
        _sessions.pop(next(iter(_sessions)), None)


def _get_session(session_id: str | None) -> tuple[str, dict[str, Any]]:
    """Return ``(session_id, session)``, creating a new session if needed."""
    with _sessions_lock:
        _prune_sessions_locked()
        if session_id and session_id in _sessions:
            session = _sessions[session_id]
            session["updated"] = time.monotonic()
            return session_id, session
        new_id = session_id or uuid.uuid4().hex
        history: Deque[dict[str, str]] = deque(maxlen=_SESSION_HISTORY_TURNS)
        session = {
            "history": history,
            "entities": {},
            "updated": time.monotonic(),
        }
        _sessions[new_id] = session
        return new_id, session


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
    session_id_in = data.get("session_id") or None

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

    session_id, session = _get_session(session_id_in)
    history_snapshot = list(session["history"])
    entities_snapshot = dict(session["entities"])

    try:
        client = _get_client()
        answer, trace = client.ask(
            question,
            history=history_snapshot,
            entities=entities_snapshot,
        )
        tool_calls = trace.get("tool_calls", [])
        # Persist the new turn back to the session.
        with _sessions_lock:
            session["history"].append({"role": "user", "content": question})
            session["history"].append({"role": "assistant", "content": answer})
            session["entities"] = trace.get("entities") or entities_snapshot
            session["updated"] = time.monotonic()
        return (
            jsonify(
                {
                    "answer": answer,
                    "used_tools": bool(tool_calls),
                    "tool_calls": [
                        {"name": tc["name"], "args": tc["args"]} for tc in tool_calls
                    ],
                    "trace": trace,
                    "session_id": session_id,
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


@app.post("/api/session/reset")
def reset_session() -> tuple[Any, int]:
    """Clear a session's conversation history."""
    data: dict[str, Any] = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id") or None
    if session_id:
        with _sessions_lock:
            _sessions.pop(session_id, None)
    return jsonify({"ok": True}), 200


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
