# app.py

from flask import Flask, render_template, request, jsonify
from bot_logic import SummeryBot  # Import the SummeryBot class
from flask_session import Session  # To handle server-side sessions
import uuid
import threading

app = Flask(__name__)

# Configure server-side session
app.config['SECRET_KEY'] = 'THISISSTRONGKEYFORSESSION'  # Replace with a strong secret key
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Dictionary to store SummeryBot instances mapped by uid
summery_bots = {}
summery_bots_lock = threading.Lock()  # To ensure thread safety

@app.route("/")
def home():
    """
    Renders the main chatbot interface.
    """
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def get_bot_response_route():
    """
    Handles POST requests to generate chatbot responses.

    Expects a JSON payload with 'uid' and 'message' fields containing the user's unique ID and input.

    Returns a JSON response with the chatbot's reply.
    """
    data = request.get_json()
    user_input = data.get("message", "").strip()
    uid = data.get("uid", "").strip()
    
    if not uid:
        # Respond with an error message if uid is missing
        return jsonify({"response": "Error: 'uid' is missing from the request.", "uid": ""})
    
    if user_input:
        with summery_bots_lock:
            if uid not in summery_bots:
                summery_bots[uid] = SummeryBot()
            bot = summery_bots[uid]
        
        response = bot.generate_response(user_input)
        return jsonify({"response": response, "uid": uid})
    
    return jsonify({"response": "Sorry, I didn't understand that.", "uid": uid})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=False)
