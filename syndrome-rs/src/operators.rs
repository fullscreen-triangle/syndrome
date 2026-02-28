//! Categorical Operators Module
//!
//! Implements mathematical operators for the Syndrome framework:
//! - Lifting operators (microscopic → macroscopic)
//! - Composition operators (combining trajectories)
//! - Projection operators (dimensional reduction)
//! - Transformation functors

use nalgebra::DMatrix;
use serde::{Deserialize, Serialize};
use crate::coherence::Oscillator;
use crate::disease::DiseaseVector;
use crate::s_entropy::SEntropyPoint;
use crate::{Result, SyndromeError};

/// Lifting operator: maps microscopic states to macroscopic observables.
///
/// L: Ω_micro → Ω_macro
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiftingOperator {
    /// Dimension of microscopic space
    pub micro_dim: usize,
    /// Dimension of macroscopic space
    pub macro_dim: usize,
    /// Lifting matrix (macro_dim × micro_dim)
    pub matrix: Vec<Vec<f64>>,
}

impl LiftingOperator {
    /// Create identity lifting (dimensions must match).
    pub fn identity(dim: usize) -> Self {
        let mut matrix = vec![vec![0.0; dim]; dim];
        for i in 0..dim {
            matrix[i][i] = 1.0;
        }
        Self {
            micro_dim: dim,
            macro_dim: dim,
            matrix,
        }
    }

    /// Create averaging operator.
    pub fn averaging(micro_dim: usize) -> Self {
        let weight = 1.0 / micro_dim as f64;
        Self {
            micro_dim,
            macro_dim: 1,
            matrix: vec![vec![weight; micro_dim]],
        }
    }

    /// Create weighted averaging operator.
    pub fn weighted_averaging(weights: &[f64]) -> Self {
        let total: f64 = weights.iter().sum();
        let normalized: Vec<f64> = weights.iter().map(|w| w / total).collect();
        Self {
            micro_dim: weights.len(),
            macro_dim: 1,
            matrix: vec![normalized],
        }
    }

    /// Create from explicit matrix.
    pub fn from_matrix(matrix: Vec<Vec<f64>>) -> Result<Self> {
        if matrix.is_empty() {
            return Err(SyndromeError::ComputationError {
                operation: "LiftingOperator::from_matrix".to_string(),
                details: "Empty matrix".to_string(),
            });
        }
        let macro_dim = matrix.len();
        let micro_dim = matrix[0].len();

        // Validate dimensions
        for row in &matrix {
            if row.len() != micro_dim {
                return Err(SyndromeError::ComputationError {
                    operation: "LiftingOperator::from_matrix".to_string(),
                    details: "Inconsistent row dimensions".to_string(),
                });
            }
        }

        Ok(Self {
            micro_dim,
            macro_dim,
            matrix,
        })
    }

    /// Apply operator to vector.
    pub fn apply(&self, input: &[f64]) -> Result<Vec<f64>> {
        if input.len() != self.micro_dim {
            return Err(SyndromeError::DimensionMismatch {
                expected: self.micro_dim,
                got: input.len(),
            });
        }

        let mut output = vec![0.0; self.macro_dim];
        for (i, row) in self.matrix.iter().enumerate() {
            output[i] = row.iter().zip(input.iter()).map(|(a, b)| a * b).sum();
        }
        Ok(output)
    }

    /// Compose two operators: (L2 ∘ L1)(x) = L2(L1(x))
    pub fn compose(&self, other: &LiftingOperator) -> Result<LiftingOperator> {
        if self.micro_dim != other.macro_dim {
            return Err(SyndromeError::DimensionMismatch {
                expected: self.micro_dim,
                got: other.macro_dim,
            });
        }

        // Matrix multiplication: result = self.matrix × other.matrix
        let mut result = vec![vec![0.0; other.micro_dim]; self.macro_dim];
        for i in 0..self.macro_dim {
            for j in 0..other.micro_dim {
                for k in 0..self.micro_dim {
                    result[i][j] += self.matrix[i][k] * other.matrix[k][j];
                }
            }
        }

        Ok(LiftingOperator {
            micro_dim: other.micro_dim,
            macro_dim: self.macro_dim,
            matrix: result,
        })
    }
}

