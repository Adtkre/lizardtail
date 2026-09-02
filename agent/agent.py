import time
import psutil
import requests
import json
from datetime import datetime
import os

ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://orchestrator:8000")
SERVICE_A_URL = os.environ.get("SERVICE_A_URL", "http://service_a:5000")

def get_telemetry():
    # Attempt to fetch the "device" telemetry which is simulated by service_a in our prototype,
    # and combine with some real local psutil usage.
    try:
        resp = requests.get(f"{SERVICE_A_URL}/metrics", timeout=2)
        service_data = resp.json()
        cpu = service_data.get("cpu", psutil.cpu_percent(interval=0.1))
        memory = service_data.get("memory", psutil.virtual_memory().percent)
        disk = service_data.get("disk", psutil.disk_usage('/').percent)
        net_recv = service_data.get("network", 0) # simulated network
        net_sent = service_data.get("network", 0)
    except Exception as e:
        # Fallback to local psutil if service_a is offline (e.g. isolated)
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        io = psutil.net_io_counters()
        net_sent = io.bytes_sent / 1024 / 1024
        net_recv = io.bytes_recv / 1024 / 1024

    process_count = len(psutil.pids())
    
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
        "network_sent": net_sent,
        "network_recv": net_recv,
        "process_count": process_count
    }

def collect_and_send():
    print(f"Agent started, sending telemetry to {ORCHESTRATOR_URL}")
    while True:
        try:
            telemetry = get_telemetry()
            # Send to orchestrator
            requests.post(f"{ORCHESTRATOR_URL}/telemetry", json=telemetry, timeout=3)
        except Exception as e:
            print(f"Error sending telemetry: {e}")
        time.sleep(2)

if __name__ == "__main__":
    collect_and_send()
