//! Coherence Computation Module
//!
//! Implements the universal coherence equation and related computations:
//!
//! η = (Π_obs - Π_deg) / (Π_opt - Π_deg)
//!
//! where:
//! - η ∈ [0, 1] is the coherence index
//! - Π_obs is the observed performance metric
//! - Π_opt is the optimal performance (η = 1)
//! - Π_deg is the degraded performance (η = 0)

use serde::{Deserialize, Serialize};
use crate::{Result, SyndromeError};

/// Oscillator class type.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum OscillatorClass {
    /// Protein folding oscillators (P)
    Protein,
    /// Enzyme catalytic oscillators (E)
    Enzyme,
    /// Ion channel gating oscillators (C)
    Channel,
    /// Membrane potential oscillators (M)
    Membrane,
    /// ATP synthesis oscillators (A)
    Atp,
    /// Gene expression oscillators (G)
    Genetic,
    /// Calcium signaling oscillators (Ca)
    Calcium,
    /// Circadian rhythm oscillators (R)
    Circadian,
}

impl OscillatorClass {
    /// Get short code for the class.
    pub fn code(&self) -> &'static str {
        match self {
            OscillatorClass::Protein => "P",
            OscillatorClass::Enzyme => "E",
            OscillatorClass::Channel => "C",
            OscillatorClass::Membrane => "M",
            OscillatorClass::Atp => "A",
            OscillatorClass::Genetic => "G",
            OscillatorClass::Calcium => "Ca",
            OscillatorClass::Circadian => "R",
        }
    }

    /// Get full name for the class.
    pub fn name(&self) -> &'static str {
        match self {
            OscillatorClass::Protein => "Protein/Misfolding",
            OscillatorClass::Enzyme => "Enzyme/Metabolic",
            OscillatorClass::Channel => "Channel/Channelopathy",
            OscillatorClass::Membrane => "Membrane/Excitability",
            OscillatorClass::Atp => "ATP/Mitochondrial",
            OscillatorClass::Genetic => "Genetic/Expression",
            OscillatorClass::Calcium => "Calcium/Signaling",
            OscillatorClass::Circadian => "Circadian/Rhythm",
        }
    }

    /// Get all oscillator classes in order.
    pub fn all() -> [OscillatorClass; 8] {
        [
            OscillatorClass::Protein,
            OscillatorClass::Enzyme,
            OscillatorClass::Channel,
            OscillatorClass::Membrane,
            OscillatorClass::Atp,
            OscillatorClass::Genetic,
            OscillatorClass::Calcium,
            OscillatorClass::Circadian,
        ]
    }

    /// Get index (0-7) for the class.
    pub fn index(&self) -> usize {
        match self {
            OscillatorClass::Protein => 0,
            OscillatorClass::Enzyme => 1,
            OscillatorClass::Channel => 2,
            OscillatorClass::Membrane => 3,
            OscillatorClass::Atp => 4,
            OscillatorClass::Genetic => 5,
            OscillatorClass::Calcium => 6,
            OscillatorClass::Circadian => 7,
        }
    }

    /// Get class from index.
    pub fn from_index(idx: usize) -> Option<Self> {
        match idx {
            0 => Some(OscillatorClass::Protein),
            1 => Some(OscillatorClass::Enzyme),
            2 => Some(OscillatorClass::Channel),
            3 => Some(OscillatorClass::Membrane),
            4 => Some(OscillatorClass::Atp),
            5 => Some(OscillatorClass::Genetic),
            6 => Some(OscillatorClass::Calcium),
            7 => Some(OscillatorClass::Circadian),
            _ => None,
        }
    }
}

/// Represents a cellular oscillator with performance metrics.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Oscillator {
    /// Oscillator class
    pub class: OscillatorClass,
    /// Observed performance metric
    pub pi_obs: f64,
    /// Optimal performance metric
    pub pi_opt: f64,
    /// Degraded performance metric
    pub pi_deg: f64,
    /// Entropic coupling weight
    pub weight: f64,
    /// Optional descriptive name
    pub name: Option<String>,
}

impl Oscillator {
    /// Create a new oscillator.
    pub fn new(
        class: OscillatorClass,
        pi_obs: f64,
        pi_opt: f64,
        pi_deg: f64,
    ) -> Self {
        Self {
            class,
            pi_obs,
            pi_opt,
            pi_deg,
            weight: 1.0,
            name: None,
        }
    }

    /// Create with weight.
    pub fn with_weight(mut self, weight: f64) -> Self {
        self.weight = weight;
        self
    }

    /// Create with name.
    pub fn with_name(mut self, name: impl Into<String>) -> Self {
        self.name = Some(name.into());
        self
    }

    /// Compute coherence index for this oscillator.
    pub fn coherence(&self) -> f64 {
        coherence_index(self.pi_obs, self.pi_opt, self.pi_deg)
    }

    /// Compute disease index D = 1 - η.
    pub fn disease_index(&self) -> f64 {
        1.0 - self.coherence()
    }
}

