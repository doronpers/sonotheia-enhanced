---
applyTo: "backend/**/*.py"
---

# Backend Development Guidelines

## Python Code Standards

### Style and Formatting
- Follow PEP 8 style guidelines
- Use `black` for automatic formatting
- Use `flake8` for linting
- Maximum line length: 88 characters (black default)
- Use type hints for function parameters and return values

### Code Organization
- Group imports: standard library, third-party, local
- Use absolute imports from project root
- Keep files focused on single responsibility
- Organize related functions into classes

### Naming Conventions
- Classes: PascalCase (e.g., `MFAOrchestrator`, `VoiceAuthenticator`)
- Functions/methods: snake_case (e.g., `authenticate_user`, `validate_device`)
- Constants: UPPER_SNAKE_CASE (e.g., `MAX_ATTEMPTS`, `DEFAULT_THRESHOLD`)
- Private methods: prefix with underscore (e.g., `_internal_helper`)

## FastAPI Patterns

### Endpoint Structure
```python
@router.post("/api/endpoint", response_model=ResponseModel)
async def endpoint_name(
    request: RequestModel,
    background_tasks: BackgroundTasks = None
) -> ResponseModel:
    """
    Brief description of endpoint.
    
    Args:
        request: Description of request model
        
    Returns:
        Description of response
        
    Raises:
        HTTPException: When and why
    """
    pass
```

### Request/Response Models
- Use Pydantic models for all request/response bodies
- Include field validation with `Field()` descriptors
- Add docstrings to model classes
- Use `Config` class for model configuration
- Example:
```python
from pydantic import BaseModel, Field

class AuthRequest(BaseModel):
    """Authentication request with factors."""
    
    user_id: str = Field(..., description="User identifier")
    amount: float = Field(gt=0, description="Transaction amount in USD")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "amount": 1000.0
            }
        }
```

### Error Handling
- Use `HTTPException` for API errors
- Include meaningful error messages
- Return appropriate status codes:
  - 400 for validation errors
  - 401 for authentication failures
  - 403 for authorization failures
  - 404 for not found
  - 500 for internal errors
- Log errors with context

## Audio Processing

### Audio Data Handling
- Accept audio in common formats (WAV, MP3, FLAC)
- Normalize sample rates to 16kHz for processing
- Use NumPy arrays for audio data manipulation
- Use LibROSA for feature extraction
- Handle audio files with context managers

### Voice Authentication
- Implement deepfake detection with confidence scores
- Perform speaker verification against enrolled voiceprints
- Check audio quality and reject poor samples
- Return detailed diagnostic information

## Authentication Components

### MFA Orchestrator
- Follow policy-based decision making
- Support multiple authentication factors (voice, device, behavioral)
- Calculate risk scores based on transaction context
- Return structured results with factor-level details
- Support step-up authentication flows

### Factor Validation
- Each factor returns confidence score (0.0 to 1.0)
- Include evidence/reasoning in results
- Handle missing or invalid factor data gracefully
- Combine factors using weighted scoring

## SAR Generation

### Template-Based Generation
- Use Jinja2 templates in `backend/sar/templates/`
- Pass structured context data to templates
- Include all required SAR fields
- Format amounts and dates consistently
- Add watermarks in demo mode

### SAR Models
- Define comprehensive Pydantic models
- Include all FinCEN required fields
- Validate data before generation
- Support multiple SAR types (structuring, synthetic voice, etc.)

## Database Operations

### SQLAlchemy Patterns
- Use async database operations with `asyncpg`
- Define models in dedicated files
- Use migrations for schema changes
- Include proper indexes on queried columns
- Handle connection pooling appropriately

## Testing

### Test Structure
- Use `pytest` for all tests
- Use `pytest-asyncio` for async tests
- Use `httpx` for API endpoint testing
- Group tests by component/feature
- Include unit, integration, and API tests

### Test Naming
```python
def test_authenticate_with_valid_voice_factor():
    """Test authentication succeeds with valid voice sample."""
    pass

def test_reject_synthetic_voice():
    """Test authentication rejects detected synthetic voice."""
    pass
```

### Fixtures
- Use fixtures for common test data
- Create reusable mock objects
- Clean up resources after tests

## Configuration

### Settings Management
- Load settings from `config/settings.yaml`
- Use environment variables for secrets
- Provide sensible defaults
- Validate configuration at startup
- Document all configuration options

### Demo Mode
- Check `demo_mode` flag in settings
- Add watermarks to generated outputs
- Use synthetic/safe data
- Never expose real model weights or sensitive data

## Security Considerations

### Input Validation
- Validate all inputs with Pydantic
- Sanitize file uploads
- Check file sizes and types
- Implement rate limiting
- Use parameterized queries (SQLAlchemy handles this)

### Data Protection
- Never log sensitive data (audio content, PII)
- Encrypt data at rest
- Use HTTPS in production
- Implement proper CORS policies
- Follow GDPR/privacy regulations

## Dependencies

### Adding New Dependencies
- Add to `requirements.txt` with pinned versions
- Check for security vulnerabilities
- Prefer well-maintained packages
- Document why the dependency is needed
- Consider bundle size impact

### Version Compatibility
- Support Python 3.10+
- Note: parselmouth-praat is incompatible with Python 3.12+
- Use `praat-parselmouth` if PRAAT features needed
- Test with supported Python versions
