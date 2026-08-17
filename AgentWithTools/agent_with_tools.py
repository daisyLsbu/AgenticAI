"""
Tool-using version of the local agent - same Ollama model, same memory
system, but now it can call local tools (see tools.py) when it decides
it needs to: do arithmetic, check the time, or read a file from its
workspace/ folder, before answering.

Usage:
    python agent_with_tools.py
    python agent_with_tools.py --model qwen2.5:7b-instruct
    python agent_with_tools.py --reset

Try asking it things like:
    "what's 47 * 68?"
    "what time is it?"
    "what files are in your workspace?"
    "read notes.txt and summarize it"    (after adding workspace/notes.txt)
"""

import argparse

from agent_core import DEFAULT_MODEL, AgentError, chat_once, load_history, reset_history, save_history
from tools import AVAILABLE_FUNCTIONS, TOOL_SCHEMAS


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Ollama-based AI agent with tool-calling")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model tag to use (must support tool calling)")
    parser.add_argument("--session", default="tools-cli", help="Conversation/session id (separate memory per id)")
    parser.add_argument("--reset", action="store_true", help="Clear saved conversation memory for this session")
    args = parser.parse_args()

    if args.reset:
        reset_history(args.session)
        print("Memory cleared.")

    history = load_history(args.session)

    print(f"Tool-using agent ready (model: {args.model}, session: {args.session}). Type 'exit' or 'quit' to stop.\n")

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

        try:
            reply = chat_once(
                args.model,
                history,
                user_message,
                tools=TOOL_SCHEMAS,
                available_functions=AVAILABLE_FUNCTIONS,
            )
            print(f"agent> {reply}")
        except AgentError as e:
            print(f"[error] {e}")
            history.pop()  # drop the user message we couldn't get a reply to
            continue

        save_history(args.session, history)


if __name__ == "__main__":
    main()