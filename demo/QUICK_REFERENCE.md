# Incode Demo - Quick Reference

## Starting the Demo

```bash
demo\launch_demo.bat
```

Or with Docker:
```bash
docker-compose up --build
```

## Key URLs

- **API Documentation**: http://localhost:8000/docs
- **Frontend Dashboard**: http://localhost:3000
- **Health Check**: http://localhost:8000/api/v1/health

## Key Demo Assets

| Asset | Path | Description |
|-------|------|-------------|
| **Forensic Analyzer** | `demo/forensic_viewer.html` | **[NEW]** Authentic spectral analysis. Run `demo/launch_viewer.bat`. |
| **SAR Generator** | `demo/compliance_hero.py` | **[NEW]** Generates PDF compliance reports. Run with `python`. |
| **API Tester** | `demo/test_api.ps1` | Validates API points and shows JSON responses. |
| **Demo Profiles** | `demo/profiles/*.json` | Pre-configured user scenarios. |

## Demo Scenarios

### Scenario 1: Legitimate User (Happy Path)
```bash
# Use profile: demo/profiles/good_user.json
# Expected: APPROVE decision, LOW risk
```

### Scenario 2: Deepfake Detection
```bash
# Use profile: demo/profiles/suspicious_user.json
# Expected: ESCALATE decision, HIGH risk
```

### Scenario 3: Edge Case
```bash
# Use profile: demo/profiles/edge_case.json
# Expected: APPROVE decision, MEDIUM risk
```

## Quick API Test

```powershell
.\demo\test_api.ps1
```

## Demo Flow

1. **Start Session** → Create unique session ID
2. **Incode Biometric** → Upload document/face/liveness data
3. **Sonotheia Voice** → Upload voice analysis results
4. **Risk Evaluation** → Calculate composite risk
5. **Decision** → APPROVE/DECLINE/ESCALATE
6. **Escalation** (if needed) → Human review workflow
7. **Audit Trail** → Complete compliance logging

## Key Talking Points

- **Multi-modal fusion**: Combines Incode biometric + Sonotheia voice
- **Non-blocking**: Async integration, ~3s end-to-end
- **Configurable**: Thresholds adjustable per risk tolerance
- **Compliant**: GDPR, FinCEN, SOC2, KYC/AML ready
- **Observable**: Full audit trails and metrics

## Troubleshooting

**Backend not starting?**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend not loading?**
```bash
cd frontend
npm install --legacy-peer-deps
```

**Port conflicts?**
```bash
# Change ports in docker-compose.yml or .env
```
