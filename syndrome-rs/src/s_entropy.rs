//! S-Entropy Space Module
//!
//! Implements the S-entropy coordinate system S = [0,1]³ comprising:
//! - Sₖ: Knowledge entropy (uncertainty in state identification)
//! - Sₜ: Temporal entropy (uncertainty in timing relationships)
//! - Sₑ: Evolution entropy (uncertainty in trajectory progression)
//!
//! Any categorical state in bounded phase space maps uniquely to a point in S.

use serde::{Deserialize, Serialize};
use crate::{Result, SyndromeError};

/// Point in S-entropy space.
///
/// All coordinates are normalized to [0, 1] where:
/// - 0 indicates minimum entropy (maximum certainty)
/// - 1 indicates maximum entropy (maximum uncertainty)
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct SEntropyPoint {
    /// Knowledge entropy (state identification uncertainty)
    pub s_k: f64,
    /// Temporal entropy (timing uncertainty)
    pub s_t: f64,
    /// Evolution entropy (trajectory uncertainty)
    pub s_e: f64,
}

impl SEntropyPoint {
    /// Create a new S-entropy point with validation.
    ///
    /// # Errors
    /// Returns `SyndromeError::InvalidSEntropyCoord` if any coordinate is outside [0, 1].
    pub fn new(s_k: f64, s_t: f64, s_e: f64) -> Result<Self> {
        Self::validate_coord("s_k", s_k)?;
        Self::validate_coord("s_t", s_t)?;
        Self::validate_coord("s_e", s_e)?;
        Ok(Self { s_k, s_t, s_e })
    }

    /// Create without validation (for internal use).
    #[inline]
    pub(crate) fn new_unchecked(s_k: f64, s_t: f64, s_e: f64) -> Self {
        Self { s_k, s_t, s_e }
    }

    /// Validate a single coordinate.
    fn validate_coord(name: &'static str, value: f64) -> Result<()> {
        if value < 0.0 || value > 1.0 {
            return Err(SyndromeError::InvalidSEntropyCoord {
                coord: name,
                value,
            });
        }
        Ok(())
    }

    /// Get knowledge entropy.
    #[inline]
    pub fn s_k(&self) -> f64 {
        self.s_k
    }

    /// Get temporal entropy.
    #[inline]
    pub fn s_t(&self) -> f64 {
        self.s_t
    }

    /// Get evolution entropy.
    #[inline]
    pub fn s_e(&self) -> f64 {
        self.s_e
    }

    /// Convert to tuple representation.
    #[inline]
    pub fn to_tuple(&self) -> (f64, f64, f64) {
        (self.s_k, self.s_t, self.s_e)
    }

    /// Convert to array representation.
    #[inline]
    pub fn to_array(&self) -> [f64; 3] {
        [self.s_k, self.s_t, self.s_e]
    }

    /// Create from array.
    ///
    /// # Errors
    /// Returns error if any value is outside [0, 1].
    pub fn from_array(arr: [f64; 3]) -> Result<Self> {
        Self::new(arr[0], arr[1], arr[2])
    }

    /// Compute total entropy as Euclidean norm.
    #[inline]
    pub fn total_entropy(&self) -> f64 {
        (self.s_k * self.s_k + self.s_t * self.s_t + self.s_e * self.s_e).sqrt()
    }

    /// Compute mean entropy across coordinates.
    #[inline]
    pub fn mean_entropy(&self) -> f64 {
        (self.s_k + self.s_t + self.s_e) / 3.0
    }

    /// Create the origin point (zero entropy).
    #[inline]
    pub fn origin() -> Self {
        Self::new_unchecked(0.0, 0.0, 0.0)
    }

    /// Create the maximum entropy point.
    #[inline]
    pub fn max_entropy() -> Self {
        Self::new_unchecked(1.0, 1.0, 1.0)
    }

    /// Compute distance to another point.
    #[inline]
    pub fn distance(&self, other: &Self) -> f64 {
        s_entropy_distance(self, other)
    }

