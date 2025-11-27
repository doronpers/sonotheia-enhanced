//! Sensor modules for audio analysis
//!
//! This module provides high-performance audio sensors:
//! - `vacuum`: Source-Filter Model (SFM) analysis
//! - `phase`: Multi-Phase Coherence (MPC) detection
//! - `articulation`: Speech articulation pattern analysis
//! - `result`: Standardized sensor result structure

pub mod articulation;
pub mod phase;
pub mod result;
pub mod vacuum;
