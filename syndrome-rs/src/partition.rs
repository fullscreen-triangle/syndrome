//! Partition Geometry Module
//!
//! Implements partition coordinates `(n, ℓ, m, s)` and related operations
//! derived from bounded phase space and categorical observation axioms.
//!
//! The partition capacity `C(n) = 2n²` emerges as geometric necessity from
//! spherical symmetry of bounded phase space.

use serde::{Deserialize, Serialize};
use crate::{Result, SyndromeError};

/// Chirality coordinate (spin-like binary value).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Chirality {
    /// Positive chirality (+1/2)
    Plus,
    /// Negative chirality (-1/2)
    Minus,
}

impl Chirality {
    /// Get the numerical value of chirality.
    #[inline]
    pub fn value(self) -> f64 {
        match self {
            Chirality::Plus => 0.5,
            Chirality::Minus => -0.5,
        }
    }

    /// Create chirality from numerical value.
    pub fn from_value(v: f64) -> Option<Self> {
        if (v - 0.5).abs() < 1e-10 {
            Some(Chirality::Plus)
        } else if (v + 0.5).abs() < 1e-10 {
            Some(Chirality::Minus)
        } else {
            None
        }
    }
}

/// Partition coordinates in categorical space.
///
/// # Coordinates
/// - `n`: Depth coordinate (n ≥ 1)
/// - `ell`: Complexity coordinate (0 ≤ ℓ ≤ n-1)
/// - `m`: Orientation coordinate (-ℓ ≤ m ≤ ℓ)
/// - `s`: Chirality coordinate (s ∈ {-0.5, +0.5})
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PartitionCoord {
    n: i32,
    ell: i32,
    m: i32,
    s: Chirality,
}

impl PartitionCoord {
    /// Create a new partition coordinate with validation.
    ///
    /// # Arguments
    /// * `n` - Depth coordinate (must be ≥ 1)
    /// * `ell` - Complexity coordinate (must be 0 ≤ ℓ ≤ n-1)
    /// * `m` - Orientation coordinate (must be -ℓ ≤ m ≤ ℓ)
    /// * `s` - Chirality coordinate
    ///
    /// # Errors
    /// Returns `SyndromeError::InvalidPartitionCoord` if constraints are violated.
    pub fn new(n: i32, ell: i32, m: i32, s: Chirality) -> Result<Self> {
        if !is_valid_partition_coord(n, ell, m, s.value()) {
            return Err(SyndromeError::InvalidPartitionCoord {
                n,
                ell,
                m,
                s: s.value(),
            });
        }
        Ok(Self { n, ell, m, s })
    }

    /// Create without validation (for internal use).
    #[inline]
    pub(crate) fn new_unchecked(n: i32, ell: i32, m: i32, s: Chirality) -> Self {
        Self { n, ell, m, s }
    }

    /// Get the depth coordinate.
    #[inline]
    pub fn n(&self) -> i32 {
        self.n
    }

    /// Get the complexity coordinate.
    #[inline]
    pub fn ell(&self) -> i32 {
        self.ell
    }

    /// Get the orientation coordinate.
    #[inline]
    pub fn m(&self) -> i32 {
        self.m
    }

    /// Get the chirality coordinate.
    #[inline]
    pub fn chirality(&self) -> Chirality {
        self.s
    }

    /// Get chirality as numerical value.
    #[inline]
    pub fn s(&self) -> f64 {
        self.s.value()
    }

    /// Convert to array representation for numerical operations.
    #[inline]
    pub fn to_array(&self) -> [f64; 4] {
        [self.n as f64, self.ell as f64, self.m as f64, self.s.value()]
    }

    /// Get the partition capacity at this depth.
    ///
    /// Returns `C(n) = 2n²`.
    #[inline]
    pub fn capacity(&self) -> i32 {
        partition_capacity(self.n)
    }
}

