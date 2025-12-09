#!/usr/bin/env python3
"""
Calibration Tool for Sonotheia x Incode Integration
Validates thresholds and generates baseline performance metrics
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import random

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))


class CalibrationTool:
    """Tool for calibrating detection thresholds and validating integration"""
    
    def __init__(self):
        self.results = []
        
    def generate_test_profiles(self, count: int = 20) -> List[Dict[str, Any]]:
        """Generate test profiles for calibration"""
        profiles = []
        
        # Generate legitimate users (60%)
        for i in range(int(count * 0.6)):
            profile = {
                "user_id": f"CAL-GOOD-{i:03d}",
                "scenario": "legitimate_user",
                "biometric_data": {
                    "document_verified": True,
                    "face_match_score": random.uniform(0.90, 0.98),
                    "liveness_passed": True,
                    "incode_session_id": f"incode-good-{i}"
                },
                "voice_data": {
                    "deepfake_score": random.uniform(0.05, 0.25),
                    "speaker_verified": True,
                    "speaker_score": random.uniform(0.88, 0.98),
                    "audio_quality": random.uniform(0.80, 0.95),
                    "audio_duration_seconds": random.uniform(3.0, 6.0)
                },
                "ground_truth": "legitimate",
                "expected_decision": "APPROVE"
            }
            profiles.append(profile)
        
        # Generate suspicious users (25%)
        for i in range(int(count * 0.25)):
            profile = {
                "user_id": f"CAL-SUSPICIOUS-{i:03d}",
                "scenario": "potential_deepfake",
                "biometric_data": {
                    "document_verified": True,
                    "face_match_score": random.uniform(0.82, 0.92),
                    "liveness_passed": True,
                    "incode_session_id": f"incode-suspicious-{i}"
                },
                "voice_data": {
                    "deepfake_score": random.uniform(0.45, 0.85),
                    "speaker_verified": False,
                    "speaker_score": random.uniform(0.60, 0.80),
                    "audio_quality": random.uniform(0.70, 0.85),
                    "audio_duration_seconds": random.uniform(3.0, 6.0)
                },
                "ground_truth": "deepfake",
                "expected_decision": "ESCALATE"
            }
            profiles.append(profile)
        
        # Generate edge cases (15%)
        for i in range(int(count * 0.15)):
            profile = {
                "user_id": f"CAL-EDGE-{i:03d}",
                "scenario": "edge_case",
                "biometric_data": {
                    "document_verified": True,
                    "face_match_score": random.uniform(0.85, 0.92),
                    "liveness_passed": True,
                    "incode_session_id": f"incode-edge-{i}"
                },
                "voice_data": {
                    "deepfake_score": random.uniform(0.25, 0.40),
                    "speaker_verified": True,
                    "speaker_score": random.uniform(0.80, 0.88),
                    "audio_quality": random.uniform(0.65, 0.80),
                    "audio_duration_seconds": random.uniform(2.5, 5.0)
                },
                "ground_truth": "legitimate",
                "expected_decision": "APPROVE"
            }
            profiles.append(profile)
        
        return profiles
    
    def calculate_composite_risk(
        self,
        biometric_data: Dict[str, Any],
        voice_data: Dict[str, Any],
        weights: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Calculate composite risk score with robust decision logic.

        Decision Architecture:
        1. PROSECUTION VETO: High voice risk (>0.6) triggers ESCALATE regardless of biometric
        2. DUAL-FACTOR: Otherwise use weighted composite with appropriate thresholds
        3. CONSISTENT THRESHOLDS: Aligned with RiskEngine and FusionEngine
        """
        if weights is None:
            # Voice risk is weighted higher as it's the primary fraud indicator
            weights = {"biometric": 0.3, "voice": 0.7}

        # Calculate biometric risk
        biometric_risk = 0.0
        if not biometric_data.get("document_verified"):
            biometric_risk += 0.4
        if not biometric_data.get("liveness_passed"):
            biometric_risk += 0.3
        face_score = biometric_data.get("face_match_score", 0)
        if face_score < 0.8:
            biometric_risk += (1.0 - face_score) * 0.3
        biometric_risk = min(biometric_risk, 1.0)

        # Calculate voice risk (primary deepfake indicator)
        voice_risk = voice_data.get("deepfake_score", 0)
        if not voice_data.get("speaker_verified"):
            voice_risk += 0.2
        speaker_score = voice_data.get("speaker_score", 0)
        if speaker_score < 0.8:
            voice_risk += (1.0 - speaker_score) * 0.2
        voice_risk = min(voice_risk, 1.0)

        # =====================================================
        # PROSECUTION VETO: Voice deepfake detection has veto power
        # If voice_risk is high, ESCALATE regardless of biometric score
        # This prevents the 50/50 dilution from letting deepfakes through
        # =====================================================
        VOICE_VETO_THRESHOLD = 0.6  # High confidence deepfake indicator
        prosecution_veto = voice_risk >= VOICE_VETO_THRESHOLD

        # Composite risk calculation
        # Using weighted average, but voice is weighted higher
        composite_risk = (
            biometric_risk * weights["biometric"] +
            voice_risk * weights["voice"]
        )

        # =====================================================
        # DECISION LOGIC (consistent with RiskEngine thresholds)
        # =====================================================
        # Thresholds aligned with backend/risk_engine/factors.py:
        # - LOW: < 0.3 → APPROVE
        # - MEDIUM: 0.3-0.5 → APPROVE (with caution)
        # - HIGH: 0.5-0.7 → ESCALATE
        # - CRITICAL: >= 0.7 → ESCALATE (mandatory)

        if prosecution_veto:
            # Voice deepfake veto overrides composite calculation
            decision = "ESCALATE"
            risk_level = "HIGH" if voice_risk < 0.8 else "CRITICAL"
        elif composite_risk < 0.3:
            decision = "APPROVE"
            risk_level = "LOW"
        elif composite_risk < 0.5:
            # CHANGED: Lower medium threshold for more cautious approval
            # Only approve if voice_risk is also reasonably low
            if voice_risk < 0.4:
                decision = "APPROVE"
                risk_level = "MEDIUM"
            else:
                decision = "ESCALATE"
                risk_level = "MEDIUM"
        elif composite_risk < 0.7:
            decision = "ESCALATE"
            risk_level = "HIGH"
        else:
            decision = "ESCALATE"
            risk_level = "CRITICAL"

        return {
            "composite_risk_score": composite_risk,
            "biometric_risk": biometric_risk,
            "voice_risk": voice_risk,
            "decision": decision,
            "risk_level": risk_level,
            "prosecution_veto": prosecution_veto  # Track if veto was applied
        }
    
    def evaluate_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single profile and compare to expected outcome"""
        result = self.calculate_composite_risk(
            profile["biometric_data"],
            profile["voice_data"]
        )
        
        # Compare to ground truth
        correct_decision = result["decision"] == profile["expected_decision"]
        
        return {
            "user_id": profile["user_id"],
            "scenario": profile["scenario"],
            "ground_truth": profile["ground_truth"],
            "expected_decision": profile["expected_decision"],
            "actual_decision": result["decision"],
            "correct": correct_decision,
            "composite_risk_score": result["composite_risk_score"],
            "risk_level": result["risk_level"],
            "biometric_risk": result["biometric_risk"],
            "voice_risk": result["voice_risk"]
        }
    
    def run_calibration(self, profile_count: int = 20) -> Dict[str, Any]:
        """Run full calibration suite"""
        print(f"\n{'='*60}")
        print("Sonotheia x Incode Integration Calibration")
        print(f"{'='*60}\n")
        
        # Generate test profiles
        print(f"Generating {profile_count} test profiles...")
        profiles = self.generate_test_profiles(profile_count)
        print(f"✓ Generated {len(profiles)} profiles\n")
        
        # Evaluate each profile
        print("Evaluating profiles...")
        results = []
        for profile in profiles:
            result = self.evaluate_profile(profile)
            results.append(result)
            self.results.append(result)
        
        # Calculate metrics
        total = len(results)
        correct = sum(1 for r in results if r["correct"])
        accuracy = correct / total if total > 0 else 0
        
        # Count by scenario
        legitimate_correct = sum(
            1 for r in results 
            if r["ground_truth"] == "legitimate" and r["correct"]
        )
        legitimate_total = sum(
            1 for r in results if r["ground_truth"] == "legitimate"
        )
        deepfake_correct = sum(
            1 for r in results 
            if r["ground_truth"] == "deepfake" and r["correct"]
        )
        deepfake_total = sum(
            1 for r in results if r["ground_truth"] == "deepfake"
        )
        
        # Decision distribution
        approvals = sum(1 for r in results if r["actual_decision"] == "APPROVE")
        escalations = sum(1 for r in results if r["actual_decision"] == "ESCALATE")
        
        # Risk score statistics
        risk_scores = [r["composite_risk_score"] for r in results]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        max_risk = max(risk_scores) if risk_scores else 0
        min_risk = min(risk_scores) if risk_scores else 0
        
        # Print summary
        print(f"\n{'='*60}")
        print("CALIBRATION RESULTS")
        print(f"{'='*60}\n")
        
        print(f"Overall Accuracy: {accuracy*100:.1f}% ({correct}/{total})")
        print("\nBy Scenario:")
        print(f"  Legitimate Users: {legitimate_correct}/{legitimate_total} " +
              f"({legitimate_correct/legitimate_total*100:.1f}% accuracy)")
        print(f"  Deepfake Detection: {deepfake_correct}/{deepfake_total} " +
              f"({deepfake_correct/deepfake_total*100:.1f}% accuracy)")
        
        print("\nDecision Distribution:")
        print(f"  APPROVE: {approvals} ({approvals/total*100:.1f}%)")
        print(f"  ESCALATE: {escalations} ({escalations/total*100:.1f}%)")
        
        print("\nRisk Score Statistics:")
        print(f"  Average: {avg_risk:.3f}")
        print(f"  Min: {min_risk:.3f}")
        print(f"  Max: {max_risk:.3f}")
        
        # Recommendations
        print(f"\n{'='*60}")
        print("RECOMMENDATIONS")
        print(f"{'='*60}\n")
        
        if accuracy >= 0.85:
            print("✓ Thresholds are well-calibrated")
        elif accuracy >= 0.75:
            print("⚠ Consider fine-tuning thresholds")
            print("  - Review edge cases with risk scores 0.25-0.35")
        else:
            print("✗ Thresholds need adjustment")
            print("  - Consider lowering deepfake_threshold to 0.25")
            print("  - Consider raising speaker_threshold to 0.88")
        
        if legitimate_correct / legitimate_total < 0.90:
            print("\n⚠ High false positive rate on legitimate users")
            print("  - Consider increasing deepfake_threshold to 0.35")
        
        if deepfake_correct / deepfake_total < 0.85:
            print("\n⚠ Missing deepfakes")
            print("  - Consider decreasing deepfake_threshold to 0.25")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"calibration_results_{timestamp}.json"
        
        full_results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_profiles": total,
                "accuracy": accuracy,
                "legitimate_accuracy": legitimate_correct / legitimate_total if legitimate_total > 0 else 0,
                "deepfake_detection_rate": deepfake_correct / deepfake_total if deepfake_total > 0 else 0,
                "approval_rate": approvals / total if total > 0 else 0,
                "escalation_rate": escalations / total if total > 0 else 0,
                "avg_risk_score": avg_risk
            },
            "profiles": results
        }
        
        with open(output_file, 'w') as f:
            json.dump(full_results, f, indent=2)
        
        print(f"\n✓ Results saved to: {output_file}")
        print(f"{'='*60}\n")
        
        return full_results


def main():
    """Main calibration function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Calibrate Sonotheia x Incode integration thresholds"
    )
    parser.add_argument(
        '--profiles',
        type=int,
        default=20,
        help='Number of test profiles to generate (default: 20)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for results (default: auto-generated)'
    )
    
    args = parser.parse_args()
    
    # Run calibration
    tool = CalibrationTool()
    results = tool.run_calibration(profile_count=args.profiles)
    
    # Show next steps
    print("NEXT STEPS:")
    print("1. Review calibration_results_*.json for detailed analysis")
    print("2. Adjust thresholds in backend/config/settings.yaml if needed")
    print("3. Run again with --profiles 100 for production validation")
    print("4. Test with real audio samples for final verification\n")


if __name__ == "__main__":
    main()