    /// Check if coordinates are valid (all in [0, 1]).
    #[inline]
    pub fn is_valid(&self) -> bool {
        (0.0..=1.0).contains(&self.s_k)
            && (0.0..=1.0).contains(&self.s_t)
            && (0.0..=1.0).contains(&self.s_e)
    }

    /// Linear interpolation between two points (static method).
    ///
    /// # Arguments
    /// * `p1` - Starting point (t=0)
    /// * `p2` - Ending point (t=1)
    /// * `t` - Interpolation parameter (clamped to [0, 1])
    #[inline]
    pub fn interpolate(p1: &Self, p2: &Self, t: f64) -> Self {
        let t = t.clamp(0.0, 1.0);
        Self::new_unchecked(
            (1.0 - t) * p1.s_k + t * p2.s_k,
            (1.0 - t) * p1.s_t + t * p2.s_t,
            (1.0 - t) * p1.s_e + t * p2.s_e,
        )
    }
}

impl Default for SEntropyPoint {
    fn default() -> Self {
        Self::origin()
    }
}

/// Compute distance between two S-entropy points.
///
/// Uses Euclidean distance in the flat S-entropy space.
#[inline]
pub fn s_entropy_distance(p1: &SEntropyPoint, p2: &SEntropyPoint) -> f64 {
    let dk = p1.s_k - p2.s_k;
    let dt = p1.s_t - p2.s_t;
    let de = p1.s_e - p2.s_e;
    (dk * dk + dt * dt + de * de).sqrt()
}

/// Linear interpolation between two S-entropy points.
///
/// # Arguments
/// * `p1` - Starting point (t=0)
/// * `p2` - Ending point (t=1)
/// * `t` - Interpolation parameter in [0, 1]
///
/// # Errors
/// Returns error if `t` is outside [0, 1].
pub fn interpolate_s_entropy(p1: &SEntropyPoint, p2: &SEntropyPoint, t: f64) -> Result<SEntropyPoint> {
    if t < 0.0 || t > 1.0 {
        return Err(SyndromeError::OutOfBounds {
            value: t,
            min: 0.0,
            max: 1.0,
        });
    }

    let s_k = (1.0 - t) * p1.s_k + t * p2.s_k;
    let s_t = (1.0 - t) * p1.s_t + t * p2.s_t;
    let s_e = (1.0 - t) * p1.s_e + t * p2.s_e;

    // Result is guaranteed to be in [0, 1] since both inputs are
    Ok(SEntropyPoint::new_unchecked(s_k, s_t, s_e))
}

/// Normalize raw entropy values to S-entropy coordinates.
///
/// # Arguments
/// * `values` - Raw entropy values (S_k, S_t, S_e)
/// * `bounds` - Optional bounds ((min_k, max_k), (min_t, max_t), (min_e, max_e))
///
/// # Errors
/// Returns error if bounds are degenerate (min == max).
pub fn normalize_s_entropy(
    values: (f64, f64, f64),
    bounds: Option<((f64, f64), (f64, f64), (f64, f64))>,
) -> Result<SEntropyPoint> {
    let (mut s_k, mut s_t, mut s_e) = values;

    if let Some(((min_k, max_k), (min_t, max_t), (min_e, max_e))) = bounds {
        s_k = if (max_k - min_k).abs() > 1e-10 {
            (s_k - min_k) / (max_k - min_k)
        } else {
            0.5
        };
        s_t = if (max_t - min_t).abs() > 1e-10 {
            (s_t - min_t) / (max_t - min_t)
        } else {
            0.5
        };
        s_e = if (max_e - min_e).abs() > 1e-10 {
            (s_e - min_e) / (max_e - min_e)
        } else {
            0.5
        };
    }

    // Clamp to [0, 1]
    s_k = s_k.clamp(0.0, 1.0);
    s_t = s_t.clamp(0.0, 1.0);
    s_e = s_e.clamp(0.0, 1.0);

    Ok(SEntropyPoint::new_unchecked(s_k, s_t, s_e))
}

