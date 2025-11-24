---
applyTo: "backend/sar/**/*.py"
---

# SAR (Suspicious Activity Report) Guidelines

## Purpose

The SAR module generates automated Suspicious Activity Reports for financial institutions to comply with regulatory requirements. It detects suspicious patterns and generates narrative reports in FinCEN format.

## SAR Detection Rules

### Structuring Detection
Identify transactions designed to evade reporting thresholds.

**Indicators:**
- Multiple transactions just below reporting threshold ($10,000 in US)
- Transactions within short time window
- Same parties or related accounts
- Unusual patterns of deposits/withdrawals

**Implementation:**
```python
def detect_structuring(
    transactions: list[Transaction],
    threshold_amount: float = 10000,
    threshold_percentage: float = 0.95,
    min_transactions: int = 3
) -> dict:
    """
    Detect potential structuring patterns.
    
    Args:
        transactions: List of transactions to analyze
        threshold_amount: Reporting threshold
        threshold_percentage: How close to threshold (0.95 = 95%)
        min_transactions: Minimum transactions for pattern
        
    Returns:
        {
            'detected': bool,
            'confidence': float,
            'evidence': dict,
            'reason': str
        }
    """
    pass
```

### Synthetic Voice Detection
Identify use of AI-generated or manipulated voice in authentication.

**Indicators:**
- High deepfake detection score
- Frequency spectrum anomalies
- Temporal inconsistencies
- Failed liveness checks

**Reporting Requirements:**
- Include voice authentication evidence
- Document detection methodology
- Note confidence levels
- Preserve audio samples per retention policy

### High-Value High-Risk Transactions
Flag large transactions with additional risk factors.

**Risk Factors:**
- Transaction to high-risk country
- New beneficiary
- Unusual amount for customer profile
- Off-hours transaction
- Device anomalies

**Thresholds:**
```yaml
sar_detection_rules:
  high_value_high_risk:
    enabled: true
    amount_threshold: 50000  # USD
    risk_multiplier: 2.0     # Combine multiple risk factors
```

### Unusual Transaction Patterns
- Rapid movement of funds
- Circular transactions
- Inconsistent with business/occupation
- No apparent economic purpose

## SAR Generation

### Template-Based Narrative

Use Jinja2 templates to generate consistent, compliant narratives.

**Template Location:** `backend/sar/templates/sar_narrative.j2`

**Template Structure:**
```jinja2
# SAR Narrative - Transaction ID: {{ transaction_id }}

## Subject Information
- Customer ID: {{ customer_id }}
- Name: {{ customer_name }}
- Account: {{ account_number }}

## Suspicious Activity Description
{{ activity_description }}

## Transaction Details
{% for transaction in transactions %}
- Date: {{ transaction.date }}
- Amount: ${{ transaction.amount | format_currency }}
- Type: {{ transaction.type }}
- Destination: {{ transaction.destination }}
{% endfor %}

## Risk Factors Identified
{% for factor in risk_factors %}
- {{ factor.name }}: {{ factor.description }}
  Confidence: {{ factor.confidence | format_percentage }}
{% endfor %}

## Authentication Details
{% if voice_authentication %}
Voice Authentication:
- Deepfake Score: {{ voice_authentication.deepfake_score | format_percentage }}
- Speaker Match: {{ voice_authentication.speaker_score | format_percentage }}
- Result: {{ voice_authentication.result }}
{% endif %}

## Compliance Action Taken
{{ compliance_action }}

---
Generated: {{ generation_timestamp }}
{% if demo_mode %}
⚠️ DEMO MODE - FOR DEMONSTRATION PURPOSES ONLY ⚠️
{% endif %}
```

### SAR Data Models

**Comprehensive Pydantic Models:**
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class SARTransaction(BaseModel):
    """Individual transaction in SAR report."""
    transaction_id: str
    date: datetime
    amount: float = Field(gt=0, description="Transaction amount in USD")
    type: str = Field(description="Transaction type (wire, ACH, etc.)")
    destination_country: str
    destination_account: str
    description: Optional[str] = None