/// Compute the universal coherence index.
///
/// The coherence index η is defined as:
///
/// η = (Π_obs - Π_deg) / (Π_opt - Π_deg)    if Π_opt > Π_deg
/// η = (Π_deg - Π_obs) / (Π_deg - Π_opt)    if Π_opt < Π_deg
///
/// The result is clamped to [0, 1].
///
/// # Examples
///
/// ```rust
/// use syndrome::coherence::coherence_index;
///
/// // Standard case: higher is better
/// assert!((coherence_index(0.8, 1.0, 0.0) - 0.8).abs() < 1e-10);
///
/// // Inverted case: lower is better (e.g., folding cycles)
/// assert!((coherence_index(13.0, 12.0, 16.0) - 0.75).abs() < 1e-10);
/// ```
pub fn coherence_index(pi_obs: f64, pi_opt: f64, pi_deg: f64) -> f64 {
    // Degenerate case
    if (pi_opt - pi_deg).abs() < 1e-10 {
        return 0.5;
    }

    let eta = if pi_opt > pi_deg {
        // Higher is better
        (pi_obs - pi_deg) / (pi_opt - pi_deg)
    } else {
        // Lower is better (e.g., folding cycles)
        (pi_deg - pi_obs) / (pi_deg - pi_opt)
    };

    // Clamp to [0, 1]
    eta.clamp(0.0, 1.0)
}

/// Compute weighted cellular coherence from oscillator ensemble.
///
/// η_cell = (1/W) Σᵢ wᵢ ηᵢ
///
/// where W = Σᵢ wᵢ is the total weight.
///
/// # Errors
/// Returns error if oscillators is empty.
pub fn cellular_coherence(oscillators: &[Oscillator]) -> Result<f64> {
    if oscillators.is_empty() {
        return Err(SyndromeError::EmptyCollection {
            context: "oscillators",
        });
    }

    let total_weight: f64 = oscillators.iter().map(|o| o.weight).sum();
    if total_weight.abs() < 1e-10 {
        return Ok(0.0);
    }

    let weighted_sum: f64 = oscillators
        .iter()
        .map(|o| o.weight * o.coherence())
        .sum();

    Ok(weighted_sum / total_weight)
}

/// Compute therapeutic efficacy from coherence change.
///
/// E = (η_treated - η_untreated) / (η_healthy - η_untreated)
///
/// # Arguments
/// * `eta_treated` - Coherence after treatment
/// * `eta_untreated` - Coherence before treatment
/// * `eta_healthy` - Target healthy coherence (default 1.0)
pub fn therapeutic_efficacy(
    eta_treated: f64,
    eta_untreated: f64,
    eta_healthy: f64,
) -> f64 {
    let gap = eta_healthy - eta_untreated;
    if gap.abs() < 1e-10 {
        return if eta_treated >= eta_healthy { 1.0 } else { 0.0 };
    }

    let improvement = eta_treated - eta_untreated;
    improvement / gap
}

/// Predict coherence after treatment with given efficacy.
///
/// η_pred = η + E·α·(1-η)
///
/// where α is treatment strength factor.
///
/// # Arguments
/// * `eta_untreated` - Coherence before treatment
/// * `efficacy` - Treatment efficacy E ∈ [0, 1]
/// * `alpha` - Treatment strength factor α ∈ [0, 1]
pub fn predicted_coherence_after_treatment(eta_untreated: f64, efficacy: f64, alpha: f64) -> f64 {
    (eta_untreated + efficacy * alpha * (1.0 - eta_untreated)).clamp(0.0, 1.0)
}

// =============================================================================
// Class-specific coherence functions
// =============================================================================

/// Compute coherence from protein folding cycles.
///
/// For protein folding, fewer cycles indicates better coherence:
/// η = (k_max - k_obs) / (k_max - k_min)
pub fn coherence_from_folding_cycles(k_obs: i32, k_min: i32, k_max: i32) -> f64 {
    coherence_index(k_obs as f64, k_min as f64, k_max as f64)
}

/// Compute coherence from enzyme turnover number.
///
/// For enzymes, higher turnover indicates better coherence:
/// η = (k_cat_obs - k_cat_min) / (k_cat_max - k_cat_min)
pub fn coherence_from_turnover(k_cat_obs: f64, k_cat_max: f64, k_cat_min: f64) -> f64 {
    coherence_index(k_cat_obs, k_cat_max, k_cat_min)
}

/// Compute coherence from ion channel open probability.
///
/// Channels have optimal open probability; deviation indicates dysfunction.
pub fn coherence_from_open_probability(p_o_obs: f64, p_o_opt: f64, p_o_stuck: f64) -> f64 {
    if (p_o_opt - p_o_stuck).abs() < 1e-10 {
        return 0.5;
    }

    let deviation = (p_o_obs - p_o_opt).abs();
    let max_deviation = (p_o_stuck - p_o_opt).abs();

    if max_deviation < 1e-10 {
        return if deviation < 1e-10 { 1.0 } else { 0.0 };
    }

    (1.0 - deviation / max_deviation).clamp(0.0, 1.0)
}

