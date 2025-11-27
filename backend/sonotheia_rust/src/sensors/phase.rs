//! Phase Sensor - Multi-Phase Coherence (MPC) Detection
//!
//! Detects synthetic audio by analyzing phase relationships in the spectrum.
//! Real audio has natural phase patterns, while synthetic audio often exhibits
//! unnaturally coherent or incoherent phase relationships.

use numpy::PyReadonlyArray1;
use pyo3::prelude::*;

use crate::sensors::result::SensorResult;
use crate::utils::audio::{apply_hamming_window, calculate_rms, frame_audio, validate_audio_input};
use crate::utils::fft::{compute_fft, phase_spectrum};

/// Default threshold for phase sensor pass/fail decision
const DEFAULT_THRESHOLD: f64 = 0.65;

/// Frame size in samples (32ms at 16kHz)
const FRAME_SIZE: usize = 512;

/// Hop size in samples (8ms at 16kHz)
const HOP_SIZE: usize = 128;

/// Phase Sensor for Multi-Phase Coherence detection
///
/// This sensor analyzes phase relationships across frequency bins and time frames.
/// Synthetic audio often exhibits:
///
/// - Unnaturally high phase coherence (from TTS systems)
/// - Abrupt phase discontinuities (from splicing/manipulation)
/// - Missing natural phase randomness
///
/// # Example
/// ```python
/// from sonotheia_rust import PhaseSensor
///
/// sensor = PhaseSensor()
/// result = sensor.analyze(audio_data, 16000)
/// print(f"Passed: {result.passed}, Score: {result.value}")
/// ```
#[pyclass]
#[derive(Debug, Clone)]
pub struct PhaseSensor {
    /// Detection threshold (0.0-1.0)
    #[pyo3(get, set)]
    pub threshold: f64,

    /// Sensor name identifier
    #[pyo3(get)]
    pub name: String,
}

#[pymethods]
impl PhaseSensor {
    /// Create a new PhaseSensor with optional threshold
    ///
    /// # Arguments
    /// * `threshold` - Detection threshold (0.0-1.0), default 0.65
    #[new]
    #[pyo3(signature = (threshold=None))]
    pub fn new(threshold: Option<f64>) -> Self {
        let threshold_value = threshold.unwrap_or(DEFAULT_THRESHOLD);
        let clamped_threshold = threshold_value.clamp(0.0, 1.0);

        Self {
            threshold: clamped_threshold,
            name: "phase_sensor".to_string(),
        }
    }

    /// Analyze audio data for phase coherence anomalies
    ///
    /// # Arguments
    /// * `audio` - Audio samples as numpy array (f64)
    /// * `sample_rate` - Sample rate in Hz
    ///
    /// # Returns
    /// SensorResult with pass/fail decision and analysis details
    pub fn analyze(
        &self,
        audio: PyReadonlyArray1<'_, f64>,
        sample_rate: u32,
    ) -> PyResult<SensorResult> {
        let audio_slice = audio.as_slice()?;

        // Validate input
        if let Err(e) = validate_audio_input(audio_slice, sample_rate) {
            return Ok(SensorResult::new(
                self.name.clone(),
                Some(false),
                0.0,
                self.threshold,
                Some("validation_error".to_string()),
                Some(format!("Input validation failed: {}", e)),
            ));
        }

        // Perform analysis
        let authenticity_score = self.compute_phase_coherence_score(audio_slice, sample_rate);

        // Determine pass/fail
        let passed = authenticity_score >= self.threshold;

        let detail = if passed {
            format!(
                "Phase coherence analysis passed (score: {:.2})",
                authenticity_score
            )
        } else {
            format!(
                "Abnormal phase patterns detected (score: {:.2})",
                authenticity_score
            )
        };

        Ok(SensorResult::new(
            self.name.clone(),
            Some(passed),
            authenticity_score,
            self.threshold,
            if !passed {
                Some("phase_anomaly".to_string())
            } else {
                None
            },
            Some(detail),
        ))
    }

    /// String representation for Python
    fn __repr__(&self) -> String {
        format!(
            "PhaseSensor(name='{}', threshold={})",
            self.name, self.threshold
        )
    }
}

