# LizardTail

**Self-Healing Endpoint Security**

LizardTail is an automated, self-healing cybersecurity endpoint protection prototype. It is designed to observe a device's telemetry, detect signs of compromise via machine learning, isolate affected components, verify clean versions using cryptographic hashing, and dynamically regrow (restore) them to a clean, trusted state.

## Problem Statement
Traditional antivirus systems are reactive, identifying known signatures after damage has occurred. LizardTail explores a forward-thinking response mechanism: if a system node is observed behaving abnormally matching attack profiles (like resource exhaustion or cryptominers), the system autonomously physically isolates the component, verifies a safe original image, and dynamically rebuilds the system state.

## Architecture
The system consists of Dockerized microservices simulating an endpoint environment:
- **LizardTail Dashboard (SOC UI)**: Dark-themed cybersecurity control panel communicating with the backend API.
- **Orchestrator Backend**: Brain that houses the state machine, API, and Docker controller.
- **Agent Node**: A python process running `psutil` and querying protected endpoints to aggregate accurate simulated system footprint. 
- **ML Anomaly Detector**: Isolation Forest models trained on normalized network/system datasets (inspired by ToN_IoT) stored and loaded automatically.
- **Service Env**: Simulated services (service_a, service_b) performing tasks.

## Attack Simulation & Self-Healing Pipeline
The core demonstration workflow works right from the dashboard:
1. **Simulation**: Clicking `Simulate Attack` triggers an abnormal payload (cryptominer mock + DDoS simulation) in `service_a`.
2. **Detection**: ML Isolation Forest detects the rapid CPU and synthetic network IO spikes. State changes to `ANOMALY_DETECTED`.
3. **Isolation**: The orchestrator triggers physical container isolation by halting and removing the poisoned `service_a` container from the network. State changes to `ISOLATING` -> `ISOLATED`.
4. **Verification**: The system simulates checking a trusted `SHA-256` signature matching the deployed service image hash to guarantee a trusted replacement firmware/image exists. State changes to `VERIFYING` -> `VERIFIED`.
5. **Regrow**: The orchestrator boots up a fresh, cleansed copy of `service_a` back into the secure network. State changes to `HEALING` -> `RECOVERED`.
6. **Recovery Complete**: The UI resets securely into `SYSTEM SECURE`.

## Technical Specs
- **Logic**: Python, Flask, `docker-py`
- **Dashboard**: HTML/Vanilla CSS SOC Aesthetic (Glassmorphism, Web Animations)
- **Monitoring**: `psutil`
- **Machine Learning**: `scikit-learn` Isolation Forest trained with tabular `numpy/pandas`.

## How to Run (Demo Mode)
You can launch the complete end-to-end system cleanly using Docker Compose.

From your Windows PowerShell, prefix the command with `wsl -e` since Docker lives in your WSL environment:

```powershell
wsl -e docker compose up --build -d
```

### Access Points
- **Dashboard**: `http://localhost:8000/`

## Limitations & Honesty Statement
> **IMPORTANT SECURITY NOTE**: This project is a college/research prototype demonstrating automated behavioural anomaly detection and self-healing *in a strictly controlled Docker environment*. 
- It does **not** deploy real malware.
- It does **not** harm or analyze the user's host machine.
- It does **not** collect real passwords, browsing history, or sensitive artifacts.
- Hashing verifies a simulated image string/container state and not an arbitrary vendor key.

## Future Scope
- Developing a native Windows/Linux kernel-level endpoint agent.
- Integration of digital signatures & Trusted Software Repositories.
- Enhancing AI detection for multi-vector threat tracing using federated learning.
- Enterprise-wide SOC distribution instead of single-endpoint orchestration.
