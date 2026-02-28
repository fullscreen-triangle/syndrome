//! Trajectory Computation Module
//!
//! Implements the COMPLETE algorithm for trajectory resolution:
//! - Categorical trajectory representation
//! - Constraint-based resolution
//! - Address precision computation
//! - Trajectory interpolation and completion

use serde::{Deserialize, Serialize};
use crate::s_entropy::SEntropyPoint;
use crate::partition::{PartitionCoord, address_to_value, value_to_address};
use crate::{Result, SyndromeError};

/// Precision function: ε(k) = 3^(-k)
#[inline]
pub fn address_precision(depth: usize) -> f64 {
    3.0_f64.powi(-(depth as i32))
}

/// A constraint on trajectory resolution.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Constraint {
    /// Constraint identifier
    pub id: String,
    /// Minimum depth required
    pub min_depth: usize,
    /// Target precision
    pub target_precision: f64,
    /// Whether constraint is satisfied
    pub satisfied: bool,
    /// Constraint weight for optimization
    pub weight: f64,
}

impl Constraint {
    /// Create a new constraint.
    pub fn new(id: &str, min_depth: usize, target_precision: f64) -> Self {
        Self {
            id: id.to_string(),
            min_depth,
            target_precision,
            satisfied: false,
            weight: 1.0,
        }
    }

    /// Create with custom weight.
    pub fn with_weight(mut self, weight: f64) -> Self {
        self.weight = weight;
        self
    }

    /// Check if depth satisfies this constraint.
    pub fn check(&self, depth: usize) -> bool {
        depth >= self.min_depth && address_precision(depth) <= self.target_precision
    }

    /// Update satisfaction status.
    pub fn update(&mut self, depth: usize) {
        self.satisfied = self.check(depth);
    }
}

/// Standard constraint factories.
impl Constraint {
    /// Molecular precision constraint (nanometer scale).
    pub fn molecular() -> Self {
        // ~1nm precision requires depth ~19 (3^-19 ≈ 10^-9)
        Self::new("molecular", 19, 1e-9)
    }

    /// Cellular precision constraint (micrometer scale).
    pub fn cellular() -> Self {
        // ~1μm precision requires depth ~13 (3^-13 ≈ 10^-6)
        Self::new("cellular", 13, 1e-6)
    }

    /// Tissue precision constraint (millimeter scale).
    pub fn tissue() -> Self {
        // ~1mm precision requires depth ~6 (3^-6 ≈ 10^-3)
        Self::new("tissue", 6, 1e-3)
    }

    /// Organ precision constraint (centimeter scale).
    pub fn organ() -> Self {
        // ~1cm precision requires depth ~4 (3^-4 ≈ 0.01)
        Self::new("organ", 4, 1e-2)
    }

    /// Custom precision constraint.
    pub fn custom(id: &str, precision: f64) -> Self {
        // Compute minimum depth from precision
        let min_depth = (-precision.log10() / 3.0_f64.log10()).ceil() as usize;
        Self::new(id, min_depth, precision)
    }
}

/// A waypoint in trajectory space.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Waypoint {
    /// Time parameter (normalized to [0, 1])
    pub t: f64,
    /// S-entropy coordinates
    pub s_entropy: SEntropyPoint,
    /// Optional partition coordinate
    pub partition: Option<PartitionCoord>,
    /// Address depth at this point
    pub depth: usize,
    /// Resolved value at this depth
    pub value: f64,
}

impl Waypoint {
    /// Create a new waypoint.
    pub fn new(t: f64, s_entropy: SEntropyPoint) -> Self {
        Self {
            t,
            s_entropy,
            partition: None,
            depth: 0,
            value: 0.0,
        }
    }

    /// Create with partition coordinate.
    pub fn with_partition(mut self, coord: PartitionCoord) -> Self {
        self.partition = Some(coord);
        self
    }