/// Check if partition coordinates are valid.
///
/// Valid coordinates satisfy:
/// - n ≥ 1 (at least one partition)
/// - 0 ≤ ℓ ≤ n-1 (complexity bounded by depth)
/// - -ℓ ≤ m ≤ ℓ (orientation bounded by complexity)
/// - s ∈ {-0.5, +0.5} (chirality is binary)
#[inline]
pub fn is_valid_partition_coord(n: i32, ell: i32, m: i32, s: f64) -> bool {
    if n < 1 {
        return false;
    }
    if ell < 0 || ell > n - 1 {
        return false;
    }
    if m < -ell || m > ell {
        return false;
    }
    if (s - 0.5).abs() > 1e-10 && (s + 0.5).abs() > 1e-10 {
        return false;
    }
    true
}

/// Compute partition capacity at depth n.
///
/// The capacity `C(n) = 2n²` follows from:
/// - Sum over ℓ from 0 to n-1 of (2ℓ + 1) orientations
/// - Factor of 2 for chirality
///
/// This yields the sequence: 2, 8, 18, 32, 50, 72, 98, ...
/// which matches electron shell capacities in atomic physics.
///
/// # Panics
/// Panics if `n < 1`.
#[inline]
pub fn partition_capacity(n: i32) -> i32 {
    assert!(n >= 1, "Partition depth must be >= 1, got {}", n);
    2 * n * n
}

/// Compute categorical distance between partition states.
///
/// The categorical distance is defined as Euclidean distance in
/// partition coordinate space:
///
/// `d_cat = sqrt((n₁-n₂)² + (ℓ₁-ℓ₂)² + (m₁-m₂)² + (s₁-s₂)²)`
///
/// **IMPORTANT**: Categorical distance is independent of:
/// - Spatial distance (`d_cat ⊥ d_spatial`)
/// - Optical opacity (`∂d_cat/∂τ = 0`)
///
/// This enables opacity-independent measurement of states behind
/// arbitrary optical barriers.
#[inline]
pub fn categorical_distance(sigma1: &PartitionCoord, sigma2: &PartitionCoord) -> f64 {
    categorical_distance_raw(
        sigma1.n, sigma1.ell, sigma1.m, sigma1.s(),
        sigma2.n, sigma2.ell, sigma2.m, sigma2.s(),
    )
}

/// Compute categorical distance from raw coordinates.
#[inline]
pub fn categorical_distance_raw(
    n1: i32, ell1: i32, m1: i32, s1: f64,
    n2: i32, ell2: i32, m2: i32, s2: f64,
) -> f64 {
    let dn = (n1 - n2) as f64;
    let dell = (ell1 - ell2) as f64;
    let dm = (m1 - m2) as f64;
    let ds = s1 - s2;
    (dn * dn + dell * dell + dm * dm + ds * ds).sqrt()
}

/// Enumerate all partition states at depth n.
///
/// Returns all `C(n) = 2n²` partition states at the given depth.
pub fn enumerate_partition_states(n: i32) -> Vec<PartitionCoord> {
    assert!(n >= 1, "Partition depth must be >= 1");
    let capacity = partition_capacity(n) as usize;
    let mut states = Vec::with_capacity(capacity);

    for ell in 0..n {
        for m in -ell..=ell {
            states.push(PartitionCoord::new_unchecked(n, ell, m, Chirality::Minus));
            states.push(PartitionCoord::new_unchecked(n, ell, m, Chirality::Plus));
        }
    }

    states
}

/// Resolve ternary categorical address to physical value.
///
/// An address `[t_0, t_1, ..., t_{k-1}]` with `t_i ∈ {0, 1, 2}` resolves to:
///
/// `value = range_min + Σ_i (t_i / 3^{i+1}) * (range_max - range_min)`
///
/// # Errors
/// Returns `SyndromeError::InvalidAddressDigit` if any digit is not in {0, 1, 2}.
pub fn address_to_value(address: &[i32], range_min: f64, range_max: f64) -> Result<f64> {
    if address.is_empty() {
        return Ok((range_min + range_max) / 2.0);
    }

    let delta = range_max - range_min;
    let mut value = 0.0;

    for (i, &t) in address.iter().enumerate() {
        if t < 0 || t > 2 {
            return Err(SyndromeError::InvalidAddressDigit { digit: t });
        }
        value += (t as f64) / 3.0_f64.powi((i + 1) as i32);
    }

    Ok(range_min + value * delta)
}

