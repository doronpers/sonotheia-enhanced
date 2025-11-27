# Sonotheia Enhanced Platform

> Multi-factor voice authentication & SAR reporting system combining deepfake detection, MFA orchestration, and automated suspicious activity reporting

## Features

- **Multi-Factor Authentication (MFA)**: Comprehensive authentication orchestrator with voice, device, and behavioral factors
- **Voice Deepfake Detection**: Physics-based voice authentication with liveness checks and speaker verification
- **SAR Generation**: Automated Suspicious Activity Report generation with Jinja2 templates
- **Risk Scoring**: Transaction risk assessment with configurable thresholds
- **Interactive Dashboard**: React-based dashboard with waveform visualization and factor-level explainability
- **Demo Mode**: Safe demonstration mode with watermarked outputs
- **🆕 Rust Performance Sensors**: High-performance audio sensors (VacuumSensor, PhaseSensor, ArticulationSensor) with Python bindings
- **🆕 Rate Limiting**: Protection against abuse with configurable rate limits
- **🆕 API Documentation**: Complete OpenAPI/Swagger documentation at `/docs`
- **🆕 Input Validation**: Comprehensive security-focused validation with SQL injection and XSS protection
- **🆕 Request Tracking**: Unique request IDs and response time monitoring

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Waveform     │  │ Factor Cards │  │ Evidence     │     │
│  │ Dashboard    │  │              │  │ Modal        │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↕ REST API
┌─────────────────────────────────────────────────────────────┐
│                Backend (Python/FastAPI)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ MFA          │  │ Voice        │  │ SAR          │     │
│  │ Orchestrator │  │ Detector     │  │ Generator    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Device/      │  │ Transaction  │  │ Compliance   │     │
│  │ Behavioral   │  │ Risk Scorer  │  │ Logger       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
sonotheia-enhanced/
├── backend/                    # Python/FastAPI backend
│   ├── api/
│   │   ├── main.py            # FastAPI entry point with OpenAPI docs
│   │   ├── middleware.py      # Rate limiting, auth, request tracking
│   │   └── validation.py      # Input validation and sanitization
│   ├── authentication/
│   │   ├── mfa_orchestrator.py      # MFA decision engine
│   │   ├── voice_factor.py          # Voice authentication
│   │   ├── device_factor.py         # Device validation
│   │   └── unified_orchestrator.py  # Legacy orchestrator
│   ├── sar/
│   │   ├── generator.py             # SAR narrative builder
│   │   ├── models.py                # Pydantic models with validation
│   │   └── templates/
│   │       └── sar_narrative.j2     # Jinja2 template
│   ├── config/
│   │   ├── settings.yaml            # Configuration
│   │   └── constants.py             # Shared constants and patterns
│   ├── sonotheia_rust/              # 🆕 Rust performance sensors
│   │   ├── src/
│   │   │   ├── sensors/             # VacuumSensor, PhaseSensor, ArticulationSensor
│   │   │   └── utils/               # Audio processing, FFT, error handling
│   │   ├── Cargo.toml
│   │   └── SECURITY.md
│   └── requirements.txt
├── frontend/                   # React dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── WaveformDashboard.jsx
│   │   │   ├── FactorCard.jsx
│   │   │   ├── EvidenceModal.jsx
│   │   │   └── RiskScoreBox.jsx
│   │   ├── App.js
│   │   └── index.js
│   └── package.json
├── reusable-components/        # Reusable component library
└── README.md
```

## Quick Start

### 🚀 One-Command Setup (Recommended)

The fastest way to get started:

#### Using Start Script (Cross-platform)

**Linux/Mac:**
```bash
./start.sh
```

**Windows:**
```bash
start.bat
```

The script will automatically:
- Detect and use Docker if available (recommended)
- Fall back to local setup (Python + Node.js)
- Install all dependencies
- Start both backend and frontend services

#### Using Docker Compose (Recommended)

If you have Docker installed:

```bash
docker compose up --build
# OR (for Docker Compose v1)
docker-compose up --build
```

This will start both services in containers. Access:
- **Frontend Dashboard:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

To stop:
```bash
docker compose down
# OR
./stop.sh  # Linux/Mac
stop.bat   # Windows
```

### Manual Setup

#### Backend Setup

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Start the server:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

#### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install --legacy-peer-deps
```

2. Start the development server:
```bash
npm start
```

The dashboard will be available at `http://localhost:3000`

## API Endpoints

### Authentication
- `POST /api/authenticate` - Multi-factor authentication with detailed factor results
- `POST /api/v1/authenticate` - Legacy authentication endpoint (backward compatible)

### SAR Generation
- `POST /api/sar/generate` - Generate SAR narrative from context data

### Demo Data
- `GET /api/demo/waveform/{sample_id}` - Get demo waveform data for visualization

### Health & Status
- `GET /` - Service information and status
- `GET /api/v1/health` - Health check endpoint

### Documentation
- `GET /docs` - Interactive Swagger UI documentation
- `GET /redoc` - ReDoc documentation
- `GET /openapi.json` - OpenAPI specification

## Security Features

### Rate Limiting
- Standard endpoints: 100 requests/minute
- Authentication endpoints: 50 requests/minute
- SAR generation: 20 requests/minute

### Input Validation
- SQL injection protection
- XSS (Cross-Site Scripting) prevention
- Path traversal protection
- Field length constraints
- Numeric range validation
- Format validation (IDs, country codes, channels)

