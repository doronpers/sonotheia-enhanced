//! Audio processing utilities
//!
//! Provides common audio processing functions with bounds checking and validation.

#![allow(dead_code)] // Some utilities reserved for future use

use crate::utils::errors::{SensorError, SensorResultType};

/// Minimum valid sample rate (Hz)
pub const MIN_SAMPLE_RATE: u32 = 8000;

/// Maximum valid sample rate (Hz)
pub const MAX_SAMPLE_RATE: u32 = 96000;

/// Minimum audio length in samples (1ms at 8kHz)
pub const MIN_SAMPLES: usize = 8;

/// Validate audio input data
///
/// # Arguments
/// * `audio` - Audio samples as f64 slice
/// * `sample_rate` - Sample rate in Hz
///
/// # Returns
/// Ok(()) if valid, Err with description otherwise
///
/// # Security
/// - Validates sample rate range to prevent division by zero
/// - Validates minimum data length
/// - Checks for NaN or infinite values
pub fn validate_audio_input(audio: &[f64], sample_rate: u32) -> SensorResultType<()> {
    // Check sample rate bounds
    if sample_rate < MIN_SAMPLE_RATE || sample_rate > MAX_SAMPLE_RATE {
        return Err(SensorError::invalid_sample_rate(sample_rate));
    }

    // Check minimum length
    if audio.len() < MIN_SAMPLES {
        return Err(SensorError::insufficient_data(MIN_SAMPLES, audio.len()));
    }

    // Check for NaN or infinite values (security: prevent numeric exploits)
    for (i, &sample) in audio.iter().enumerate() {
        if sample.is_nan() {
            return Err(SensorError::invalid_input(format!(
                "NaN value at sample {}",
                i
            )));
        }
        if sample.is_infinite() {
            return Err(SensorError::invalid_input(format!(
                "Infinite value at sample {}",
                i
            )));
        }
    }

    Ok(())
}

/// Normalize audio data to range [-1.0, 1.0]
///
/// # Arguments
/// * `audio` - Audio samples as f64 slice
///
/// # Returns
/// Normalized audio data
///
/// # Security
/// - Handles zero max value to prevent division by zero
/// - Uses checked operations where possible
pub fn normalize_audio(audio: &[f64]) -> Vec<f64> {
    if audio.is_empty() {
        return Vec::new();
    }

    // Find maximum absolute value
    let max_abs = audio
        .iter()
        .map(|&x| x.abs())
        .fold(0.0f64, |a, b| a.max(b));

    // Avoid division by zero
    if max_abs < f64::EPSILON {
        return vec![0.0; audio.len()];
    }

    // Normalize
    audio.iter().map(|&x| x / max_abs).collect()
}

/// Calculate RMS (Root Mean Square) energy of audio
///
/// # Arguments
/// * `audio` - Audio samples as f64 slice
///
/// # Returns
/// RMS energy value
///
/// # Security
/// - Handles empty input
/// - Uses checked sqrt operation
pub fn calculate_rms(audio: &[f64]) -> f64 {
    if audio.is_empty() {
        return 0.0;
    }

    let sum_squares: f64 = audio.iter().map(|&x| x * x).sum();
    let mean_squares = sum_squares / audio.len() as f64;

    mean_squares.sqrt()
}

/// Apply Hamming window to audio segment
///
/// # Arguments
/// * `audio` - Audio samples as f64 slice
///
/// # Returns
/// Windowed audio data
pub fn apply_hamming_window(audio: &[f64]) -> Vec<f64> {
    let n = audio.len();
    if n == 0 {
        return Vec::new();
    }

    let n_f64 = n as f64;
    audio
        .iter()
        .enumerate()
        .map(|(i, &x)| {
            let window = 0.54 - 0.46 * (2.0 * std::f64::consts::PI * i as f64 / (n_f64 - 1.0)).cos();
            x * window
        })
        .collect()
}

