"""
Standalone local AI agent (CLI) — runs entirely on your machine via Ollama.
No external API key required, no agent_core.py dependency — everything is
in this one file.

Usage:
    python agent_standalone.py
    python agent_standalone.py --model qwen2.5:7b-instruct
    python agent_standalone.py --reset        # clear saved conversation memory
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import ollama

# ---- Configuration -----------------------------------------------------

DEFAULT_MODEL = "llama3.1:8b"
MEMORY_FILE = Path(__file__).parent / "standalone_memory.json"

SYSTEM_PROMPT = (
    "You are a helpful, concise local AI assistant running fully offline "
    "on the user's own machine via Ollama. Be direct and practical."
)

# ---- Memory (conversation history) --------------------------------------


def load_history() -> list[dict]:
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            print("[warning] memory file was unreadable, starting fresh.", file=sys.stderr)
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def save_history(history: list[dict]) -> None:
    MEMORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")


# ---- Core agent call -----------------------------------------------------


def ask(model: str, history: list[dict], user_message: str) -> str:
    """Send the full conversation to Ollama and stream the reply."""
    history.append({"role": "user", "content": user_message})

    reply_chunks = []
    try:
        stream = ollama.chat(model=model, messages=history, stream=True)
        for chunk in stream:
            piece = chunk["message"]["content"]
            print(piece, end="", flush=True)
            reply_chunks.append(piece)
        print()  # newline after the streamed reply
    except ollama.ResponseError as e:
        # Common case: model not pulled yet.
        raise SystemExit(
            f"\n[error] {e.error}\n"
            f"If the model is missing, pull it first: ollama pull {model}"
        )
    except Exception as e:
        raise SystemExit(
            f"\n[error] Could not reach Ollama: {e}\n"
            f"Is the Ollama app/service running? Try: ollama list"
        )

    full_reply = "".join(reply_chunks)
    history.append({"role": "assistant", "content": full_reply})
    return full_reply


# ---- CLI loop --------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Standalone local Ollama-based AI agent")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model tag to use")
    parser.add_argument("--reset", action="store_true", help="Clear saved conversation memory")
    args = parser.parse_args()

    if args.reset and MEMORY_FILE.exists():
        MEMORY_FILE.unlink()
        print("Memory cleared.")

    history = load_history()

    print(f"Local agent ready (model: {args.model}). Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            user_message = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not user_message:
            continue
        if user_message.lower() in {"exit", "quit"}:
            print("Bye.")
            break

        print("agent> ", end="", flush=True)
        ask(args.model, history, user_message)
        save_history(history)


if __name__ == "__main__":
    main()
