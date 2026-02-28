//! Disease State Module
//!
//! Implements disease state formalism:
//! - Disease vector D = (D_P, D_E, D_C, D_M, D_A, D_G, D_Ca, D_R)
//! - Disease classification by dominant component
//! - Disease severity computation

use serde::{Deserialize, Serialize};
use crate::coherence::{Oscillator, OscillatorClass};
use crate::{Result, SyndromeError};

/// Disease class names and descriptions.
pub const DISEASE_CLASS_NAMES: [&str; 8] = [
    "Misfolding",
    "Metabolic",
    "Channelopathy",
    "Excitability",
    "Mitochondrial",
    "Expression",
    "Signaling",
    "Rhythm",
];

/// Example diseases for each class.
pub const DISEASE_CLASS_EXAMPLES: [&[&str]; 8] = [
    &["Alzheimer's", "Parkinson's", "Prion diseases", "Huntington's"],
    &["Diabetes", "PKU", "Gaucher disease", "Galactosemia"],
    &["Cystic fibrosis", "Long QT syndrome", "Myotonia", "Episodic ataxia"],
    &["Epilepsy", "Cardiac arrhythmia", "Migraine"],
    &["MELAS", "Leigh syndrome", "LHON", "Mitochondrial myopathy"],
    &["Cancer", "Developmental disorders", "Thalassemia"],
    &["Malignant hyperthermia", "Timothy syndrome", "Cardiac disorders"],
    &["Sleep disorders", "Jet lag", "Seasonal affective disorder"],
];

/// Disease state vector across eight oscillator classes.
///
/// D = (D_P, D_E, D_C, D_M, D_A, D_G, D_Ca, D_R)
///
/// where D_i = 1 - η_i is the disease index for class i.
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct DiseaseVector {
    /// D_P: Protein (misfolding)
    pub d_p: f64,
    /// D_E: Enzyme (metabolic)
    pub d_e: f64,
    /// D_C: Channel (channelopathy)
    pub d_c: f64,
    /// D_M: Membrane (excitability)
    pub d_m: f64,
    /// D_A: ATP (mitochondrial)
    pub d_a: f64,
    /// D_G: Genetic (expression)
    pub d_g: f64,
    /// D_Ca: Calcium (signaling)
    pub d_ca: f64,
    /// D_R: Circadian (rhythm)
    pub d_r: f64,
}

impl DiseaseVector {
    /// Create a new disease vector with validation.
    ///
    /// # Errors
    /// Returns error if any component is outside [0, 1].
    pub fn new(
        d_p: f64,
        d_e: f64,
        d_c: f64,
        d_m: f64,
        d_a: f64,
        d_g: f64,
        d_ca: f64,
        d_r: f64,
    ) -> Result<Self> {
        let v = Self {
            d_p,
            d_e,
            d_c,
            d_m,
            d_a,
            d_g,
            d_ca,
            d_r,
        };
        v.validate()?;
        Ok(v)
    }

    /// Create without validation (for internal use).
    pub(crate) fn new_unchecked(
        d_p: f64,
        d_e: f64,
        d_c: f64,
        d_m: f64,
        d_a: f64,
        d_g: f64,
        d_ca: f64,
        d_r: f64,
    ) -> Self {
        Self {
            d_p,
            d_e,
            d_c,
            d_m,
            d_a,
            d_g,
            d_ca,
            d_r,
        }
    }

    /// Validate all components are in [0, 1].
    fn validate(&self) -> Result<()> {
        let components = [
            ("P", self.d_p),
            ("E", self.d_e),
            ("C", self.d_c),
            ("M", self.d_m),
            ("A", self.d_a),
            ("G", self.d_g),
            ("Ca", self.d_ca),
            ("R", self.d_r),
        ];

        for &(class, value) in &components {
            if value < 0.0 || value > 1.0 {
                return Err(SyndromeError::InvalidDiseaseIndex { class, value });
            }
        }
        Ok(())
    }

    /// Convert to array representation.
    #[inline]
    pub fn to_array(&self) -> [f64; 8] {
        [
            self.d_p, self.d_e, self.d_c, self.d_m,
            self.d_a, self.d_g, self.d_ca, self.d_r,
        ]
    }

    /// Create from array.
    ///
    /// # Errors
    /// Returns error if any value is outside [0, 1].
    pub fn from_array(arr: [f64; 8]) -> Result<Self> {
        Self::new(
            arr[0], arr[1], arr[2], arr[3],
            arr[4], arr[5], arr[6], arr[7],
        )
    }

