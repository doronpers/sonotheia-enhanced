# Integration Guide

This guide shows how to integrate Sonotheia Enhanced into your existing systems.

## Table of Contents

1. [Banking & Financial Institutions](#banking--financial-institutions)
2. [Real Estate & Escrow Systems](#real-estate--escrow-systems)
3. [General Integration Patterns](#general-integration-patterns)
4. [Configuration Best Practices](#configuration-best-practices)
5. [Testing Your Integration](#testing-your-integration)

---

## Banking & Financial Institutions

### Wire Transfer Authentication

Integrate Sonotheia into your wire transfer approval workflow:

```python
from backend.authentication.mfa_orchestrator import (
    MFAOrchestrator, 
    TransactionContext, 
    AuthenticationFactors
)

# Initialize once at application startup
orchestrator = MFAOrchestrator()

def process_wire_transfer(transfer_request):
    """
    Authenticate wire transfer request with multi-factor authentication
    """
    # Build transaction context
    context = TransactionContext(
        transaction_id=transfer_request['id'],
        customer_id=transfer_request['customer_id'],
        transaction_type='wire_transfer',
        amount_usd=transfer_request['amount'],
        destination_country=transfer_request['destination_country'],
        is_new_beneficiary=not is_beneficiary_known(
            transfer_request['beneficiary_id']
        ),
        channel='online_banking'
    )
    
    # Collect authentication factors
    factors = AuthenticationFactors(
        voice={
            'audio_data': transfer_request.get('voice_sample')
        } if transfer_request.get('voice_sample') else None,
        device={
            'device_id': transfer_request['device_id'],
            'integrity_check': verify_device_integrity(
                transfer_request['device_id']
            ),
            'location_consistent': check_location_consistency(
                transfer_request['customer_id'],
                transfer_request['location']
            )
        }
    )
    
    # Authenticate
    result = orchestrator.authenticate(context, factors)
    
    # Handle decision
    if result['decision'] == 'APPROVE':
        # Execute wire transfer
        execute_transfer(transfer_request)
        log_approval(transfer_request['id'], result)
        return {'status': 'approved', 'details': result}
        
    elif result['decision'] == 'STEP_UP':
        # Request additional authentication
        request_additional_factor(
            transfer_request['customer_id'],
            'voice'  # Or other missing factor
        )
        return {'status': 'pending', 'message': 'Additional authentication required'}
        
    elif result['decision'] == 'MANUAL_REVIEW':
        # Queue for manual review
        queue_for_review(transfer_request, result)
        notify_compliance_team(transfer_request['id'], result['risk_level'])
        return {'status': 'under_review', 'details': result}
        
    else:  # DECLINE
        # Decline transaction
        decline_transfer(transfer_request, result)
        log_decline(transfer_request['id'], result)
        
        # Check if SAR should be filed
        if result['sar_flags']:
            initiate_sar_investigation(transfer_request, result['sar_flags'])
        
        return {'status': 'declined', 'reason': result}
```

### Automated SAR Filing

```python
from backend.sar.generator import SARGenerator
from backend.sar.models import SARContext, SARTransaction
from datetime import date

sar_generator = SARGenerator()

def generate_sar_for_customer(customer_id, suspicious_transactions):
    """
    Generate SAR narrative for suspicious customer activity
    """
    # Fetch customer details
    customer = get_customer_details(customer_id)
    
    # Aggregate transaction data
    total_amount = sum(tx['amount'] for tx in suspicious_transactions)
    
    # Build SAR context
    context = SARContext(
        customer_name=customer['name'],
        customer_id=customer_id,
        account_number=customer['account_number'],
        account_opened=customer['account_opened'],
        occupation=customer['occupation'],
        suspicious_activity="Structured wire transfers to avoid reporting threshold",
        start_date=min(tx['date'] for tx in suspicious_transactions),
        end_date=max(tx['date'] for tx in suspicious_transactions),
        count=len(suspicious_transactions),
        amount=total_amount,
        pattern="structuring",
        red_flags=[
            "Multiple transactions just below $10,000 threshold",
            "Frequent wire transfers to high-risk jurisdictions",
            "Customer unable to provide business documentation",
            "Synthetic voice detected in authentication attempts"
        ],
        transactions=[
            SARTransaction(
                transaction_id=tx['id'],
                date=tx['date'],
                type=tx['type'],
                amount=tx['amount'],
                destination=tx['destination']
            )
            for tx in suspicious_transactions
        ],
        doc_id=generate_doc_id()
    )
    
    # Generate SAR narrative
    narrative = sar_generator.generate_sar(context)
    validation = sar_generator.validate_sar_quality(narrative)
    
    if validation['ready_for_filing']:
        file_sar(narrative, context)
    else:
        # Flag for manual review
        flag_for_manual_sar_review(narrative, validation['issues'])
    
    return {'narrative': narrative, 'validation': validation}
```

---

## Real Estate & Escrow Systems

### Multi-Party Wire Verification

```python
def verify_closing_wire_instructions(closing):
    """
    Verify all parties in a real estate closing before releasing wire
    """
    # Authenticate buyer
    buyer_auth = authenticate_party(
        party_id=closing['buyer_id'],
        party_type='buyer',
        amount=closing['purchase_price'],
        voice_sample=closing['buyer_voice_sample'],
        device_info=closing['buyer_device']
    )
    
    # Authenticate seller
    seller_auth = authenticate_party(
        party_id=closing['seller_id'],
        party_type='seller',
        amount=closing['net_proceeds'],
        voice_sample=closing['seller_voice_sample'],
        device_info=closing['seller_device']
    )
    
    # Both parties must approve
    if (buyer_auth['decision'] == 'APPROVE' and 
        seller_auth['decision'] == 'APPROVE'):
        
        # Release wire
        release_escrow_wire(closing)
        notify_all_parties(closing, 'funds_released')
        return {'status': 'completed'}
        
    else:
        # Hold funds and notify
        hold_escrow(closing)
        notify_title_company(closing, [buyer_auth, seller_auth])
        
        return {
            'status': 'on_hold',
            'buyer_status': buyer_auth['decision'],
            'seller_status': seller_auth['decision']
        }

def authenticate_party(party_id, party_type, amount, voice_sample, device_info):
    """Authenticate a single party in the transaction"""
    context = TransactionContext(
        transaction_id=f"{party_type}_{party_id}",
        customer_id=party_id,
        transaction_type='real_estate_wire',
        amount_usd=amount,
        destination_country='US',
        is_new_beneficiary=False,
        channel='escrow_platform'
    )
    
    factors = AuthenticationFactors(
        voice={'audio_data': voice_sample} if voice_sample else None,
        device=device_info
    )
    
    return orchestrator.authenticate(context, factors)
```

---

## General Integration Patterns

### Webhook Integration

For asynchronous authentication results:

```python
from fastapi import BackgroundTasks

@app.post("/webhook/authenticate")
async def authenticate_webhook(
    request: AuthenticationRequest,
    background_tasks: BackgroundTasks
):
    """
    Webhook endpoint for asynchronous authentication
    """
    def process_authentication():
        # Perform authentication
        result = orchestrator.authenticate(context, factors)
        
        # Send result to callback URL
        send_result_to_callback(
            request.callback_url,
            result
        )
    
    background_tasks.add_task(process_authentication)
    return {"status": "processing", "transaction_id": request.transaction_id}
```

### Batch Processing

For processing multiple authentication requests:

```python
def batch_authenticate(requests):
    """
    Process multiple authentication requests in batch
    """
    results = []
    
    for req in requests:
        context = build_context(req)
        factors = collect_factors(req)
        result = orchestrator.authenticate(context, factors)
        results.append({
            'transaction_id': req['transaction_id'],
            'result': result
        })
    
    return results
```

---

## Configuration Best Practices

### Environment-Specific Configuration

```yaml
# config/settings.production.yaml
authentication_policy:
  minimum_factors: 3  # Stricter in production
  require_different_categories: true

voice:
  deepfake_threshold: 0.2  # Lower threshold = more sensitive
  speaker_threshold: 0.90  # Higher threshold = more strict

sar_detection_rules:
  structuring:
    enabled: true
    threshold_amount: 5000  # Lower threshold for production
```

### Load Configuration Dynamically

```python
import os
from pathlib import Path

def load_config():
    env = os.getenv('ENVIRONMENT', 'development')
    config_file = f"config/settings.{env}.yaml"
    
    if not Path(config_file).exists():
        config_file = "config/settings.yaml"
    
    with open(config_file) as f:
        return yaml.safe_load(f)

orchestrator = MFAOrchestrator(config=load_config())
```

---

## Testing Your Integration

### Unit Tests

```python
import pytest
from backend.authentication.mfa_orchestrator import MFAOrchestrator

def test_high_value_transaction_requires_voice():
    orchestrator = MFAOrchestrator()
    
    context = TransactionContext(
        transaction_id="TEST001",
        customer_id="CUST123",
        transaction_type="wire_transfer",
        amount_usd=50000,  # High value
        destination_country="US",
        is_new_beneficiary=False,
        channel="online_banking"
    )
    
    # Only device factor provided
    factors = AuthenticationFactors(
        device={'device_id': 'DEV123', 'integrity_check': True}
    )
    
    result = orchestrator.authenticate(context, factors)
    
    # Should require step-up (voice)
    assert result['decision'] == 'STEP_UP'
```

### Integration Tests

```python
import requests

def test_api_authentication():
    response = requests.post(
        'http://localhost:8000/api/authenticate',
        json={
            'transaction_id': 'TEST001',
            'customer_id': 'CUST123',
            'amount_usd': 15000,
            'channel': 'wire_transfer',
            'device_info': {
                'device_id': 'DEV456',
                'integrity_check': True
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'decision' in data
    assert 'risk_score' in data
```

### Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 -T 'application/json' \
   -p test_request.json \
   http://localhost:8000/api/authenticate

# Using locust
locust -f load_test.py --host=http://localhost:8000
```

---

## Support & Troubleshooting

### Common Issues

1. **Authentication always returns DECLINE**
   - Check that you're providing at least 2 factors
   - Verify device trust score is above threshold
   - Check logs for specific failure reasons

2. **SAR generation fails**
   - Ensure all required fields in SARContext are provided
   - Check date formats (must be ISO 8601)
   - Verify transactions array is not empty

3. **High latency**
   - Consider caching device trust scores
   - Use async/background processing for non-critical operations
   - Enable connection pooling for database queries

### Logging

Enable detailed logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set specific logger levels
logging.getLogger('backend.authentication').setLevel(logging.DEBUG)
```

---

## Next Steps

1. Review the [API Documentation](API.md) for detailed endpoint specifications
2. Check the [Configuration Guide](backend/config/settings.yaml) for all available options
3. Explore the [example implementations](examples/) for your use case
4. Set up monitoring and alerting for production deployments

For questions or support, contact the development team.
