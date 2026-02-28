//! Error types for the Syndrome framework.

use thiserror::Error;

/// Errors that can occur in the Syndrome framework.
#[derive(Error, Debug, Clone, PartialEq)]
pub enum SyndromeError {
    /// Invalid partition coordinate
    #[error("Invalid partition coordinate: n={n}, ℓ={ell}, m={m}, s={s}")]
    InvalidPartitionCoord {
        n: i32,
        ell: i32,
        m: i32,
        s: f64,
    },

    /// Value out of bounds
    #[error("Value {value} out of bounds [{min}, {max}]")]
    OutOfBounds {
        value: f64,
        min: f64,
        max: f64,
    },

    /// Invalid S-entropy coordinate
    #[error("Invalid S-entropy coordinate: {coord} = {value} (must be in [0, 1])")]
    InvalidSEntropyCoord {
        coord: &'static str,
        value: f64,
    },

    /// Invalid coherence parameters
    #[error("Invalid coherence parameters: pi_opt ({pi_opt}) equals pi_deg ({pi_deg})")]
    InvalidCoherenceParams {
        pi_opt: f64,
        pi_deg: f64,
    },

    /// Invalid disease index
    #[error("Invalid disease index: D_{class} = {value} (must be in [0, 1])")]
    InvalidDiseaseIndex {
        class: &'static str,
        value: f64,
    },

    /// Invalid address digit
    #[error("Invalid address digit: {digit} (must be 0, 1, or 2)")]
    InvalidAddressDigit {
        digit: i32,
    },

    /// Trajectory computation failed
    #[error("Trajectory computation failed: {reason}")]
    TrajectoryFailed {
        reason: String,
    },

    /// Constraint violation
    #[error("Constraint '{name}' violated")]
    ConstraintViolation {
        name: String,
    },

    /// Empty collection
    #[error("Empty collection: {context}")]
    EmptyCollection {
        context: &'static str,
    },

    /// Dimension mismatch
    #[error("Dimension mismatch: expected {expected}, got {got}")]
    DimensionMismatch {
        expected: usize,
        got: usize,
    },

    /// Index out of bounds
    #[error("Index {index} out of bounds (max: {max})")]
    IndexOutOfBounds {
        index: usize,
        max: usize,
    },

    /// Computation error
    #[error("Computation error in {operation}: {details}")]
    ComputationError {
        operation: String,
        details: String,
    },

    /// Invalid S-entropy point
    #[error("Invalid S-entropy point: ({s_k}, {s_t}, {s_e})")]
    InvalidSEntropyPoint {
        s_k: f64,
        s_t: f64,
        s_e: f64,
    },
}
