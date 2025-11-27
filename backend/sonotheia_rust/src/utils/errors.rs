//! Error types for sensor operations
//!
//! Provides structured error handling with security-conscious error messages.

use thiserror::Error;

/// Errors that can occur during sensor operations
#[derive(Error, Debug)]
pub enum SensorError {
    /// Input data validation error
    #[error("Invalid input: {0}")]
    InvalidInput(String),

    /// Audio data is empty or too short
    #[error("Audio data is empty or below minimum length ({0} samples required, got {1})")]
    InsufficientData(usize, usize),

    /// Sample rate is invalid
    #[error("Invalid sample rate: {0} Hz (expected 8000-96000 Hz)")]
    InvalidSampleRate(u32),

    /// FFT computation error
    #[error("FFT computation failed: {0}")]
    FftError(String),

    /// Numeric overflow detected
    #[error("Numeric overflow in {0}")]
    Overflow(String),

    /// Array index out of bounds
    #[error("Array index out of bounds: {0}")]
    IndexOutOfBounds(String),

    /// Internal processing error
    #[error("Internal error: {0}")]
    InternalError(String),
}

impl SensorError {
    /// Create an invalid input error with validation
    pub fn invalid_input<S: Into<String>>(msg: S) -> Self {
        SensorError::InvalidInput(msg.into())
    }

    /// Create an insufficient data error
    pub fn insufficient_data(required: usize, actual: usize) -> Self {
        SensorError::InsufficientData(required, actual)
    }

    /// Create an invalid sample rate error
    pub fn invalid_sample_rate(rate: u32) -> Self {
        SensorError::InvalidSampleRate(rate)
    }

    /// Check if this error should be logged as a warning vs error
    pub fn is_user_error(&self) -> bool {
        matches!(
            self,
            SensorError::InvalidInput(_)
                | SensorError::InsufficientData(_, _)
                | SensorError::InvalidSampleRate(_)
        )
    }
}

/// Result type alias for sensor operations
pub type SensorResultType<T> = Result<T, SensorError>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_messages() {
        let err = SensorError::invalid_input("audio data is empty");
        assert!(err.to_string().contains("Invalid input"));

        let err = SensorError::insufficient_data(1000, 100);
        assert!(err.to_string().contains("1000"));
        assert!(err.to_string().contains("100"));
    }

    #[test]
    fn test_is_user_error() {
        assert!(SensorError::InvalidInput("test".to_string()).is_user_error());
        assert!(SensorError::InsufficientData(100, 10).is_user_error());
        assert!(!SensorError::InternalError("test".to_string()).is_user_error());
    }
}