    /// Set resolved address.
    pub fn with_resolution(mut self, depth: usize, value: f64) -> Self {
        self.depth = depth;
        self.value = value;
        self
    }
}

/// A complete trajectory through state space.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Trajectory {
    /// Ordered waypoints
    pub waypoints: Vec<Waypoint>,
    /// Active constraints
    pub constraints: Vec<Constraint>,
    /// Maximum resolution depth achieved
    pub max_depth: usize,
    /// Whether trajectory is complete
    pub complete: bool,
    /// Total trajectory length in S-entropy space
    pub length: f64,
}

impl Trajectory {
    /// Create an empty trajectory.
    pub fn new() -> Self {
        Self {
            waypoints: Vec::new(),
            constraints: Vec::new(),
            max_depth: 0,
            complete: false,
            length: 0.0,
        }
    }

    /// Create trajectory from waypoints.
    pub fn from_waypoints(waypoints: Vec<Waypoint>) -> Self {
        let length = Self::compute_length(&waypoints);
        Self {
            waypoints,
            constraints: Vec::new(),
            max_depth: 0,
            complete: false,
            length,
        }
    }

    /// Add a waypoint.
    pub fn add_waypoint(&mut self, waypoint: Waypoint) {
        self.waypoints.push(waypoint);
        self.length = Self::compute_length(&self.waypoints);
    }

    /// Add a constraint.
    pub fn add_constraint(&mut self, constraint: Constraint) {
        self.constraints.push(constraint);
    }

    /// Compute trajectory length.
    fn compute_length(waypoints: &[Waypoint]) -> f64 {
        if waypoints.len() < 2 {
            return 0.0;
        }

        waypoints
            .windows(2)
            .map(|w| w[0].s_entropy.distance(&w[1].s_entropy))
            .sum()
    }

    /// Get current precision.
    pub fn precision(&self) -> f64 {
        address_precision(self.max_depth)
    }

    /// Check if all constraints are satisfied.
    pub fn constraints_satisfied(&self) -> bool {
        self.constraints.iter().all(|c| c.satisfied)
    }

    /// Get unsatisfied constraints.
    pub fn unsatisfied_constraints(&self) -> Vec<&Constraint> {
        self.constraints.iter().filter(|c| !c.satisfied).collect()
    }

    /// Interpolate trajectory at parameter t ∈ [0, 1].
    pub fn interpolate(&self, t: f64) -> Option<SEntropyPoint> {
        if self.waypoints.is_empty() {
            return None;
        }
        if self.waypoints.len() == 1 {
            return Some(self.waypoints[0].s_entropy);
        }

        let t = t.clamp(0.0, 1.0);

        // Find bounding waypoints
        for i in 0..self.waypoints.len() - 1 {
            let w0 = &self.waypoints[i];
            let w1 = &self.waypoints[i + 1];

            if t >= w0.t && t <= w1.t {
                // Linear interpolation
                let local_t = if (w1.t - w0.t).abs() < 1e-10 {
                    0.0
                } else {
                    (t - w0.t) / (w1.t - w0.t)
                };

                return Some(SEntropyPoint::interpolate(&w0.s_entropy, &w1.s_entropy, local_t));
            }
        }

        // Fallback to last point
        Some(self.waypoints.last()?.s_entropy)
    }

    /// Sample trajectory at n uniformly spaced points.
    pub fn sample(&self, n: usize) -> Vec<SEntropyPoint> {
        if n == 0 {
            return Vec::new();
        }
        if n == 1 {
            return self.interpolate(0.5).into_iter().collect();
        }

        (0..n)
            .filter_map(|i| {
                let t = i as f64 / (n - 1) as f64;
                self.interpolate(t)
            })
            .collect()
    }
}

impl Default for Trajectory {
    fn default() -> Self {
        Self::new()
    }
}

