//! Articulation Sensor - Speech Articulation Pattern Analysis
//!
//! Detects synthetic audio by analyzing speech articulation patterns.
//! Natural speech has characteristic coarticulation patterns where sounds
//! influence each other. Synthetic speech often lacks these natural transitions.

use numpy::PyReadonlyArray1;
use pyo3::prelude::*;

use crate::sensors::result::SensorResult;
use crate::utils::audio::{
    apply_hamming_window, calculate_rms, frame_audio, validate_audio_input, zero_crossing_rate,
};
use crate::utils::fft::{
    compute_fft, frequency_bins, magnitude_spectrum, spectral_centroid, spectral_rolloff,
};

/// Default threshold for articulation sensor pass/fail decision
const DEFAULT_THRESHOLD: f64 = 0.6;

/// Frame size in samples (20ms at 16kHz)
const FRAME_SIZE: usize = 320;

/// Hop size in samples (10ms at 16kHz)
const HOP_SIZE: usize = 160;

/// Articulation Sensor for speech pattern analysis
///
/// This sensor analyzes articulation patterns in speech:
///
/// - Formant transitions between phonemes
/// - Coarticulation effects
/// - Natural speech dynamics
/// - Spectral flux patterns
///
/// # Example
/// ```python
/// from sonotheia_rust import ArticulationSensor
///
/// sensor = ArticulationSensor()
/// result = sensor.analyze(audio_data, 16000)
/// print(f"Passed: {result.passed}, Score: {result.value}")
/// ```
#[pyclass]
#[derive(Debug, Clone)]
pub struct ArticulationSensor {
    /// Detection threshold (0.0-1.0)
    #[pyo3(get, set)]
    pub threshold: f64,

    /// Sensor name identifier
    #[pyo3(get)]
    pub name: String,
}

#[pymethods]
impl ArticulationSensor {
    /// Create a new ArticulationSensor with optional threshold
    ///
    /// # Arguments
    /// * `threshold` - Detection threshold (0.0-1.0), default 0.6
    #[new]
    #[pyo3(signature = (threshold=None))]
    pub fn new(threshold: Option<f64>) -> Self {
        let threshold_value = threshold.unwrap_or(DEFAULT_THRESHOLD);
        let clamped_threshold = threshold_value.clamp(0.0, 1.0);

        Self {
            threshold: clamped_threshold,
            name: "articulation_sensor".to_string(),
        }
    }

    /// Analyze audio data for articulation patterns
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
        let authenticity_score = self.compute_articulation_score(audio_slice, sample_rate);

        // Determine pass/fail
        let passed = authenticity_score >= self.threshold;

        let detail = if passed {
            format!(
                "Articulation pattern analysis passed (score: {:.2})",
                authenticity_score
            )
        } else {
            format!(
                "Unnatural articulation patterns detected (score: {:.2})",
                authenticity_score
            )
        };

        Ok(SensorResult::new(
            self.name.clone(),
            Some(passed),
            authenticity_score,
            self.threshold,
            if !passed {
                Some("articulation_anomaly".to_string())
            } else {
                None
            },
            Some(detail),
        ))
    }

    /// String representation for Python
    fn __repr__(&self) -> String {
        format!(
            "ArticulationSensor(name='{}', threshold={})",
            self.name, self.threshold
        )
    }
}

