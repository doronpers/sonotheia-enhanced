# Sonotheia Enhanced - Copilot Instructions (Detailed)

Note: The canonical agent runbook and guardrails live in `AGENTS.md` at repository root. Use it for onboarding and PR policies.

This document is a detailed, actionable guide to help an AI coding agent (Copilot) contribute safely and effectively to Sonotheia Enhanced. It collects project-specific patterns, examples, and requirements found in the codebase and merges them with the existing guidance under `.github/instructions/`.

## Big-picture architecture and rationale

- Backend: Python/FastAPI in `backend/` (entry point: `backend/api/main.py`). The backend exposes API endpoints, middleware, and business logic. Pydantic models live with the feature they belong to (e.g., SAR under `backend/sar/models.py`).
- Frontend: React app under `frontend/` using Plotly, Material-UI, Waveforms, and the REST API for backend integration.
- SAR generator: Template-driven narratives in `backend/sar/templates/sar_narrative.j2` with `SARGenerator` and `SARContext` for validation.
- Authentication: MFA Orchestrator in `backend/authentication/` (MFAOrchestrator, UnifiedOrchestrator), with `VoiceAuthenticator` and `DeviceValidator` factor validators. The orchestrator applies policy, computes risk, and returns diagnostic details.

Why this layout: The repo separates domain concerns (auth, sar, api) for clear ownership and testing, using Pydantic models and modular components.

## Important repo-wide patterns for code agents

- Use Pydantic models for request/response shapes. Add `Field()` descriptors and `field_validator` for validations. See `backend/sar/models.py` and `backend/api/main.py` (AuthRequest and AuthenticationResponse).
- Use `backend/api/validation.py` for input sanitization and security checks. Prefer `validate_id`, `validate_amount`, `validate_base64_audio`, and `validate_text_input` wherever applicable.
- Add endpoints to `backend/api/main.py`. Use `@limiter.limit('X/minute')` to set rate limits and include `api_key: Optional[str] = Depends(verify_api_key)` for route protection when needed.
- Middleware order matters: `add_security_headers_middleware` → `add_request_id_middleware` → `log_request_middleware`. Request ID and Response Time headers are required by tests and monitoring.
- Use `get_error_response(error_code, message, details=None)` for consistent error payloads at endpoint failure points.

## Security & Demo Mode

- `DEMO_MODE` environment variable (found in `.env.example` and `docker-compose.yml`) toggles demo behaviors across modules. Demo mode uses placeholder logic and synthetic data—do not use demo-mode code in production.
- `backend/api/middleware.py` reads `API_KEYS` and `DEMO_API_KEY` environment variables. Do not store secrets in the repo.
- Sensitive data such as audio bytes and PII should not be logged. Instead log decisions and reason codes.

## Where to look first when changing/adding features

- `backend/api/main.py` — Routing, OpenAPI documentation, rate limits, dependencies.
- `backend/api/middleware.py` — API key verification, limiter setup, request id injection, security headers, error handling.
- `backend/api/validation.py` — Input sanitization and validation helpers.
- `backend/authentication/` — MFA orchestration and factor validators (`mfa_orchestrator.py`, `voice_factor.py`, `device_factor.py`). Demo behavior & placeholders are located here.
- `backend/sar/` — SAR context models (`models.py`), generator (`generator.py`), and templates (`templates/sar_narrative.j2`). Implement an `env.filters` in `SARGenerator` if template formatting needed.
- `backend/config/` — `settings.yaml` and `constants.py` define thresholds and validation constants.
- `backend/tests/` — Unit and API tests, run them to validate changes.

## Adding an endpoint — Example pattern

Follow the style and tests already present. Minimal skeleton:

1) Create/extend a Pydantic request/response model (in `backend/api/` or feature folder)

```python
class NewRequest(BaseModel):
    transaction_id: str = Field(..., description='...')
    amount_usd: float = Field(..., gt=0)
    # use field_validator for custom checks
```

2) Add endpoint in `backend/api/main.py`:

