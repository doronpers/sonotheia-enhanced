# FastAPI Endpoint Template

This snippet provides a ready-to-copy FastAPI endpoint skeleton following the project's conventions.

Usage: copy into a new function in `backend/api/main.py` or a routers file.

```python
@app.post(
    '/api/feature/new',
    response_model=NewResponseModel,
    tags=['feature'],
    summary='Feature: New operation',
    description='Perform a new feature operation with validation and error handling'
)
@limiter.limit('50/minute')  # Choose an appropriate rate limit
async def feature_new(request: Request, 
                      body: NewRequestModel, 
                      api_key: Optional[str] = Depends(verify_api_key)):
    """
    Brief description of the endpoint.
    """
    try:
        # Validate using existing validators if needed
        # result = feature.process(FeatureRequest(**body.model_dump()))
        result = {}  # Replace with real logic
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=get_error_response('VALIDATION_ERROR', str(e)))
    except Exception as e:
        logger.error("Processing error", exc_info=True)
        raise HTTPException(status_code=500, detail=get_error_response('PROCESSING_ERROR', 'Internal error'))
```