/// Convert physical value to ternary categorical address.
///
/// # Errors
/// Returns `SyndromeError::OutOfBounds` if value is outside range.
pub fn value_to_address(
    value: f64,
    depth: usize,
    range_min: f64,
    range_max: f64,
) -> Result<Vec<i32>> {
    if value < range_min || value > range_max {
        return Err(SyndromeError::OutOfBounds {
            value,
            min: range_min,
            max: range_max,
        });
    }

    // Normalize to [0, 1]
    let normalized = (value - range_min) / (range_max - range_min);

    let mut address = Vec::with_capacity(depth);
    let mut remaining = normalized;

    for _ in 0..depth {
        let digit = (remaining * 3.0).floor() as i32;
        let digit = digit.min(2); // Clamp to valid range
        address.push(digit);
        remaining = remaining * 3.0 - digit as f64;
    }

    Ok(address)
}

/// Compute precision of address at given depth.
///
/// Precision = 1 / 3^depth
#[inline]
pub fn address_precision(depth: usize) -> f64 {
    1.0 / 3.0_f64.powi(depth as i32)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_partition_capacity() {
        assert_eq!(partition_capacity(1), 2);
        assert_eq!(partition_capacity(2), 8);
        assert_eq!(partition_capacity(3), 18);
        assert_eq!(partition_capacity(4), 32);
        assert_eq!(partition_capacity(5), 50);
    }

    #[test]
    fn test_valid_coords() {
        assert!(PartitionCoord::new(1, 0, 0, Chirality::Plus).is_ok());
        assert!(PartitionCoord::new(2, 1, -1, Chirality::Minus).is_ok());
        assert!(PartitionCoord::new(3, 2, 2, Chirality::Plus).is_ok());
    }

    #[test]
    fn test_invalid_coords() {
        // n < 1
        assert!(PartitionCoord::new(0, 0, 0, Chirality::Plus).is_err());
        // ell >= n
        assert!(PartitionCoord::new(2, 2, 0, Chirality::Plus).is_err());
        // |m| > ell
        assert!(PartitionCoord::new(2, 1, 2, Chirality::Plus).is_err());
    }

    #[test]
    fn test_enumerate_states() {
        let states = enumerate_partition_states(2);
        assert_eq!(states.len(), 8);
    }

    #[test]
    fn test_categorical_distance_self() {
        let coord = PartitionCoord::new(2, 1, 0, Chirality::Plus).unwrap();
        assert!((categorical_distance(&coord, &coord)).abs() < 1e-10);
    }

    #[test]
    fn test_categorical_distance_chirality() {
        let c1 = PartitionCoord::new(1, 0, 0, Chirality::Plus).unwrap();
        let c2 = PartitionCoord::new(1, 0, 0, Chirality::Minus).unwrap();
        assert!((categorical_distance(&c1, &c2) - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_address_resolution() {
        let address = vec![1, 1, 1];
        let value = address_to_value(&address, 0.0, 1.0).unwrap();
        assert!((value - 0.481481).abs() < 0.001);
    }

    #[test]
    fn test_value_to_address() {
        let value = 0.5;
        let address = value_to_address(value, 5, 0.0, 1.0).unwrap();
        let resolved = address_to_value(&address, 0.0, 1.0).unwrap();
        assert!((value - resolved).abs() < address_precision(5));
    }

    #[test]
    fn test_address_precision() {
        assert!((address_precision(1) - 1.0/3.0).abs() < 1e-10);
        assert!((address_precision(2) - 1.0/9.0).abs() < 1e-10);
        assert!((address_precision(3) - 1.0/27.0).abs() < 1e-10);
    }
}
