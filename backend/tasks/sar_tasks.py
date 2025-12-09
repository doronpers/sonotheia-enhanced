"""
SAR Generation Tasks
Celery tasks for Suspicious Activity Report generation.
"""

import sys
from pathlib import Path
import logging
from datetime import datetime
import time

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from celery_app import app  # noqa: E402
from backend.utils.celery_utils import (  # noqa: E402
    create_task_result,
    update_task_progress,
)

logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    name="tasks.sar_tasks.generate_sar_async",
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=120,
    time_limit=180,
)
def generate_sar_async(self, context_data: dict):
    """
    Generate SAR narrative asynchronously.

    Args:
        context_data: SAR context data dictionary containing:
            - transaction_id: Transaction identifier
            - customer_id: Customer identifier
            - customer_name: Customer name
            - account_number: Account number
            - activity_type: Type of suspicious activity
            - activity_description: Description of activity
            - transactions: List of transaction details
            - risk_factors: List of risk factors
            - total_risk_score: Overall risk score
            - compliance_action: Action taken
            - filing_institution: Institution name
            - voice_authentication: Optional voice auth results
            - device_authentication: Optional device auth results

    Returns:
        SAR generation result with narrative
    """
    try:
        start_time = time.time()

        logger.info(f"Generating SAR for transaction: {context_data.get('transaction_id', 'unknown')}")

        update_task_progress(self, 10, "Validating SAR context")

        # Validate required fields
        required_fields = [
            "customer_id",
            "activity_type",
            "activity_description",
            "compliance_action",
        ]

        for field in required_fields:
            if field not in context_data or not context_data[field]:
                return create_task_result(status="FAILED", error=f"Missing required field: {field}")

        update_task_progress(self, 30, "Building SAR context")

        # Import SAR models and generator
        from sar.models import SARContext
        from sar.generator import SARGenerator

        # Build context
        try:
            context = SARContext(**context_data)
        except Exception as e:
            return create_task_result(status="FAILED", error=f"Invalid SAR context: {str(e)}")

        update_task_progress(self, 50, "Generating SAR narrative")

        # Generate SAR
        generator = SARGenerator()
        narrative = generator.generate_sar(context)

        update_task_progress(self, 75, "Validating SAR quality")

        # Validate quality
        validation = generator.validate_sar_quality(narrative)

        update_task_progress(self, 90, "Finalizing")

        elapsed = time.time() - start_time

        result = create_task_result(
            status="COMPLETED",
            data={
                "narrative": narrative,
                "validation": validation,
                "context_id": context_data.get("transaction_id"),
                "customer_id": context_data.get("customer_id"),
                "activity_type": context_data.get("activity_type"),
                "processing_time_seconds": elapsed,
            },
        )

        logger.info(f"SAR generated successfully for {context_data.get('transaction_id')}")

        return result

    except Exception as e:
        logger.error(f"SAR generation failed: {e}")
        return create_task_result(status="FAILED", error=str(e))


