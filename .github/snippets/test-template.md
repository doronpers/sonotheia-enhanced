# Test Template (pytest + FastAPI TestClient)

A minimal pattern for creating endpoint integration tests using `fastapi.testclient`.

```python
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from api.main import app

client = TestClient(app)


def test_your_endpoint_happy_path():
    payload = {
        "transaction_id": "TXN-001",
        "customer_id": "CUST-001",
        "amount_usd": 1000.00
    }
    resp = client.post('/api/your-endpoint', json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert 'decision' in data or 'result' in data
    assert 'x-request-id' in resp.headers


def test_your_endpoint_validation_error():
    # Missing required fields or invalid fields
    payload = {"transaction_id": "TXN-001"}
    resp = client.post('/api/your-endpoint', json=payload)
    assert resp.status_code == 422
```
