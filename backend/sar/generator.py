"""
SAR Generator - Automated Suspicious Activity Report generation
Uses Jinja2 templates to generate SAR narratives from context data
"""

from jinja2 import Environment, FileSystemLoader
from .models import SARContext
from pathlib import Path
from typing import Dict


class SARGenerator:
    """Automated Suspicious Activity Report generation."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
    
    def generate_sar(self, context: SARContext) -> str:
        """Generate SAR narrative from context."""
        template = self.env.get_template("sar_narrative.j2")
        narrative = template.render(**context.model_dump())
        return narrative
    
    def validate_sar_quality(self, sar_narrative: str) -> Dict:
        """Validate SAR completeness and quality."""
        issues = []
        
        # Check length
        if len(sar_narrative) < 200:
            issues.append("Narrative too brief (min 200 characters)")
        
        # Check for key terms
        required_terms = ['suspicious', 'transaction', 'customer']
        for term in required_terms:
            if term.lower() not in sar_narrative.lower():
                issues.append(f"Missing required term: {term}")
        
        quality_score = max(0.0, 1.0 - (len(issues) * 0.2))
        
        return {
            'quality_score': quality_score,
            'issues': issues,
            'ready_for_filing': len(issues) == 0
        }