impl PhaseSensor {
    /// Compute phase coherence authenticity score
    fn compute_phase_coherence_score(&self, audio: &[f64], sample_rate: u32) -> f64 {
        // Adjust frame parameters based on sample rate
        let frame_size = (sample_rate as usize * FRAME_SIZE) / 16000;
        let hop_size = (sample_rate as usize * HOP_SIZE) / 16000;

        // Frame the audio
        let frames = frame_audio(audio, frame_size, hop_size);

        if frames.len() < 2 {
            return 0.5; // Neutral score for insufficient data
        }

        // Pre-allocate phase spectra vector
        let mut phase_spectra: Vec<Vec<f64>> = Vec::with_capacity(frames.len());

        for frame in &frames {
            let windowed = apply_hamming_window(frame);
            let rms = calculate_rms(&windowed);

            // Skip silent frames
            if rms < 1e-6 {
                continue;
            }

            if let Ok(fft_result) = compute_fft(&windowed) {
                let phases = phase_spectrum(&fft_result);
                phase_spectra.push(phases);
            }
        }

        if phase_spectra.len() < 2 {
            return 0.5;
        }

        // Compute phase coherence metrics
        let coherence_score = self.compute_cross_frame_coherence(&phase_spectra);
        let derivative_score = self.compute_phase_derivative_score(&phase_spectra);
        let randomness_score = self.compute_phase_randomness_score(&phase_spectra);

        // Combined score
        let combined = 0.4 * coherence_score + 0.3 * derivative_score + 0.3 * randomness_score;

        combined.clamp(0.0, 1.0)
    }

    /// Compute cross-frame phase coherence
    ///
    /// High coherence across frames can indicate synthetic audio
    fn compute_cross_frame_coherence(&self, phase_spectra: &[Vec<f64>]) -> f64 {
        if phase_spectra.len() < 2 {
            return 0.5;
        }

        let mut coherence_values: Vec<f64> = Vec::new();

        // Compare adjacent frames
        for i in 1..phase_spectra.len() {
            let prev = &phase_spectra[i - 1];
            let curr = &phase_spectra[i];

            let min_len = prev.len().min(curr.len());
            if min_len < 10 {
                continue;
            }

            // Compute phase difference variance
            let phase_diffs: Vec<f64> = prev
                .iter()
                .take(min_len)
                .zip(curr.iter())
                .map(|(&p1, &p2)| self.wrap_phase(p2 - p1))
                .collect();

            // Variance of phase differences
            let mean_diff = phase_diffs.iter().sum::<f64>() / phase_diffs.len() as f64;
            let variance = phase_diffs
                .iter()
                .map(|&d| (d - mean_diff).powi(2))
                .sum::<f64>()
                / phase_diffs.len() as f64;

            // Lower variance = higher coherence (potentially synthetic)
            coherence_values.push(variance);
        }

        if coherence_values.is_empty() {
            return 0.5;
        }

        let mean_coherence = coherence_values.iter().sum::<f64>() / coherence_values.len() as f64;

        // Expected variance for natural speech is around 1-3
        // Very low variance (<0.5) suggests unnaturally coherent phases (synthetic)
        // Very high variance (>5) suggests random noise or heavy manipulation
        if mean_coherence < 0.3 {
            // Too coherent - likely synthetic
            (mean_coherence / 0.3).min(1.0) * 0.5
        } else if mean_coherence > 5.0 {
            // Too random - potentially manipulated
            (5.0 / mean_coherence).min(1.0) * 0.7
        } else {
            // Natural range
            1.0
        }
    }

    /// Compute phase derivative (instantaneous frequency) score
    fn compute_phase_derivative_score(&self, phase_spectra: &[Vec<f64>]) -> f64 {
        if phase_spectra.len() < 3 {
            return 0.5;
        }

        let mut continuity_scores: Vec<f64> = Vec::new();

        // Check phase continuity (second derivative)
        for i in 2..phase_spectra.len() {
            let prev2 = &phase_spectra[i - 2];
            let prev1 = &phase_spectra[i - 1];
            let curr = &phase_spectra[i];

            let min_len = prev2.len().min(prev1.len()).min(curr.len());
            if min_len < 10 {
                continue;
            }

            // Second derivative of phase (acceleration)
            let accelerations: Vec<f64> = (0..min_len)
                .map(|j| {
                    let d1 = self.wrap_phase(prev1[j] - prev2[j]);
                    let d2 = self.wrap_phase(curr[j] - prev1[j]);
                    (d2 - d1).abs()
                })
                .collect();

            let mean_accel = accelerations.iter().sum::<f64>() / accelerations.len() as f64;
            continuity_scores.push(mean_accel);
        }

        if continuity_scores.is_empty() {
            return 0.5;
        }

        let mean_continuity =
            continuity_scores.iter().sum::<f64>() / continuity_scores.len() as f64;

        // Natural speech has moderate phase acceleration
        // Very low acceleration suggests synthetic smoothness
        // Very high acceleration suggests discontinuities
        if mean_continuity < 0.1 {
            (mean_continuity / 0.1).min(1.0) * 0.5
        } else if mean_continuity > 2.0 {
            (2.0 / mean_continuity).min(1.0) * 0.6
        } else {
            1.0
        }
    }

