# API Documentation

## Base URL

Development: `http://localhost:8000`

## Authentication Endpoints

### POST /api/authenticate

Enhanced multi-factor authentication with detailed factor results.

**Request Body:**
```json
{
  "transaction_id": "string",
  "customer_id": "string",
  "amount_usd": 15000.0,
  "channel": "wire_transfer",
  "voice_sample": "base64_encoded_audio (optional)",
  "device_info": {
    "device_id": "string",
    "integrity_check": true,
    "location_consistent": true
  }
}
```

**Response:**
```json
{
  "decision": "APPROVE|DECLINE|STEP_UP|MANUAL_REVIEW",
  "confidence": 0.85,
  "risk_score": 0.25,
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "factor_results": {
    "voice": {
      "deepfake_score": 0.15,
      "liveness_passed": true,
      "liveness_confidence": 0.95,
      "speaker_verification_score": 0.96,
      "decision": "PASS|FAIL",
      "explanation": "string"
    },
    "device": {
      "device_trusted": true,
      "device_id": "string",
      "trust_score": 1.0,
      "decision": "PASS|FAIL",
      "explanation": "string"
    }
  },
  "transaction_risk": {
    "overall_risk": 0.25,
    "risk_level": "LOW",
    "risk_factors": [
      "Medium value transaction: $15,000.00"
    ]
  },
  "sar_flags": []
}
```

**Decision Types:**
- `APPROVE`: Transaction approved, all checks passed
- `DECLINE`: Transaction declined, insufficient or failed factors
- `STEP_UP`: Additional authentication required
- `MANUAL_REVIEW`: Critical risk, requires manual review

**Risk Levels:**
- `LOW`: Risk score < 0.3
- `MEDIUM`: Risk score 0.3-0.5
- `HIGH`: Risk score 0.5-0.7
- `CRITICAL`: Risk score >= 0.7

---

## SAR Endpoints

### POST /api/sar/generate

Generate SAR (Suspicious Activity Report) narrative from context data.

**Request Body:**
```json
{
  "customer_name": "John Doe",
  "customer_id": "CUST123",
  "account_number": "ACC789456",
  "account_opened": "2020-01-15",
  "occupation": "Business Owner",
  "suspicious_activity": "Structured transactions to avoid reporting",
  "start_date": "2024-11-01",
  "end_date": "2024-11-23",
  "count": 5,
  "amount": 49500.00,
  "pattern": "structuring pattern",
  "red_flags": [
    "Multiple transactions just below $10,000 threshold",
    "Frequent cash deposits followed by wire transfers"
  ],
  "transactions": [
    {
      "transaction_id": "TX001",
      "date": "2024-11-05",
      "type": "wire transfer",
      "amount": 9900.00,
      "destination": "Foreign Bank Account"
    }
  ],
  "doc_id": "DOC-2024-1123-001"
}
```

**Response:**
```json
{
  "narrative": "SAR filed for John Doe (ID: CUST123)...",
  "validation": {
    "quality_score": 1.0,
    "issues": [],
    "ready_for_filing": true
  }
}
```

---

## Demo Data Endpoints

### GET /api/demo/waveform/{sample_id}

Get demo waveform data for visualization.

**Parameters:**
- `sample_id` (path): Sample identifier (e.g., "sample1")

**Response:**
```json
{
  "x": [0.0, 0.004, 0.008, ...],
  "y": [0.0, 0.015, 0.028, ...],
  "segments": [
    {
      "start": 0.0,
      "end": 2.0,
      "type": "genuine",
      "label": "Genuine",
      "confidence": 0.95
    },
    {
      "start": 2.0,
      "end": 4.0,
      "type": "synthetic",
      "label": "Synthetic",
      "confidence": 0.88
    }
  ],
  "sample_id": "sample1"
}
```

---

## Health & Status Endpoints

### GET /

Get service information and status.

**Response:**
```json
{
  "service": "Sonotheia Enhanced Platform",
  "version": "1.0.0",
  "status": "operational",
  "features": [
    "Multi-Factor Authentication",
    "Voice Deepfake Detection",
    "SAR Generation",
    "Risk Scoring"
  ],
  "author": "doronpers"
}
```

### GET /api/v1/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "sonotheia-enhanced"
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid input)
- `422`: Unprocessable Entity (validation error)
- `500`: Internal Server Error

---

## Rate Limiting

In production, rate limiting should be configured. Recommended limits:

- `/api/authenticate`: 100 requests/minute per IP
- `/api/sar/generate`: 10 requests/minute per IP
- Demo endpoints: 1000 requests/minute per IP

---

## CORS Configuration

The API allows CORS from the following origins by default (development):
- `http://localhost:3000`
- `http://localhost:3001`
- `http://localhost:3002`
- `http://localhost:3003`
- `http://localhost:3004`

For production, configure specific origins in `backend/api/main.py`.

---

## Authentication (Production)

For production deployments, implement authentication:

1. Add API key authentication
2. Use OAuth 2.0 / JWT tokens
3. Configure in FastAPI middleware

Example:
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/api/authenticate")
async def authenticate(request: AuthenticationRequest, token: str = Depends(security)):
    # Verify token
    ...
```

---

## Best Practices

1. **Always validate input**: Use Pydantic models for request validation
2. **Handle errors gracefully**: Return meaningful error messages
3. **Log all authentication attempts**: For audit trails
4. **Use HTTPS in production**: Never send sensitive data over HTTP
5. **Implement rate limiting**: Prevent abuse and DoS attacks
6. **Monitor SAR flags**: Set up alerts for critical SAR flags
7. **Regularly update thresholds**: Based on operational feedback
