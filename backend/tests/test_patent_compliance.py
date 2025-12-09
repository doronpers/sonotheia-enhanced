"""
Patent Compliance Test Suite

Automated tests to ensure Sonotheia sensors do not infringe on Pindrop's
Source-Filter Model patents by verifying:
1. No LPC usage
2. No residual analysis
3. No glottal closure/opening detection
4. Compliance documentation exists
"""

import re
import pytest
from pathlib import Path


class TestPatentCompliance:
    """Test suite for patent compliance verification."""
    
    BACKEND_DIR = Path(__file__).parent.parent
    SENSORS_DIR = BACKEND_DIR / "sensors"
    DOCS_DIR = BACKEND_DIR.parent / "Documentation"
    
    # Prohibited patterns that indicate potential patent infringement
    PROHIBITED_PATTERNS = [
        (r'librosa\.lpc', "librosa.lpc() - LPC usage"),
        (r'scipy\.signal\.lpc', "scipy.signal.lpc() - LPC usage"),
        (r'LPC\s+residual', "LPC residual analysis"),
        (r'residual\s+error', "Residual error signal"),
        (r'glottal\s+closure', "Glottal closure detection"),
        (r'glottal\s+opening', "Glottal opening detection"),
        (r'GCI', "Glottal Closure Instance"),
        (r'GOI', "Glottal Opening Instance"),
        (r'source.*filter.*model', "Source-Filter Model terminology"),
    ]
    
    def test_no_lpc_in_formant_trajectory(self):
        """Verify formant_trajectory.py does not use LPC."""
        sensor_file = self.SENSORS_DIR / "formant_trajectory.py"
        
        assert sensor_file.exists(), f"formant_trajectory.py not found at {sensor_file}"
        
        with open(sensor_file, 'r') as f:
            content = f.read()
        
        # Check for prohibited patterns
        for pattern, description in self.PROHIBITED_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            assert len(matches) == 0, \
                f"Found prohibited pattern '{description}' in formant_trajectory.py: {matches}"
    
    def test_no_lpc_in_phase_coherence(self):
        """Verify phase_coherence.py does not use LPC."""
        sensor_file = self.SENSORS_DIR / "phase_coherence.py"
        
        assert sensor_file.exists(), "phase_coherence.py not found"
        
        with open(sensor_file, 'r') as f:
            content = f.read()
        
        # Check for prohibited patterns
        for pattern, description in self.PROHIBITED_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            assert len(matches) == 0, \
                f"Found prohibited pattern '{description}' in phase_coherence.py: {matches}"
    
    def test_no_lpc_in_coarticulation(self):
        """Verify coarticulation.py does not use LPC."""
        sensor_file = self.SENSORS_DIR / "coarticulation.py"
        
        assert sensor_file.exists(), "coarticulation.py not found"
        
        with open(sensor_file, 'r') as f:
            content = f.read()
        
        # Check for prohibited patterns
        for pattern, description in self.PROHIBITED_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            assert len(matches) == 0, \
                f"Found prohibited pattern '{description}' in coarticulation.py: {matches}"
    
    def test_no_lpc_in_all_sensors(self):
        """Scan all sensor files for prohibited LPC usage."""
        if not self.SENSORS_DIR.exists():
            pytest.skip(f"Sensors directory not found: {self.SENSORS_DIR}")
        
        violations = []
        
        for sensor_file in self.SENSORS_DIR.glob("*.py"):
            # Skip __init__.py and non-sensor files
            if sensor_file.name.startswith('__') or sensor_file.name in ['base.py', 'registry.py', 'utils.py', 'fusion.py']:
                continue
            
            with open(sensor_file, 'r') as f:
                content = f.read()
            
            # Check for prohibited patterns
            for pattern, description in self.PROHIBITED_PATTERNS:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    violations.append({
                        'file': sensor_file.name,
                        'pattern': description,
                        'matches': matches
                    })
        
        # Build error message if violations found
        if violations:
            error_msg = "Patent compliance violations detected:\n"
            for v in violations:
                error_msg += f"\n  {v['file']}: {v['pattern']}\n"
                error_msg += f"    Matches: {v['matches']}\n"
            pytest.fail(error_msg)
    
    def test_vocal_tract_py_deleted_or_renamed(self):
        """Verify old vocal_tract.py (LPC-based) is removed or renamed."""
        old_file = self.SENSORS_DIR / "vocal_tract.py"
        
        # If file exists, it should NOT contain LPC usage
        if old_file.exists():
            with open(old_file, 'r') as f:
                content = f.read()
            
            # Check if it still uses LPC
            lpc_patterns = [r'librosa\.lpc', r'scipy\.signal\.lpc', r'LPC.*coefficient']
            for pattern in lpc_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    pytest.fail(
                        f"vocal_tract.py still exists and contains LPC usage: {matches}\n"
                        f"This file should be deleted or replaced with formant_trajectory.py"
                    )
    
    def test_formant_trajectory_exists(self):
        """Verify new formant_trajectory.py sensor exists."""
        new_sensor = self.SENSORS_DIR / "formant_trajectory.py"
        assert new_sensor.exists(), \
            "formant_trajectory.py not found - patent-safe sensor not implemented"
    
    def test_formant_trajectory_uses_velocities(self):
        """Verify formant_trajectory.py analyzes velocities (not static values)."""
        sensor_file = self.SENSORS_DIR / "formant_trajectory.py"
        
        with open(sensor_file, 'r') as f:
            content = f.read()
        
        # Should contain velocity-related terms
        required_terms = [
            r'velocity',
            r'trajectory',
            r'Hz.*per.*10ms',  # Velocity units
        ]
        
        for term in required_terms:
            assert re.search(term, content, re.IGNORECASE), \
                f"formant_trajectory.py missing expected term: '{term}'"
    
    def test_phase_coherence_uses_entropy(self):
        """Verify phase_coherence.py uses entropy analysis."""
        sensor_file = self.SENSORS_DIR / "phase_coherence.py"
        
        with open(sensor_file, 'r') as f:
            content = f.read()
        
        # Should contain entropy-related terms
        required_terms = [
            r'entropy',
            r'instantaneous.*frequency',
            r'phase.*derivative',
        ]
        
        for term in required_terms:
            assert re.search(term, content, re.IGNORECASE), \
                f"phase_coherence.py missing expected term: '{term}'"
    
    def test_patent_compliance_doc_exists(self):
        """Verify PATENT_COMPLIANCE.md documentation exists."""
        doc_file = self.DOCS_DIR / "PATENT_COMPLIANCE.md"
        assert doc_file.exists(), \
            "PATENT_COMPLIANCE.md not found in Documentation/"
    
    def test_patent_compliance_doc_complete(self):
        """Verify PATENT_COMPLIANCE.md covers key topics."""
        doc_file = self.DOCS_DIR / "PATENT_COMPLIANCE.md"
        
        if not doc_file.exists():
            pytest.skip("PATENT_COMPLIANCE.md not found")
        
        with open(doc_file, 'r') as f:
            content = f.read()
        
        # Required sections
        required_sections = [
            r'Pindrop.*Patent',
            r'Design.*Around',
            r'Freedom.*to.*Operate',
            r'FormantTrajectory',
            r'PhaseCoherence',
            r'Coarticulation',
        ]
        
        for section in required_sections:
            assert re.search(section, content, re.IGNORECASE), \
                f"PATENT_COMPLIANCE.md missing section: '{section}'"
    
    def test_fusion_weights_updated(self):
        """Verify fusion.py uses patent-safe sensor set."""
        fusion_file = self.SENSORS_DIR / "fusion.py"
        
        with open(fusion_file, 'r') as f:
            content = f.read()
        
        # Should reference new sensors
        assert re.search(r'FormantTrajectory', content), \
            "fusion.py does not reference FormantTrajectory sensor"
        
        # Should NOT reference deprecated sensors
        deprecated_patterns = [
            r'"BreathSensor":\s*0\.[0-9]+',  # Active weight
            r'"VocalTractSensor":\s*0\.[0-9]+',  # Active weight (should be commented)
        ]
        
        for pattern in deprecated_patterns:
            matches = re.findall(pattern, content)
            # Allow commented-out references
            if matches:
                for match in matches:
                    # Find context lines
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if match in line and not line.strip().startswith('#'):
                            pytest.fail(
                                f"fusion.py contains active (non-commented) deprecated sensor weight: {match}"
                            )


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
