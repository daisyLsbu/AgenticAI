"""
Local AI Agent (CLI) — runs entirely on your machine via Ollama.
No external API key required.

Usage:
    python agent.py                # interactive chat
    python agent.py --model qwen2.5:7b-instruct
    python agent.py --reset        # clear this session's saved memory
"""

import argparse

from agent_core import DEFAULT_MODEL, AgentError, chat_once, load_history, reset_history, save_history


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Ollama-based AI agent")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model tag to use")
    parser.add_argument("--session", default="cli", help="Conversation/session id (separate memory per id)")
    parser.add_argument("--reset", action="store_true", help="Clear saved conversation memory for this session")
    args = parser.parse_args()

    if args.reset:
        reset_history(args.session)
        print("Memory cleared.")

    history = load_history(args.session)

    print(f"Local agent ready (model: {args.model}, session: {args.session}). Type 'exit' or 'quit' to stop.\n")

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
        try:
            chat_once(args.model, history, user_message, on_token=lambda piece: print(piece, end="", flush=True))
            print()
        except AgentError as e:
            print(f"\n[error] {e}")
            history.pop()  # drop the user message we couldn't get a reply to
            continue

        save_history(args.session, history)


if __name__ == "__main__":
    main()
