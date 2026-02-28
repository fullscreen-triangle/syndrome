"""
Disease State Module

Implements disease state formalism:
- Disease vector D = (D_P, D_E, D_C, D_M, D_A, D_G, D_Ca, D_R)
- Disease classification by dominant component
- Disease severity computation
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import numpy as np

from syndrome.core.coherence import Oscillator, coherence_index


# Oscillator class definitions
OSCILLATOR_CLASSES = ["P", "E", "C", "M", "A", "G", "Ca", "R"]

DISEASE_CLASS_NAMES = {
    "P": "Misfolding",
    "E": "Metabolic",
    "C": "Channelopathy",
    "M": "Excitability",
    "A": "Mitochondrial",
    "G": "Expression",
    "Ca": "Signaling",
    "R": "Rhythm",
}

DISEASE_CLASS_EXAMPLES = {
    "P": ["Alzheimer's", "Parkinson's", "Prion diseases", "Huntington's"],
    "E": ["Diabetes", "PKU", "Gaucher disease", "Galactosemia"],
    "C": ["Cystic fibrosis", "Long QT syndrome", "Myotonia", "Episodic ataxia"],
    "M": ["Epilepsy", "Cardiac arrhythmia", "Migraine"],
    "A": ["MELAS", "Leigh syndrome", "LHON", "Mitochondrial myopathy"],
    "G": ["Cancer", "Developmental disorders", "Thalassemia"],
    "Ca": ["Malignant hyperthermia", "Timothy syndrome", "Cardiac disorders"],
    "R": ["Sleep disorders", "Jet lag", "Seasonal affective disorder"],
}


@dataclass
class DiseaseVector:
    """
    Disease state vector across eight oscillator classes.

    D = (D_P, D_E, D_C, D_M, D_A, D_G, D_Ca, D_R)

    where D_i = 1 - η_i is the disease index for class i.
    """
    D_P: float  # Protein (misfolding)
    D_E: float  # Enzyme (metabolic)
    D_C: float  # Channel (channelopathy)
    D_M: float  # Membrane (excitability)
    D_A: float  # ATP (mitochondrial)
    D_G: float  # Genetic (expression)
    D_Ca: float  # Calcium (signaling)
    D_R: float  # Circadian (rhythm)

    def __post_init__(self) -> None:
        """Validate disease indices are in [0, 1]."""
        for name in OSCILLATOR_CLASSES:
            val = getattr(self, f"D_{name}")
            if not 0.0 <= val <= 1.0:
                raise ValueError(
                    f"Disease index D_{name} must be in [0, 1], got {val}"
                )

    def to_array(self) -> np.ndarray:
        """Convert to numpy array."""
        return np.array([
            self.D_P, self.D_E, self.D_C, self.D_M,
            self.D_A, self.D_G, self.D_Ca, self.D_R
        ], dtype=np.float64)

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "D_P": self.D_P,
            "D_E": self.D_E,
            "D_C": self.D_C,
            "D_M": self.D_M,
            "D_A": self.D_A,
            "D_G": self.D_G,
            "D_Ca": self.D_Ca,
            "D_R": self.D_R,
        }

    @classmethod
    def from_array(cls, arr: np.ndarray) -> "DiseaseVector":
        """Create from numpy array."""
        if len(arr) != 8:
            raise ValueError(f"Array must have length 8, got {len(arr)}")
        return cls(
            D_P=float(arr[0]),
            D_E=float(arr[1]),
            D_C=float(arr[2]),
            D_M=float(arr[3]),
            D_A=float(arr[4]),
            D_G=float(arr[5]),
            D_Ca=float(arr[6]),
            D_R=float(arr[7]),
        )

    @classmethod
    def from_coherences(
        cls,
        eta_P: float = 1.0,
        eta_E: float = 1.0,
        eta_C: float = 1.0,
        eta_M: float = 1.0,
        eta_A: float = 1.0,
        eta_G: float = 1.0,
        eta_Ca: float = 1.0,
        eta_R: float = 1.0,
    ) -> "DiseaseVector":
        """Create disease vector from coherence values."""
        return cls(
            D_P=1.0 - eta_P,
            D_E=1.0 - eta_E,
            D_C=1.0 - eta_C,
            D_M=1.0 - eta_M,
            D_A=1.0 - eta_A,
            D_G=1.0 - eta_G,
            D_Ca=1.0 - eta_Ca,
            D_R=1.0 - eta_R,
        )

    def dominant_class(self) -> str:
        """Get the dominant disease class (argmax D_i)."""
        arr = self.to_array()
        idx = int(np.argmax(arr))
        return OSCILLATOR_CLASSES[idx]

    def dominant_value(self) -> float:
        """Get the dominant disease index value."""
        return float(np.max(self.to_array()))

    def severity(self, weights: Optional[np.ndarray] = None) -> float:
        """
        Compute total disease severity.

        D_total = (1/W) Σᵢ wᵢ Dᵢ

        Args:
            weights: Optional weights for each class

        Returns:
            Disease severity in [0, 1]
        """
        arr = self.to_array()
        if weights is None:
            return float(np.mean(arr))
        else:
            weights = np.asarray(weights)
            return float(np.sum(weights * arr) / np.sum(weights))

    def classification(self) -> Tuple[str, str, List[str]]:
        """
        Full disease classification.

        Returns:
            Tuple of (class_code, class_name, example_diseases)
        """
        dom_class = self.dominant_class()
        return (
            dom_class,
            DISEASE_CLASS_NAMES[dom_class],
            DISEASE_CLASS_EXAMPLES[dom_class],
        )


def disease_vector(oscillators: List[Oscillator]) -> DiseaseVector:
    """
    Compute disease vector from oscillator ensemble.

    Groups oscillators by class and computes weighted disease index
    for each class.

    Args:
        oscillators: List of Oscillator objects

    Returns:
        DiseaseVector
    """
    # Group by class
    class_coherences: Dict[str, List[Tuple[float, float]]] = {
        c: [] for c in OSCILLATOR_CLASSES
    }

    for osc in oscillators:
        eta = osc.coherence()
        weight = osc.weight
        class_coherences[osc.osc_class].append((eta, weight))

    # Compute weighted average coherence per class
    disease_indices = {}
    for c in OSCILLATOR_CLASSES:
        values = class_coherences[c]
        if values:
            total_weight = sum(w for _, w in values)
            if total_weight > 0:
                weighted_eta = sum(eta * w for eta, w in values) / total_weight
            else:
                weighted_eta = 1.0  # Default to healthy
        else:
            weighted_eta = 1.0  # No oscillators = assume healthy

        disease_indices[f"D_{c}"] = 1.0 - weighted_eta

    return DiseaseVector(**disease_indices)


def disease_vector_from_dicts(oscillators: List[Dict]) -> DiseaseVector:
    """
    Compute disease vector from list of dictionaries.

    Args:
        oscillators: List of dicts with keys:
            'class', 'pi_obs', 'pi_opt', 'pi_deg', 'weight'

    Returns:
        DiseaseVector
    """
    osc_objects = [
        Oscillator(
            osc_class=d["class"],
            pi_obs=d["pi_obs"],
            pi_opt=d["pi_opt"],
            pi_deg=d["pi_deg"],
            weight=d.get("weight", 1.0),
        )
        for d in oscillators
    ]
    return disease_vector(osc_objects)


def classify_disease(D: DiseaseVector) -> str:
    """
    Classify disease by dominant component.

    class(D) = argmax_i D_i

    Args:
        D: Disease vector

    Returns:
        Disease class code (P, E, C, M, A, G, Ca, R)
    """
    return D.dominant_class()


def disease_severity(D: DiseaseVector, weights: Optional[np.ndarray] = None) -> float:
    """
    Compute total disease severity.

    Args:
        D: Disease vector
        weights: Optional class weights

    Returns:
        Severity in [0, 1]
    """
    return D.severity(weights)


def disease_signature_distance(D1: DiseaseVector, D2: DiseaseVector) -> float:
    """
    Compute distance between two disease signatures.

    Uses Euclidean distance in 8-dimensional disease space.

    Args:
        D1: First disease vector
        D2: Second disease vector

    Returns:
        Distance >= 0
    """
    return float(np.linalg.norm(D1.to_array() - D2.to_array()))


def healthy_vector() -> DiseaseVector:
    """Return a healthy disease vector (all zeros)."""
    return DiseaseVector(
        D_P=0.0, D_E=0.0, D_C=0.0, D_M=0.0,
        D_A=0.0, D_G=0.0, D_Ca=0.0, D_R=0.0
    )


def generate_disease_profile(
    dominant_class: str,
    severity: float,
    spread: float = 0.1
) -> DiseaseVector:
    """
    Generate a synthetic disease profile.

    Args:
        dominant_class: Dominant oscillator class
        severity: Severity of dominant class (0-1)
        spread: Random spread to other classes

    Returns:
        DiseaseVector with specified characteristics
    """
    if dominant_class not in OSCILLATOR_CLASSES:
        raise ValueError(f"Invalid class: {dominant_class}")

    indices = {}
    for c in OSCILLATOR_CLASSES:
        if c == dominant_class:
            indices[f"D_{c}"] = severity
        else:
            # Random background with given spread
            indices[f"D_{c}"] = np.random.uniform(0, spread)

    return DiseaseVector(**indices)