/// COMPLETE Algorithm: Categorical Observation via Monotonic Partition-Limited
/// Entropy-constrained Trajectory Enumeration.
///
/// Resolves a trajectory to specified precision through iterative refinement.
pub fn complete_trajectory(
    initial: SEntropyPoint,
    target: SEntropyPoint,
    constraints: Vec<Constraint>,
    max_iterations: usize,
) -> Result<Trajectory> {
    // Validate inputs
    if !initial.is_valid() || !target.is_valid() {
        return Err(SyndromeError::InvalidSEntropyPoint {
            s_k: initial.s_k,
            s_t: initial.s_t,
            s_e: initial.s_e,
        });
    }

    // Create initial trajectory with start and end points
    let mut trajectory = Trajectory::new();
    trajectory.add_waypoint(Waypoint::new(0.0, initial));
    trajectory.add_waypoint(Waypoint::new(1.0, target));

    // Add constraints
    for c in constraints {
        trajectory.add_constraint(c);
    }

    // Determine target depth from constraints
    let target_depth = trajectory
        .constraints
        .iter()
        .map(|c| c.min_depth)
        .max()
        .unwrap_or(10);

    // Iterative refinement
    for iteration in 0..max_iterations {
        // Current depth
        let depth = (iteration + 1).min(target_depth);
        trajectory.max_depth = depth;

        // Refine waypoints
        for waypoint in &mut trajectory.waypoints {
            // Encode primary S-entropy coordinate to address
            let primary_value = waypoint.s_entropy.s_k; // Use knowledge entropy
            let address = value_to_address(primary_value, depth, 0.0, 1.0)?;
            let resolved_value = address_to_value(&address, 0.0, 1.0)?;

            waypoint.depth = depth;
            waypoint.value = resolved_value;
        }

        // Update constraint satisfaction
        for constraint in &mut trajectory.constraints {
            constraint.update(depth);
        }

        // Check completion
        if trajectory.constraints_satisfied() {
            trajectory.complete = true;
            break;
        }
    }

    // Final length computation
    trajectory.length = Trajectory::compute_length(&trajectory.waypoints);

    Ok(trajectory)
}

/// Create a linear trajectory between two points.
pub fn linear_trajectory(
    start: SEntropyPoint,
    end: SEntropyPoint,
    num_waypoints: usize,
) -> Trajectory {
    let mut trajectory = Trajectory::new();

    let n = num_waypoints.max(2);
    for i in 0..n {
        let t = i as f64 / (n - 1) as f64;
        let point = SEntropyPoint::interpolate(&start, &end, t);
        trajectory.add_waypoint(Waypoint::new(t, point));
    }

    trajectory
}

/// Create a curved trajectory through multiple control points.
pub fn curved_trajectory(control_points: &[SEntropyPoint], samples_per_segment: usize) -> Trajectory {
    if control_points.is_empty() {
        return Trajectory::new();
    }
    if control_points.len() == 1 {
        let mut t = Trajectory::new();
        t.add_waypoint(Waypoint::new(0.0, control_points[0]));
        return t;
    }

    let mut trajectory = Trajectory::new();
    let total_segments = control_points.len() - 1;
    let samples = samples_per_segment.max(2);

    for (seg_idx, window) in control_points.windows(2).enumerate() {
        let start = &window[0];
        let end = &window[1];

        let start_sample = if seg_idx == 0 { 0 } else { 1 };
        for i in start_sample..samples {
            let local_t = i as f64 / (samples - 1) as f64;
            let global_t = (seg_idx as f64 + local_t) / total_segments as f64;
            let point = SEntropyPoint::interpolate(start, end, local_t);
            trajectory.add_waypoint(Waypoint::new(global_t, point));
        }
    }

    trajectory
}

/// Compute trajectory distance (arc length in S-entropy space).
pub fn trajectory_distance(t: &Trajectory) -> f64 {
    t.length
}