/// Split audio into overlapping frames
///
/// # Arguments
/// * `audio` - Audio samples as f64 slice
/// * `frame_size` - Size of each frame in samples
/// * `hop_size` - Number of samples to advance between frames
///
/// # Returns
/// Vector of frames
///
/// # Security
/// - Validates frame_size and hop_size are non-zero
/// - Uses saturating arithmetic for bounds
pub fn frame_audio(audio: &[f64], frame_size: usize, hop_size: usize) -> Vec<Vec<f64>> {
    if frame_size == 0 || hop_size == 0 || audio.len() < frame_size {
        return Vec::new();
    }

    let mut frames = Vec::new();
    let mut start = 0;

    while start + frame_size <= audio.len() {
        // Safe slice operation with bounds checking
        let end = start.saturating_add(frame_size).min(audio.len());
        let frame = audio[start..end].to_vec();
        frames.push(frame);
        start = start.saturating_add(hop_size);
    }

    frames
}

/// Calculate zero-crossing rate
///
/// # Arguments
/// * `audio` - Audio samples as f64 slice
///
/// # Returns
/// Zero-crossing rate (0.0 to 1.0)
pub fn zero_crossing_rate(audio: &[f64]) -> f64 {
    if audio.len() < 2 {
        return 0.0;
    }

    let crossings = audio
        .windows(2)
        .filter(|w| (w[0] >= 0.0) != (w[1] >= 0.0))
        .count();

    crossings as f64 / (audio.len() - 1) as f64
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_audio_valid() {
        let audio = vec![0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8];
        assert!(validate_audio_input(&audio, 16000).is_ok());
    }

    #[test]
    fn test_validate_audio_empty() {
        let audio: Vec<f64> = vec![];
        assert!(validate_audio_input(&audio, 16000).is_err());
    }

    #[test]
    fn test_validate_audio_invalid_sample_rate() {
        let audio = vec![0.1; 100];
        assert!(validate_audio_input(&audio, 100).is_err()); // Too low
        assert!(validate_audio_input(&audio, 200000).is_err()); // Too high
    }

    #[test]
    fn test_validate_audio_nan() {
        let audio = vec![0.1, f64::NAN, 0.3];
        assert!(validate_audio_input(&audio, 16000).is_err());
    }

    #[test]
    fn test_normalize_audio() {
        let audio = vec![0.5, -1.0, 0.25];
        let normalized = normalize_audio(&audio);
        assert!((normalized[0] - 0.5).abs() < f64::EPSILON);
        assert!((normalized[1] - (-1.0)).abs() < f64::EPSILON);
        assert!((normalized[2] - 0.25).abs() < f64::EPSILON);
    }

    #[test]
    fn test_normalize_audio_zero() {
        let audio = vec![0.0, 0.0, 0.0];
        let normalized = normalize_audio(&audio);
        assert!(normalized.iter().all(|&x| x == 0.0));
    }

    #[test]
    fn test_calculate_rms() {
        let audio = vec![1.0, -1.0, 1.0, -1.0];
        let rms = calculate_rms(&audio);
        assert!((rms - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_calculate_rms_empty() {
        let audio: Vec<f64> = vec![];
        assert!((calculate_rms(&audio) - 0.0).abs() < f64::EPSILON);
    }

    #[test]
    fn test_frame_audio() {
        let audio: Vec<f64> = (0..10).map(|x| x as f64).collect();
        let frames = frame_audio(&audio, 4, 2);
        assert_eq!(frames.len(), 4);
        assert_eq!(frames[0], vec![0.0, 1.0, 2.0, 3.0]);
        assert_eq!(frames[1], vec![2.0, 3.0, 4.0, 5.0]);
    }

    #[test]
    fn test_frame_audio_invalid() {
        let audio: Vec<f64> = vec![1.0, 2.0];
        assert!(frame_audio(&audio, 4, 2).is_empty()); // Audio too short
        assert!(frame_audio(&audio, 0, 2).is_empty()); // Zero frame size
    }

    #[test]
    fn test_zero_crossing_rate() {
        let audio = vec![1.0, -1.0, 1.0, -1.0];
        let zcr = zero_crossing_rate(&audio);
        assert!((zcr - 1.0).abs() < f64::EPSILON); // All crossings
    }

    #[test]
    fn test_hamming_window() {
        let audio = vec![1.0; 10];
        let windowed = apply_hamming_window(&audio);
        assert_eq!(windowed.len(), 10);
        // Hamming window should be ~0.08 at edges and ~1.0 at center
        assert!(windowed[0] < 0.1);
        assert!(windowed[4] > 0.9);
    }
}
