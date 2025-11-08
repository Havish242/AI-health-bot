"""
Simple CLI client that sends messages to the Flask server at http://localhost:5000/chat.
If the server is unreachable, it falls back to a local assistant instance.
"""
import json
import sys

try:
    import requests
except Exception:
    requests = None

from assistant import HealthAssistant

SERVER_URL = "http://127.0.0.1:5000/chat"


def run_cli():
    assistant = HealthAssistant()
    print("Health assistant CLI. Type 'exit' to quit.")
    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye")
            return
        if not message:
            continue
        if message.lower() in ("exit", "quit"):
            print("Goodbye")
            return

        # Try server first
        if requests is not None:
            try:
                resp = requests.post(SERVER_URL, json={"message": message}, timeout=3)
                data = resp.json()
                print("Bot:", data.get("reply"))
                continue
            except Exception as e:
                # Fall back to local
                print("(Server not reachable, using local assistant) ")

        reply = assistant.respond(message)
        print("Bot:", reply)


if __name__ == "__main__":
    run_cli()
