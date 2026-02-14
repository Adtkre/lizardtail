from flask import Flask, jsonify, request
import docker
import time
import threading
import requests
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Docker client
client = docker.from_env()

# Event log
event_log = []

def log_event(message, event_type="INFO"):
    """Add event to log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    event = {
        "timestamp": timestamp,
        "type": event_type,
        "message": message
    }
    event_log.append(event)
    print(f"[{timestamp}] {event_type}: {message}")

def get_container_status():
    """Get status of all containers"""
    try:
        containers = client.containers.list(all=True)
        status_list = []
        for container in containers:
            if 'lizardtail' in container.name:
                status_list.append({
                    "name": container.name,
                    "status": container.status,
                    "id": container.short_id
                })
        return status_list
    except Exception as e:
        log_event(f"Error getting container status: {str(e)}", "ERROR")
        return []

def check_service_health(service_name, port):
    """Check if service is responding normally"""
    try:
        response = requests.get(f"http://{service_name}:{port}/health", timeout=3)
        data = response.json()
        return data.get("status") == "healthy"
    except Exception as e:
        log_event(f"Health check failed for {service_name}: {str(e)}", "WARNING")
        return False

def heal_service(container_name):
    """Stop, remove, and recreate a compromised container"""
    try:
        log_event(f"Starting healing process for {container_name}", "HEALING")
        
        # Get container
        try:
            container = client.containers.get(container_name)
        except docker.errors.NotFound:
            log_event(f"Container {container_name} not found", "ERROR")
            return False
        
        # Get container info before stopping
        image_name = container.image.tags[0] if container.image.tags else None
        network_name = list(container.attrs['NetworkSettings']['Networks'].keys())[0]
        ports = container.attrs['HostConfig']['PortBindings']
        
        log_event(f"Stopping container {container_name}...", "HEALING")
        container.stop(timeout=5)
        
        log_event(f"Removing container {container_name}...", "HEALING")
        container.remove()
        
        log_event(f"Recreating container {container_name}...", "HEALING")
        
        # Recreate container with same configuration
        port_bindings = {}
        for container_port, host_config in ports.items():
            host_port = host_config[0]['HostPort']
            port_bindings[container_port] = host_port
        
        new_container = client.containers.run(
            image=image_name,
            name=container_name,
            detach=True,
            network=network_name,
            ports=port_bindings,
            restart_policy={"Name": "unless-stopped"}
        )
        
        log_event(f"Container {container_name} successfully healed", "SUCCESS")
        return True
        
    except Exception as e:
        log_event(f"Failed to heal {container_name}: {str(e)}", "ERROR")
        return False

@app.route('/status', methods=['GET'])
def status():
    """Get system status"""
    containers = get_container_status()
    return jsonify({
        "containers": containers,
        "total": len(containers)
    }), 200

@app.route('/logs', methods=['GET'])
def logs():
    """Get event logs"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify({
        "logs": event_log[-limit:]
    }), 200

@app.route('/heal/<container_name>', methods=['POST'])
def heal(container_name):
    """Trigger healing for a specific container"""
    log_event(f"Manual heal triggered for {container_name}", "COMMAND")
    success = heal_service(container_name)
    if success:
        return jsonify({"message": f"{container_name} healed successfully"}), 200
    else:
        return jsonify({"message": f"Failed to heal {container_name}"}), 500

@app.route('/infect/<service_name>', methods=['POST'])
def infect(service_name):
    """Trigger infection on a service"""
    try:
        if service_name == "service_a":
            response = requests.post("http://lizardtail_service_a:5000/infect", timeout=5)
            log_event(f"Infection triggered on {service_name}", "ATTACK")
            return jsonify({"message": f"{service_name} infected"}), 200
        else:
            return jsonify({"message": "Only service_a can be infected"}), 400
    except Exception as e:
        log_event(f"Failed to infect {service_name}: {str(e)}", "ERROR")
        return jsonify({"message": str(e)}), 500

@app.route('/auto-heal', methods=['POST'])
def auto_heal():
    """Detect and heal compromised service"""
    log_event("Auto-heal check initiated", "COMMAND")
    
    # Check service_a health
    if not check_service_health("lizardtail_service_a", 5000):
        log_event("service_a detected as unhealthy, triggering heal", "DETECTION")
        success = heal_service("lizardtail_service_a")
        if success:
            return jsonify({"message": "service_a healed"}), 200
        else:
            return jsonify({"message": "Healing failed"}), 500
    else:
        log_event("All services healthy", "INFO")
        return jsonify({"message": "All services healthy"}), 200

if __name__ == '__main__':
    log_event("Orchestrator started", "SYSTEM")
    app.run(host='0.0.0.0', port=8000, debug=False)
