# Snippets for agents

This directory contains copy-paste friendly code templates for common tasks:

- `endpoint-skeleton.md` - standard FastAPI endpoint pattern used in the repo
- `pydantic-model.md` - Pydantic model template with Field and validator examples
- `test-template.md` - pytest + TestClient integration test skeleton
- `frontend-component.md` - React component template (Material-UI + Plotly/Waveform hints)
- `c-template.md` - Minimal C program template with build/run notes

How to use:
- Copy the code block into your target file (e.g., `backend/api/main.py`) and adapt the model and logic.
- Add tests under `backend/tests/` for new endpoints and validations.
- Run `cd backend && pytest -q` to validate you didn't break anything.