    /// Create from coherence values.
    pub fn from_coherences(
        eta_p: f64,
        eta_e: f64,
        eta_c: f64,
        eta_m: f64,
        eta_a: f64,
        eta_g: f64,
        eta_ca: f64,
        eta_r: f64,
    ) -> Result<Self> {
        Self::new(
            1.0 - eta_p,
            1.0 - eta_e,
            1.0 - eta_c,
            1.0 - eta_m,
            1.0 - eta_a,
            1.0 - eta_g,
            1.0 - eta_ca,
            1.0 - eta_r,
        )
    }

    /// Get the dominant disease class (argmax D_i).
    pub fn dominant_class(&self) -> OscillatorClass {
        let arr = self.to_array();
        let (idx, _) = arr
            .iter()
            .enumerate()
            .max_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap())
            .unwrap();
        OscillatorClass::from_index(idx).unwrap()
    }

    /// Get the dominant disease index value.
    pub fn dominant_value(&self) -> f64 {
        self.to_array()
            .iter()
            .cloned()
            .fold(f64::NEG_INFINITY, f64::max)
    }

    /// Compute total disease severity.
    ///
    /// D_total = (1/W) Σᵢ wᵢ Dᵢ
    ///
    /// If no weights provided, uses equal weights (mean).
    pub fn severity(&self, weights: Option<&[f64; 8]>) -> f64 {
        let arr = self.to_array();

        match weights {
            None => arr.iter().sum::<f64>() / 8.0,
            Some(w) => {
                let total_weight: f64 = w.iter().sum();
                if total_weight.abs() < 1e-10 {
                    return 0.0;
                }
                let weighted_sum: f64 = arr.iter().zip(w.iter()).map(|(d, w)| d * w).sum();
                weighted_sum / total_weight
            }
        }
    }

    /// Get index for given class.
    pub fn get(&self, class: OscillatorClass) -> f64 {
        match class {
            OscillatorClass::Protein => self.d_p,
            OscillatorClass::Enzyme => self.d_e,
            OscillatorClass::Channel => self.d_c,
            OscillatorClass::Membrane => self.d_m,
            OscillatorClass::Atp => self.d_a,
            OscillatorClass::Genetic => self.d_g,
            OscillatorClass::Calcium => self.d_ca,
            OscillatorClass::Circadian => self.d_r,
        }
    }

    /// Full disease classification.
    ///
    /// Returns (class_code, class_name, example_diseases).
    pub fn classification(&self) -> (&'static str, &'static str, &'static [&'static str]) {
        let class = self.dominant_class();
        let idx = class.index();
        (class.code(), DISEASE_CLASS_NAMES[idx], DISEASE_CLASS_EXAMPLES[idx])
    }
}