/// Projection operator: reduces dimensionality.
///
/// P: R^n → R^m where m ≤ n
#[derive(Debug, Clone)]
pub struct ProjectionOperator {
    /// Source dimension
    pub source_dim: usize,
    /// Target dimension
    pub target_dim: usize,
    /// Projection indices
    pub indices: Vec<usize>,
}

impl ProjectionOperator {
    /// Create projection to first m coordinates.
    pub fn first_n(source_dim: usize, target_dim: usize) -> Result<Self> {
        if target_dim > source_dim {
            return Err(SyndromeError::DimensionMismatch {
                expected: source_dim,
                got: target_dim,
            });
        }
        Ok(Self {
            source_dim,
            target_dim,
            indices: (0..target_dim).collect(),
        })
    }

    /// Create projection to specified indices.
    pub fn select(source_dim: usize, indices: Vec<usize>) -> Result<Self> {
        for &idx in &indices {
            if idx >= source_dim {
                return Err(SyndromeError::IndexOutOfBounds {
                    index: idx,
                    max: source_dim,
                });
            }
        }
        Ok(Self {
            source_dim,
            target_dim: indices.len(),
            indices,
        })
    }

    /// Apply projection.
    pub fn apply(&self, input: &[f64]) -> Result<Vec<f64>> {
        if input.len() != self.source_dim {
            return Err(SyndromeError::DimensionMismatch {
                expected: self.source_dim,
                got: input.len(),
            });
        }
        Ok(self.indices.iter().map(|&i| input[i]).collect())
    }
}

/// Oscillator aggregation operator.
///
/// Aggregates multiple oscillators into class-level coherence.
pub struct AggregationOperator {
    /// Aggregation weights per class
    pub class_weights: [f64; 8],
}

impl AggregationOperator {
    /// Create uniform aggregation.
    pub fn uniform() -> Self {
        Self {
            class_weights: [1.0; 8],
        }
    }

    /// Create with custom weights.
    pub fn weighted(weights: [f64; 8]) -> Self {
        Self {
            class_weights: weights,
        }
    }