/// Check if trajectory satisfies monotonicity constraint.
///
/// A trajectory is monotonic if the specified coordinate never decreases.
pub fn is_monotonic(trajectory: &Trajectory, coordinate: char) -> bool {
    if trajectory.waypoints.len() < 2 {
        return true;
    }

    let extract = |w: &Waypoint| -> f64 {
        match coordinate {
            'k' | 'K' => w.s_entropy.s_k,
            't' | 'T' => w.s_entropy.s_t,
            'e' | 'E' => w.s_entropy.s_e,
            _ => w.s_entropy.s_k,
        }
    };

    trajectory
        .waypoints
        .windows(2)
        .all(|w| extract(&w[1]) >= extract(&w[0]) - 1e-10)
}

/// Compute trajectory curvature at each waypoint.
pub fn trajectory_curvature(trajectory: &Trajectory) -> Vec<f64> {
    if trajectory.waypoints.len() < 3 {
        return vec![0.0; trajectory.waypoints.len()];
    }

    let mut curvatures = vec![0.0];

    for i in 1..trajectory.waypoints.len() - 1 {
        let p0 = &trajectory.waypoints[i - 1].s_entropy;
        let p1 = &trajectory.waypoints[i].s_entropy;
        let p2 = &trajectory.waypoints[i + 1].s_entropy;

        // Discrete curvature approximation
        let v1 = (p1.s_k - p0.s_k, p1.s_t - p0.s_t, p1.s_e - p0.s_e);
        let v2 = (p2.s_k - p1.s_k, p2.s_t - p1.s_t, p2.s_e - p1.s_e);

        let len1 = (v1.0 * v1.0 + v1.1 * v1.1 + v1.2 * v1.2).sqrt();
        let len2 = (v2.0 * v2.0 + v2.1 * v2.1 + v2.2 * v2.2).sqrt();

        if len1 < 1e-10 || len2 < 1e-10 {
            curvatures.push(0.0);
            continue;
        }

        // Angle between consecutive segments
        let dot = v1.0 * v2.0 + v1.1 * v2.1 + v1.2 * v2.2;
        let cos_theta = (dot / (len1 * len2)).clamp(-1.0, 1.0);
        let theta = cos_theta.acos();

        // Curvature = angle / arc length
        curvatures.push(2.0 * theta / (len1 + len2));
    }

    curvatures.push(0.0);
    curvatures
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_address_precision() {
        assert!((address_precision(0) - 1.0).abs() < 1e-10);
        assert!((address_precision(1) - 1.0 / 3.0).abs() < 1e-10);
        assert!((address_precision(2) - 1.0 / 9.0).abs() < 1e-10);
    }

    #[test]
    fn test_constraint_creation() {
        let c = Constraint::molecular();
        assert_eq!(c.min_depth, 19);
        assert!(!c.satisfied);

        let c = Constraint::cellular();
        assert_eq!(c.min_depth, 13);

        let c = Constraint::custom("test", 0.001);
        assert!(c.min_depth >= 6);
    }

    #[test]
    fn test_constraint_satisfaction() {
        let mut c = Constraint::tissue();
        assert!(!c.check(3));
        // depth 6 gives 3^-6 ≈ 0.00137 > 1e-3, so it fails
        // depth 7 gives 3^-7 ≈ 0.00046 < 1e-3, so it passes
        assert!(!c.check(6));
        assert!(c.check(7));
        assert!(c.check(10));

        c.update(10);
        assert!(c.satisfied);
    }

    #[test]
    fn test_waypoint() {
        let s = SEntropyPoint::new(0.5, 0.5, 0.5).unwrap();
        let w = Waypoint::new(0.0, s);
        assert_eq!(w.t, 0.0);
        assert_eq!(w.depth, 0);
    }

    #[test]
    fn test_trajectory_creation() {
        let t = Trajectory::new();
        assert!(t.waypoints.is_empty());
        assert_eq!(t.length, 0.0);
    }

    #[test]
    fn test_trajectory_from_waypoints() {
        let s1 = SEntropyPoint::new(0.0, 0.0, 0.0).unwrap();
        let s2 = SEntropyPoint::new(1.0, 1.0, 1.0).unwrap();

        let waypoints = vec![Waypoint::new(0.0, s1), Waypoint::new(1.0, s2)];

        let t = Trajectory::from_waypoints(waypoints);
        assert_eq!(t.waypoints.len(), 2);
        assert!((t.length - 3.0_f64.sqrt()).abs() < 1e-10);
    }

    #[test]
    fn test_trajectory_interpolation() {
        let s1 = SEntropyPoint::new(0.0, 0.0, 0.0).unwrap();
        let s2 = SEntropyPoint::new(1.0, 1.0, 1.0).unwrap();

        let waypoints = vec![Waypoint::new(0.0, s1), Waypoint::new(1.0, s2)];
        let t = Trajectory::from_waypoints(waypoints);

        let mid = t.interpolate(0.5).unwrap();
        assert!((mid.s_k - 0.5).abs() < 1e-10);
        assert!((mid.s_t - 0.5).abs() < 1e-10);
        assert!((mid.s_e - 0.5).abs() < 1e-10);
    }

    #[test]
    fn test_complete_trajectory() {
        let start = SEntropyPoint::new(0.1, 0.1, 0.1).unwrap();
        let end = SEntropyPoint::new(0.9, 0.9, 0.9).unwrap();

        let constraints = vec![Constraint::tissue()];
        let result = complete_trajectory(start, end, constraints, 10);

        assert!(result.is_ok());
        let t = result.unwrap();
        assert!(t.max_depth >= 6);
    }

    #[test]
    fn test_linear_trajectory() {
        let start = SEntropyPoint::new(0.0, 0.0, 0.0).unwrap();
        let end = SEntropyPoint::new(1.0, 0.0, 0.0).unwrap();

        let t = linear_trajectory(start, end, 5);
        assert_eq!(t.waypoints.len(), 5);
        assert!((t.length - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_curved_trajectory() {
        let points = vec![
            SEntropyPoint::new(0.0, 0.0, 0.0).unwrap(),
            SEntropyPoint::new(0.5, 0.5, 0.5).unwrap(),
            SEntropyPoint::new(1.0, 0.0, 1.0).unwrap(),
        ];

        let t = curved_trajectory(&points, 3);
        assert!(t.waypoints.len() >= 3);
    }

    #[test]
    fn test_monotonicity() {
        let start = SEntropyPoint::new(0.0, 0.0, 0.0).unwrap();
        let end = SEntropyPoint::new(1.0, 1.0, 1.0).unwrap();

        let t = linear_trajectory(start, end, 5);
        assert!(is_monotonic(&t, 'k'));
        assert!(is_monotonic(&t, 't'));
        assert!(is_monotonic(&t, 'e'));
    }

    #[test]
    fn test_trajectory_curvature() {
        let start = SEntropyPoint::new(0.0, 0.0, 0.0).unwrap();
        let end = SEntropyPoint::new(1.0, 0.0, 0.0).unwrap();

        let t = linear_trajectory(start, end, 5);
        let curvatures = trajectory_curvature(&t);

        // Linear trajectory should have zero curvature
        assert_eq!(curvatures.len(), 5);
        for c in &curvatures[1..curvatures.len() - 1] {
            assert!(c.abs() < 1e-10);
        }
    }

    #[test]
    fn test_trajectory_sampling() {
        let start = SEntropyPoint::new(0.0, 0.0, 0.0).unwrap();
        let end = SEntropyPoint::new(1.0, 1.0, 1.0).unwrap();

        let t = linear_trajectory(start, end, 2);
        let samples = t.sample(5);

        assert_eq!(samples.len(), 5);
        assert!((samples[0].s_k - 0.0).abs() < 1e-10);
        assert!((samples[4].s_k - 1.0).abs() < 1e-10);
    }
}
