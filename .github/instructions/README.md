# GitHub Copilot Instructions

This directory contains instruction files for GitHub Copilot coding agent. These files help Copilot understand the repository structure, coding standards, and best practices when working on issues and pull requests.

## Files Overview

### `general.instructions.md`
**Applies to:** All files in the repository

General guidelines covering:
- Project overview and architecture
- Technology stack (Python/FastAPI backend, React frontend)
- Build and test commands
- Code quality standards
- Git workflow and security considerations

### `backend.instructions.md`
**Applies to:** `backend/**/*.py`

Python/FastAPI specific guidelines:
- Python code standards (PEP 8, type hints, formatting with black/flake8)
- FastAPI endpoint patterns and Pydantic models
- Audio processing with LibROSA and NumPy
- Authentication and SAR components
- Database operations with SQLAlchemy
- Testing patterns with pytest

### `frontend.instructions.md`
**Applies to:** `frontend/**/*.{js,jsx,ts,tsx}`

React specific guidelines:
- React functional components and hooks
- Material-UI (MUI) usage patterns
- State management and data fetching
- API integration with Axios
- Visualization components (Plotly.js, WaveSurfer.js)
- Performance optimization and accessibility

### `authentication.instructions.md`
**Applies to:** `backend/authentication/**/*.py`

Authentication system guidelines:
- MFA orchestrator decision flow and policies
- Voice authentication (deepfake detection, speaker verification, liveness checks)
- Device authentication and trust scoring
- Behavioral factors
- Testing strategies
- Security and audit logging

### `sar.instructions.md`
**Applies to:** `backend/sar/**/*.py`

SAR/compliance specific guidelines:
- SAR detection rules (structuring, synthetic voice, high-risk transactions)
- Template-based narrative generation with Jinja2
- FinCEN compliance requirements
- Pydantic v2 data models
- Demo mode implementation
- Audit logging and error handling

## How Copilot Uses These Instructions

1. **Automatic Application**: When Copilot coding agent works on a task, it automatically reads relevant instruction files based on the `applyTo` patterns in the YAML frontmatter.

2. **Context-Aware**: Instructions are scoped to specific file paths, so backend work follows Python guidelines while frontend work follows React guidelines.

3. **Best Practices**: Instructions ensure consistent code quality, testing practices, and security standards across all contributions.

4. **Onboarding**: These instructions serve as documentation for both Copilot and human developers joining the project.

## Updating Instructions

When updating these instructions:
- Keep them concise and actionable
- Include code examples for complex patterns
- Update the `applyTo` patterns if file structure changes
- Test that Copilot follows the guidelines when working on tasks
- Document any repository-specific requirements or constraints

## References

- [GitHub Copilot Instructions Documentation](https://docs.github.com/en/copilot/tutorials/coding-agent/get-the-best-results)
- [Best practices for Copilot coding agent](https://github.blog/ai-and-ml/github-copilot/onboarding-your-ai-peer-programmer-setting-up-github-copilot-coding-agent-for-success/)
