//! Vacuum Sensor - Source-Filter Model (SFM) Analysis
//!
//! Detects synthetic audio by analyzing the source-filter model characteristics
//! of voice production. Real human speech follows predictable source-filter
//! patterns, while synthetic speech often exhibits anomalies.

use numpy::PyReadonlyArray1;
use pyo3::prelude::*;

use crate::sensors::result::SensorResult;
use crate::utils::audio::{apply_hamming_window, calculate_rms, frame_audio, validate_audio_input};
use crate::utils::fft::{compute_fft, magnitude_spectrum, spectral_centroid, spectral_bandwidth};

/// Default threshold for vacuum sensor pass/fail decision
const DEFAULT_THRESHOLD: f64 = 0.7;

/// Frame size in samples (25ms at 16kHz)
const FRAME_SIZE: usize = 400;

/// Hop size in samples (10ms at 16kHz)
const HOP_SIZE: usize = 160;

/// Vacuum Sensor for Source-Filter Model analysis
///
/// This sensor analyzes audio using principles of the source-filter model
/// of speech production. It detects anomalies that indicate synthetic audio:
///
/// - Spectral envelope irregularities
/// - Unnatural formant transitions
/// - Inconsistent source characteristics
///
/// # Example
/// ```python
/// from sonotheia_rust import VacuumSensor
///
/// sensor = VacuumSensor()
/// result = sensor.analyze(audio_data, 16000)
/// print(f"Passed: {result.passed}, Score: {result.value}")
/// ```
#[pyclass]
#[derive(Debug, Clone)]
pub struct VacuumSensor {
    /// Detection threshold (0.0-1.0)
    #[pyo3(get, set)]
    pub threshold: f64,

    /// Sensor name identifier
    #[pyo3(get)]
    pub name: String,
}

#[pymethods]
impl VacuumSensor {
    /// Create a new VacuumSensor with optional threshold
    ///
    /// # Arguments
    /// * `threshold` - Detection threshold (0.0-1.0), default 0.7
    #[new]
    #[pyo3(signature = (threshold=None))]
    pub fn new(threshold: Option<f64>) -> Self {
        let threshold_value = threshold.unwrap_or(DEFAULT_THRESHOLD);
        // Clamp threshold to valid range
        let clamped_threshold = threshold_value.clamp(0.0, 1.0);

        Self {
            threshold: clamped_threshold,
            name: "vacuum_sensor".to_string(),
        }
    }

    /// Analyze audio data for source-filter model anomalies
    ///
    /// # Arguments
    /// * `audio` - Audio samples as numpy array (f64)
    /// * `sample_rate` - Sample rate in Hz
    ///
    /// # Returns
    /// SensorResult with pass/fail decision and analysis details
    ///
    /// # Security
    /// - Validates all input data
    /// - Handles edge cases gracefully
    pub fn analyze(
        &self,
        audio: PyReadonlyArray1<'_, f64>,
        sample_rate: u32,
    ) -> PyResult<SensorResult> {
        // Convert numpy array to slice with bounds checking
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
        let authenticity_score = self.compute_sfm_score(audio_slice, sample_rate);

        // Determine pass/fail
        let passed = authenticity_score >= self.threshold;

        let detail = if passed {
            format!(
                "Source-filter model analysis passed (score: {:.2})",
                authenticity_score
            )
        } else {
            format!(
                "Potential synthetic audio detected (score: {:.2})",
                authenticity_score
            )
        };

        Ok(SensorResult::new(
            self.name.clone(),
            Some(passed),
            authenticity_score,
            self.threshold,
            if !passed {
                Some("sfm_anomaly".to_string())
            } else {
                None
            },
            Some(detail),
        ))
    }

    /// String representation for Python
    fn __repr__(&self) -> String {
        format!(
            "VacuumSensor(name='{}', threshold={})",
            self.name, self.threshold
        )
    }
}

impl VacuumSensor {
    /// Compute source-filter model authenticity score
    ///
    /// Returns a score from 0.0 (likely synthetic) to 1.0 (likely authentic)
    fn compute_sfm_score(&self, audio: &[f64], sample_rate: u32) -> f64 {
        // Adjust frame parameters based on sample rate
        let frame_size = (sample_rate as usize * FRAME_SIZE) / 16000;
        let hop_size = (sample_rate as usize * HOP_SIZE) / 16000;

        // Frame the audio
        let frames = frame_audio(audio, frame_size, hop_size);

        if frames.is_empty() {
            return 0.5; // Neutral score for insufficient data
        }

        // Pre-allocate with estimated capacity
        let mut spectral_features: Vec<SpectralFeatures> = Vec::with_capacity(frames.len());

        // Pre-compute frequency bins once (same for all frames of same size)
        let freq_resolution = sample_rate as f64 / frame_size as f64;

        for frame in &frames {
            // Apply window
            let windowed = apply_hamming_window(frame);

            // Skip silent frames
            let rms = calculate_rms(&windowed);
            if rms < 1e-6 {
                continue;
            }

            // Compute FFT
            if let Ok(fft_result) = compute_fft(&windowed) {
                let magnitudes = magnitude_spectrum(&fft_result);

                // Create frequency bins (computed once per magnitude length)
                let freqs: Vec<f64> = (0..magnitudes.len())
                    .map(|i| i as f64 * freq_resolution)
                    .collect();

                // Compute spectral features
                let centroid = spectral_centroid(&magnitudes, &freqs);
                let bandwidth = spectral_bandwidth(&magnitudes, &freqs, centroid);

                spectral_features.push(SpectralFeatures {
                    centroid,
                    bandwidth,
                    rms,
                });
            }
        }

        if spectral_features.len() < 3 {
            return 0.5; // Insufficient frames for analysis
        }

        // Analyze feature patterns
        self.analyze_patterns(&spectral_features)
    }

