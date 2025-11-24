"""
SAR Generator - Automated Suspicious Activity Report generation
Uses Jinja2 templates to generate SAR narratives from context data
"""

from jinja2 import Environment, FileSystemLoader
from .models import SARContext, SARReport, RiskIntelligence, KnownScheme
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import uuid


class SARGenerator:
    """Automated Suspicious Activity Report generation with intelligence features."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
        # In-memory storage for demo (use database in production)
        self._reports = {}
    
    def generate_sar(self, context: SARContext) -> str:
        """Generate SAR narrative from context."""
        # Enhance context with intelligence if not provided
        if not context.risk_intelligence:
            context.risk_intelligence = self._generate_risk_intelligence(context)
        
        template = self.env.get_template("sar_narrative.j2")
        narrative = template.render(**context.dict())
        return narrative
    
    def create_sar_report(self, context: SARContext) -> SARReport:
        """Create a complete SAR report with metadata."""
        narrative = self.generate_sar(context)
        validation = self.validate_sar_quality(narrative)
        
        sar_id = f"SAR-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        report = SARReport(
            sar_id=sar_id,
            context=context,
            narrative=narrative,
            quality_score=validation['quality_score'],
            ready_for_filing=validation['ready_for_filing']
        )
        
        # Store report
        self._reports[sar_id] = report
        
        return report
    
    def get_report(self, sar_id: str) -> SARReport:
        """Retrieve a SAR report by ID."""
        return self._reports.get(sar_id)
    
    def list_reports(self, status: str = None, limit: int = 100) -> List[SARReport]:
        """List SAR reports with optional filtering."""
        reports = list(self._reports.values())
        
        if status:
            reports = [r for r in reports if r.context.filing_status.value == status]
        
        # Sort by creation date, newest first
        reports.sort(key=lambda r: r.generated_at, reverse=True)
        
        return reports[:limit]
    
    def validate_sar_quality(self, sar_narrative: str) -> Dict:
        """Validate SAR completeness and quality."""
        issues = []
        
        # Check length
        if len(sar_narrative) < 500:
            issues.append("Narrative too brief (min 500 characters recommended)")
        
        # Check for key sections
        required_sections = [
            'SUBJECT INFORMATION',
            'SUSPICIOUS ACTIVITY SUMMARY',
            'TRANSACTION DETAILS',
            'RED FLAGS'
        ]
        for section in required_sections:
            if section not in sar_narrative:
                issues.append(f"Missing required section: {section}")
        
        # Check for key terms
        required_terms = ['suspicious', 'transaction', 'customer', 'activity']
        missing_terms = []
        for term in required_terms:
            if term.lower() not in sar_narrative.lower():
                missing_terms.append(term)
        
        if missing_terms:
            issues.append(f"Missing key terms: {', '.join(missing_terms)}")
        
        # Calculate quality score
        quality_score = max(0.0, 1.0 - (len(issues) * 0.15))
        
        return {
            'quality_score': quality_score,
            'issues': issues,
            'ready_for_filing': len(issues) == 0 and quality_score >= 0.8
        }
    
    def _generate_risk_intelligence(self, context: SARContext) -> RiskIntelligence:
        """Generate risk intelligence analysis from transaction data."""
        # Analyze transaction patterns
        pattern_analysis = self._analyze_patterns(context)
        
        # Calculate risk score based on multiple factors
        risk_score = self._calculate_risk_score(context, pattern_analysis)
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "CRITICAL"
        elif risk_score >= 0.5:
            risk_level = "HIGH"
        elif risk_score >= 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Identify behavioral anomalies
        behavioral_anomalies = self._identify_behavioral_anomalies(context)
        
        # Analyze temporal patterns
        temporal_patterns = self._analyze_temporal_patterns(context)
        
        # Identify geographic risks
        geographic_risks = self._identify_geographic_risks(context)
        
        return RiskIntelligence(
            overall_risk_score=risk_score,
            risk_level=risk_level,
            pattern_analysis=pattern_analysis,
            behavioral_anomalies=behavioral_anomalies,
            temporal_patterns=temporal_patterns,
            geographic_risks=geographic_risks,
            related_entities=[],
            similarity_to_known_schemes=self._match_known_schemes(context)
        )
    
    def _calculate_risk_score(self, context: SARContext, pattern_analysis: Dict) -> float:
        """Calculate overall risk score."""
        risk_factors = []
        
        # Transaction volume risk
        if context.count > 10:
            risk_factors.append(0.3)
        elif context.count > 5:
            risk_factors.append(0.2)
        
        # Amount risk
        if context.amount > 100000:
            risk_factors.append(0.3)
        elif context.amount > 50000:
            risk_factors.append(0.2)
        
        # Pattern risk
        if 'structuring' in context.pattern.lower():
            risk_factors.append(0.4)
        elif 'rapid' in context.pattern.lower():
            risk_factors.append(0.3)
        
        # Red flags count
        red_flag_risk = min(len(context.red_flags) * 0.1, 0.4)
        risk_factors.append(red_flag_risk)
        
        # Average the risk factors
        return min(sum(risk_factors) / max(len(risk_factors), 1), 1.0)
    
    def _analyze_patterns(self, context: SARContext) -> Dict:
        """Analyze transaction patterns."""
        transactions = context.transactions
        
        if not transactions:
            return {}
        
        amounts = [tx.amount for tx in transactions]
        dates = [tx.date for tx in transactions]
        
        return {
            'avg_transaction_amount': sum(amounts) / len(amounts),
            'max_transaction_amount': max(amounts),
            'min_transaction_amount': min(amounts),
            'transaction_frequency': len(transactions) / max((dates[-1] - dates[0]).days, 1),
            'unique_destinations': len(set(tx.destination for tx in transactions if tx.destination))
        }
    
    def _identify_behavioral_anomalies(self, context: SARContext) -> List[str]:
        """Identify behavioral anomalies in transaction patterns."""
        anomalies = []
        
        transactions = context.transactions
        if not transactions:
            return anomalies
        
        amounts = [tx.amount for tx in transactions]
        
        # Check for amounts just below reporting threshold
        threshold_dodging = [amt for amt in amounts if 9000 <= amt < 10000]
        if len(threshold_dodging) >= 2:
            anomalies.append(f"Multiple transactions ({len(threshold_dodging)}) just below $10,000 reporting threshold")
        
        # Check for rapid succession
        if context.count >= 3:
            dates = sorted([tx.date for tx in transactions])
            if len(dates) >= 2 and (dates[-1] - dates[0]).days <= 7:
                anomalies.append(f"{context.count} transactions within {(dates[-1] - dates[0]).days} days indicates rapid activity")
        
        # Check for round amounts (potential structuring)
        round_amounts = [amt for amt in amounts if amt % 1000 == 0]
        if len(round_amounts) >= 3:
            anomalies.append(f"{len(round_amounts)} transactions with round amounts (possible deliberate structuring)")
        
        return anomalies
    
    def _analyze_temporal_patterns(self, context: SARContext) -> List[str]:
        """Analyze temporal patterns in transactions."""
        patterns = []
        
        transactions = context.transactions
        if not transactions or len(transactions) < 2:
            return patterns
        
        # Check for weekend/holiday activity
        weekend_txs = [tx for tx in transactions if tx.date.weekday() >= 5]
        if len(weekend_txs) >= 2:
            patterns.append(f"{len(weekend_txs)} transactions on weekends (unusual for business accounts)")
        
        # Check for consistent intervals
        dates = sorted([tx.date for tx in transactions])
        intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        if len(set(intervals)) <= 2 and len(intervals) >= 2:
            patterns.append(f"Regular transaction intervals detected (every {intervals[0]}-{max(intervals)} days)")
        
        return patterns
    
    def _identify_geographic_risks(self, context: SARContext) -> List[str]:
        """Identify geographic risk factors."""
        risks = []
        
        # High-risk countries (simplified list for demo)
        high_risk_countries = ['iran', 'north korea', 'syria', 'offshore']
        
        destinations = [tx.destination.lower() for tx in context.transactions if tx.destination]
        
        for country in high_risk_countries:
            if any(country in dest for dest in destinations):
                risks.append(f"Transactions to high-risk jurisdiction: {country.title()}")
        
        # Multiple international destinations
        international_dests = [d for d in destinations if any(x in d for x in ['international', 'foreign', 'overseas'])]
        if len(international_dests) >= 2:
            risks.append(f"Multiple international destinations ({len(international_dests)} transactions)")
        
        return risks
    
    def _match_known_schemes(self, context: SARContext) -> List[KnownScheme]:
        """Match transaction patterns to known fraud schemes."""
        schemes = []
        
        # Known scheme patterns (simplified for demo)
        if 'structuring' in context.pattern.lower():
            schemes.append(KnownScheme(
                name='Currency Transaction Structuring (Smurfing)',
                similarity_score=0.85,
                description='Breaking large amounts into smaller transactions to avoid reporting'
            ))
        
        if 'layering' in context.pattern.lower():
            schemes.append(KnownScheme(
                name='Money Laundering - Layering',
                similarity_score=0.78,
                description='Complex layers of financial transactions to obscure source'
            ))
        
        if any('rapid' in flag.lower() for flag in context.red_flags):
            schemes.append(KnownScheme(
                name='Rapid Movement of Funds',
                similarity_score=0.72,
                description='Quick movement of funds typical of fraud or laundering'
            ))
        
        return schemes