/// Compute Shannon entropy from probability distribution.
///
/// S = -Σ p_i log(p_i)
///
/// Normalized to [0, 1] by dividing by log(N).
pub fn shannon_entropy(probabilities: &[f64]) -> f64 {
    if probabilities.is_empty() {
        return 0.0;
    }

    let n = probabilities.len();
    if n == 1 {
        return 0.0;
    }

    // Shannon entropy
    let entropy: f64 = probabilities
        .iter()
        .filter(|&&p| p > 0.0)
        .map(|&p| -p * p.ln())
        .sum();

    // Normalize by maximum entropy log(N)
    let max_entropy = (n as f64).ln();
    if max_entropy.abs() < 1e-10 {
        return 0.0;
    }

    (entropy / max_entropy).clamp(0.0, 1.0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_s_entropy() {
        let p = SEntropyPoint::new(0.5, 0.3, 0.7).unwrap();
        assert!((p.s_k() - 0.5).abs() < 1e-10);
        assert!((p.s_t() - 0.3).abs() < 1e-10);
        assert!((p.s_e() - 0.7).abs() < 1e-10);
    }

    #[test]
    fn test_invalid_s_entropy() {
        assert!(SEntropyPoint::new(1.5, 0.5, 0.5).is_err());
        assert!(SEntropyPoint::new(-0.1, 0.5, 0.5).is_err());
    }

    #[test]
    fn test_total_entropy() {
        let p = SEntropyPoint::new(0.0, 0.0, 0.0).unwrap();
        assert!(p.total_entropy().abs() < 1e-10);

        let p = SEntropyPoint::new(1.0, 1.0, 1.0).unwrap();
        assert!((p.total_entropy() - 3.0_f64.sqrt()).abs() < 1e-10);
    }

    #[test]
    fn test_distance_self() {
        let p = SEntropyPoint::new(0.5, 0.5, 0.5).unwrap();
        assert!(s_entropy_distance(&p, &p).abs() < 1e-10);
    }

    #[test]
    fn test_distance_symmetry() {
        let p1 = SEntropyPoint::new(0.1, 0.2, 0.3).unwrap();
        let p2 = SEntropyPoint::new(0.4, 0.5, 0.6).unwrap();
        assert!((s_entropy_distance(&p1, &p2) - s_entropy_distance(&p2, &p1)).abs() < 1e-10);
    }

    #[test]
    fn test_interpolation() {
        let p1 = SEntropyPoint::new(0.0, 0.0, 0.0).unwrap();
        let p2 = SEntropyPoint::new(1.0, 1.0, 1.0).unwrap();

        let mid = interpolate_s_entropy(&p1, &p2, 0.5).unwrap();
        assert!((mid.s_k() - 0.5).abs() < 1e-10);
        assert!((mid.s_t() - 0.5).abs() < 1e-10);
        assert!((mid.s_e() - 0.5).abs() < 1e-10);
    }

    #[test]
    fn test_interpolation_boundaries() {
        let p1 = SEntropyPoint::new(0.2, 0.3, 0.4).unwrap();
        let p2 = SEntropyPoint::new(0.8, 0.7, 0.6).unwrap();

        let at_start = interpolate_s_entropy(&p1, &p2, 0.0).unwrap();
        assert!((at_start.s_k() - p1.s_k()).abs() < 1e-10);

        let at_end = interpolate_s_entropy(&p1, &p2, 1.0).unwrap();
        assert!((at_end.s_k() - p2.s_k()).abs() < 1e-10);
    }

    #[test]
    fn test_shannon_entropy_uniform() {
        // Uniform distribution should give entropy = 1 (normalized)
        let probs = vec![0.25, 0.25, 0.25, 0.25];
        let entropy = shannon_entropy(&probs);
        assert!((entropy - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_shannon_entropy_deterministic() {
        // Deterministic distribution should give entropy = 0
        let probs = vec![1.0, 0.0, 0.0, 0.0];
        let entropy = shannon_entropy(&probs);
        assert!(entropy.abs() < 1e-10);
    }
}
