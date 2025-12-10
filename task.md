# Sonotheia Enhanced - Project Tasks

## Phase 1: Demo Setup & Verification [COMPLETED]
- [x] **Environment Verification**
    - [x] Check Python/Node versions (Python 3.12, Node 24)
    - [x] Verify Docker availability
    - [x] Confirm CUDA support in codebase
- [x] **Demo Preparation**
    - [x] Create demo user profiles (Good, Suspicious, Edge Case)
    - [x] Create setup scripts (`demo/setup_demo.sh`, `demo/launch_demo.bat`)
    - [x] Create API test scripts (`demo/test_api.ps1`)
    - [x] Update documentation (`demo/QUICK_REFERENCE.md`)
- [x] **Calibration & Fixes**
    - [x] Run baseline calibration (100% accuracy verified)
    - [x] Fix Windows encoding issues in scripts
    - [x] Fix `FusionEngine` syntax error
    - [x] Fix `huggingface_hub` dependency issue
- [x] **API Verification**
    - [x] Verify Health Check endpoint
    - [x] Verify Session Creation & Biometric/Voice updates
    - [x] Verify Risk Evaluation & Decision logic
- [x] **Demo Enhancements (Incode Showcase)**
    - [x] **Compliance Hero**: Automated PDF SAR Generator (`demo/compliance_hero.py`)
    - [x] **Forensic Viewer**: Authentic Web Audio Spectrogram (`demo/forensic_viewer.html`)
    - [x] **Launcher**: CORS-compatible viewer launcher (`demo/launch_viewer.bat`)

## Phase 2: Showcase & Integration [IN PROGRESS]
- [x] **Core Integration**
    - [x] Backend: Add `fpdf2` and `backend/sar/pdf_generator.py`.
    - [x] Backend: Expose `POST /sar/{id}/generate-pdf` and `GET /sar/{id}/pdf`.
    - [x] Backend: Serve static forensic assets from `backend/static/forensics`.
    - [x] Frontend: Port `ForensicViewer.jsx` and add `/forensics` route.
- [ ] Practice run of complete demo flow
- [ ] Integration with Incode SDK (Mock or Real)
- [ ] Production Deployment planning
