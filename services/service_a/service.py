from flask import Flask, jsonify
from flask_cors import CORS
import random
import time
import psutil

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ── Global state ──────────────────────────────────────────────
infected = False   # MUST be module-level; every route uses `global infected`


# ── Helpers ───────────────────────────────────────────────────
def get_real_metrics():
    """Return real container metrics, fall back to random on error."""
    try:
        cpu     = psutil.cpu_percent(interval=0.1)
        memory  = psutil.virtual_memory().percent
        disk    = psutil.disk_usage('/').percent
        net     = psutil.net_io_counters()
        network = (net.bytes_sent + net.bytes_recv) / (1024 * 1024)
        return {
            "cpu":     round(cpu, 1),
            "memory":  round(memory, 1),
            "disk":    round(disk, 1),
            "network": round(network, 2),
        }
    except Exception as e:
        print(f"psutil error: {e}")
        return {
            "cpu":     round(random.uniform(20, 40), 1),
            "memory":  round(random.uniform(30, 50), 1),
            "disk":    round(random.uniform(40, 60), 1),
            "network": round(random.uniform(5, 15), 2),
        }


# ── /metrics ──────────────────────────────────────────────────
@app.route('/metrics', methods=['GET'])
def metrics():
    if infected:
        time.sleep(0.5)   # simulate degraded response (was 2 s — too slow for UI)
        return jsonify({
            "cpu":         round(random.uniform(95, 99.9), 1),
            "memory":      round(random.uniform(90, 99), 1),
            "disk":        round(random.uniform(85, 95), 1),
            "network":     round(random.uniform(500, 999), 2),
            "status":      "INFECTED",
            "service":     "service_a",
            "threat_type": "Resource Exhaustion Attack",
        }), 200
    else:
        m = get_real_metrics()
        return jsonify({**m, "status": "healthy", "service": "service_a", "source": "real"}), 200


# ── /sensor ───────────────────────────────────────────────────
# FIX: was calling metrics() and treating the Response object as a dict — now
#      we call get_real_metrics() directly so we always get a plain dict.
@app.route('/sensor', methods=['GET'])
def sensor():
    if infected:
        cpu = round(random.uniform(95, 99.9), 1)
        return jsonify({"temperature": cpu, "status": "INFECTED", "service": "service_a"}), 200
    else:
        m = get_real_metrics()
        return jsonify({"temperature": m["cpu"], "status": "healthy", "service": "service_a"}), 200


# ── /infect ───────────────────────────────────────────────────
# FIX: `global infected` was missing — without it Python treats `infected`
#      as a local variable and the assignment never persists.
@app.route('/infect', methods=['POST'])
def infect():
    global infected          # ← this was the main bug
    infected = True
    return jsonify({
        "message":     "Service infected — resource exhaustion attack initiated",
        "status":      "compromised",
        "attack_type": "Cryptominer + DDoS",
    }), 200


# ── /health ───────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status":  "infected" if infected else "healthy",
        "service": "service_a",
    }), 200


# ── Run ───────────────────────────────────────────────────────
if __name__ == '__main__':
    print("service_a running on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)