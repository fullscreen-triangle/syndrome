//! # Syndrome Framework
//!
//! Categorical Resolution of Disease Trajectories through Partition Geometry
//! and Oscillator Coherence.
//!
//! This crate implements the mathematical framework for computing disease trajectories
//! through categorical partition geometry, as described in the foundational papers.
//!
//! ## Core Concepts
//!
//! - **Partition Coordinates**: `(n, ℓ, m, s)` with capacity `C(n) = 2n²`
//! - **S-Entropy Space**: `[0,1]³` with coordinates `(Sₖ, Sₜ, Sₑ)`
//! - **Universal Coherence**: `η = (Π_obs - Π_deg)/(Π_opt - Π_deg)`
//! - **Disease Vector**: `D = (D_P, D_E, D_C, D_M, D_A, D_G, D_Ca, D_R)`
//!
//! ## Example
//!
//! ```rust
//! use syndrome::prelude::*;
//!
//! // Create a partition coordinate
//! let coord = PartitionCoord::new(2, 1, 0, Chirality::Plus).unwrap();
//! assert_eq!(coord.capacity(), 8);
//!
//! // Compute coherence from performance metrics
//! let eta = coherence_index(0.8, 1.0, 0.0);
//! assert!((eta - 0.8).abs() < 1e-10);
//! ```

pub mod partition;
pub mod s_entropy;
pub mod coherence;
pub mod disease;
pub mod trajectory;
pub mod operators;
pub mod error;

/// Prelude for convenient imports
pub mod prelude {
    pub use crate::partition::{
        PartitionCoord, Chirality, partition_capacity, categorical_distance,
        enumerate_partition_states, address_to_value, value_to_address,
    };
    pub use crate::s_entropy::{SEntropyPoint, s_entropy_distance, interpolate_s_entropy};
    pub use crate::coherence::{
        coherence_index, Oscillator, OscillatorClass, cellular_coherence,
        therapeutic_efficacy, predicted_coherence_after_treatment,
    };
    pub use crate::disease::{
        DiseaseVector, disease_vector_from_oscillators, classify_disease,
        disease_severity, disease_signature_distance, healthy_vector,
    };
    pub use crate::trajectory::{
        Trajectory, Constraint, complete_trajectory, address_precision,
    };
    pub use crate::error::SyndromeError;
}

pub use error::SyndromeError;
pub type Result<T> = std::result::Result<T, SyndromeError>;