    /// Compute phase randomness score
    ///
    /// Natural audio has some randomness in phase relationships
    fn compute_phase_randomness_score(&self, phase_spectra: &[Vec<f64>]) -> f64 {
        if phase_spectra.is_empty() {
            return 0.5;
        }

        // Analyze distribution of phases in high-frequency bins
        // Natural audio should have roughly uniform phase distribution
        let mut phase_distributions: Vec<f64> = Vec::new();

        for phases in phase_spectra {
            if phases.len() < 20 {
                continue;
            }

            // Look at high-frequency bins (where phase should be more random)
            let high_freq_start = phases.len() * 2 / 3;
            let high_freq_phases = &phases[high_freq_start..];

            // Compute entropy-like measure
            let normalized: Vec<f64> = high_freq_phases
                .iter()
                .map(|&p| (self.wrap_phase(p) + std::f64::consts::PI) / (2.0 * std::f64::consts::PI))
                .collect();

            // Check uniformity using variance from expected value (0.5)
            let mean = normalized.iter().sum::<f64>() / normalized.len() as f64;
            let deviation = (mean - 0.5).abs();
            phase_distributions.push(deviation);
        }

        if phase_distributions.is_empty() {
            return 0.5;
        }

        let mean_deviation =
            phase_distributions.iter().sum::<f64>() / phase_distributions.len() as f64;

        // Small deviation = uniform distribution = natural
        // Large deviation = clustered phases = potentially synthetic
        if mean_deviation > 0.3 {
            (0.3 / mean_deviation).min(1.0) * 0.7
        } else {
            1.0
        }
    }

    /// Wrap phase to [-pi, pi] range using efficient modular arithmetic
    #[inline]
    fn wrap_phase(&self, phase: f64) -> f64 {
        let two_pi = 2.0 * std::f64::consts::PI;
        let mut wrapped = phase % two_pi;
        if wrapped > std::f64::consts::PI {
            wrapped -= two_pi;
        } else if wrapped < -std::f64::consts::PI {
            wrapped += two_pi;
        }
        wrapped
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_phase_sensor_creation() {
        let sensor = PhaseSensor::new(None);
        assert_eq!(sensor.name, "phase_sensor");
        assert!((sensor.threshold - DEFAULT_THRESHOLD).abs() < f64::EPSILON);
    }

    #[test]
    fn test_phase_sensor_custom_threshold() {
        let sensor = PhaseSensor::new(Some(0.8));
        assert!((sensor.threshold - 0.8).abs() < f64::EPSILON);
    }

    #[test]
    fn test_wrap_phase() {
        let sensor = PhaseSensor::new(None);

        // Test wrapping
        let pi = std::f64::consts::PI;
        assert!((sensor.wrap_phase(0.0) - 0.0).abs() < 1e-10);
        assert!((sensor.wrap_phase(pi) - pi).abs() < 1e-10);
        assert!((sensor.wrap_phase(2.0 * pi) - 0.0).abs() < 1e-10);
        assert!((sensor.wrap_phase(-2.0 * pi) - 0.0).abs() < 1e-10);
        // 3*pi wraps to pi (not -pi, as it wraps down from 3pi to pi)
        assert!((sensor.wrap_phase(3.0 * pi) - pi).abs() < 1e-10);
    }

    #[test]
    fn test_coherence_score_natural_range() {
        let sensor = PhaseSensor::new(None);

        // Simulate natural phase variance
        let phase_spectra: Vec<Vec<f64>> = (0..5)
            .map(|i| {
                (0..50)
                    .map(|j| (i as f64 * 0.3 + j as f64 * 0.1).sin() * std::f64::consts::PI)
                    .collect()
            })
            .collect();

        let score = sensor.compute_cross_frame_coherence(&phase_spectra);
        // Should be in reasonable range for natural-like phases
        assert!(score > 0.3);
    }
}
