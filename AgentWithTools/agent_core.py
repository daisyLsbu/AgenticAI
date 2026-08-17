"""
Shared agent logic used by both the CLI (agent.py) and the HTTP server (server.py).

Keeping this in one place means the CLI and the future Slack bot are always
talking to the exact same agent behaviour — no drift between interfaces.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Optional

import ollama

DEFAULT_MODEL = "llama3.1:8b"

# One memory file per "session" (a CLI run, a Slack channel, a Slack user...).
# Keeping histories separate means Slack conversations won't bleed into each
# other or into your terminal sessions.
MEMORY_DIR = Path(__file__).parent / "memory"
MEMORY_DIR.mkdir(exist_ok=True)

SYSTEM_PROMPT = (
    "You are a helpful, concise local AI assistant running fully offline "
    "on the user's own machine via Ollama. Be direct and practical."
)


def _memory_path(session_id: str) -> Path:
    # Sanitize so Slack channel/user IDs can't escape the memory directory.
    safe_id = "".join(c for c in session_id if c.isalnum() or c in ("-", "_")) or "default"
    return MEMORY_DIR / f"{safe_id}.json"


def load_history(session_id: str = "default") -> list[dict]:
    path = _memory_path(session_id)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def save_history(session_id: str, history: list[dict]) -> None:
    _memory_path(session_id).write_text(json.dumps(history, indent=2), encoding="utf-8")


def reset_history(session_id: str = "default") -> None:
    path = _memory_path(session_id)
    if path.exists():
        path.unlink()


class AgentError(RuntimeError):
    """Raised when Ollama can't be reached or the model isn't available."""


def chat_once(
    model: str,
    history: list[dict],
    user_message: str,
    on_token: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Send the full conversation (history + new user_message) to Ollama.

    If on_token is given, it's called with each streamed chunk as it arrives
    (used by the CLI to print live). Otherwise the full reply is fetched and
    returned in one go (used by the HTTP server).

    Mutates `history` in place: appends the user message and the reply.
    """
    history.append({"role": "user", "content": user_message})

    try:
        if on_token:
            chunks = []
            for chunk in ollama.chat(model=model, messages=history, stream=True):
                piece = chunk["message"]["content"]
                on_token(piece)
                chunks.append(piece)
            full_reply = "".join(chunks)
        else:
            response = ollama.chat(model=model, messages=history, stream=False)
            full_reply = response["message"]["content"]
    except ollama.ResponseError as e:
        raise AgentError(
            f"{e.error} (if the model is missing, pull it first: ollama pull {model})"
        ) from e
    except Exception as e:
        raise AgentError(
            f"Could not reach Ollama: {e}. Is the Ollama app/service running?"
        ) from e

    history.append({"role": "assistant", "content": full_reply})
    return full_reply
