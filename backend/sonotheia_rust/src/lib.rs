//! Sonotheia Rust Performance Sensors
//!
//! High-performance audio analysis sensors for the Sonotheia Enhanced platform.
//! Provides Python bindings via PyO3.
//!
//! # Security Considerations
//! - All array operations include bounds checking
//! - Overflow checks enabled in release builds
//! - No unsafe code unless explicitly documented
//! - Input validation on all public functions

mod sensors;
mod utils;

use pyo3::prelude::*;

pub use sensors::{
    articulation::ArticulationSensor,
    phase::PhaseSensor,
    result::SensorResult,
    vacuum::VacuumSensor,
};
pub use utils::errors::SensorError;

/// Initialize the sonotheia_rust Python module
#[pymodule]
fn sonotheia_rust(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Register sensor classes
    m.add_class::<VacuumSensor>()?;
    m.add_class::<PhaseSensor>()?;
    m.add_class::<ArticulationSensor>()?;
    m.add_class::<SensorResult>()?;

    // Add version info
    m.add("__version__", "0.1.0")?;
    m.add("__author__", "Sonotheia Team")?;

    Ok(())
}