/// Compute coherence from membrane potential oscillation amplitude.
///
/// η = ΔV_obs / ΔV_max
pub fn coherence_from_membrane_amplitude(delta_v_obs: f64, delta_v_max: f64) -> f64 {
    if delta_v_max <= 0.0 {
        return 0.0;
    }
    (delta_v_obs / delta_v_max).clamp(0.0, 1.0)
}

/// Compute coherence from circadian period stability.
///
/// η = 1 - σ_T / T_0
pub fn coherence_from_period_stability(sigma_t: f64, t_0: f64) -> f64 {
    if t_0 <= 0.0 {
        return 0.0;
    }
    (1.0 - sigma_t / t_0).clamp(0.0, 1.0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_coherence_index_basic() {
        assert!((coherence_index(0.8, 1.0, 0.0) - 0.8).abs() < 1e-10);
        assert!((coherence_index(0.0, 1.0, 0.0) - 0.0).abs() < 1e-10);
        assert!((coherence_index(1.0, 1.0, 0.0) - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_coherence_index_inverted() {
        // Fewer folding cycles is better
        assert!((coherence_index(13.0, 12.0, 16.0) - 0.75).abs() < 1e-10);
        assert!((coherence_index(12.0, 12.0, 16.0) - 1.0).abs() < 1e-10);
        assert!((coherence_index(16.0, 12.0, 16.0) - 0.0).abs() < 1e-10);
    }

    #[test]
    fn test_coherence_index_degenerate() {
        assert!((coherence_index(0.5, 0.5, 0.5) - 0.5).abs() < 1e-10);
    }

    #[test]
    fn test_coherence_clamping() {
        // Out of range should be clamped
        assert!((coherence_index(1.5, 1.0, 0.0) - 1.0).abs() < 1e-10);
        assert!((coherence_index(-0.5, 1.0, 0.0) - 0.0).abs() < 1e-10);
    }

    #[test]
    fn test_oscillator() {
        let osc = Oscillator::new(OscillatorClass::Protein, 0.8, 1.0, 0.0);
        assert!((osc.coherence() - 0.8).abs() < 1e-10);
        assert!((osc.disease_index() - 0.2).abs() < 1e-10);
    }

    #[test]
    fn test_cellular_coherence() {
        let oscillators = vec![
            Oscillator::new(OscillatorClass::Protein, 0.8, 1.0, 0.0).with_weight(1.0),
            Oscillator::new(OscillatorClass::Enzyme, 0.6, 1.0, 0.0).with_weight(1.0),
        ];
        let eta = cellular_coherence(&oscillators).unwrap();
        assert!((eta - 0.7).abs() < 1e-10);
    }

    #[test]
    fn test_cellular_coherence_weighted() {
        let oscillators = vec![
            Oscillator::new(OscillatorClass::Protein, 0.8, 1.0, 0.0).with_weight(2.0),
            Oscillator::new(OscillatorClass::Enzyme, 0.6, 1.0, 0.0).with_weight(1.0),
        ];
        let eta = cellular_coherence(&oscillators).unwrap();
        // (2*0.8 + 1*0.6) / 3 = 2.2 / 3 ≈ 0.733
        assert!((eta - 0.7333333).abs() < 1e-5);
    }

    #[test]
    fn test_therapeutic_efficacy() {
        // Full recovery: eta_treated=1.0, eta_untreated=0.4, eta_healthy=1.0
        assert!((therapeutic_efficacy(1.0, 0.4, 1.0) - 1.0).abs() < 1e-10);
        // No effect: eta_treated=0.4, eta_untreated=0.4
        assert!((therapeutic_efficacy(0.4, 0.4, 1.0) - 0.0).abs() < 1e-10);
        // 50% efficacy: eta_treated=0.7, eta_untreated=0.4
        assert!((therapeutic_efficacy(0.7, 0.4, 1.0) - 0.5).abs() < 1e-10);
    }

    #[test]
    fn test_predicted_coherence() {
        // eta_pred = 0.4 + 0.5*1.0*(1-0.4) = 0.4 + 0.3 = 0.7
        let eta = predicted_coherence_after_treatment(0.4, 0.5, 1.0);
        assert!((eta - 0.7).abs() < 1e-10);
    }

    #[test]
    fn test_folding_cycles() {
        assert!((coherence_from_folding_cycles(12, 12, 16) - 1.0).abs() < 1e-10);
        assert!((coherence_from_folding_cycles(14, 12, 16) - 0.5).abs() < 1e-10);
        assert!((coherence_from_folding_cycles(16, 12, 16) - 0.0).abs() < 1e-10);
    }

    #[test]
    fn test_oscillator_classes() {
        assert_eq!(OscillatorClass::Protein.index(), 0);
        assert_eq!(OscillatorClass::Circadian.index(), 7);
        assert_eq!(OscillatorClass::from_index(0), Some(OscillatorClass::Protein));
        assert_eq!(OscillatorClass::from_index(8), None);
    }
}