    /// Aggregate oscillators to disease vector.
    pub fn aggregate(&self, oscillators: &[Oscillator]) -> DiseaseVector {
        // Group by class
        let mut class_coherences: [Vec<(f64, f64)>; 8] = Default::default();

        for osc in oscillators {
            let eta = osc.coherence();
            class_coherences[osc.class.index()].push((eta, osc.weight));
        }

        // Compute weighted average coherence per class
        let mut disease_indices = [0.0; 8];
        for (i, values) in class_coherences.iter().enumerate() {
            if values.is_empty() {
                disease_indices[i] = 0.0;
            } else {
                let total_weight: f64 = values.iter().map(|(_, w)| w).sum();
                if total_weight.abs() < 1e-10 {
                    disease_indices[i] = 0.0;
                } else {
                    let weighted_eta: f64 =
                        values.iter().map(|(eta, w)| eta * w).sum::<f64>() / total_weight;
                    disease_indices[i] = (1.0 - weighted_eta) * self.class_weights[i];
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
}

impl Default for AggregationOperator {
    fn default() -> Self {
        Self::uniform()
    }
}

/// Coarse-graining operator for renormalization.
#[derive(Debug, Clone)]
pub struct CoarseGrainOperator {
    /// Block size for coarse-graining
    pub block_size: usize,
    /// Aggregation method
    pub method: CoarseGrainMethod,
}

/// Methods for coarse-graining.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum CoarseGrainMethod {
    /// Simple average
    Mean,
    /// Root mean square
    Rms,
    /// Maximum value
    Max,
    /// Minimum value
    Min,
}

impl CoarseGrainOperator {
    /// Create with specified block size.
    pub fn new(block_size: usize, method: CoarseGrainMethod) -> Self {
        Self { block_size, method }
    }

    /// Apply coarse-graining to array.
    pub fn apply(&self, input: &[f64]) -> Vec<f64> {
        if self.block_size == 0 || input.is_empty() {
            return Vec::new();
        }

        input
            .chunks(self.block_size)
            .map(|block| match self.method {
                CoarseGrainMethod::Mean => block.iter().sum::<f64>() / block.len() as f64,
                CoarseGrainMethod::Rms => {
                    (block.iter().map(|x| x * x).sum::<f64>() / block.len() as f64).sqrt()
                }
                CoarseGrainMethod::Max => {
                    block.iter().cloned().fold(f64::NEG_INFINITY, f64::max)
                }
                CoarseGrainMethod::Min => {
                    block.iter().cloned().fold(f64::INFINITY, f64::min)
                }
            })
            .collect()
    }
}

/// S-entropy transformation functor.
pub struct SEntropyFunctor {
    /// Scaling factors
    pub scale: [f64; 3],
    /// Translation offsets
    pub offset: [f64; 3],
}

impl SEntropyFunctor {
    /// Create identity functor.
    pub fn identity() -> Self {
        Self {
            scale: [1.0, 1.0, 1.0],
            offset: [0.0, 0.0, 0.0],
        }
    }

    /// Create scaling functor.
    pub fn scaling(s_k: f64, s_t: f64, s_e: f64) -> Self {
        Self {
            scale: [s_k, s_t, s_e],
            offset: [0.0, 0.0, 0.0],
        }
    }

    /// Create translation functor.
    pub fn translation(d_k: f64, d_t: f64, d_e: f64) -> Self {
        Self {
            scale: [1.0, 1.0, 1.0],
            offset: [d_k, d_t, d_e],
        }
    }

    /// Apply functor to point.
    pub fn apply(&self, point: SEntropyPoint) -> SEntropyPoint {
        let s_k = (point.s_k * self.scale[0] + self.offset[0]).clamp(0.0, 1.0);
        let s_t = (point.s_t * self.scale[1] + self.offset[1]).clamp(0.0, 1.0);
        let s_e = (point.s_e * self.scale[2] + self.offset[2]).clamp(0.0, 1.0);

        SEntropyPoint::new_unchecked(s_k, s_t, s_e)
    }

    /// Compose two functors.
    pub fn compose(&self, other: &SEntropyFunctor) -> SEntropyFunctor {
        // (f ∘ g)(x) = f(g(x)) = scale_f * (scale_g * x + offset_g) + offset_f
        //           = (scale_f * scale_g) * x + (scale_f * offset_g + offset_f)
        SEntropyFunctor {
            scale: [
                self.scale[0] * other.scale[0],
                self.scale[1] * other.scale[1],
                self.scale[2] * other.scale[2],
            ],
            offset: [
                self.scale[0] * other.offset[0] + self.offset[0],
                self.scale[1] * other.offset[1] + self.offset[1],
                self.scale[2] * other.offset[2] + self.offset[2],
            ],
        }
    }
}

impl Default for SEntropyFunctor {
    fn default() -> Self {
        Self::identity()
    }
}

/// Coherence-preserving transformation.
///
/// Maps coherence values while preserving their relative ordering.
pub struct CoherenceTransform {
    /// Transform type
    pub kind: TransformKind,
    /// Parameters
    pub params: Vec<f64>,
}

/// Types of coherence transformations.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum TransformKind {
    /// Identity transformation
    Identity,
    /// Power law: η^p
    Power,
    /// Sigmoid: 1/(1 + exp(-k(η - η₀)))
    Sigmoid,
    /// Threshold: step function at η₀
    Threshold,
    /// Linear scaling: a*η + b
    Linear,
}

impl CoherenceTransform {
    /// Create identity transform.
    pub fn identity() -> Self {
        Self {
            kind: TransformKind::Identity,
            params: vec![],
        }
    }

    /// Create power transform.
    pub fn power(exponent: f64) -> Self {
        Self {
            kind: TransformKind::Power,
            params: vec![exponent],
        }
    }

    /// Create sigmoid transform.
    pub fn sigmoid(steepness: f64, center: f64) -> Self {
        Self {
            kind: TransformKind::Sigmoid,
            params: vec![steepness, center],
        }
    }

    /// Create threshold transform.
    pub fn threshold(eta_0: f64) -> Self {
        Self {
            kind: TransformKind::Threshold,
            params: vec![eta_0],
        }
    }

    /// Create linear transform.
    pub fn linear(slope: f64, intercept: f64) -> Self {
        Self {
            kind: TransformKind::Linear,
            params: vec![slope, intercept],
        }
    }

    /// Apply transform to coherence value.
    pub fn apply(&self, eta: f64) -> f64 {
        let result = match self.kind {
            TransformKind::Identity => eta,
            TransformKind::Power => {
                let p = self.params.first().copied().unwrap_or(1.0);
                eta.powf(p)
            }
            TransformKind::Sigmoid => {
                let k = self.params.first().copied().unwrap_or(10.0);
                let eta_0 = self.params.get(1).copied().unwrap_or(0.5);
                1.0 / (1.0 + (-k * (eta - eta_0)).exp())
            }
            TransformKind::Threshold => {
                let eta_0 = self.params.first().copied().unwrap_or(0.5);
                if eta >= eta_0 { 1.0 } else { 0.0 }
            }
            TransformKind::Linear => {
                let a = self.params.first().copied().unwrap_or(1.0);
                let b = self.params.get(1).copied().unwrap_or(0.0);
                a * eta + b
            }
        };
        result.clamp(0.0, 1.0)
    }
}

impl Default for CoherenceTransform {
    fn default() -> Self {
        Self::identity()
    }
}

/// Compute singular value decomposition for dimensional reduction.
pub fn svd_reduce(data: &[Vec<f64>], target_dim: usize) -> Result<Vec<Vec<f64>>> {
    if data.is_empty() {
        return Ok(Vec::new());
    }

    let n_rows = data.len();
    let n_cols = data[0].len();

    if target_dim > n_cols {
        return Err(SyndromeError::DimensionMismatch {
            expected: n_cols,
            got: target_dim,
        });
    }

    // Convert to nalgebra matrix
    let mut flat: Vec<f64> = Vec::with_capacity(n_rows * n_cols);
    for row in data {
        if row.len() != n_cols {
            return Err(SyndromeError::ComputationError {
                operation: "svd_reduce".to_string(),
                details: "Inconsistent row dimensions".to_string(),
            });
        }
        flat.extend(row);
    }

    let matrix = DMatrix::from_row_slice(n_rows, n_cols, &flat);

    // Compute SVD
    let svd = matrix.svd(true, false);

    // Project onto first target_dim components
    let u = svd.u.ok_or_else(|| SyndromeError::ComputationError {
        operation: "svd_reduce".to_string(),
        details: "SVD failed to compute U matrix".to_string(),
    })?;

    let s = &svd.singular_values;

    // U_reduced * S_reduced
    let mut result = Vec::with_capacity(n_rows);
    for i in 0..n_rows {
        let mut row = Vec::with_capacity(target_dim);
        for j in 0..target_dim {
            row.push(u[(i, j)] * s[j]);
        }
        result.push(row);
    }

    Ok(result)
}

/// Principal component analysis.
pub fn pca(data: &[Vec<f64>], n_components: usize) -> Result<(Vec<Vec<f64>>, Vec<f64>)> {
    if data.is_empty() {
        return Ok((Vec::new(), Vec::new()));
    }

    let n_samples = data.len();
    let n_features = data[0].len();

    // Center the data
    let mut means = vec![0.0; n_features];
    for row in data {
        for (j, &val) in row.iter().enumerate() {
            means[j] += val;
        }
    }
    for mean in &mut means {
        *mean /= n_samples as f64;
    }

    let centered: Vec<Vec<f64>> = data
        .iter()
        .map(|row| row.iter().zip(&means).map(|(v, m)| v - m).collect())
        .collect();

    // Use SVD for PCA
    let reduced = svd_reduce(&centered, n_components)?;

    // Compute explained variance (singular values squared / n_samples)
    let mut flat: Vec<f64> = Vec::with_capacity(n_samples * n_features);
    for row in &centered {
        flat.extend(row);
    }
    let matrix = DMatrix::from_row_slice(n_samples, n_features, &flat);
    let svd = matrix.svd(false, false);

    let explained_variance: Vec<f64> = svd
        .singular_values
        .iter()
        .take(n_components)
        .map(|s| s * s / (n_samples as f64 - 1.0))
        .collect();

    Ok((reduced, explained_variance))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::coherence::OscillatorClass;

    #[test]
    fn test_lifting_identity() {
        let op = LiftingOperator::identity(3);
        let input = vec![1.0, 2.0, 3.0];
        let output = op.apply(&input).unwrap();
        assert_eq!(output, input);
    }

    #[test]
    fn test_lifting_averaging() {
        let op = LiftingOperator::averaging(4);
        let input = vec![1.0, 2.0, 3.0, 4.0];
        let output = op.apply(&input).unwrap();
        assert_eq!(output.len(), 1);
        assert!((output[0] - 2.5).abs() < 1e-10);
    }

    #[test]
    fn test_lifting_composition() {
        let op1 = LiftingOperator::identity(3);
        let op2 = LiftingOperator::averaging(3);
        let composed = op2.compose(&op1).unwrap();

        let input = vec![1.0, 2.0, 3.0];
        let output = composed.apply(&input).unwrap();
        assert_eq!(output.len(), 1);
        assert!((output[0] - 2.0).abs() < 1e-10);
    }

    #[test]
    fn test_projection() {
        let proj = ProjectionOperator::first_n(5, 3).unwrap();
        let input = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let output = proj.apply(&input).unwrap();
        assert_eq!(output, vec![1.0, 2.0, 3.0]);
    }

    #[test]
    fn test_projection_select() {
        let proj = ProjectionOperator::select(5, vec![0, 2, 4]).unwrap();
        let input = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let output = proj.apply(&input).unwrap();
        assert_eq!(output, vec![1.0, 3.0, 5.0]);
    }

    #[test]
    fn test_coarse_grain_mean() {
        let op = CoarseGrainOperator::new(2, CoarseGrainMethod::Mean);
        let input = vec![1.0, 3.0, 5.0, 7.0];
        let output = op.apply(&input);
        assert_eq!(output, vec![2.0, 6.0]);
    }

    #[test]
    fn test_coarse_grain_max() {
        let op = CoarseGrainOperator::new(2, CoarseGrainMethod::Max);
        let input = vec![1.0, 3.0, 5.0, 7.0];
        let output = op.apply(&input);
        assert_eq!(output, vec![3.0, 7.0]);
    }

    #[test]
    fn test_s_entropy_functor() {
        let f = SEntropyFunctor::scaling(0.5, 0.5, 0.5);
        let p = SEntropyPoint::new(0.8, 0.8, 0.8).unwrap();
        let result = f.apply(p);
        assert!((result.s_k - 0.4).abs() < 1e-10);
    }

    #[test]
    fn test_functor_composition() {
        let f1 = SEntropyFunctor::scaling(2.0, 2.0, 2.0);
        let f2 = SEntropyFunctor::translation(0.1, 0.1, 0.1);
        let composed = f1.compose(&f2);

        let p = SEntropyPoint::new(0.2, 0.2, 0.2).unwrap();
        let result = composed.apply(p);
        // f1(f2(x)) = 2.0 * (1.0 * 0.2 + 0.1) = 2.0 * 0.3 = 0.6
        assert!((result.s_k - 0.6).abs() < 1e-10);
    }

    #[test]
    fn test_coherence_transform_power() {
        let t = CoherenceTransform::power(2.0);
        assert!((t.apply(0.5) - 0.25).abs() < 1e-10);
    }

    #[test]
    fn test_coherence_transform_sigmoid() {
        let t = CoherenceTransform::sigmoid(10.0, 0.5);
        assert!(t.apply(0.5) > 0.49 && t.apply(0.5) < 0.51);
        assert!(t.apply(0.9) > 0.9);
        assert!(t.apply(0.1) < 0.1);
    }

    #[test]
    fn test_coherence_transform_threshold() {
        let t = CoherenceTransform::threshold(0.5);
        assert_eq!(t.apply(0.6), 1.0);
        assert_eq!(t.apply(0.4), 0.0);
    }

    #[test]
    fn test_aggregation_operator() {
        let op = AggregationOperator::uniform();
        let oscillators = vec![
            Oscillator::new(OscillatorClass::Protein, 0.8, 1.0, 0.0),
            Oscillator::new(OscillatorClass::Enzyme, 0.6, 1.0, 0.0),
        ];
        let disease = op.aggregate(&oscillators);
        assert!((disease.d_p - 0.2).abs() < 1e-10);
        assert!((disease.d_e - 0.4).abs() < 1e-10);
    }

    #[test]
    fn test_svd_reduce() {
        let data = vec![
            vec![1.0, 2.0, 3.0],
            vec![4.0, 5.0, 6.0],
            vec![7.0, 8.0, 9.0],
        ];
        let reduced = svd_reduce(&data, 2).unwrap();
        assert_eq!(reduced.len(), 3);
        assert_eq!(reduced[0].len(), 2);
    }

    #[test]
    fn test_pca() {
        let data = vec![
            vec![1.0, 2.0],
            vec![3.0, 4.0],
            vec![5.0, 6.0],
        ];
        let (transformed, variance) = pca(&data, 1).unwrap();
        assert_eq!(transformed.len(), 3);
        assert_eq!(variance.len(), 1);
        assert!(variance[0] > 0.0);
    }
}
