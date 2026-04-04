from flask import Flask, request, jsonify, render_template
from ai_engine import get_ai_response
from conversation import detect_stage, add_guidance, create_profile, update_profile
from database import save_lead
from config import ALLOWED_ORIGINS, FLASK_HOST, FLASK_PORT

app = Flask(__name__)
SESSION_STATE = {}


def _get_session(session_id):
    if session_id not in SESSION_STATE:
        SESSION_STATE[session_id] = {
            "profile": create_profile(),
            "history": [],
        }
    return SESSION_STATE[session_id]


def _origin_allowed(origin):
    if not origin:
        return False
    if "*" in ALLOWED_ORIGINS:
        return True
    return origin in ALLOWED_ORIGINS


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "").strip()

    if "*" in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = "*"
    elif _origin_allowed(origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"

    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization,X-Session-Id"
    return response

@app.route("/", methods=["GET"])
def health_check():
    """Endpoint to verify the server is alive."""
    return jsonify({"status": "online", "service": "AgentX"})

@app.route("/chat-demo", methods=["GET"])
def chat_demo():
    """Simple browser demo page that uses /chat endpoint."""
    return render_template("chatbot_demo.html")


@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return ("", 204)

    json_data = request.get_json(silent=True)
    if isinstance(json_data, dict):
        data = json_data
    elif request.form:
        data = request.form.to_dict(flat=True)
    else:
        data = {}

    user_message = str(
        data.get("message")
        or data.get("text")
        or data.get("prompt")
        or ""
    ).strip()

    if not user_message:
        if request.is_json and json_data is None:
            return jsonify({
                "error": "Invalid JSON body. Use: {\"message\": \"your text\", \"session_id\": \"optional\"}"
            }), 400
        return jsonify({"error": "Missing text. Send one of: message | text | prompt"}), 400

    session_id = str(
        data.get("session_id")
        or request.headers.get("X-Session-Id")
        or "default"
    ).strip() or "default"
    session = _get_session(session_id)

    # Detect stage
    stage = detect_stage(user_message)

    # Update personalization state
    session["profile"] = update_profile(session["profile"], user_message)
    session["history"].append(user_message)
    session["history"] = session["history"][-6:]

    # Save lead with stage and extracted contact fields (if any)
    save_lead(user_message, stage)

    # Add lead + personalization guidance
    guidance = add_guidance(stage, user_message, session["profile"], session["history"])

    # AI response with integrated guidance
    try:
        ai_reply = get_ai_response(user_message, guidance)
    except Exception as e:
        return jsonify({
            "error": "Internal AI Engine Error",
            "details": str(e)
        }), 500

    return jsonify({"reply": ai_reply, "session_id": session_id})


if __name__ == "__main__":
    print("\n" + "="*40)
    print("AgentX Server is starting...")
    print(f"Target: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"Demo UI: http://{FLASK_HOST}:{FLASK_PORT}/chat-demo")
    print("Keep this window OPEN while testing.")
    print("="*40 + "\n")
    app.run(debug=False, host=FLASK_HOST, port=FLASK_PORT)