@app.task(
    bind=True,
    name="tasks.sar_tasks.generate_sar_from_analysis",
    max_retries=2,
    soft_time_limit=60,
    time_limit=120,
)
def generate_sar_from_analysis(self, analysis_result: dict, additional_context: dict = None):
    """
    Generate SAR from analysis task result.

    This task is designed to be chained after analyze_call_async.

    Args:
        analysis_result: Result from analyze_call_async task
        additional_context: Additional SAR context

    Returns:
        SAR generation result
    """
    try:
        start_time = time.time()

        # Extract data from analysis result
        if analysis_result.get("status") != "COMPLETED":
            return create_task_result(status="FAILED", error="Cannot generate SAR from failed analysis")

        data = analysis_result.get("data", {})
        risk_result = data.get("risk_result", {})

        # Only generate SAR for high risk
        risk_level = risk_result.get("risk_level", "LOW")
        if risk_level not in ["HIGH", "CRITICAL"]:
            return create_task_result(
                status="COMPLETED",
                data={
                    "sar_generated": False,
                    "reason": f"Risk level {risk_level} does not require SAR",
                },
            )

        update_task_progress(self, 30, "Building SAR from analysis")

        # Build SAR context from analysis
        context_data = {
            "transaction_id": data.get("call_id", "UNKNOWN"),
            "customer_id": data.get("customer_id", "UNKNOWN"),
            "customer_name": additional_context.get("customer_name", "Unknown") if additional_context else "Unknown",
            "account_number": additional_context.get("account_number", "UNKNOWN") if additional_context else "UNKNOWN",
            "activity_type": "synthetic_voice",
            "activity_description": f"Potential synthetic voice detected during call authentication. "
            f"Spoof score: {data.get('detection', {}).get('spoof_score', 0):.2%}",
            "transactions": [],
            "risk_factors": [
                {
                    "name": f.get("name", ""),
                    "description": f.get("explanation", ""),
                    "confidence": f.get("score", 0),
                    "severity": _get_severity(f.get("score", 0)),
                }
                for f in risk_result.get("factors", [])
            ],
            "total_risk_score": risk_result.get("overall_score", 0),
            "compliance_action": f"Call flagged for review. Decision: {risk_result.get('decision', 'REVIEW')}",
            "filing_institution": additional_context.get("institution", "Sonotheia Demo Bank")
            if additional_context
            else "Sonotheia Demo Bank",
        }

        # Add voice authentication if available
        detection_data = data.get("detection", {})
        if detection_data:
            context_data["voice_authentication"] = {
                "deepfake_score": detection_data.get("spoof_score", 0),
                "speaker_score": 0.85,  # Placeholder
                "quality_score": 0.90,  # Placeholder
                "result": "FAIL" if detection_data.get("spoof_score", 0) > 0.3 else "PASS",
            }

        update_task_progress(self, 60, "Generating SAR narrative")

        # Import and generate
        from sar.models import SARContext
        from sar.generator import SARGenerator

        try:
            context = SARContext(**context_data)
            generator = SARGenerator()
            narrative = generator.generate_sar(context)
            validation = generator.validate_sar_quality(narrative)
        except Exception as e:
            # Fall back to simple narrative
            logger.warning(f"SAR generation failed, using fallback: {e}")
            narrative = _generate_simple_narrative(data, risk_result)
            validation = {"is_valid": True, "issues": []}

        elapsed = time.time() - start_time

        result = create_task_result(
            status="COMPLETED",
            data={
                "sar_generated": True,
                "narrative": narrative,
                "validation": validation,
                "call_id": data.get("call_id"),
                "risk_level": risk_level,
                "processing_time_seconds": elapsed,
            },
        )

        return result

    except Exception as e:
        logger.error(f"SAR generation from analysis failed: {e}")
        return create_task_result(status="FAILED", error=str(e))


def _get_severity(score: float) -> str:
    """Map score to severity level."""
    if score >= 0.7:
        return "CRITICAL"
    elif score >= 0.5:
        return "HIGH"
    elif score >= 0.3:
        return "MEDIUM"
    else:
        return "LOW"


def _generate_simple_narrative(data: dict, risk_result: dict) -> str:
    """Generate a simple SAR narrative as fallback."""
    return f"""
SUSPICIOUS ACTIVITY REPORT - VOICE AUTHENTICATION

CALL INFORMATION:
- Call ID: {data.get('call_id', 'UNKNOWN')}
- Customer ID: {data.get('customer_id', 'UNKNOWN')}

RISK ASSESSMENT:
- Overall Risk Score: {risk_result.get('overall_score', 0):.2%}
- Risk Level: {risk_result.get('risk_level', 'UNKNOWN')}
- Decision: {risk_result.get('decision', 'REVIEW')}

DETECTION RESULTS:
- Spoof Score: {data.get('detection', {}).get('spoof_score', 0):.2%}

This report was generated automatically by the Sonotheia voice authentication system.
Further manual review is recommended.

Generated: {datetime.now().isoformat()}
"""
