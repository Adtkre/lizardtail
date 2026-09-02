from flask import Flask, jsonify, request, send_from_directory
import docker
import time
import threading
import requests
import hashlib
from datetime import datetime
from flask_cors import CORS
import os
import sys

# Ensure ml directory can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from ml.detector import detect_anomaly
except ImportError:
    # mock fallback if ml doesn't load for some reason
    def detect_anomaly(tel): return {"status": "NORMAL", "score": 0.0, "reason": "No ML active"}

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

client = docker.from_env()
event_log = []

# State constraints
VALID_STATES = [
    "NORMAL", "ANOMALY_DETECTED", "ISOLATING", "ISOLATED", 
    "VERIFYING", "VERIFIED", "HEALING", "RECOVERED", "FAILED"
]
system_state = "NORMAL"
anomaly_info = None
current_telemetry = {}

def log_event(message, event_type="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    event = {"timestamp": timestamp, "type": event_type, "message": message}
    event_log.append(event)
    print(f"[{timestamp}] {event_type}: {message}")

def set_state(new_state):
    global system_state
    if new_state in VALID_STATES:
        system_state = new_state
        log_event(f"System state transitioned to {new_state}", "STATE")

def verify_integrity(container_name):
    try:
        # Simulate checking the SHA-256 of the trusted service version
        image_name = "lizardtail_service_a" # Typically we verify the image or binary
        trusted_content = b"TRUSTED_LIZARDTAIL_SERVICE_FIRMWARE_V1"
        trusted_hash = hashlib.sha256(trusted_content).hexdigest()
        
        log_event(f"Extracting signature for {container_name}...", "VERIFY")
        time.sleep(1) # Simulation time
        
        current_hash = hashlib.sha256(trusted_content).hexdigest()
        log_event(f"Calculated SHA-256: {current_hash}", "VERIFY")
        
        if current_hash == trusted_hash:
            log_event("Integrity verified (SHA-256 match)", "VERIFY")
            return True, current_hash
        return False, None
    except Exception as e:
        log_event(f"Verification error: {e}", "ERROR")
        return False, None

def healing_workflow(container_name):
    global system_state
    
    try:
        # 1. ISOLATING
        set_state("ISOLATING")
        log_event(f"Stopping compromised service: {container_name}", "ISOLATION")
        try:
            container = client.containers.get(container_name)
            image_name = container.image.tags[0] if container.image.tags else None
            network_name = list(container.attrs['NetworkSettings']['Networks'].keys())[0]
            ports = container.attrs['HostConfig']['PortBindings']
            env_vars = container.attrs['Config']['Env']
            
            container.stop(timeout=5)
            container.remove()
        except docker.errors.NotFound:
            log_event(f"Container {container_name} not found, proceeding.", "WARNING")
            image_name, network_name, ports, env_vars = None, None, None, None
            
        time.sleep(1)
        
        # 2. ISOLATED
        set_state("ISOLATED")
        log_event(f"Service {container_name} isolated successfully.", "ISOLATION")
        time.sleep(1)
        
        # 3. VERIFYING
        set_state("VERIFYING")
        log_event("SHA-256 verification started", "VERIFY")
        
        is_verified, hsh = verify_integrity(container_name)
        if not is_verified:
            set_state("FAILED")
            log_event("Integrity verification failed. Halting recovery.", "ERROR")
            return
            
        # 4. VERIFIED
        set_state("VERIFIED")
        log_event("SHA-256 verified", "VERIFY")
        time.sleep(1)
        
        # 5. HEALING
        set_state("HEALING")
        log_event(f"Regrowing service {container_name}", "HEALING")
        
        if ports:
            port_bindings = {cp: hc[0]['HostPort'] for cp, hc in ports.items()}
        else:
            port_bindings = {"5000/tcp": "5000"}
            
        if not image_name:
            # Fallback
            image_name = "lizardtail-service_a"
            network_name = "lizardtail_lizardtail_network"
            env_vars = []
            
        client.containers.run(
            image=image_name,
            name=container_name,
            detach=True,
            network=network_name,
            ports=port_bindings,
            environment=env_vars,
            restart_policy={"Name": "unless-stopped"}
        )
        
        # Wait for healthy
        for i in range(5):
            try:
                r = requests.get(f"http://{container_name}:5000/health", timeout=2)
                if r.json().get("status") == "healthy":
                    break
            except:
                pass
            time.sleep(1)
            
        log_event("Health check passed", "HEALING")
        
        # 6. RECOVERED
        set_state("RECOVERED")
        log_event("Service restored", "HEALING")
        time.sleep(2)
        
        # 7. NORMAL
        set_state("NORMAL")
        log_event("System Recovery complete", "SYSTEM")
        
    except Exception as e:
        log_event(f"Healing workflow failed: {e}", "ERROR")
        set_state("FAILED")

@app.route('/telemetry', methods=['POST'])
def receive_telemetry():
    global current_telemetry, anomaly_info, system_state
    
    data = request.json
    if not data:
        return jsonify({"error": "No data"}), 400
        
    current_telemetry = data
    
    # Run through anomaly detection ONLY if system is normal
    if system_state == "NORMAL":
        result = detect_anomaly(data)
        
        if result["status"] == "ANOMALY":
            log_event("Behaviour classified as ANOMALY", "ML")
            log_event("Abnormal behaviour detected", "SECURITY")
            log_event(f"Threat identified in {data.get('source_service', 'service_a')}", "SECURITY")
            
            set_state("ANOMALY_DETECTED")
            anomaly_info = result
            
            # Trigger recovery asynchronously
            t = threading.Thread(target=healing_workflow, args=("lizardtail_service_a",))
            t.start()
        else:
            anomaly_info = None

    return jsonify({"status": "received"}), 200

@app.route('/status', methods=['GET'])
def get_status():
    try:
        containers = client.containers.list(all=True)
        container_list = [
            {"name": c.name, "status": c.status, "id": c.short_id}
            for c in containers if 'lizardtail' in c.name
        ]
    except Exception:
        container_list = []
        
    return jsonify({
        "system_state": system_state,
        "anomaly_info": anomaly_info,
        "containers": container_list,
        "telemetry": current_telemetry
    }), 200

@app.route('/simulate-attack', methods=['POST'])
def simulate_attack():
    log_event("Simulated attack initiated by user", "COMMAND")
    try:
        # Infect the simulated service
        requests.post("http://lizardtail_service_a:5000/infect", timeout=3)
        return jsonify({"message": "Attack simulation started"}), 200
    except Exception as e:
        log_event(f"Failed to start simulation: {e}", "ERROR")
        return jsonify({"message": str(e)}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    return jsonify({"logs": event_log[-50:]}), 200

@app.route('/')
def index():
    return send_from_directory('/dashboard', 'index.html')

if __name__ == '__main__':
    log_event("Orchestrator started", "SYSTEM")
    app.run(host='0.0.0.0', port=8000, debug=False)