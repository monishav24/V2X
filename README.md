# SmartV2X-CP Ultra

> **AI-Driven Real-Time Edge-Based Collision Prediction & Monitoring Platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal.svg)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev)

---

## Architecture Overview

```
┌─────────────┐     HTTPS/JWT     ┌─────────────────┐     API      ┌──────────────┐
│  OBU Vehicle │ ───────────────► │  Edge RSU Server │ ──────────► │ Backend Cloud│
│  (sensors    │                  │  (FastAPI +      │              │ (Analytics + │
│   + AI pred) │                  │   WebSocket)     │              │  ML pipeline)│
└─────────────┘                  └────────┬─────────┘              └──────────────┘
                                          │ WebSocket
                                          ▼
                                ┌──────────────────┐
                                │  React Dashboard │
                                │  (Leaflet + live)│
                                └──────────────────┘
```

**Key Features:**
- Real-time collision prediction using LSTM+GRU neural network
- Extended Kalman Filter sensor fusion (GPS + IMU + Radar)
- Collision Probability Map with spatial grid analysis
- Reinforcement Learning based warning dissemination
- JWT authentication with RBAC across all services
- Hardware-ready OBU software with sensor abstraction
- Premium dark-theme dashboard with live WebSocket updates

---

## Project Structure

```
sdp/
├── obu/                          # On-Board Unit (Vehicle Software)
│   ├── sensors/                  # GPS, IMU, Radar drivers + HAL
│   ├── fusion/                   # Extended Kalman Filter
│   ├── prediction/               # LSTM+GRU trajectory model
│   ├── collision/                # Risk assessment engine
│   ├── communication/            # Edge API client (HTTPS + JWT)
│   ├── main.py                   # OBU main loop
│   └── config.yaml               # Hardware configuration
├── edge_rsu/                     # Edge RSU Server
│   ├── api/                      # REST + WebSocket routes
│   ├── auth/                     # JWT + RBAC
│   ├── services/                 # CP-Map, risk aggregator, RL
│   ├── cache/                    # Redis + in-memory fallback
│   ├── middleware/                # Rate limiter
│   ├── database/                 # SQLAlchemy models + schemas
│   └── main.py                   # FastAPI entry point
├── backend/                      # Backend Cloud Server
│   ├── api/                      # Cloud analytics routes
│   ├── analytics/                # Hotspot & time-series engine
│   ├── ml_pipeline/              # Model trainer + versioning
│   ├── database/                 # Cloud DB models + connection
│   └── main.py                   # FastAPI entry point
├── dashboard/                    # React Frontend
│   ├── src/
│   │   ├── components/           # Map, Alerts, Latency, etc.
│   │   ├── pages/                # Dashboard page
│   │   ├── context/              # Auth context
│   │   └── api/                  # Auth + WebSocket clients
│   └── index.html
├── hardware/                     # Hardware Pairing Toolkit
│   ├── handshake.py              # Challenge-response auth
│   ├── vehicle_id.py             # Unique ID generator
│   ├── heartbeat.py              # Heartbeat & offline detect
│   └── firmware_config_template.yaml
├── k8s/                          # Kubernetes manifests
├── docker-compose.yml
├── Dockerfile.edge
├── Dockerfile.backend
├── Dockerfile.dashboard
└── .env.example
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (for containerized deployment)
- PostgreSQL 16 (or use built-in SQLite fallback)
- Redis 7 (optional, in-memory fallback available)

### 1. Clone & Setup

```bash
git clone <repo-url>
cd sdp
cp .env.example .env
# Edit .env with your production secrets
```

### 2. Edge RSU Server

```bash
cd edge_rsu
pip install -r requirements.txt
uvicorn edge_rsu.main:app --host 0.0.0.0 --port 8000 --reload
```

API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Backend Cloud Server

```bash
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

### 4. Dashboard

```bash
cd dashboard
npm install
npm run dev
```

Dashboard: [http://localhost:5173](http://localhost:5173)

**Demo credentials:** `admin / admin123` or `operator / operator123`

### 5. OBU (Simulation Mode)

```bash
cd obu
pip install -r requirements.txt
python main.py
```

---

## Docker Deployment

```bash
# Start all services
docker-compose up -d

# Services available at:
#   Edge RSU:   http://localhost:8000
#   Backend:    http://localhost:8001
#   Dashboard:  http://localhost:3000
```

---

## API Endpoints

### Edge RSU Server (`:8000`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/vehicle/register` | Register OBU device |
| POST | `/api/vehicle/update` | Vehicle state update |
| POST | `/api/vehicle/heartbeat` | Heartbeat ping |
| GET | `/api/vehicle/list` | List active vehicles |
| GET | `/api/health` | System health |
| GET | `/api/analytics` | Real-time analytics |
| POST | `/api/auth/login` | JWT authentication |
| WS | `/ws/live` | Live WebSocket feed |

### Backend Cloud (`:8001`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics` | Cloud analytics |
| GET | `/api/collision-history` | Collision event log |
| POST | `/api/vehicle/register` | Cloud registration |
| GET | `/health` | Health check |

---

## Hardware Integration

### Device Pairing Flow

1. **Provision** — Flash `firmware_config_template.yaml` with device-specific values
2. **Handshake** — OBU performs HMAC challenge-response with edge server
3. **Register** — OBU sends registration payload (ID, firmware, sensors)
4. **Heartbeat** — Periodic heartbeats maintain online status
5. **Stream** — OBU streams fused sensor data to edge server

### Supported Sensors

| Sensor | Interface | Tested Models |
|--------|-----------|---------------|
| GPS | UART/USB | u-blox NEO-6M, NEO-M8N |
| IMU | I2C | MPU-6050, BNO055 |
| Radar | UART | mmWave TI IWR1443 |

---

## Security

- **JWT Authentication** with configurable expiry
- **RBAC** with role hierarchy: `admin > operator > viewer`
- **HMAC Challenge-Response** device handshake
- **Rate Limiting** per client IP (token bucket)
- **CORS** restricted to configured origins
- **HTTPS** enforced in production

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| OBU Processing | Python, PyTorch, ONNX Runtime |
| Edge Server | FastAPI, SQLAlchemy, Redis, WebSocket |
| Backend | FastAPI, PostgreSQL, PyTorch |
| Frontend | React 18, Vite, Leaflet, Chart.js |
| DevOps | Docker, Kubernetes, Nginx |
| Security | JWT (python-jose), HMAC, bcrypt |

---

## License

MIT License — see [LICENSE](LICENSE) for details.

**SmartV2X Inc.** — Building Safer Roads with AI