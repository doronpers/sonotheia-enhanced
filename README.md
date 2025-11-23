# Sonotheia Unified Platform

> Unified forensic audio authentication system combining deepfake detection, MFA orchestration, and SAR generation

## Project Structure

```
sonotheia-unified/
├── backend/           # Python/FastAPI backend
├── frontend/          # React dashboard
├── datasets/          # Demo and test data
├── models/           # Model weights (git-ignored)
├── docker/           # Docker configurations
├── scripts/          # Utility scripts
└── tests/            # Test suites
```

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## Repositories Integrated

- Website-Sonotheia-v251120: Frontend patterns
- websonoth: Docker setup, API structure
- SonoCheck: Rust extensions, detection algorithms
- RecApp: Consent management, recording pipeline

Created: 2025-11-23 by doronpers
