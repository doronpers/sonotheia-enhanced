# Sonotheia Enhanced - General Development Guidelines

## Project Overview

Sonotheia Enhanced is a multi-factor voice authentication and SAR (Suspicious Activity Report) reporting system that combines:
- Deepfake detection
- MFA (Multi-Factor Authentication) orchestration
- Automated suspicious activity reporting
- Real-time risk assessment
- Interactive dashboard with waveform visualization

## Repository Structure

- `backend/` - Python/FastAPI backend with authentication and SAR services
- `frontend/` - React-based interactive dashboard
- `reusable-components/` - Shared component library

## Technology Stack

**Backend:**
- Python 3.x with FastAPI
- Pydantic for data validation
- NumPy, SciPy, LibROSA for audio processing
- PyTorch for ML models
- Jinja2 for SAR template rendering
- SQLAlchemy for database operations

**Frontend:**
- React 18.x
- Material-UI (@mui/material)
- Plotly.js for visualizations
- WaveSurfer.js for audio waveforms
- Axios for API calls

## Build and Test Commands

### Backend
```bash
cd backend
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run linters
flake8 .
black .

# Start development server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
# Install dependencies
npm install --legacy-peer-deps

# Run tests
npm test

# Run linter
npm run lint

# Start development server
npm start
```

## Code Quality Standards

### General
- Make minimal, surgical changes to accomplish the task
- Preserve existing working code unless fixing security vulnerabilities
- Follow existing code patterns and conventions
- Add comments only where they match existing style or explain complex logic
- Use existing libraries; avoid adding new dependencies unless necessary

### Testing
- Run existing tests before making changes to understand baseline
- Ensure changes don't break existing tests (unless fixing bugs)
- Tests must pass before finalizing changes
- Document-only changes don't require test runs

### Security
- Never commit secrets or credentials
- Validate all user inputs
- Follow secure coding practices
- Run security checks before finalizing changes
- Fix vulnerabilities in code you modify

## Documentation
- Keep README.md, API.md, and other docs updated when making functional changes
- Use clear, concise language
- Include examples for new features
- Update inline code documentation when changing function signatures or behavior

## Git Workflow
- Commit messages should be clear and descriptive
- Keep commits focused on specific changes
- Use `.gitignore` to exclude build artifacts, `node_modules`, etc.
- Review committed files to ensure minimal scope

## API Conventions
- RESTful endpoint design
- Use proper HTTP status codes
- Include comprehensive error messages
- Validate request bodies with Pydantic models
- Return consistent JSON response structures

## Configuration
- Configuration lives in `backend/config/settings.yaml`
- Demo mode is enabled by default (disable in production)
- Environment-specific settings should use environment variables
- Document all configuration options