class VoiceAuthenticationEvidence(BaseModel):
    """Voice authentication evidence for SAR."""
    deepfake_score: float = Field(ge=0, le=1)
    speaker_score: float = Field(ge=0, le=1)
    quality_score: float = Field(ge=0, le=1)
    result: str = Field(description="PASS or FAIL")
    evidence: dict = Field(default_factory=dict)

class RiskFactor(BaseModel):
    """Individual risk factor."""
    name: str
    description: str
    confidence: float = Field(ge=0, le=1)
    severity: str = Field(description="LOW, MEDIUM, HIGH, CRITICAL")

class SARContext(BaseModel):
    """Complete context for SAR generation."""
    # Subject information
    customer_id: str
    customer_name: str
    account_number: str
    
    # Activity information
    activity_type: str = Field(
        description="structuring, synthetic_voice, unusual_pattern, etc."
    )
    activity_description: str
    
    # Transactions
    transactions: List[SARTransaction]
    
    # Risk assessment
    risk_factors: List[RiskFactor]
    total_risk_score: float = Field(ge=0, le=1)
    
    # Authentication evidence
    voice_authentication: Optional[VoiceAuthenticationEvidence] = None
    device_authentication: Optional[dict] = None
    
    # Compliance
    compliance_action: str
    filing_institution: str
    report_date: datetime = Field(default_factory=datetime.now)
    
    # Demo mode flag
    demo_mode: bool = Field(default=False)

class SARNarrative(BaseModel):
    """Generated SAR narrative."""
    sar_id: str
    narrative: str
    context: SARContext
    generated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### Generation Process

```python
class SARGenerator:
    """Generate SAR narratives from context data."""
    
    def __init__(self, template_path: str, demo_mode: bool = True):
        """Initialize generator with template."""
        self.env = Environment(loader=FileSystemLoader(template_path))
        self.template = self.env.get_template('sar_narrative.j2')
        self.demo_mode = demo_mode
        
        # Add custom filters
        self.env.filters['format_currency'] = self._format_currency
        self.env.filters['format_percentage'] = self._format_percentage
    
    def generate(self, context: SARContext) -> SARNarrative:
        """
        Generate SAR narrative from context.
        
        Args:
            context: Complete SAR context data
            
        Returns:
            Generated SAR narrative
            
        Raises:
            ValueError: If context is incomplete
        """
        # Validate context
        self._validate_context(context)
        
        # Set demo mode flag
        context.demo_mode = self.demo_mode
        
        # Generate narrative
        narrative = self.template.render(
            **context.dict(),
            generation_timestamp=datetime.now().isoformat()
        )
        
        # Create SAR ID
        sar_id = self._generate_sar_id(context)
        
        return SARNarrative(
            sar_id=sar_id,
            narrative=narrative,
            context=context
        )
    
    def _validate_context(self, context: SARContext):
        """Validate SAR context is complete."""
        if not context.transactions:
            raise ValueError("SAR must include at least one transaction")
        
        if not context.risk_factors:
            raise ValueError("SAR must include at least one risk factor")
        
        if not context.activity_description:
            raise ValueError("Activity description is required")
    
    def _generate_sar_id(self, context: SARContext) -> str:
        """Generate unique SAR ID."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"SAR-{context.customer_id}-{timestamp}"
    
    def _format_currency(self, amount: float) -> str:
        """Format currency with commas and 2 decimal places."""
        return f"{amount:,.2f}"
    
    def _format_percentage(self, score: float) -> str:
        """Format score as percentage."""
        return f"{score * 100:.1f}%"
```

## FinCEN Compliance

### Required Fields
- Filing institution information
- Subject information (name, ID, account)
- Suspicious activity type
- Transaction details (date, amount, type)
- Narrative description
- Date range of suspicious activity
- Amount involved
- Actions taken

### Reporting Timeline
- File within 30 days of initial detection
- Maintain supporting documentation for 5 years
- Include all relevant evidence
- Document investigation steps

### Data Protection
- SAR filings are confidential
- Do not disclose to subject of SAR
- Protect SAR data with strict access controls
- Encrypt SAR data at rest and in transit

