from flask import Flask, jsonify
import random
import time
from flask_cors import CORS

app = Flask(__name__)

# IMPORTANT: enable CORS for all routes
CORS(app)

# Global state
infected = False


# ---------------- SENSOR ----------------
@app.route('/sensor', methods=['GET'])
def sensor():
    """Return temperature data - normal or infected"""
    global infected

    if infected:
        # Infected behavior: slow + abnormal values
        time.sleep(2)
        temp = random.randint(500, 999)
        status = "INFECTED"
    else:
        temp = round(random.uniform(22.0, 28.0), 1)
        status = "healthy"

    return jsonify({
        "temperature": temp,
        "status": status,
        "service": "service_a"
    }), 200


# ---------------- INFECT ----------------
@app.route('/infect', methods=['POST'])
def infect():
    """Trigger malicious behavior"""
    global infected
    infected = True

    return jsonify({
        "message": "Service infected",
        "status": "compromised"
    }), 200


# ---------------- HEALTH ----------------
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "infected" if infected else "healthy",
        "service": "service_a"
    }), 200


# ---------------- RESET (optional but useful) ----------------
@app.route('/reset', methods=['POST'])
def reset():
    global infected
    infected = False
    return jsonify({"message": "Service reset"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