    /// Analyze spectral patterns for authenticity indicators
    fn analyze_patterns(&self, features: &[SpectralFeatures]) -> f64 {
        if features.is_empty() {
            return 0.5;
        }

        // 1. Spectral centroid stability (authentic speech has natural variation)
        let centroid_score = self.compute_stability_score(
            &features.iter().map(|f| f.centroid).collect::<Vec<_>>(),
            50.0,  // Minimum expected variation
            500.0, // Maximum expected variation
        );

        // 2. Bandwidth consistency (synthetic often has unnatural bandwidth patterns)
        let bandwidth_score = self.compute_stability_score(
            &features.iter().map(|f| f.bandwidth).collect::<Vec<_>>(),
            20.0,
            200.0,
        );

        // 3. Energy dynamics (authentic speech has natural amplitude variation)
        let energy_score = self.compute_stability_score(
            &features.iter().map(|f| f.rms).collect::<Vec<_>>(),
            0.01,
            0.5,
        );

        // 4. Smoothness score (frame-to-frame transitions)
        let smoothness_score = self.compute_smoothness_score(features);

        // Combined score with weights
        let combined = 0.25 * centroid_score
            + 0.25 * bandwidth_score
            + 0.25 * energy_score
            + 0.25 * smoothness_score;

        // Clamp to valid range
        combined.clamp(0.0, 1.0)
    }

    /// Compute stability score based on variance within expected range
    fn compute_stability_score(&self, values: &[f64], min_var: f64, max_var: f64) -> f64 {
        if values.len() < 2 {
            return 0.5;
        }

        let mean = values.iter().sum::<f64>() / values.len() as f64;
        let variance = values
            .iter()
            .map(|&x| (x - mean).powi(2))
            .sum::<f64>()
            / (values.len() - 1) as f64;

        let std_dev = variance.sqrt();

        // Score based on whether variation is in expected range
        if std_dev < min_var {
            // Too stable - potentially synthetic
            (std_dev / min_var).min(1.0)
        } else if std_dev > max_var {
            // Too variable - potentially anomalous
            (max_var / std_dev).min(1.0)
        } else {
            // Within expected range - good
            1.0
        }
    }

    /// Compute smoothness score based on frame transitions
    fn compute_smoothness_score(&self, features: &[SpectralFeatures]) -> f64 {
        if features.len() < 2 {
            return 0.5;
        }

        // Compute frame-to-frame differences
        let mut centroid_diffs: Vec<f64> = Vec::new();

        for i in 1..features.len() {
            let diff = (features[i].centroid - features[i - 1].centroid).abs();
            centroid_diffs.push(diff);
        }

        if centroid_diffs.is_empty() {
            return 0.5;
        }

        // Calculate mean and std of differences
        let mean_diff = centroid_diffs.iter().sum::<f64>() / centroid_diffs.len() as f64;

        // Very abrupt changes suggest synthetic manipulation
        // Typical authentic speech has gradual transitions
        let max_expected_diff = 200.0; // Hz

        if mean_diff > max_expected_diff {
            (max_expected_diff / mean_diff).min(1.0)
        } else {
            1.0
        }
    }
}

/// Internal structure for spectral features
struct SpectralFeatures {
    centroid: f64,
    bandwidth: f64,
    rms: f64,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vacuum_sensor_creation() {
        let sensor = VacuumSensor::new(None);
        assert_eq!(sensor.name, "vacuum_sensor");
        assert!((sensor.threshold - DEFAULT_THRESHOLD).abs() < f64::EPSILON);
    }

    #[test]
    fn test_vacuum_sensor_custom_threshold() {
        let sensor = VacuumSensor::new(Some(0.8));
        assert!((sensor.threshold - 0.8).abs() < f64::EPSILON);
    }

    #[test]
    fn test_vacuum_sensor_threshold_clamping() {
        let sensor = VacuumSensor::new(Some(1.5));
        assert!((sensor.threshold - 1.0).abs() < f64::EPSILON);

        let sensor = VacuumSensor::new(Some(-0.5));
        assert!((sensor.threshold - 0.0).abs() < f64::EPSILON);
    }

    #[test]
    fn test_stability_score() {
        let sensor = VacuumSensor::new(None);

        // Normal variation
        let values = vec![100.0, 110.0, 95.0, 105.0, 100.0];
        let score = sensor.compute_stability_score(&values, 5.0, 50.0);
        assert!(score > 0.8);

        // Too stable
        let values = vec![100.0, 100.0, 100.0, 100.0];
        let score = sensor.compute_stability_score(&values, 5.0, 50.0);
        assert!(score < 0.5);
    }

    #[test]
    fn test_smoothness_score() {
        let sensor = VacuumSensor::new(None);

        // Smooth transitions
        let features = vec![
            SpectralFeatures {
                centroid: 1000.0,
                bandwidth: 500.0,
                rms: 0.1,
            },
            SpectralFeatures {
                centroid: 1010.0,
                bandwidth: 510.0,
                rms: 0.11,
            },
            SpectralFeatures {
                centroid: 1020.0,
                bandwidth: 520.0,
                rms: 0.12,
            },
        ];
        let score = sensor.compute_smoothness_score(&features);
        assert!(score > 0.9);
    }
}
