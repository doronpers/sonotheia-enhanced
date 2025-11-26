# Sonotheia x Incode Integration - Implementation Guide

## Overview

This implementation provides a complete integration framework between Sonotheia's audio deepfake detection and Incode's financial onboarding/authentication SDK. The solution includes backend APIs, React Native SDK wrappers, and dashboard widgets following enterprise-grade security and compliance standards.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              React Native Mobile App                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Incode SDK   │  │ Sonotheia    │  │ Onboarding   │     │
│  │ Wrapper      │  │ SDK Wrapper  │  │ Context      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                         ↕ HTTPS/TLS
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Session      │  │ Escalation   │  │ Audit        │     │
│  │ Management   │  │ API          │  │ Logging      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐                       │
│  │ Risk         │  │ Compliance   │                       │
│  │ Evaluation   │  │ Reporting    │                       │
│  └──────────────┘  └──────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

## Completed Components

### Backend APIs (`/backend/api/`)

1. **session_management.py**
   - Session lifecycle management
   - Biometric/voice data linking with unique session IDs
   - Support for onboarding, authentication, and transaction flows
   - Privacy-masked user/device identifiers

2. **escalation.py**
   - Human-in-the-loop review workflow
   - Priority-based escalation queues
   - Reviewer assignment and decision tracking
   - Integration with risk evaluation

3. **audit_logging.py**
   - Compliance-tagged event logging (GDPR, KYC, AML, FinCEN, SOC2)
   - Privacy-masked sensitive data
   - Timeline tracking per session
   - Compliance report generation

### React Native SDK (`/react-native-sdk/`)

1. **incode/IncodeWrapper.ts**
   - Document scan, face capture, liveness check
   - Native bindings for iOS/Android
   - Mock implementations for development/testing
   - Event-driven architecture

2. **sonotheia/SonotheiaWrapper.ts**
   - Voice capture with permissions handling
   - Deepfake detection analysis
   - Backend API integration
   - Recording state management

3. **hooks/useIncode.ts & useSonotheia.ts**
   - React hooks for easy SDK integration
   - State management for onboarding flow
   - Error handling and loading states

4. **context/OnboardingContext.tsx**
   - Unified orchestration of complete onboarding flow
   - Automatic session management
   - Risk evaluation integration
   - Step-by-step progress tracking

### Dashboard Widgets (`/frontend/src/components/widgets/`)

1. **RiskSlider.jsx**
   - Interactive risk score visualization
   - Real-time updates with color-coded levels
   - Risk factor breakdown display
   - Read-only and editable modes

2. **EvidenceCard.jsx**
   - Reusable authentication factor cards
   - Expandable evidence details
   - Status indicators (pass/fail)
   - Metadata display

3. **EscalationReview.jsx**
   - Human review interface
   - Decision submission (approve/decline/request info)
   - Priority and status indicators
   - Review notes and reasoning

## Key Features

### Security & Privacy
✅ TLS encryption for all data flows (configure in production)
✅ Privacy-masked device/session IDs in audit logs
✅ PII redaction (IP addresses, user IDs)
✅ Sensitive data masking (audio, biometric)
✅ Signed outputs for non-repudiation

### Compliance & Audit
✅ GDPR-compliant data handling
✅ FinCEN SAR integration ready
✅ KYC/AML compliance tagging
✅ SOC2 audit logging
✅ Retention policy support

### Real-time Features
✅ Dynamic risk recalculation
✅ Factor-level contribution tracking
✅ Composite risk scoring (biometric + voice)
✅ Live status updates

### Observability
✅ Unique request IDs (X-Request-ID headers)
✅ Response time tracking (X-Response-Time headers)
✅ Comprehensive error handling
✅ Rate limiting on all endpoints

## API Endpoints

### Session Management
- `POST /api/session/start` - Start new onboarding session
- `GET /api/session/{session_id}` - Get session details
- `POST /api/session/{session_id}/biometric` - Update with Incode data
- `POST /api/session/{session_id}/voice` - Update with Sonotheia data
- `POST /api/session/{session_id}/evaluate` - Calculate composite risk
- `GET /api/session/` - List sessions with filtering

