//! FFT operations with bounds checking
//!
//! Provides safe FFT operations for spectral analysis.

#![allow(dead_code)] // Some utilities reserved for future use

use crate::utils::errors::{SensorError, SensorResultType};
use rustfft::{num_complex::Complex, FftPlanner};

/// Compute FFT of real-valued audio data
///
/// # Arguments
/// * `audio` - Audio samples as f64 slice
///
/// # Returns
/// Complex FFT result
///
/// # Security
/// - Validates input is non-empty
/// - Uses bounds-checked operations
pub fn compute_fft(audio: &[f64]) -> SensorResultType<Vec<Complex<f64>>> {
    if audio.is_empty() {
        return Err(SensorError::invalid_input("Cannot compute FFT of empty data"));
    }

    let n = audio.len();

    // Convert to complex
    let mut buffer: Vec<Complex<f64>> = audio.iter().map(|&x| Complex::new(x, 0.0)).collect();

    // Create FFT planner and perform FFT
    let mut planner = FftPlanner::new();
    let fft = planner.plan_fft_forward(n);

    fft.process(&mut buffer);

    Ok(buffer)
}

/// Compute magnitude spectrum from FFT result
///
/// # Arguments
/// * `fft_result` - Complex FFT output
///
/// # Returns
/// Magnitude spectrum (positive frequencies only)
///
/// # Security
/// - Returns only positive frequency bins (N/2 + 1)
pub fn magnitude_spectrum(fft_result: &[Complex<f64>]) -> Vec<f64> {
    if fft_result.is_empty() {
        return Vec::new();
    }

    // Only positive frequencies (N/2 + 1 bins)
    let n_positive = fft_result.len() / 2 + 1;

    fft_result
        .iter()
        .take(n_positive)
        .map(|c| c.norm())
        .collect()
}

/// Compute power spectrum from FFT result
///
/// # Arguments
/// * `fft_result` - Complex FFT output
///
/// # Returns
/// Power spectrum (magnitude squared)
pub fn power_spectrum(fft_result: &[Complex<f64>]) -> Vec<f64> {
    if fft_result.is_empty() {
        return Vec::new();
    }

    let n_positive = fft_result.len() / 2 + 1;

    fft_result
        .iter()
        .take(n_positive)
        .map(|c| c.norm_sqr())
        .collect()
}

/// Compute phase spectrum from FFT result
///
/// # Arguments
/// * `fft_result` - Complex FFT output
///
/// # Returns
/// Phase spectrum in radians
pub fn phase_spectrum(fft_result: &[Complex<f64>]) -> Vec<f64> {
    if fft_result.is_empty() {
        return Vec::new();
    }

    let n_positive = fft_result.len() / 2 + 1;

    fft_result
        .iter()
        .take(n_positive)
        .map(|c| c.arg())
        .collect()
}

/// Compute frequency bins for FFT result
///
/// # Arguments
/// * `n_samples` - Number of samples in original audio
/// * `sample_rate` - Sample rate in Hz
///
/// # Returns
/// Vector of frequency values in Hz
pub fn frequency_bins(n_samples: usize, sample_rate: u32) -> Vec<f64> {
    if n_samples == 0 {
        return Vec::new();
    }

    let n_positive = n_samples / 2 + 1;
    let freq_resolution = sample_rate as f64 / n_samples as f64;

    (0..n_positive)
        .map(|i| i as f64 * freq_resolution)
        .collect()
}

/// Find spectral centroid (center of mass of spectrum)
///
/// # Arguments
/// * `magnitudes` - Magnitude spectrum
/// * `frequencies` - Corresponding frequency bins
///
/// # Returns
/// Spectral centroid in Hz
pub fn spectral_centroid(magnitudes: &[f64], frequencies: &[f64]) -> f64 {
    if magnitudes.is_empty() || frequencies.is_empty() {
        return 0.0;
    }

    let min_len = magnitudes.len().min(frequencies.len());

    let weighted_sum: f64 = magnitudes
        .iter()
        .take(min_len)
        .zip(frequencies.iter())
        .map(|(&m, &f)| m * f)
        .sum();

    let total_magnitude: f64 = magnitudes.iter().take(min_len).sum();

    if total_magnitude < f64::EPSILON {
        return 0.0;
    }

    weighted_sum / total_magnitude
}

