"""
Slack front-end for the local agent. Runs over Socket Mode, so no public URL,
tunnel, or webhook is needed — everything (Slack connection + the LLM call)
happens from your own machine, still with no external AI API key.

Setup (see SLACK_SETUP.md for the full walkthrough):
    1. Create the Slack app from slack-manifest.yaml, install it to your workspace.
    2. Copy .env.example to .env and fill in SLACK_BOT_TOKEN and SLACK_APP_TOKEN.
    3. pip install -r requirements.txt
    4. python slack_bot.py

Usage in Slack:
    @local-agent <message>   in a channel it's been invited to
    or just DM it directly
"""

import os
import re

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from agent_core import DEFAULT_MODEL, AgentError, chat_once, load_history, save_history

load_dotenv()

BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
if not BOT_TOKEN or not APP_TOKEN:
    raise SystemExit(
        "Missing SLACK_BOT_TOKEN and/or SLACK_APP_TOKEN.\n"
        "Copy .env.example to .env and fill both in (see SLACK_SETUP.md)."
    )

app = App(token=BOT_TOKEN)

MENTION_PATTERN = re.compile(r"<@[A-Z0-9]+>\s*")


def _respond(text: str, session_id: str, say) -> None:
    text = text.strip()
    if not text:
        return
    history = load_history(session_id)
    try:
        reply = chat_once(DEFAULT_MODEL, history, text)
    except AgentError as e:
        say(f":warning: {e}")
        return
    save_history(session_id, history)
    say(reply)


@app.event("app_mention")
def handle_mention(event, say):
    # Strip the leading "@local-agent" mention from the message text.
    text = MENTION_PATTERN.sub("", event.get("text", ""), count=1)
    # One memory thread per channel it's mentioned in.
    _respond(text, session_id=f"slack-channel-{event['channel']}", say=say)


@app.event("message")
def handle_dm(event, say):
    # Only handle direct messages here; app_mention covers channels.
    if event.get("channel_type") != "im":
        return
    if event.get("bot_id") or event.get("subtype"):
        return  # ignore the bot's own messages, edits, deletions, etc.
    # One memory thread per user who DMs it.
    _respond(event.get("text", ""), session_id=f"slack-dm-{event['user']}", say=say)


if __name__ == "__main__":
    print("Local agent Slack bot starting (Socket Mode)...")
    SocketModeHandler(app, APP_TOKEN).start()