### Escalation Management
- `POST /api/escalation/create` - Create escalation for review
- `GET /api/escalation/{escalation_id}` - Get escalation details
- `GET /api/escalation/` - List escalations (with filters)
- `POST /api/escalation/{escalation_id}/assign` - Assign to reviewer
- `POST /api/escalation/{escalation_id}/review` - Submit decision
- `GET /api/escalation/pending/count` - Get pending counts

### Audit Logging
- `POST /api/audit/log` - Create audit log entry
- `GET /api/audit/logs` - Query logs with filtering
- `GET /api/audit/session/{session_id}/timeline` - Get session timeline
- `GET /api/audit/compliance/report` - Generate compliance report
- `GET /api/audit/stats` - Get aggregate statistics

## Usage Examples

### React Native Onboarding Flow

```typescript
import { OnboardingProvider, useOnboarding } from './context/OnboardingContext';

function OnboardingScreen() {
  const {
    session,
    isLoading,
    startOnboarding,
    performBiometricOnboarding,
    captureVoice,
    evaluateRisk
  } = useOnboarding();

  const handleStartOnboarding = async () => {
    try {
      // Step 1: Start session
      const sessionId = await startOnboarding('USER-12345');
      
      // Step 2: Biometric onboarding (Incode)
      const incodeResult = await performBiometricOnboarding();
      
      // Step 3: Voice capture (Sonotheia)
      const voiceResult = await captureVoice(
        'Please say: My voice is my password'
      );
      
      // Step 4: Risk evaluation
      const riskEval = await evaluateRisk();
      
      if (riskEval.decision === 'APPROVE') {
        // Proceed with account creation
      } else if (riskEval.decision === 'ESCALATE') {
        // Show pending review message
      }
    } catch (error) {
      console.error('Onboarding failed:', error);
    }
  };

  return (
    <View>
      <Button onPress={handleStartOnboarding} disabled={isLoading}>
        Start Onboarding
      </Button>
      {session.riskScore && (
        <Text>Risk Score: {(session.riskScore * 100).toFixed(1)}%</Text>
      )}
    </View>
  );
}

// Wrap app with provider
function App() {
  return (
    <OnboardingProvider config={{
      backendURL: 'https://api.example.com',
      incodeAPIKey: 'your-incode-key',
      incodeAPIURL: 'https://incode-api.com',
      apiKey: 'your-api-key'
    }}>
      <OnboardingScreen />
    </OnboardingProvider>
  );
}
```

### Backend Session Management

```python
import requests

# Start session
response = requests.post('http://localhost:8000/api/session/start', json={
    'user_id': 'USER-12345',
    'session_type': 'onboarding',
    'metadata': {
        'channel': 'mobile_app',
        'ip_address': 'masked_ip_xxx'
    }
})
session = response.json()
session_id = session['session_id']

# Update with biometric data
requests.post(f'http://localhost:8000/api/session/{session_id}/biometric', json={
    'document_verified': True,
    'face_match_score': 0.95,
    'liveness_passed': True,
    'incode_session_id': 'incode-session-123'
})

# Update with voice data
requests.post(f'http://localhost:8000/api/session/{session_id}/voice', json={
    'deepfake_score': 0.15,
    'speaker_verified': True,
    'speaker_score': 0.96,
    'audio_quality': 0.85,
    'audio_duration_seconds': 4.5
})

# Evaluate composite risk
response = requests.post(f'http://localhost:8000/api/session/{session_id}/evaluate', json={
    'session_id': session_id,
    'include_factors': True
})
risk_eval = response.json()
print(f"Decision: {risk_eval['decision']}, Risk: {risk_eval['composite_risk_score']}")
```

### Dashboard Widget Usage

