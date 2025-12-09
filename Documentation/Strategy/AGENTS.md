# Sonotheia Enhanced - Agents Guide & Guardrails

This repository includes human and automated contributors; `AGENTS.md` is for AI coding agents and maintainers who want a focused, workflow-driven runbook and a set of unambiguous guardrails.

TL;DR - What agents must follow
- Follow existing patterns: Pydantic models, middleware, centralized validators in `backend/api/validation.py`, and `get_error_response` for errors.
- **Frontend Dependencies**: Do NOT upgrade `react`, `react-dom`, `react-router-dom`, or `@mui/*` beyond the versions specified in `frontend/package.json` (React 18, Router 6, MUI 5). The build system (`react-scripts` v5) is incompatible with newer versions.
- Demo mode is strictly for demonstration. Do not convert demo placeholders to production behavior unless accompanied by tests, configuration updates, and a design doc.
- Do not log PII (audio bytes, SSNs, etc.). Redact or avoid logging sensitive content.
- Add tests to `backend/tests/` and run `pytest` before submitting changes.
- Use `@limiter.limit` and `verify_api_key` for endpoints, and preserve middleware order: `security headers` > `request ID` > `logging`.

Onboarding (First steps)
1. Clone the repository and read `README.md` and `Documentation/API.md`.
2. Run the test suite locally:

   ```bash
   cd backend
   pytest -q
   ```

3. Start services locally for integration tests (use Docker or scripts):

   ```bash
   ./start.sh
   # or
   docker compose up --build
   ```

High-level repo map
- `backend/api/main.py`: FastAPI endpoints, rate-limits, and OpenAPI configuration.
- `backend/api/middleware.py`: Request ID injection, response time header, security headers, API key verification.
- `backend/api/validation.py`: Central validators (IDs, amounts, base64 audio, XSS/SQL injection checks).
- `backend/authentication/`: MFA orchestrators and factor validators (`mfa_orchestrator.py`, `voice_factor.py`, `device_factor.py`).
- `backend/sar/`: SAR models (`models.py`), generator (`generator.py`), and templates.
- `backend/config/`: `settings.yaml`, `constants.py` for thresholds and limits.

Agent Workflows (What to do when asked to implement or modify)
1. Understand the requirements & scope of change.
2. Write a small, focused change. Prefer incremental PRs.
3. Create/extend Pydantic models (use `Field()` and `field_validator`). Prefer a feature-local model in `backend/api/` or `backend/sar/models.py`.
4. Add the endpoint to `backend/api/main.py` following existing tagging, rate limiting and error handling patterns:

   - Include `@limiter.limit('X/minute')` (choose limit based on resource intensity).
   - Include `api_key: Optional[str] = Depends(verify_api_key)` to protect endpoints for production.

5. Use validation helpers from `backend/api/validation.py`. If the helper is missing and needs to be added, add tests that validate expected behavior for valid and invalid inputs.
6. Add unit and integration tests under `backend/tests/` and ensure tests assert `X-Request-ID` and `X-Response-Time` exist in responses.
7. Run `flake8` and `black` in the backend and update code style where necessary.

Guardrails (Non-negotiable restrictions)
- Do not remove `DEMO_MODE` checks or flip default `DEMO_MODE` to production in a PR that introduces demo-only logic.
- Never commit secrets (API keys, passwords). Use environment variables and `.env.example` as a template.
- Avoid adding code that directly logs raw audio content or PII; extract metadata, decisions, and reason codes instead.
- New endpoints must include test coverage and a validator for every user-supplied parameter.
- Do not increase API limits without a documented reasoning and explicit tests for performance and security tradeoffs.

What to check before creating a PR (Agent's PR checklist)
1. Unit and integration tests pass: `cd backend && pytest -q`.
2. Lint and format: `cd backend && black . && flake8 .`.
3. No secrets in code; `git diff` should be inspected for API keys, tokens, or test audio.
4. `DEMO_MODE` not accidentally changed in production-targeted features.
5. New endpoint contains `@limiter.limit` and `verify_api_key` unless explicitly a demo endpoint.
6. Added tests verify edge cases (invalid inputs, malformed audio, large payloads), as well as success paths.

When to ask for human review
- Adding new ML models or model weights; anything requiring external data / credentials.
- Changes that may affect regulatory compliance (SAR generation, logs retention, PII handling).
- Any change that modifies security or configuration defaults.

Pattern Examples (Short copy-paste templates)

- Add endpoint (FastAPI skeleton):

  ```python
  @app.post('/api/feature/new', tags=['feature'])
  @limiter.limit('50/minute')
  async def feature_new(request: Request, body: FeatureRequest, api_key: Optional[str] = Depends(verify_api_key)):
      try:
          validated = FeatureRequest(**body.model_dump())
          result = feature.process(validated)
          return result
      except ValueError as e:
          raise HTTPException(status_code=422, detail=get_error_response('VALIDATION_ERROR', str(e)))
      except Exception as e:
          logger.error("Processing error", exc_info=True)
          raise HTTPException(status_code=500, detail=get_error_response('PROCESSING_ERROR', 'Internal error'))
  ```

- Validation: use `validate_base64_audio` for audio input to ensure magic bytes match and size limits:
- Validation: use `validate_base64_audio` for audio input to ensure magic bytes match and size limits, and `validate_audio_duration` to enforce min/max duration for WAV audio.

  ```python
  from api.validation import validate_base64_audio
  audio = validate_base64_audio(body.get('voice_sample'))
  ```

Consolidated Documentation Improvements
- Prefer `backend/api/main.py` as the central reference for available endpoints and their rate-limits.
- `backend/api/validation.py` should be the single source of truth for cross-cutting validation patterns; prefer adding helpers there rather than sprinkling validation inline.
- Add or update `Documentation/API.md` to include any new endpoints and examples.

Additions & Next steps
- This repo already includes `.github/snippets/` with endpoint, model, and test templates (copy-paste ready). Use these when scaffolding PRs.
- Optionally add a CI check to fail PRs if `DEMO_MODE` is disabled without tests/justification.

Thank you — use this guide as the canonical agent runbook. If you'd like, I can now produce a `./.github/snippets` set for `MFA`, `SAR`, and a `FastAPI endpoint + tests` template.
