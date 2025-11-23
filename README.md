# Sonotheia Enhanced Platform

> Multi-factor voice authentication & SAR reporting system combining deepfake detection, MFA orchestration, and automated suspicious activity reporting

## Features

- **Multi-Factor Authentication (MFA)**: Comprehensive authentication orchestrator with voice, device, and behavioral factors
- **Voice Deepfake Detection**: Physics-based voice authentication with liveness checks and speaker verification
- **SAR Generation**: Automated Suspicious Activity Report generation with Jinja2 templates
- **Risk Scoring**: Transaction risk assessment with configurable thresholds
- **Interactive Dashboard**: React-based dashboard with waveform visualization and factor-level explainability
- **Demo Mode**: Safe demonstration mode with watermarked outputs

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
│   │   └── main.py            # FastAPI entry point
│   ├── authentication/
│   │   ├── mfa_orchestrator.py      # MFA decision engine
│   │   ├── voice_factor.py          # Voice authentication
│   │   ├── device_factor.py         # Device validation
│   │   └── unified_orchestrator.py  # Legacy orchestrator
│   ├── sar/
│   │   ├── generator.py             # SAR narrative builder
│   │   ├── models.py                # Pydantic models
│   │   └── templates/
│   │       └── sar_narrative.j2     # Jinja2 template
│   ├── config/
│   │   └── settings.yaml            # Configuration
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

### Backend Setup

1. Install dependencies:
```bash
cd backend
pip install fastapi uvicorn pydantic pyyaml jinja2 numpy
```

2. Start the server:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend Setup

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

## Repositories Integrated

This platform integrates patterns and components from:
- Website-Sonotheia-v251120: Frontend patterns
- websonoth: Docker setup, API structure
- SonoCheck: Detection algorithms
- RecApp: Consent management, recording pipeline

## Credits

Created: 2025-11-23 by doronpers

Enhanced with superior aspects from "Sonotheia Multi-Factor Voice Authentication & SAR.md"
