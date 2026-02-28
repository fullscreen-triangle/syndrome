"""
Core mathematical foundations for the Syndrome framework.

This module provides:
- Partition coordinates and geometry
- S-entropy space operations
- Coherence computation
- Disease state formalism
- Trajectory computation
- Partition operators
"""

from syndrome.core.partition import (
    PartitionCoord,
    partition_capacity,
    categorical_distance,
    is_valid_partition_coord,
)
from syndrome.core.s_entropy import (
    SEntropyPoint,
    s_entropy_distance,
    normalize_s_entropy,
)
from syndrome.core.coherence import (
    coherence_index,
    cellular_coherence,
    coherence_from_folding_cycles,
    coherence_from_turnover,
)
from syndrome.core.disease import (
    disease_vector,
    classify_disease,
    disease_severity,
    OSCILLATOR_CLASSES,
    DISEASE_CLASS_NAMES,
)
from syndrome.core.trajectory import (
    complete_trajectory,
    resolve_address,
)
from syndrome.core.operators import (
    PartitionOperator,
    photon_operator,
    phase_lock_operator,
    gradient_operator,
)

__all__ = [
    # Partition
    "PartitionCoord",
    "partition_capacity",
    "categorical_distance",
    "is_valid_partition_coord",
    # S-Entropy
    "SEntropyPoint",
    "s_entropy_distance",
    "normalize_s_entropy",
    # Coherence
    "coherence_index",
    "cellular_coherence",
    "coherence_from_folding_cycles",
    "coherence_from_turnover",
    # Disease
    "disease_vector",
    "classify_disease",
    "disease_severity",
    "OSCILLATOR_CLASSES",
    "DISEASE_CLASS_NAMES",
    # Trajectory
    "complete_trajectory",
    "resolve_address",
    # Operators
    "PartitionOperator",
    "photon_operator",
    "phase_lock_operator",
    "gradient_operator",
]