/// Find spectral bandwidth (spread of spectrum around centroid)
///
/// # Arguments
/// * `magnitudes` - Magnitude spectrum
/// * `frequencies` - Corresponding frequency bins
/// * `centroid` - Spectral centroid
///
/// # Returns
/// Spectral bandwidth in Hz
pub fn spectral_bandwidth(magnitudes: &[f64], frequencies: &[f64], centroid: f64) -> f64 {
    if magnitudes.is_empty() || frequencies.is_empty() {
        return 0.0;
    }

    let min_len = magnitudes.len().min(frequencies.len());

    let weighted_variance: f64 = magnitudes
        .iter()
        .take(min_len)
        .zip(frequencies.iter())
        .map(|(&m, &f)| m * (f - centroid).powi(2))
        .sum();

    let total_magnitude: f64 = magnitudes.iter().take(min_len).sum();

    if total_magnitude < f64::EPSILON {
        return 0.0;
    }

    (weighted_variance / total_magnitude).sqrt()
}

/// Find spectral rolloff point
///
/// # Arguments
/// * `magnitudes` - Magnitude spectrum
/// * `rolloff_percent` - Percentage of total energy (e.g., 0.85 for 85%)
///
/// # Returns
/// Index of rolloff frequency bin
pub fn spectral_rolloff(magnitudes: &[f64], rolloff_percent: f64) -> usize {
    if magnitudes.is_empty() {
        return 0;
    }

    let total_energy: f64 = magnitudes.iter().sum();
    let target_energy = total_energy * rolloff_percent.clamp(0.0, 1.0);

    let mut cumulative = 0.0;
    for (i, &mag) in magnitudes.iter().enumerate() {
        cumulative += mag;
        if cumulative >= target_energy {
            return i;
        }
    }

    magnitudes.len() - 1
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compute_fft() {
        // Simple sine wave
        let n = 64;
        let audio: Vec<f64> = (0..n)
            .map(|i| (2.0 * std::f64::consts::PI * 4.0 * i as f64 / n as f64).sin())
            .collect();

        let result = compute_fft(&audio).unwrap();
        assert_eq!(result.len(), n);
    }

    #[test]
    fn test_compute_fft_empty() {
        let audio: Vec<f64> = vec![];
        assert!(compute_fft(&audio).is_err());
    }

    #[test]
    fn test_magnitude_spectrum() {
        let fft_result = vec![
            Complex::new(1.0, 0.0),
            Complex::new(0.0, 1.0),
            Complex::new(0.5, 0.5),
            Complex::new(0.0, 0.0),
        ];

        let mags = magnitude_spectrum(&fft_result);
        assert_eq!(mags.len(), 3); // N/2 + 1

        assert!((mags[0] - 1.0).abs() < 1e-10);
        assert!((mags[1] - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_frequency_bins() {
        let bins = frequency_bins(100, 10000);
        assert_eq!(bins.len(), 51); // N/2 + 1
        assert!((bins[0] - 0.0).abs() < f64::EPSILON);
        assert!((bins[1] - 100.0).abs() < f64::EPSILON); // 10000/100 = 100 Hz resolution
    }

    #[test]
    fn test_spectral_centroid() {
        let magnitudes = vec![0.0, 1.0, 0.0, 0.0];
        let frequencies = vec![0.0, 100.0, 200.0, 300.0];

        let centroid = spectral_centroid(&magnitudes, &frequencies);
        assert!((centroid - 100.0).abs() < f64::EPSILON);
    }

    #[test]
    fn test_spectral_rolloff() {
        let magnitudes = vec![0.1, 0.2, 0.3, 0.4]; // Total = 1.0
        let rolloff = spectral_rolloff(&magnitudes, 0.6); // 60% at index 2
        assert_eq!(rolloff, 2);
    }
}
