"""
Flask API wrapper for the HealthAssistant.
POST /chat  -> {"message": "..."}
Response: {"reply": "..."}
"""
from flask import Flask, request, jsonify, render_template, Response
import base64
import json
import datetime
from assistant import HealthAssistant

app = Flask(__name__)
assistant = HealthAssistant()

@app.route("/chat", methods=["POST", "GET"])
def chat():
    # Accept POST with JSON {"message": "..."} or GET /chat?message=...
    if request.method == "GET":
        message = request.args.get("message", "")
        use_ai = request.args.get("use_ai", None)
        if isinstance(use_ai, str):
            use_ai = use_ai.lower() in ("1", "true", "yes", "on")
    else:
        data = request.get_json(force=True, silent=True) or {}
        message = data.get("message", "")
        use_ai = data.get("use_ai", None)

    # Pass per-request override to assistant.respond. If use_ai is None, assistant uses its default.
    reply = assistant.respond(message, use_openai=use_ai)
    # Report whether the assistant used the AI model for this reply. Use getattr to be safe.
    used_ai = bool(getattr(assistant, "last_used_openai", False))

    # Append this exchange to persistent history
    try:
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "user": message,
            "reply": reply,
            "ai": used_ai,
        }
        append_history(entry)
    except Exception:
        # don't break the chat on history errors
        pass

    return jsonify({"reply": reply, "ai": used_ai})


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "ok",
        "message": "Health Assistant running. Use POST /chat with JSON {\"message\": \"...\"} or GET /chat?message=..."
    })


@app.route("/chatbox", methods=["GET"])
def chatbox():
    """Serve a simple web chat UI that talks to /chat."""
    return render_template("chatbox.html")


# Simple file-backed history storage. This is intentionally tiny and dependency-free.
HISTORY_FILE = "chat_history.json"


def read_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return []
    except Exception:
        # On any error, return empty history to avoid breaking endpoints
        return []


def append_history(entry: dict):
    hist = read_history()
    hist.append(entry)
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as fh:
            json.dump(hist, fh, ensure_ascii=False, indent=2)
    except Exception:
        # best-effort: ignore write errors
        pass


def clear_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as fh:
            json.dump([], fh)
    except Exception:
        pass


@app.route("/history", methods=["GET"])
def history():
    """Return the saved chat history as JSON."""
    return jsonify({"history": read_history()})


@app.route("/history/clear", methods=["POST"])
def history_clear():
    """Clear saved chat history."""
    clear_history()
    return jsonify({"status": "ok"})


_FAVICON_PNG = base64.b64decode(
    b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII='
)


@app.route('/favicon.ico')
def favicon():
    """Return a tiny transparent PNG as favicon to avoid 404s in logs."""
    return Response(_FAVICON_PNG, mimetype='image/png')

if __name__ == "__main__":
    # For development only. Use a WSGI server for production.
    app.run(host="0.0.0.0", port=5000, debug=True)