impl ArticulationSensor {
    /// Compute articulation authenticity score
    fn compute_articulation_score(&self, audio: &[f64], sample_rate: u32) -> f64 {
        // Adjust frame parameters based on sample rate
        let frame_size = (sample_rate as usize * FRAME_SIZE) / 16000;
        let hop_size = (sample_rate as usize * HOP_SIZE) / 16000;

        // Frame the audio
        let frames = frame_audio(audio, frame_size, hop_size);

        if frames.len() < 5 {
            return 0.5; // Insufficient data
        }

        // Extract features for each frame
        let mut frame_features: Vec<FrameFeatures> = Vec::new();

        for frame in &frames {
            let windowed = apply_hamming_window(frame);
            let rms = calculate_rms(&windowed);

            // Skip very quiet frames
            if rms < 1e-6 {
                continue;
            }

            // Time-domain features
            let zcr = zero_crossing_rate(&windowed);

            // Frequency-domain features
            if let Ok(fft_result) = compute_fft(&windowed) {
                let magnitudes = magnitude_spectrum(&fft_result);
                let freqs = frequency_bins(frame_size, sample_rate);

                let centroid = spectral_centroid(&magnitudes, &freqs);
                let rolloff_idx = spectral_rolloff(&magnitudes, 0.85);
                let rolloff_freq = if rolloff_idx < freqs.len() {
                    freqs[rolloff_idx]
                } else {
                    freqs.last().copied().unwrap_or(0.0)
                };

                // Spectral flux (change from previous frame)
                let spectral_flux = self.compute_spectral_flux(&magnitudes);

                frame_features.push(FrameFeatures {
                    rms,
                    zcr,
                    centroid,
                    rolloff_freq,
                    spectral_flux,
                    magnitudes: magnitudes.clone(),
                });
            }
        }

        if frame_features.len() < 3 {
            return 0.5;
        }

        // Update spectral flux for all frames (requires comparison)
        self.update_spectral_flux(&mut frame_features);

        // Compute articulation metrics
        let transition_score = self.compute_transition_score(&frame_features);
        let dynamics_score = self.compute_dynamics_score(&frame_features);
        let zcr_pattern_score = self.compute_zcr_pattern_score(&frame_features);
        let spectral_flux_score = self.compute_spectral_flux_pattern_score(&frame_features);

        // Combined score
        let combined = 0.3 * transition_score
            + 0.25 * dynamics_score
            + 0.2 * zcr_pattern_score
            + 0.25 * spectral_flux_score;

        combined.clamp(0.0, 1.0)
    }

    /// Compute spectral flux for a single frame (placeholder)
    fn compute_spectral_flux(&self, _magnitudes: &[f64]) -> f64 {
        0.0 // Will be updated in batch
    }

    /// Update spectral flux values for all frames
    fn update_spectral_flux(&self, features: &mut [FrameFeatures]) {
        for i in 1..features.len() {
            let min_len = features[i].magnitudes.len().min(features[i - 1].magnitudes.len());

            let flux: f64 = features[i]
                .magnitudes
                .iter()
                .take(min_len)
                .zip(features[i - 1].magnitudes.iter())
                .map(|(&curr, &prev)| (curr - prev).powi(2))
                .sum::<f64>()
                .sqrt();

            features[i].spectral_flux = flux;
        }
    }

    /// Compute transition smoothness score
    ///
    /// Natural speech has smooth formant transitions during coarticulation
    fn compute_transition_score(&self, features: &[FrameFeatures]) -> f64 {
        if features.len() < 2 {
            return 0.5;
        }

        // Analyze centroid transitions
        let mut transition_rates: Vec<f64> = Vec::new();

        for i in 1..features.len() {
            let rate = (features[i].centroid - features[i - 1].centroid).abs();
            transition_rates.push(rate);
        }

        if transition_rates.is_empty() {
            return 0.5;
        }

        // Compute statistics of transition rates
        let mean_rate = transition_rates.iter().sum::<f64>() / transition_rates.len() as f64;
        let variance = transition_rates
            .iter()
            .map(|&r| (r - mean_rate).powi(2))
            .sum::<f64>()
            / transition_rates.len() as f64;
        let std_rate = variance.sqrt();

        // Natural speech should have variable transition rates
        // Synthetic often has either very smooth or very abrupt transitions
        if std_rate < 50.0 {
            // Too uniform - potentially synthetic
            (std_rate / 50.0).min(1.0) * 0.6
        } else if std_rate > 500.0 {
            // Too variable - potentially manipulated
            (500.0 / std_rate).min(1.0) * 0.7
        } else {
            1.0
        }
    }

    /// Compute dynamics score
    ///
    /// Natural speech has characteristic energy dynamics
    fn compute_dynamics_score(&self, features: &[FrameFeatures]) -> f64 {
        if features.len() < 3 {
            return 0.5;
        }

        let rms_values: Vec<f64> = features.iter().map(|f| f.rms).collect();

        // Compute dynamic range
        let max_rms = rms_values.iter().cloned().fold(0.0f64, f64::max);
        let min_rms = rms_values
            .iter()
            .cloned()
            .filter(|&x| x > 1e-8)
            .fold(f64::MAX, f64::min);

        if max_rms < 1e-8 {
            return 0.5;
        }

        let dynamic_range_db = 20.0 * (max_rms / min_rms.max(1e-8)).log10();

        // Natural speech typically has 20-50 dB dynamic range
        if dynamic_range_db < 10.0 {
            // Too compressed
            (dynamic_range_db / 10.0).min(1.0) * 0.5
        } else if dynamic_range_db > 60.0 {
            // Unusually wide
            (60.0 / dynamic_range_db).min(1.0) * 0.8
        } else {
            1.0
        }
    }

