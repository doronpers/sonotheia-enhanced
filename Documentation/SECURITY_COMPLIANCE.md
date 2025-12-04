---
title: Security & Compliance
tags: [security, compliance, ssl, data-handling]
---

# Security & Compliance

Security posture, threat model, and compliance considerations for Sonotheia.

## Threat Model

### Identified Threats

1. **Audio File Attacks**
   - Large file uploads (DoS)
   - Malformed audio files
   - **Mitigation**: File size limits (50MB), format validation

2. **Data Exfiltration**
   - Sensitive audio data in transit
   - **Mitigation**: TLS 1.3 encryption, HTTPS only

3. **API Abuse**
   - Rate limiting bypass
   - **Mitigation**: Rate limiting (60 req/min), IP-based throttling (planned)

4. **Injection Attacks**
   - Malicious file content
   - **Mitigation**: Content-type validation, audio format restrictions

## Data Handling

### Audio Uploads

- **Storage**: Audio files are processed in-memory, not persisted
- **Retention**: No audio data stored after processing
- **Transmission**: Encrypted in transit (TLS 1.3)

### Logging

- **PII Masking**: Enabled by default (`backend/config/settings.yaml`)
- **Request IDs**: Included for audit trails
- **Log Retention**: Configurable (default: 7 years for compliance)

### Evidence Data

- **SAR Outputs**: May contain redacted PII
- **Sensor Results**: No PII, only acoustic measurements
- **Metadata**: Timestamps, processing times, no user data

## API Authentication

**Current State:** Open API (no authentication)

**Planned:**
- API key authentication
- OAuth 2.0 support
- JWT tokens for enterprise

📖 **See [ENTERPRISE_INTEGRATION.md](ENTERPRISE_INTEGRATION.md)** for enterprise authentication.

## Rate Limiting

**Current:** 60 requests per minute (configurable)

**Planned:**
- Per-IP rate limiting
- Per-API-key quotas
- Burst protection

## SSL/TLS Requirements

### Production Requirements

- **TLS Version**: 1.2 minimum, 1.3 preferred
- **Cipher Suites**: High security only
- **Certificate**: Valid, trusted CA
- **HSTS**: Enabled for custom domains

### Configuration

**Nginx:**
```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
add_header Strict-Transport-Security "max-age=31536000" always;
```

📖 **See [DEPLOYMENT.md](DEPLOYMENT.md)** for SSL setup.

## Nginx Security Headers

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000" always;
```

## File Upload Limits

- **Maximum Size**: 50 MB (configurable)
- **Maximum Duration**: 300 seconds (5 minutes)
- **Allowed Formats**: WAV, MP3, OGG, FLAC, M4A
- **Content-Type Validation**: Enforced

## Detection Policy

**Current Thresholds:**
- Breath: 14.0 seconds max phonation
- Dynamic Range: 12.0 minimum crest factor
- Bandwidth: 4000 Hz minimum rolloff

**Calibration:**
- Thresholds tuned on labeled dataset
- Documented in `backend/config/settings.yaml`
- See [ROADMAP.md](ROADMAP.md) Milestone 3 for calibration process
Sonotheia uses alternative, physics-based detection methods that are safe and effective:
1.  **Dynamic Velocity (Formant Trajectories)**:
    - **Sensor**: `FormantTrajectorySensor`
    - **Method**: Analyzes the *speed of change* (velocity) of formants over time.
    - **Logic**: Deepfakes often exhibit unnatural "jumps" in frequency that violate the maximum velocity of human articulators. This is a dynamic analysis, not static.
2.  **Phase Coherence (Phase Derivatives)**:
    - **Sensor**: `PhaseCoherenceSensor`
    - **Method**: Analyzes the entropy of the phase derivative (instantaneous frequency).
    - **Logic**: Detects "Glottal Inertia" violations using phase mathematics and amplitude rise velocity, avoiding the source-filter model entirely.
3.  **Simultaneous Articulation (Two-Mouth Problem)**:
    - **Sensor**: `VocalTractSensor`
    - **Method**: Detects conflicting anatomical states (e.g., evidence of both a closed and open vocal tract at the same exact moment).
    - **Logic**: Relies on physical impossibility of simultaneous states, not on static tract length measurements.
4.  **Coarticulation (Motor Planning)**:
    - **Sensor**: `CoarticulationSensor`
    - **Method**: Models the anticipation of the next sound.
    - **Logic**: Analyzes transition smoothness and planning, which is distinct from spectral correctness.

## Compliance Support

### SOX (Sarbanes-Oxley)

- **Audit Logging**: Immutable audit trails
- **Data Retention**: 7 years (configurable)
- **Access Controls**: Planned for enterprise

### PCI-DSS

- **Data Handling**: No cardholder data processed
- **Encryption**: TLS 1.3 in transit
- **Access Logging**: Request/response logging

### HIPAA (Healthcare)

- **PHI Protection**: PII redaction in SAR outputs
- **Data Minimization**: No audio storage
- **Access Controls**: Planned for enterprise

### BSA/AML

- **SAR Generation**: Compliance-ready reports
- **Evidence Packaging**: Immutable audit trails
- **Reporting**: Automated SAR generation

📖 **See [ENTERPRISE_INTEGRATION.md](ENTERPRISE_INTEGRATION.md)** for compliance features.

## Operational Resilience

### Rate Limiting

**Current:**
- 60 requests per minute (configurable)

**Planned:**
- Per-IP rate limiting
- Burst protection
- Quota management

### Monitoring

- **Health Checks**: `/health` endpoint
- **Metrics**: Prometheus-compatible `/metrics`
- **Logging**: Structured JSON logs

### Error Handling

- **Sanitized Errors**: No sensitive data in error messages
- **Graceful Degradation**: Fallbacks for optional features
- **Timeout Protection**: 60-second request timeout

## Security Best Practices

1. **Keep Dependencies Updated**: Regular security audits
2. **Use HTTPS Only**: No HTTP in production
3. **Validate All Inputs**: File size, format, content-type
4. **Limit File Sizes**: Prevent DoS attacks
5. **Monitor Logs**: Regular security log review
6. **Rotate Secrets**: API keys, certificates

## Related Documentation

- [ENTERPRISE_INTEGRATION.md](ENTERPRISE_INTEGRATION.md) - Enterprise security features
- [DEPLOYMENT.md](DEPLOYMENT.md) - SSL/TLS setup
- [ROADMAP.md](ROADMAP.md) - Security improvements planned

---

**Last Updated:** 2025-01-XX  
**Security Contact:** security@sonotheia.ai

