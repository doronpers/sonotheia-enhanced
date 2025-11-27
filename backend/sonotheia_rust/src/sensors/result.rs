//! Standardized sensor result structure
//!
//! Provides a common result format compatible with the Python sensor framework.

use pyo3::prelude::*;
use std::collections::HashMap;

/// Standardized result structure for all sensors
///
/// # Fields
/// - `sensor_name`: Identifier for the sensor that produced this result
/// - `passed`: Pass/fail decision (None for info-only sensors)
/// - `value`: Measured value from the analysis
/// - `threshold`: Decision threshold used
/// - `reason`: Optional failure reason code
/// - `detail`: Human-readable explanation
/// - `metadata`: Additional key-value data
///
/// # Example
/// ```
/// use sonotheia_rust::SensorResult;
///
/// let result = SensorResult::new(
///     "vacuum_sensor".to_string(),
///     Some(true),
///     0.85,
///     0.7,
///     None,
///     Some("Source-filter model analysis passed".to_string()),
/// );
/// ```
#[pyclass]
#[derive(Debug, Clone)]
pub struct SensorResult {
    #[pyo3(get)]
    pub sensor_name: String,

    #[pyo3(get)]
    pub passed: Option<bool>,

    #[pyo3(get)]
    pub value: f64,

    #[pyo3(get)]
    pub threshold: f64,

    #[pyo3(get)]
    pub reason: Option<String>,

    #[pyo3(get)]
    pub detail: Option<String>,

    #[pyo3(get)]
    pub metadata: HashMap<String, String>,
}

#[pymethods]
impl SensorResult {
    /// Create a new SensorResult
    ///
    /// # Arguments
    /// * `sensor_name` - Identifier for the sensor
    /// * `passed` - Pass/fail decision (use None for info-only)
    /// * `value` - Measured value from analysis
    /// * `threshold` - Decision threshold
    /// * `reason` - Optional failure reason code
    /// * `detail` - Optional human-readable explanation
    #[new]
    #[pyo3(signature = (sensor_name, passed, value, threshold, reason=None, detail=None))]
    pub fn new(
        sensor_name: String,
        passed: Option<bool>,
        value: f64,
        threshold: f64,
        reason: Option<String>,
        detail: Option<String>,
    ) -> Self {
        Self {
            sensor_name,
            passed,
            value,
            threshold,
            reason,
            detail,
            metadata: HashMap::new(),
        }
    }

    /// Add metadata to the result
    ///
    /// # Arguments
    /// * `key` - Metadata key
    /// * `value` - Metadata value
    pub fn add_metadata(&mut self, key: String, value: String) {
        self.metadata.insert(key, value);
    }

    /// Check if the sensor passed
    ///
    /// Returns true if passed is Some(true), false otherwise
    pub fn is_pass(&self) -> bool {
        self.passed.unwrap_or(false)
    }

    /// Check if the sensor failed
    ///
    /// Returns true if passed is Some(false)
    pub fn is_fail(&self) -> bool {
        matches!(self.passed, Some(false))
    }

    /// String representation for Python
    fn __repr__(&self) -> String {
        let status = match self.passed {
            Some(true) => "PASS",
            Some(false) => "FAIL",
            None => "INFO",
        };
        format!(
            "SensorResult(sensor_name='{}', status={}, value={:.4}, threshold={:.4})",
            self.sensor_name, status, self.value, self.threshold
        )
    }

    /// Convert to dictionary for Python
    /// 
    /// # Panics
    /// This function will panic if PyObject conversion fails, which should only
    /// happen if the Python interpreter is in an invalid state.
    #[allow(clippy::expect_used)]  // Panic is acceptable here - GIL is held
    pub fn to_dict(&self) -> HashMap<String, PyObject> {
        Python::with_gil(|py| {
            let mut dict = HashMap::new();
            
            // Helper macro to reduce code duplication
            macro_rules! insert_py {
                ($key:expr, $val:expr) => {
                    dict.insert(
                        $key.to_string(), 
                        $val.into_pyobject(py)
                            .expect("GIL conversion failed")
                            .into_any()
                            .unbind()
                    );
                };
            }
            
            insert_py!("sensor_name", self.sensor_name.clone());
            insert_py!("passed", self.passed);
            insert_py!("value", self.value);
            insert_py!("threshold", self.threshold);
            insert_py!("reason", self.reason.clone());
            insert_py!("detail", self.detail.clone());
            
            dict
        })
    }
}

impl Default for SensorResult {
    fn default() -> Self {
        Self {
            sensor_name: String::new(),
            passed: None,
            value: 0.0,
            threshold: 0.0,
            reason: None,
            detail: None,
            metadata: HashMap::new(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sensor_result_creation() {
        let result = SensorResult::new(
            "test_sensor".to_string(),
            Some(true),
            0.95,
            0.8,
            None,
            Some("Test passed".to_string()),
        );

        assert_eq!(result.sensor_name, "test_sensor");
        assert_eq!(result.passed, Some(true));
        assert!((result.value - 0.95).abs() < f64::EPSILON);
        assert!((result.threshold - 0.8).abs() < f64::EPSILON);
        assert!(result.is_pass());
        assert!(!result.is_fail());
    }

    #[test]
    fn test_sensor_result_fail() {
        let result = SensorResult::new(
            "test_sensor".to_string(),
            Some(false),
            0.5,
            0.8,
            Some("below_threshold".to_string()),
            Some("Value below threshold".to_string()),
        );

        assert!(!result.is_pass());
        assert!(result.is_fail());
    }

    #[test]
    fn test_sensor_result_metadata() {
        let mut result = SensorResult::new(
            "test_sensor".to_string(),
            Some(true),
            0.95,
            0.8,
            None,
            None,
        );

        result.add_metadata("processing_time_ms".to_string(), "15".to_string());
        assert_eq!(
            result.metadata.get("processing_time_ms"),
            Some(&"15".to_string())
        );
    }
}