### Request Tracking
- Every request receives a unique `X-Request-ID` header
- Response time tracking via `X-Response-Time` header
- Comprehensive request/response logging

### API Authentication (Optional)
API key authentication can be enabled for production:
```bash
# Add header to requests:
X-API-Key: your-api-key-here
```

## Configuration

Edit `backend/config/settings.yaml` to configure:

- **Authentication policies**: Minimum factors, risk thresholds
- **Voice detection**: Deepfake thresholds, speaker verification thresholds
- **Device validation**: Trust score thresholds, enrollment requirements
- **High-risk countries**: List of countries requiring extra scrutiny
- **SAR detection rules**: Structuring detection, synthetic voice detection

## Key Components

### Backend

- **MFAOrchestrator**: Main authentication decision engine with comprehensive policy rules
- **VoiceAuthenticator**: Voice deepfake detection, liveness checks, speaker verification
- **DeviceValidator**: Device trust scoring and validation
- **SARGenerator**: Automated SAR narrative generation using Jinja2 templates

### Frontend

- **WaveformDashboard**: Interactive waveform visualization with Plotly.js
- **FactorCard**: Expandable authentication factor cards with explanations
- **RiskScoreBox**: Visual risk score indicator with risk factors
- **EvidenceModal**: Tabbed modal for detailed evidence viewing

## Integration Examples

### Banking/Financial Institutions

```python
from backend.authentication.mfa_orchestrator import MFAOrchestrator, TransactionContext, AuthenticationFactors

# Initialize orchestrator
orchestrator = MFAOrchestrator()

# Wire transfer workflow
def process_wire_transfer(transaction_data):
    context = TransactionContext(
        transaction_id=transaction_data['id'],
        customer_id=transaction_data['customer_id'],
        transaction_type='wire_transfer',
        amount_usd=transaction_data['amount'],
        destination_country=transaction_data['destination_country'],
        is_new_beneficiary=transaction_data['is_new_beneficiary'],
        channel='wire_transfer'
    )
    
    factors = AuthenticationFactors(
        voice={'audio_data': transaction_data['voice_sample']},
        device=transaction_data['device_info']
    )
    
    result = orchestrator.authenticate(context, factors)
    
    if result['decision'] == 'APPROVE':
        execute_wire_transfer(transaction_data)
    elif result['decision'] == 'STEP_UP':
        request_additional_auth(transaction_data)
    else:
        decline_transaction(transaction_data, result)
```

### Real Estate Systems

```python
# Escrow/closing workflow
def verify_wire_instructions(closing_data):
    # Multi-party verification
    buyer_auth = authenticate_party(closing_data['buyer'])
    seller_auth = authenticate_party(closing_data['seller'])
    
    if buyer_auth['decision'] == 'APPROVE' and seller_auth['decision'] == 'APPROVE':
        release_wire(closing_data)
    else:
        hold_for_review(closing_data, [buyer_auth, seller_auth])
```

## Security & Compliance

- ✅ No model source code exposed in frontend
- ✅ Rate limiting on API endpoints (configure in production)
- ✅ Demo data watermarked
- ✅ Authentication required for production (configure in main.py)
- ✅ HTTPS enforced in production (configure in deployment)
- ✅ Input validation on all endpoints
- ✅ Audit logging enabled

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality

```bash
# Backend linting
cd backend
flake8 .
black .

# Frontend linting
cd frontend
npm run lint
```

## Docker Setup

### Building and Running with Docker

The project includes Docker configuration for easy deployment:

```bash
# Build and start all services (Docker Compose v2)
docker compose up --build

# OR with Docker Compose v1
docker-compose up --build

# Run in detached mode (background)
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v
```

### Docker Configuration

The `docker-compose.yml` file configures:
- **Backend service** on port 8000
- **Frontend service** on port 3000
- Automatic health checks
- Volume mounting for development
- Network isolation

Individual Dockerfiles are located in:
- `backend/Dockerfile` - Python/FastAPI backend
- `frontend/Dockerfile` - React frontend with nginx

## Troubleshooting

### Common Issues

#### Port Already in Use
If ports 3000 or 8000 are already in use:

```bash
# Find and kill process on port 8000 (backend)
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different ports with Docker Compose
docker compose up --build  # Uses configured ports
```

#### Docker Build Fails
```bash
# Clear Docker cache and rebuild
docker compose down -v
docker system prune -a
docker compose up --build
```

#### Frontend Can't Connect to Backend
Ensure the backend is running and accessible:
```bash
# Check backend is responding
curl http://localhost:8000/

# Check Docker network
docker network inspect sonotheia-network
```

#### Module Not Found (Python)
```bash
# Reinstall backend dependencies
cd backend
pip install --force-reinstall -r requirements.txt
```

#### npm Install Issues
```bash
# Clear npm cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

### Getting Help

- Check logs: `docker compose logs -f`
- Verify services: `docker compose ps`
- Test backend: http://localhost:8000/docs
- Test frontend: http://localhost:3000

## Repositories Integrated

This platform integrates patterns and components from:
- Website-Sonotheia-v251120: Frontend patterns
- websonoth: Docker setup, API structure
- SonoCheck: Detection algorithms
- RecApp: Consent management, recording pipeline

## Credits

Created: 2025-11-23 by doronpers

Enhanced with superior aspects from "Sonotheia Multi-Factor Voice Authentication & SAR.md"
