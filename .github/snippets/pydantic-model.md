# Pydantic Model Template

A typical Pydantic model for request/response shapes. Put new models under a feature folder e.g. `backend/api/` or `backend/sar/models.py`.

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List

class NewRequestModel(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "transaction_id": "TXN-001",
                "amount_usd": 1000.0
            }
        }
    )

    transaction_id: str = Field(..., description="Transaction identifier")
    customer_id: str = Field(..., description="Customer identifier")
    amount_usd: float = Field(..., gt=0, description="Amount in USD")
    voice_sample: Optional[str] = Field(None, description="Base64-encoded audio")

    @field_validator('transaction_id', 'customer_id')
    @classmethod
    def validate_ids(cls, v, info):
        if len(v) > 100:
            raise ValueError(f"{info.field_name} too long")
        return v

class NewResponseModel(BaseModel):
    decision: str
    confidence: float
    explanation: Optional[str] = None

```