## Demo Mode Implementation

### Watermarking
```python
def add_demo_watermark(narrative: str, demo_mode: bool) -> str:
    """Add demo watermark to SAR narrative."""
    if demo_mode:
        watermark = "\n\n" + "="*80 + "\n"
        watermark += "⚠️  DEMO MODE - FOR DEMONSTRATION PURPOSES ONLY  ⚠️\n"
        watermark += "This is not a real SAR filing. Do not submit to FinCEN.\n"
        watermark += "="*80 + "\n"
        return narrative + watermark
    return narrative
```

### Synthetic Data
- Use fictional customer names and IDs
- Generate realistic but fake transaction data
- Clearly mark as demonstration data
- Never use real customer information in demo

## API Endpoints

### Generate SAR
```python
@router.post("/api/sar/generate", response_model=SARNarrative)
async def generate_sar(
    context: SARContext,
    background_tasks: BackgroundTasks
) -> SARNarrative:
    """
    Generate SAR narrative from context.
    
    Args:
        context: SAR context with transaction and risk data
        background_tasks: For async processing
        
    Returns:
        Generated SAR narrative
    """
    generator = SARGenerator(
        template_path="backend/sar/templates",
        demo_mode=settings.demo_mode
    )
    
    narrative = generator.generate(context)
    
    # Log SAR generation (audit trail)
    background_tasks.add_task(
        log_sar_generation,
        sar_id=narrative.sar_id,
        customer_id=context.customer_id
    )
    
    return narrative
```

## Testing SAR Generation

### Unit Tests
```python
def test_generate_sar_with_structuring():
    """Test SAR generation for structuring pattern."""
    context = SARContext(
        customer_id="CUST123",
        customer_name="Test Customer",
        account_number="ACC456",
        activity_type="structuring",
        activity_description="Multiple transactions below threshold",
        transactions=[
            SARTransaction(
                transaction_id="TXN1",
                date=datetime.now(),
                amount=9500,
                type="wire_transfer",
                destination_country="US",
                destination_account="DEST1"
            ),
            # More transactions...
        ],
        risk_factors=[
            RiskFactor(
                name="Structuring Pattern",
                description="3 transactions in 2 hours, each ~95% of threshold",
                confidence=0.92,
                severity="HIGH"
            )
        ],
        total_risk_score=0.89,
        compliance_action="Transaction blocked, SAR filed",
        filing_institution="Demo Bank"
    )
    
    generator = SARGenerator(template_path="templates", demo_mode=True)
    narrative = generator.generate(context)
    
    assert narrative.sar_id.startswith("SAR-CUST123-")
    assert "structuring" in narrative.narrative.lower()
    assert "DEMO MODE" in narrative.narrative
```

### Integration Tests
```python
async def test_sar_endpoint():
    """Test SAR generation endpoint."""
    context_data = {...}  # SAR context
    
    response = await client.post(
        "/api/sar/generate",
        json=context_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "sar_id" in data
    assert "narrative" in data
    assert len(data["narrative"]) > 100
```

## Audit and Logging

### SAR Generation Logging
```python
def log_sar_generation(
    sar_id: str,
    customer_id: str,
    activity_type: str,
    risk_score: float
):
    """Log SAR generation for audit trail."""
    logger.info(
        "SAR generated",
        extra={
            "sar_id": sar_id,
            "customer_id": customer_id,  # Hash in production
            "activity_type": activity_type,
            "risk_score": risk_score,
            "timestamp": datetime.now().isoformat()
        }
    )
```

### Compliance Logging
- Log all SAR generation requests
- Record who generated each SAR
- Track SAR filing status
- Maintain audit trail for regulators
- Separate logs for demo vs. production

## Error Handling

### Validation Errors
- Check for required fields
- Validate data types and ranges
- Ensure transaction amounts are positive
- Verify dates are reasonable

### Template Errors
- Handle missing template files
- Catch template rendering errors
- Provide fallback templates
- Log template errors for investigation

### System Errors
- Handle database failures gracefully
- Retry on transient errors
- Return partial results when possible
- Provide meaningful error messages to users
