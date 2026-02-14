# 🦎 LizardTail - Self-Healing Secure Microservice System

A dockerized distributed system demonstrating automatic detection and recovery of compromised services.

## Architecture

```
┌─────────────────┐
│   Dashboard     │  (HTML/JS - Live monitoring)
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼────┐ ┌─▼────────────┐
│Service │ │ Orchestrator │  (Python + Docker SDK)
│   A    │ │              │
└────────┘ └──────────────┘
    │              │
┌───▼────┐    ┌───▼────┐
│Service │    │ Docker │
│   B    │    │ Engine │
└────────┘    └────────┘
```

## Components

### Layer 1 - User Application (Dashboard)
- **Location**: `dashboard/index.html`
- **Features**:
  - Live temperature monitoring (updates every second)
  - Container status display
  - Event logs viewer
  - Manual attack/heal controls
  - System metrics

### Layer 2 - Services
- **Service A** (`services/service_a/`):
  - Flask API on port 5000
  - `/sensor` - Returns temperature data
  - `/infect` - Triggers malicious behavior
  - `/health` - Health check endpoint
  - Normal: 22-28°C, fast response
  - Infected: 500-999°C, 2s delay

- **Service B** (`services/service_b/`):
  - Flask API on port 5001
  - Dummy service for demonstration
  - `/status` - Status endpoint
  - `/health` - Health check endpoint

### Layer 3 - Orchestrator
- **Location**: `orchestrator/orchestrator.py`
- **Port**: 8000
- **Features**:
  - Docker SDK integration
  - Container health monitoring
  - Automatic service healing
  - Event logging
  - REST API for control

### Layer 4 - Infrastructure
- **Docker Compose**: Orchestrates all services
- **Network**: Private bridge network
- **Volumes**: Docker socket mounted for orchestrator

## Quick Start

### Prerequisites
- Docker (20.x or higher)
- Docker Compose (2.x or higher)
- Bash shell

### Installation & Launch

```bash
cd lizardtail
./run.sh
```

This will:
1. Clean up old containers
2. Build all Docker images
3. Start all services
4. Launch the dashboard

### Manual Commands

```bash
# Start system
docker-compose up -d

# View logs
docker-compose logs -f

# Stop system
docker-compose down

# Rebuild
docker-compose build --no-cache

# Check status
docker-compose ps
```

## Usage Scenarios

### Scenario 1: Normal Operation
1. Open dashboard
2. Observe temperature readings (22-28°C)
3. Check container status (all running)
4. View event logs

### Scenario 2: Attack & Manual Heal
1. Click "ATTACK SERVICE_A" button
2. Observe:
   - Temperature spikes to 500+°C
   - Response time increases to 2+ seconds
   - Status changes to "INFECTED"
3. Click "HEAL SERVICE_A" button
4. Watch orchestrator:
   - Stop infected container
   - Remove container
   - Recreate clean container
5. Service returns to normal

### Scenario 3: Auto-Heal
1. Click "ATTACK SERVICE_A"
2. Wait for infection symptoms
3. Click "AUTO-HEAL"
4. Orchestrator automatically:
   - Detects unhealthy service
   - Triggers healing process
   - Restores service to healthy state

### Scenario 4: API Testing

```bash
# Get temperature
curl http://localhost:5000/sensor

# Check health
curl http://localhost:5000/health

# Trigger infection
curl -X POST http://localhost:8000/infect/service_a

# Check orchestrator status
curl http://localhost:8000/status

# Get logs
curl http://localhost:8000/logs

# Trigger manual heal
curl -X POST http://localhost:8000/heal/lizardtail_service_a

# Trigger auto-heal
curl -X POST http://localhost:8000/auto-heal
```

## API Endpoints

### Service A (Port 5000)
- `GET /sensor` - Get temperature reading
- `POST /infect` - Trigger infection
- `GET /health` - Health check

### Orchestrator (Port 8000)
- `GET /status` - Get container status
- `GET /logs?limit=N` - Get event logs
- `POST /heal/<container_name>` - Heal specific container
- `POST /infect/<service_name>` - Infect service
- `POST /auto-heal` - Auto-detect and heal

## How It Works

### Infection Process
1. User triggers `/infect` endpoint
2. Service A sets `infected = True`
3. `/sensor` endpoint now:
   - Returns abnormal values (500-999°C)
   - Responds slowly (2s delay)

### Healing Process
1. Detection (manual or auto)
2. Orchestrator connects to Docker Engine
3. Gets container by name
4. Stops container gracefully
5. Removes container
6. Recreates with same config:
   - Same image
   - Same network
   - Same port bindings
   - Same restart policy
7. New container starts clean (not infected)

### Key Features
- **Zero Downtime**: Service B continues running
- **State Reset**: New container has no infection state
- **Config Preservation**: Ports, networks maintained
- **Event Logging**: All actions logged with timestamps
- **Real-time Monitoring**: Dashboard updates live

## Troubleshooting

### Services won't start
```bash
# Check Docker is running
docker info

# Check for port conflicts
lsof -i :5000
lsof -i :5001
lsof -i :8000

# View detailed logs
docker-compose logs
```

### Dashboard shows connection errors
- Ensure all services are running: `docker-compose ps`
- Wait 10 seconds for services to initialize
- Check network: `docker network ls`

### Heal operation fails
- Check orchestrator logs: `docker logs lizardtail_orchestrator`
- Verify Docker socket is mounted: `docker-compose config`
- Ensure orchestrator has Docker API access

### Permission denied on run.sh
```bash
chmod +x run.sh
```

## Project Structure

```
lizardtail/
├── docker-compose.yml       # Service orchestration
├── run.sh                   # Launch script
├── README.md               # This file
├── dashboard/
│   └── index.html          # Web dashboard
├── orchestrator/
│   ├── Dockerfile          # Orchestrator image
│   └── orchestrator.py     # Healing logic
└── services/
    ├── service_a/
    │   ├── Dockerfile
    │   ├── service.py      # Main service
    │   └── requirements.txt
    └── service_b/
        ├── Dockerfile
        ├── service.py
        └── requirements.txt
```

## Technical Details

### Dependencies
- **Python**: 3.11-slim
- **Flask**: 3.0.0
- **Docker SDK**: Latest
- **Requests**: Latest

### Network
- Bridge network: `lizardtail_network`
- All services on same network
- Inter-service communication via container names

### Security Considerations
- This is a DEMO system for learning
- In production, add:
  - Authentication/authorization
  - Encrypted communication
  - Resource limits
  - Security scanning
  - Network policies

## Learning Objectives

This project demonstrates:
1. **Microservices Architecture**: Decoupled services
2. **Docker Orchestration**: Multi-container management
3. **Self-Healing Systems**: Automatic recovery
4. **Health Monitoring**: Service health checks
5. **Event-Driven Architecture**: Detection → Response
6. **Real-time Dashboards**: Live data visualization
7. **Container Lifecycle**: Create, stop, remove, recreate
8. **API Design**: RESTful endpoints

## License

MIT License - Educational purposes

## Author

Built for learning distributed systems and self-healing architectures.
