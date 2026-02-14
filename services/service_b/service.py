from flask import Flask, jsonify
import time

app = Flask(__name__)

@app.route('/status', methods=['GET'])
def status():
    """Simple status endpoint"""
    return jsonify({
        "message": "Service B running",
        "service": "service_b"
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "service": "service_b"
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