impl Default for DiseaseVector {
    /// Returns a healthy vector (all zeros).
    fn default() -> Self {
        Self::new_unchecked(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    }
}

/// Compute disease vector from oscillator ensemble.
///
/// Groups oscillators by class and computes weighted disease index
/// for each class.
pub fn disease_vector_from_oscillators(oscillators: &[Oscillator]) -> DiseaseVector {
    // Group by class and compute weighted average coherence
    let mut class_data: [Vec<(f64, f64)>; 8] = Default::default();

    for osc in oscillators {
        let eta = osc.coherence();
        let weight = osc.weight;
        class_data[osc.class.index()].push((eta, weight));
    }

    let mut disease_indices = [0.0; 8];
    for (i, values) in class_data.iter().enumerate() {
        if values.is_empty() {
            disease_indices[i] = 0.0; // Default to healthy
        } else {
            let total_weight: f64 = values.iter().map(|(_, w)| w).sum();
            if total_weight.abs() < 1e-10 {
                disease_indices[i] = 0.0;
            } else {
                let weighted_eta: f64 = values.iter().map(|(eta, w)| eta * w).sum::<f64>() / total_weight;
                disease_indices[i] = 1.0 - weighted_eta;
            }
        }
    }

    DiseaseVector::new_unchecked(
        disease_indices[0],
        disease_indices[1],
        disease_indices[2],
        disease_indices[3],
        disease_indices[4],
        disease_indices[5],
        disease_indices[6],
        disease_indices[7],
    )
}

/// Classify disease by dominant component.
///
/// class(D) = argmax_i D_i
pub fn classify_disease(d: &DiseaseVector) -> OscillatorClass {
    d.dominant_class()
}

/// Compute total disease severity.
pub fn disease_severity(d: &DiseaseVector, weights: Option<&[f64; 8]>) -> f64 {
    d.severity(weights)
}

/// Compute distance between two disease signatures.
///
/// Uses Euclidean distance in 8-dimensional disease space.
pub fn disease_signature_distance(d1: &DiseaseVector, d2: &DiseaseVector) -> f64 {
    let a1 = d1.to_array();
    let a2 = d2.to_array();

    let sum_sq: f64 = a1
        .iter()
        .zip(a2.iter())
        .map(|(x, y)| (x - y).powi(2))
        .sum();

    sum_sq.sqrt()
}

/// Return a healthy disease vector (all zeros).
pub fn healthy_vector() -> DiseaseVector {
    DiseaseVector::default()
}

/// Generate a synthetic disease profile.
pub fn generate_disease_profile(
    dominant_class: OscillatorClass,
    severity: f64,
    spread: f64,
) -> DiseaseVector {
    use rand::Rng;
    let mut rng = rand::thread_rng();

    let mut indices = [0.0; 8];
    let dom_idx = dominant_class.index();

    for (i, val) in indices.iter_mut().enumerate() {
        if i == dom_idx {
            *val = severity.clamp(0.0, 1.0);
        } else {
            *val = (rng.gen::<f64>() * spread).clamp(0.0, 1.0);
        }
    }

    DiseaseVector::new_unchecked(
        indices[0], indices[1], indices[2], indices[3],
        indices[4], indices[5], indices[6], indices[7],
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_healthy_vector() {
        let h = healthy_vector();
        assert!(h.severity(None).abs() < 1e-10);
    }

    #[test]
    fn test_disease_vector_validation() {
        assert!(DiseaseVector::new(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5).is_ok());
        assert!(DiseaseVector::new(1.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5).is_err());
        assert!(DiseaseVector::new(-0.1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5).is_err());
    }

    #[test]
    fn test_dominant_class() {
        let d = DiseaseVector::new(0.8, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1).unwrap();
        assert_eq!(d.dominant_class(), OscillatorClass::Protein);

        let d = DiseaseVector::new(0.1, 0.9, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1).unwrap();
        assert_eq!(d.dominant_class(), OscillatorClass::Enzyme);
    }

    #[test]
    fn test_severity() {
        let d = DiseaseVector::new(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5).unwrap();
        assert!((d.severity(None) - 0.5).abs() < 1e-10);

        let d = DiseaseVector::new(1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0).unwrap();
        assert!((d.severity(None) - 0.125).abs() < 1e-10);
    }

    #[test]
    fn test_from_coherences() {
        let d = DiseaseVector::from_coherences(0.8, 0.9, 0.7, 0.85, 0.6, 0.95, 0.75, 0.9).unwrap();
        assert!((d.d_p - 0.2).abs() < 1e-10);
        assert!((d.d_e - 0.1).abs() < 1e-10);
    }

    #[test]
    fn test_disease_signature_distance() {
        let d1 = healthy_vector();
        let d2 = healthy_vector();
        assert!(disease_signature_distance(&d1, &d2).abs() < 1e-10);

        let d1 = DiseaseVector::new(1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0).unwrap();
        let d2 = DiseaseVector::new(0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0).unwrap();
        assert!((disease_signature_distance(&d1, &d2) - 2.0_f64.sqrt()).abs() < 1e-10);
    }

    #[test]
    fn test_disease_from_oscillators() {
        let oscillators = vec![
            Oscillator::new(OscillatorClass::Protein, 0.2, 1.0, 0.0),
            Oscillator::new(OscillatorClass::Enzyme, 0.8, 1.0, 0.0),
        ];
        let d = disease_vector_from_oscillators(&oscillators);
        assert!((d.d_p - 0.8).abs() < 1e-10);
        assert!((d.d_e - 0.2).abs() < 1e-10);
    }

    #[test]
    fn test_classification() {
        let d = DiseaseVector::new(0.85, 0.2, 0.15, 0.3, 0.25, 0.18, 0.22, 0.12).unwrap();
        let (code, name, _) = d.classification();
        assert_eq!(code, "P");
        assert_eq!(name, "Misfolding");
    }
}
