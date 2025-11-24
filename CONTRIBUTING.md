# Contributing to Sonotheia Enhanced

Thank you for your interest in contributing to Sonotheia Enhanced! This document provides guidelines and best practices for contributing to the project.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Code Standards](#code-standards)
4. [Testing Guidelines](#testing-guidelines)
5. [Documentation](#documentation)
6. [Automated Documentation](#automated-documentation)
7. [Pull Request Process](#pull-request-process)
8. [Architecture Guidelines](#architecture-guidelines)

---

## Getting Started

### Prerequisites

- **Docker** (recommended) or:
  - Python 3.11+ (Note: 3.12+ not fully supported due to some dependencies)
  - Node.js 18+
  - npm
- Git

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/doronpers/sonotheia-enhanced.git
cd sonotheia-enhanced

# One-command setup
./start.sh  # Linux/Mac
start.bat   # Windows

# Or with Docker
docker compose up --build
```

---

## Development Setup

### Backend Development

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run linters
flake8 .
black .
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install --legacy-peer-deps

# Run development server
npm start

# Run tests
npm test

# Run linter
npm run lint
```

---

## Code Standards

### Python Code Standards

#### Style and Formatting
- Follow PEP 8 style guidelines
- Use `black` for automatic formatting (line length: 88)
- Use `flake8` for linting
- Add type hints for all function parameters and return values

#### Naming Conventions
- **Classes**: PascalCase (e.g., `MFAOrchestrator`, `VoiceAuthenticator`)
- **Functions/methods**: snake_case (e.g., `authenticate_user`, `validate_device`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_ATTEMPTS`, `DEFAULT_THRESHOLD`)
- **Private methods**: prefix with underscore (e.g., `_internal_helper`)

#### Code Organization
```python
# Imports
import standard_library
import third_party
import local_modules

# Constants
MAX_RETRIES = 3

# Classes and functions
class MyClass:
    """Docstring describing the class."""
    
    def public_method(self, param: str) -> dict:
        """
        Brief description.
        
        Args:
            param: Description of parameter
            
        Returns:
            Description of return value
            
        Raises:
            ValueError: When and why
        """
        pass
```

### JavaScript/React Code Standards

#### Naming Conventions
- **Components**: PascalCase (e.g., `WaveformDashboard`, `FactorCard`)
- **Functions**: camelCase (e.g., `handleSubmit`, `fetchData`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `API_BASE_URL`)
- **CSS classes**: kebab-case

#### Component Structure
```jsx
// Imports
import React, { useState, useEffect } from 'react';
import { Box, Card } from '@mui/material';

// Component
function ComponentName({ prop1, prop2 }) {
  // State
  const [data, setData] = useState(null);
  
  // Effects
  useEffect(() => {
    // Effect logic
  }, [dependencies]);
  
  // Event handlers
  const handleEvent = () => {
    // Handler logic
  };
  
  // Render
  return (
    <Box>
      {/* JSX */}
    </Box>
  );
}

export default ComponentName;
```

---

## Testing Guidelines

### Backend Testing

#### Test Structure
```python
import pytest
from fastapi.testclient import TestClient

def test_feature_description():
    """Test that feature works as expected."""
    # Arrange
    input_data = {...}
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result['status'] == 'success'
    assert 'data' in result
```

#### Test Categories
1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **API Tests**: Test endpoint behavior
4. **Edge Cases**: Test boundary conditions
5. **Security Tests**: Test validation and sanitization

### Frontend Testing

```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import ComponentName from './ComponentName';

describe('ComponentName', () => {
  it('displays correct content', () => {
    render(<ComponentName prop="value" />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });
  
  it('handles user interaction', () => {
    render(<ComponentName />);
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByText('Updated Text')).toBeInTheDocument();
  });
});
```

### Running Tests

```bash
# Backend
cd backend
pytest                    # Run all tests
pytest tests/test_api.py  # Run specific test file
pytest -v                 # Verbose output
pytest -k "validation"    # Run tests matching pattern

# Frontend
cd frontend
npm test                  # Run all tests
npm test -- --coverage    # With coverage report
```

---

## Documentation

### Code Documentation

#### Python Docstrings
```python
def authenticate_user(user_id: str, factors: dict) -> dict:
    """
    Authenticate user with provided factors.
    
    This function performs multi-factor authentication by evaluating
    the provided authentication factors against configured policies.
    
    Args:
        user_id: Unique identifier for the user
        factors: Dictionary of authentication factors
            {
                'voice': {'audio_data': bytes},
                'device': {'device_id': str}
            }
    
    Returns:
        Authentication result dictionary:
            {
                'decision': str,  # 'APPROVE', 'DENY', 'STEP_UP'
                'confidence': float,
                'factors_evaluated': list
            }
    
    Raises:
        ValueError: If user_id is empty or factors is invalid
        HTTPException: If authentication service is unavailable
    
    Example:
        >>> result = authenticate_user('user123', {'voice': {...}})
        >>> print(result['decision'])
        'APPROVE'
    """
    pass
```

#### API Documentation
- Use OpenAPI/Swagger annotations in FastAPI
- Include request/response examples
- Document all error codes
- Add description for each parameter

### Markdown Documentation
- Use clear, concise language
- Include code examples for all features
- Add diagrams where helpful
- Keep table of contents updated
- Cross-reference related documents

---

## Automated Documentation

### Overview

The project includes automated documentation maintenance and generation systems. See [`.github/README.md`](.github/README.md) for complete details.

### Quick Commands

**Validate documentation before committing:**
```bash
python .github/scripts/validate-docs.py
python .github/scripts/check-links.py
```

**Generate documentation from code:**
```bash
python .github/scripts/generate-api-docs.py
python .github/scripts/generate-component-docs.py
```

**Update changelog:**
```bash
python .github/scripts/update-changelog.py
```

### Automated Workflows

The following workflows run automatically:

1. **Documentation Review** (Weekly + on push/PR)
   - Validates all documentation
   - Checks for broken links
   - Detects outdated dates
   - Creates issues for problems

2. **Auto-Generate Docs** (On code changes)
   - Generates API documentation from FastAPI routes
   - Generates component docs from docstrings
   - Updates CHANGELOG.md from commits
   - Creates PRs for review

### Best Practices

**When writing code:**
- Add comprehensive docstrings to all functions/classes
- Update inline comments for complex logic
- Document API endpoints with descriptions
- Use type hints consistently

**When writing documentation:**
- Follow existing structure and style
- Run validation before committing
- Update dates when making significant changes
- Test all links work correctly

**For documentation PRs:**
- The automation will comment with validation results
- Address any errors before merging
- Review auto-generated content carefully

See [`.github/QUICK_REFERENCE.md`](.github/QUICK_REFERENCE.md) for more commands and tips.

---

## Pull Request Process

### Before Submitting

1. **Run all tests**
   ```bash
   # Backend
   cd backend && pytest
   
   # Frontend
   cd frontend && npm test
   ```

2. **Run linters**
   ```bash
   # Backend
   cd backend && flake8 . && black .
   
   # Frontend
   cd frontend && npm run lint
   ```

3. **Update documentation**
   - Update relevant README sections
   - Update API.md if API changed
   - Add entry to CHANGELOG.md
   - Update inline code comments

4. **Test manually**
   - Run the application locally
   - Test your changes in the UI
   - Verify API endpoints work correctly

### PR Guidelines

#### Title Format
```
[Component] Brief description of changes

Examples:
[Backend] Add rate limiting middleware
[Frontend] Enhance waveform visualization
[Docs] Update API documentation
[Security] Fix input validation in SAR endpoint
```

#### Description Template
```markdown
## Description
Brief summary of changes

## Changes Made
- Added feature X
- Fixed bug Y
- Improved performance of Z

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Documentation updated

## Related Issues
Fixes #123
Relates to #456

## Screenshots (if applicable)
[Add screenshots of UI changes]

## Checklist
- [ ] Code follows project style guidelines
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] No new security vulnerabilities
- [ ] Backward compatibility maintained
```

### Review Process

1. **Automated Checks**
   - All tests must pass
   - Linters must pass
   - CodeQL security scan must pass

2. **Code Review**
   - At least one approval required
   - Address all review comments
   - Keep PR focused and small

3. **Merge**
   - Squash commits when merging
   - Use descriptive merge commit message

---

## Architecture Guidelines

### Hybrid OOP/FP Pattern

This project uses a **hybrid Object-Oriented and Functional Programming** approach:

#### When to Use OOP
- State management
- Plugin architectures
- Framework integration
- Lifecycle management

```python
class AuthenticationFactor:
    """Use OOP for structure and state."""
    
    def __init__(self, config: dict):
        self.config = config
        self.threshold = config.get('threshold', 0.8)
    
    def authenticate(self, data: dict) -> dict:
        # Delegate to pure function
        score = calculate_authenticity_score(data)
        return self._build_result(score)
```

#### When to Use FP
- Data transformations
- Business logic
- Calculations
- Validations

```python
def calculate_authenticity_score(data: dict) -> float:
    """Pure function for testability."""
    # No side effects, no state
    features = extract_features(data)
    score = compute_score(features)
    return score
```

### Component Guidelines

#### Backend Components

**Pydantic Models**
```python
from pydantic import BaseModel, Field, field_validator

class AuthRequest(BaseModel):
    """Request model with validation."""
    
    user_id: str = Field(..., description="User identifier")
    amount: float = Field(gt=0, description="Transaction amount")
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not v or len(v) > 100:
            raise ValueError("Invalid user_id")
        return v
```

**API Endpoints**
```python
@router.post("/api/authenticate", response_model=AuthResponse)
async def authenticate(
    request: AuthRequest,
    background_tasks: BackgroundTasks = None
) -> AuthResponse:
    """
    Endpoint docstring with description.
    """
    try:
        result = orchestrator.authenticate(request)
        return AuthResponse(**result)
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### Frontend Components

**Functional Components with Hooks**
```jsx
import React, { useState, useEffect } from 'react';

function FeatureComponent({ data, onUpdate }) {
  const [state, setState] = useState(initialState);
  
  useEffect(() => {
    // Side effects here
    return () => {
      // Cleanup
    };
  }, [dependencies]);
  
  return (
    <div>
      {/* JSX */}
    </div>
  );
}
```

### Error Handling

**Backend**
```python
try:
    result = perform_operation()
except SpecificError as e:
    logger.warning(f"Expected error: {e}")
    return {'status': 'failed', 'reason': str(e)}
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal error")
```

**Frontend**
```jsx
const [error, setError] = useState(null);

const handleOperation = async () => {
  try {
    const result = await apiCall();
    setError(null);
  } catch (err) {
    setError(err.message);
    console.error('Operation failed:', err);
  }
};
```

---

## Security Guidelines

### Input Validation
- **Always** validate and sanitize user input
- Use Pydantic models for request validation
- Check for SQL injection, XSS, path traversal
- Enforce length limits on all string fields
- Validate numeric ranges

### Secure Coding Practices
- Never log sensitive data (passwords, tokens, audio content)
- Use parameterized queries (SQLAlchemy handles this)
- Implement rate limiting on all endpoints
- Use HTTPS in production
- Keep dependencies updated

### Example Validation
```python
from backend.api.validation import (
    sanitize_string,
    validate_id,
    validate_amount
)

# Sanitize input
safe_string = sanitize_string(user_input)

# Validate with specific rules
user_id = validate_id(raw_id, "user_id")
amount = validate_amount(raw_amount, min_value=0, max_value=1000000)
```

---

## Getting Help

- **Documentation**: Check README.md, API.md, and INTEGRATION.md
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions
- **Code Examples**: Check `examples/` directory (when available)

---

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the project and community
- Show empathy towards other contributors

### Unacceptable Behavior

- Harassment or discriminatory language
- Trolling or insulting comments
- Personal or political attacks
- Publishing others' private information

---

## License

By contributing to Sonotheia Enhanced, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing to Sonotheia Enhanced!**

For questions about contributing, please open an issue or discussion on GitHub.

---

**Last Updated**: 2025-11-24
