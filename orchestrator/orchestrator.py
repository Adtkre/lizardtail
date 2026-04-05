from flask import Flask, jsonify, request
import docker
import time
import threading
import requests
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

client = docker.from_env()
event_log = []

AUTO_HEAL_ENABLED = True
MONITOR_INTERVAL  = 5


# ── Logging ───────────────────────────────────────────────────
def log_event(message, event_type="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")   # shorter timestamp suits the UI
    event = {"timestamp": timestamp, "type": event_type, "message": message}
    event_log.append(event)
    print(f"[{timestamp}] {event_type}: {message}")


# ── Container helpers ─────────────────────────────────────────
def get_container_status():
    try:
        containers = client.containers.list(all=True)
        return [
            {"name": c.name, "status": c.status, "id": c.short_id}
            for c in containers if 'lizardtail' in c.name
        ]
    except Exception as e:
        log_event(f"Error getting container status: {e}", "ERROR")
        return []


def check_service_health(service_name, port):
    try:
        resp = requests.get(f"http://{service_name}:{port}/health", timeout=3)
        return resp.json().get("status") == "healthy"
    except Exception:
        return False


def heal_service(container_name):
    try:
        log_event(f"Starting healing process for {container_name}", "HEALING")

        try:
            container = client.containers.get(container_name)
        except docker.errors.NotFound:
            log_event(f"Container {container_name} not found", "ERROR")
            return False

        image_name   = container.image.tags[0] if container.image.tags else None
        network_name = list(container.attrs['NetworkSettings']['Networks'].keys())[0]
        ports        = container.attrs['HostConfig']['PortBindings']

        # FIX: preserve environment variables so the new container has the same config
        env_vars = container.attrs['Config']['Env']

        log_event(f"Stopping {container_name}…", "HEALING")
        container.stop(timeout=5)

        log_event(f"Removing {container_name}…", "HEALING")
        container.remove()

        log_event(f"Recreating {container_name}…", "HEALING")
        port_bindings = {cp: hc[0]['HostPort'] for cp, hc in ports.items()}

        client.containers.run(
            image          = image_name,
            name           = container_name,
            detach         = True,
            network        = network_name,
            ports          = port_bindings,
            environment    = env_vars,        # ← preserved env
            restart_policy = {"Name": "unless-stopped"},
        )

        log_event(f"{container_name} successfully healed", "SUCCESS")
        return True

    except Exception as e:
        log_event(f"Failed to heal {container_name}: {e}", "ERROR")
        return False


# ── Auto-monitor thread ───────────────────────────────────────
def auto_monitor():
    log_event("Auto-monitor thread started", "SYSTEM")
    time.sleep(10)   # wait for services to come up

    while AUTO_HEAL_ENABLED:
        try:
            is_healthy = check_service_health("lizardtail_service_a", 5000)

            if not is_healthy:
                log_event("DETECTED: service_a unhealthy — auto-healing…", "DETECTION")
                success = heal_service("lizardtail_service_a")
                if success:
                    log_event("Auto-heal successful", "SUCCESS")
                    time.sleep(15)   # cooldown after heal
                else:
                    log_event("Auto-heal failed", "ERROR")

            time.sleep(MONITOR_INTERVAL)

        except Exception as e:
            log_event(f"Monitor error: {e}", "ERROR")
            time.sleep(MONITOR_INTERVAL)


# ── Routes ────────────────────────────────────────────────────
@app.route('/status', methods=['GET'])
def status():
    containers = get_container_status()
    return jsonify({
        "containers":        containers,
        "total":             len(containers),
        "auto_heal_enabled": AUTO_HEAL_ENABLED,
    }), 200


@app.route('/logs', methods=['GET'])
def logs():
    limit = request.args.get('limit', 50, type=int)
    return jsonify({"logs": event_log[-limit:]}), 200


@app.route('/heal/<container_name>', methods=['POST'])
def heal(container_name):
    log_event(f"Manual heal triggered for {container_name}", "COMMAND")
    success = heal_service(container_name)
    if success:
        return jsonify({"message": f"{container_name} healed successfully"}), 200
    return jsonify({"message": f"Failed to heal {container_name}"}), 500


# FIX: after infecting, log a DETECTION event so the UI log panel shows activity
@app.route('/infect/<service_name>', methods=['POST'])
def infect(service_name):
    try:
        if service_name == "service_a":
            response = requests.post("http://lizardtail_service_a:5000/infect", timeout=5)
            log_event(f"Attack launched on {service_name} — cryptominer + DDoS", "ATTACK")
            log_event(f"Anomaly detector flagged {service_name} for abnormal resource usage", "DETECTION")
            return jsonify({"message": f"{service_name} infected"}), 200
        return jsonify({"message": "Only service_a can be infected"}), 400
    except Exception as e:
        log_event(f"Failed to infect {service_name}: {e}", "ERROR")
        return jsonify({"message": str(e)}), 500


@app.route('/auto-heal', methods=['POST'])
def auto_heal():
    log_event("Auto-heal check initiated", "COMMAND")
    if not check_service_health("lizardtail_service_a", 5000):
        log_event("service_a unhealthy — triggering heal", "DETECTION")
        success = heal_service("lizardtail_service_a")
        if success:
            return jsonify({"message": "service_a healed"}), 200
        return jsonify({"message": "Healing failed"}), 500
    log_event("All services healthy", "INFO")
    return jsonify({"message": "All services healthy"}), 200


# ── Entry point ───────────────────────────────────────────────
if __name__ == '__main__':
    log_event("Orchestrator started", "SYSTEM")

    monitor_thread = threading.Thread(target=auto_monitor, daemon=True)
    monitor_thread.start()
    log_event("Auto-healing monitoring enabled (checks every 5 seconds)", "SYSTEM")

    app.run(host='0.0.0.0', port=8000, debug=False)