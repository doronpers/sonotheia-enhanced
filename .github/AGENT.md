# Sonotheia Enhanced - AI Agent Onboarding & On-Call Guide

This is a quick, practical onboarding guide for AI agents (Copilot, Codex, etc.) to become productive in this repository.

## Purpose

- Provide a reproducible checklist to prepare the environment and start contributing quickly.
- Explain the most common editing patterns and files that matter in this repo.
- Share explicit safety and contribution rules that every automated or human contributor should follow.

## Quick Start Checklist

1. Read `README.md` at the repo root to understand service behavior and quick start steps.
1. Run tests immediately to get a working baseline.

   - Backend tests:

     ```bash
     cd backend
     pytest -q
     ```

   - Frontend tests (optional for UI changes):

     ```bash
     cd frontend
     npm test
     ```

1. Start services locally (Docker recommended):

   ```bash
   ./start.sh  # macOS/Linux
   start.bat   # Windows
   # or docker compose up --build
   ```

1. Run the backend locally (without Docker) to iterate faster:

   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Repo Map: Where to look first

- `backend/api/main.py`: FastAPI routes and high-level endpoints. Add endpoints and middleware here.
- `backend/api/middleware.py`: Request tracking (`X-Request-ID`), `X-Response-Time`, `verify_api_key`, and rate limiting (`limiter`). Middleware order matters.
- `backend/api/validation.py`: Input sanitization and security checks (SQL injection / XSS / path traversal). Use these helpers for new inputs.
- `backend/authentication/`: MFA orchestrators and factor validators (voice, device).
- `backend/sar/`: SAR models, generator, and Jinja templates in `templates/`.
- `backend/config/`: `settings.yaml` and `constants.py` for thresholds and limits.
- `backend/tests/`: Tests for API and validation behavior (run via pytest).
- `frontend/`: React dashboard, components, and test harness.

## Common Conventions & Patterns

- Pydantic models define request/response shapes. Use `Field()` descriptors and `field_validator` to centralize validation.
- Use `limiter.limit('X/minute')` on endpoints. Choose limits conservatively for resource-heavy endpoints (SAR generation: `20/min`).
- Add `api_key: Optional[str] = Depends(verify_api_key)` for production endpoints (optional in demo mode).
- Use `get_error_response` for consistent error payloads.
- Do not log raw audio bytes or PII. Log decisions, reason codes, and request IDs instead.

## Demo Mode & Safety

- `DEMO_MODE` (env) toggles demo behavior; demo logic is NOT production-ready and contains placeholders.
- Placeholder methods: `VoiceAuthenticator.detect_deepfake`, `VoiceAuthenticator.verify_speaker`, `DeviceValidator._check_enrollment` return demo values. If adding a production implementation, add tests and configuration.
- `DEMO_API_KEY` in `.env.example` is for demo only. Never commit real keys or secrets.

## Validation & Security

- Use central validators in `backend/api/validation.py`: `validate_id`, `validate_amount`, `validate_base64_audio`, `validate_text_input`.
- `validate_base64_audio` validates magic bytes and size for audio files.
- Escape and validate all inputs before rendering Jinja templates for SAR generation.

## Testing Guidance (AI agent actions)

1. For new endpoints:

   - Add a Pydantic request/response model under `backend/api/` or the corresponding feature folder.
   - Add an integration test in `backend/tests/` using `TestClient`.
   - Check headers: `X-Request-ID` and `X-Response-Time` are present.

1. For validation changes:

   - Add unit tests in `backend/tests/test_validation.py` for both valid and invalid cases.

1. For SAR and template changes:

   - Add a unit test for `SARGenerator.generate_sar` and `validate_sar_quality`.

1. Run tests locally and in CI before submitting PRs.

## Code Examples & Shortcuts

- Endpoint skeleton (copyable):

  ```python
  @app.post('/api/your-endpoint', tags=['feature'])
  @limiter.limit('50/minute')
  async def your_endpoint(request: Request, body: YourRequestModel, api_key: Optional[str] = Depends(verify_api_key)):
      try:
          # Use helpers from backend/api/validation.py
          result = your_feature.process(body)
          return result
      except ValueError as e:
          raise HTTPException(status_code=422, detail=get_error_response('VALIDATION_ERROR', str(e)))
      except Exception:
          raise HTTPException(status_code=500, detail=get_error_response('PROCESSING_ERROR', 'Internal error'))
  ```

- Minimal test example for an endpoint:

  ```python
  def test_new_endpoint():
      client = TestClient(app)
      payload = { ... }
      resp = client.post('/api/your-endpoint', json=payload)
      assert resp.status_code == 200
      assert 'x-request-id' in resp.headers
  ```

## PR Submission Checklist (what the agent must verify)

1. Run backend tests: `cd backend && pytest -q` → all tests pass.
1. Add or update tests for all new behaviors or validations.
1. Lint & format: Run `flake8 .` and `black .` in `backend`.
1. Update `README.md` or `Documentation/` if the API or workflow changed.
1. Ensure `DEMO_MODE` or demo placeholder code is not accidentally represented as the final production logic.

## Operational Hints for Agents

- Favor small, focused changes with tests; avoid large refactors without tests.
- Use `X-Request-ID` to correlate logs and request tests.
- Stick to `backend/config/constants.py` for constants and validation limits.

## When to Ask For Human Review

- Adding production ML models (voice deepfake detection or speaker verification) that require model weights or external services.
- Changing `DEMO_MODE` default to `false` or enabling production paths without tests.
- Anything that stores or transmits PII beyond small test examples.

## Where to Get More Context

- `README.md` and `Documentation/` (API.md, USAGE_GUIDE.md, INTEGRATION.md) for detailed examples and policies.
- `backend/api/main.py` for endpoint patterns and middleware ordering.

## Additional notes

- I can add a `./.github/snippets` directory with code templates for endpoints, models, and tests. Tell me which area to prioritize (MFA, SAR, or CI/test templates).

Welcome aboard. When in doubt, create a small PR with tests and ask for review.