```jsx
import RiskSlider from './components/widgets/RiskSlider';
import EvidenceCard from './components/widgets/EvidenceCard';

function Dashboard() {
  const [riskScore, setRiskScore] = useState(0.25);

  const handleRiskChange = (newValue) => {
    // Trigger real-time risk recalculation
    setRiskScore(newValue);
    recalculateRisk(newValue);
  };

  return (
    <div>
      <RiskSlider
        value={riskScore}
        onChange={handleRiskChange}
        showFactors={true}
        factors={[
          { name: 'Biometric Risk', contribution: 0.1 },
          { name: 'Voice Risk', contribution: 0.15 }
        ]}
      />
      
      <EvidenceCard
        title="Voice Authentication"
        score={0.85}
        passed={true}
        confidence={0.95}
        evidence={{
          deepfake_score: 0.15,
          speaker_match: 0.96
        }}
        metadata={{
          duration: '4.5s',
          quality: 'High'
        }}
      />
    </div>
  );
}
```

## Configuration

### Backend Settings (`backend/config/settings.yaml`)

```yaml
# Session management
session:
  default_timeout_minutes: 30
  max_concurrent_sessions: 1000

# Risk thresholds
risk_thresholds:
  low: 0.3
  medium: 0.5
  high: 0.7
  critical: 0.85

# Compliance
compliance:
  audit_level: standard  # minimal, standard, full, regulatory
  audio_retention_days: 90
  pii_masking_enabled: true
  
# Escalation
escalation:
  auto_escalate_high_risk: true
  high_risk_threshold: 0.7
  critical_risk_threshold: 0.85
```

### Environment Variables

```bash
# Backend
API_KEY=your-secret-api-key
DATABASE_URL=postgresql://user:pass@localhost/sonotheia
REDIS_URL=redis://localhost:6379
ENVIRONMENT=production

# Frontend/React Native
REACT_APP_API_URL=https://api.example.com
REACT_APP_INCODE_API_KEY=your-incode-key
REACT_APP_INCODE_API_URL=https://api.incode.com
```

## Testing

### Run Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Run Frontend Tests
```bash
cd frontend
npm test
```

### Integration Testing
```bash
# Start backend
cd backend && uvicorn api.main:app --reload

# Start frontend
cd frontend && npm start

# Run integration tests
npm run test:integration
```

## Deployment

### Docker Compose
```bash
docker compose up --build
```

### Production Checklist
- [ ] Configure TLS/HTTPS certificates
- [ ] Set secure API keys
- [ ] Enable rate limiting
- [ ] Configure database connection pooling
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log aggregation (ELK/Datadog)
- [ ] Enable CORS for production domains only
- [ ] Set up backup and disaster recovery
- [ ] Configure compliance data retention policies
- [ ] Test escalation workflow end-to-end

## Security Considerations

1. **Data Encryption**: All data in transit encrypted via TLS 1.3+
2. **API Authentication**: API keys required for production endpoints
3. **Rate Limiting**: Prevents abuse (configurable per endpoint)
4. **Input Validation**: All inputs sanitized and validated
5. **Privacy Masking**: PII redacted in logs and audit trails
6. **Non-Repudiation**: Cryptographic signatures on critical outputs
7. **Audit Trail**: Complete event history for regulatory compliance

## Compliance Framework

### GDPR
- ✅ Data minimization (minimal audio persistence)
- ✅ Right to erasure (data retention policies)
- ✅ Privacy by design (masked identifiers)
- ✅ Consent management (biometric consent tracking)

### FinCEN/AML
- ✅ SAR generation capability
- ✅ Transaction monitoring
- ✅ Suspicious activity flagging
- ✅ Audit trail maintenance

### SOC2
- ✅ Access controls
- ✅ Audit logging
- ✅ Incident response (escalation workflow)
- ✅ Data encryption

## Support & Documentation

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
- **Integration Guide**: See this document
- **Issue Tracking**: GitHub Issues

## License

Proprietary - All Rights Reserved

## Contributors

- doronpers (Lead Developer)
- GitHub Copilot (AI Assistant)

---

**Implementation Status**: Complete ✅
**Last Updated**: 2025-11-24