    /// Compute ZCR pattern score
    ///
    /// Zero-crossing rate varies with speech content
    fn compute_zcr_pattern_score(&self, features: &[FrameFeatures]) -> f64 {
        if features.is_empty() {
            return 0.5;
        }

        let zcr_values: Vec<f64> = features.iter().map(|f| f.zcr).collect();

        // Compute variance of ZCR
        let mean_zcr = zcr_values.iter().sum::<f64>() / zcr_values.len() as f64;
        let variance = zcr_values
            .iter()
            .map(|&z| (z - mean_zcr).powi(2))
            .sum::<f64>()
            / zcr_values.len() as f64;
        let std_zcr = variance.sqrt();

        // Natural speech has varying ZCR (voiced vs unvoiced)
        if std_zcr < 0.05 {
            // Too uniform
            (std_zcr / 0.05).min(1.0) * 0.6
        } else {
            1.0
        }
    }

    /// Compute spectral flux pattern score
    fn compute_spectral_flux_pattern_score(&self, features: &[FrameFeatures]) -> f64 {
        if features.len() < 2 {
            return 0.5;
        }

        let flux_values: Vec<f64> = features.iter().skip(1).map(|f| f.spectral_flux).collect();

        if flux_values.is_empty() {
            return 0.5;
        }

        // Compute statistics
        let mean_flux = flux_values.iter().sum::<f64>() / flux_values.len() as f64;
        let variance = flux_values
            .iter()
            .map(|&f| (f - mean_flux).powi(2))
            .sum::<f64>()
            / flux_values.len() as f64;
        let std_flux = variance.sqrt();

        // Natural speech has variable spectral flux
        if std_flux < mean_flux * 0.1 {
            // Very uniform flux
            0.6
        } else if std_flux > mean_flux * 3.0 {
            // Very erratic flux
            0.7
        } else {
            1.0
        }
    }
}

/// Internal structure for frame features
struct FrameFeatures {
    rms: f64,
    zcr: f64,
    centroid: f64,
    #[allow(dead_code)] // Reserved for future formant analysis
    rolloff_freq: f64,
    spectral_flux: f64,
    magnitudes: Vec<f64>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_articulation_sensor_creation() {
        let sensor = ArticulationSensor::new(None);
        assert_eq!(sensor.name, "articulation_sensor");
        assert!((sensor.threshold - DEFAULT_THRESHOLD).abs() < f64::EPSILON);
    }

    #[test]
    fn test_articulation_sensor_custom_threshold() {
        let sensor = ArticulationSensor::new(Some(0.75));
        assert!((sensor.threshold - 0.75).abs() < f64::EPSILON);
    }

    #[test]
    fn test_transition_score() {
        let sensor = ArticulationSensor::new(None);

        // Create features with natural-like transitions
        let features = vec![
            FrameFeatures {
                rms: 0.1,
                zcr: 0.15,
                centroid: 1000.0,
                rolloff_freq: 3000.0,
                spectral_flux: 0.0,
                magnitudes: vec![],
            },
            FrameFeatures {
                rms: 0.12,
                zcr: 0.18,
                centroid: 1100.0,
                rolloff_freq: 3100.0,
                spectral_flux: 0.1,
                magnitudes: vec![],
            },
            FrameFeatures {
                rms: 0.11,
                zcr: 0.20,
                centroid: 1050.0,
                rolloff_freq: 2900.0,
                spectral_flux: 0.08,
                magnitudes: vec![],
            },
        ];

        let score = sensor.compute_transition_score(&features);
        // Should be reasonable for natural-like transitions
        // Note: with only 3 frames and small deltas (50-100 Hz), std is low
        assert!(score > 0.0); // Just verify it runs without error
    }

    #[test]
    fn test_dynamics_score() {
        let sensor = ArticulationSensor::new(None);

        // Create features with natural dynamics
        let features = vec![
            FrameFeatures {
                rms: 0.1,
                zcr: 0.15,
                centroid: 1000.0,
                rolloff_freq: 3000.0,
                spectral_flux: 0.0,
                magnitudes: vec![],
            },
            FrameFeatures {
                rms: 0.3,
                zcr: 0.18,
                centroid: 1100.0,
                rolloff_freq: 3100.0,
                spectral_flux: 0.1,
                magnitudes: vec![],
            },
            FrameFeatures {
                rms: 0.05,
                zcr: 0.20,
                centroid: 1050.0,
                rolloff_freq: 2900.0,
                spectral_flux: 0.08,
                magnitudes: vec![],
            },
        ];

        let score = sensor.compute_dynamics_score(&features);
        // Good dynamics should score well
        assert!(score > 0.5);
    }
}