```python
@app.post('/api/new/operation', response_model=NewResponse, tags=['feature'])
@limiter.limit('50/minute')
async def new_operation(request: Request, body: NewRequest, api_key: Optional[str] = Depends(verify_api_key)):
    try:
        # Validate inputs using helpers in backend/api/validation.py
        # Do not log PII or audio bytes
        result = feature.process(body)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=get_error_response('VALIDATION_ERROR', str(e)))
    except Exception
        raise HTTPException(status_code=500, detail=get_error_response('PROCESSING_ERROR', '...'))
```

Execution notes: Add appropriate `@limiter.limit` depending on operation intensity and apply `verify_api_key` dependency for production-level endpoints.

## Pydantic & Validation best practices

- Use `Field` metadata for OpenAPI and `ConfigDict` for examples and json encoders when needed.
- Prefer to validate with `field_validator` to centralize checks in models (`SARContext`, `AuthenticationRequest`).
- Use `validate_base64_audio` for voice samples—it validates magic bytes and sizes.
- For small functions with domain-specific validation, create a helper in `backend/api/validation.py` or a per-feature validation helper.

## Voice and Device factors — guidance

- `VoiceAuthenticator` (in `backend/authentication/voice_factor.py`) uses placeholders in demo mode: `detect_deepfake`, `check_liveness`, `verify_speaker` return fixed values. In production integrate ML models and use caution for privacy.
- `DeviceValidator` (in `devices/*`) handles enrollment and trust scoring. Demo code sets `is_enrolled` to True; replace with DB checks when implementing production device enrollment.
- Keep return payloads consistent with `AuthenticationResponse` payloads shown in `backend/sar/models.py`.

## SAR generation & templates

- Use Jinja2 templates under `backend/sar/templates/`. Use `SARGenerator` and call `generate_sar(context)` and `validate_sar_quality` to produce narrative and quality checks.
- Keep a demo watermark if `DEMO_MODE` is enabled.
- Use filters for currency and percentage formatting in templates if necessary (e.g., `format_currency`, `format_percentage`), and add them under `SARGenerator.env.filters`.

## Tests — writing and conventions

- Feature tests live under `backend/tests/`. They use `fastapi.testclient.TestClient(app)` and look for `X-Request-ID`, `X-Response-Time` headers. Ensure these are preserved.
- Test naming: `test_featureName_condition_expectedOutcome`, e.g., `test_enhanced_authenticate_valid_request`.
- For new endpoints, add tests that mimic input validation and success/error conditions. Keep tests minimal but cover edge cases.
- Async endpoints can be tested with `pytest-asyncio` or via `TestClient` synchronous calls.

## Linting & formatting

- Backend: `black .` (default black settings), `flake8 .`.
- Frontend: `npm run lint`, `npm test`.

## PR checklist for Copilot / Agents

Before creating or updating PRs, re-check:
- `DEMO_MODE` remains set appropriately for development.
- No secrets in code or configs. Use env var references only.
- Add or update tests for any new behavior. Run `pytest`.
- Confirm `X-Request-ID` and `X-Response-Time` headers exist after changes.
- Ensure `verify_api_key` or appropriate authentication is applied for production-sensitive endpoints.
- Ensure rate limits set via `@limiter.limit` match endpoint resource usage.

## Quick code snippets for common tasks

- Add `@limiter.limit` with appropriate value. Example: `@limiter.limit('20/minute')` for SAR generation.
- Add `api_key` dependency: `api_key: Optional[str] = Depends(verify_api_key)`.
- Standard error response: `raise HTTPException(status_code=422, detail=get_error_response('VALIDATION_ERROR', message))`.

## Integration & deploy notes

- Use `docker compose up --build` to run both services. `start.sh` abstracts this.
- For production, set `DEMO_MODE=false` and configure `API_KEYS` with a secure storage.

## Where to ask when uncertain

- If uncertain about a policy boundary (e.g., enabling production ML models, changing `DEMO_MODE`), open an issue or add a PR discussion, explaining risk and proposed safeguards.

---
If you'd like, I can convert the code snippets into test-ready templates and add them under `.github/snippets/` for Copilot to reference. Want me to add snippet files or examples for a specific area (e.g., `MFA`, `SAR`, `Voice`)?

