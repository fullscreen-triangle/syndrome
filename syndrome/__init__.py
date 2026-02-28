"""
Syndrome: Categorical Resolution of Disease Trajectories

A computational framework for resolving disease trajectories through
categorical partition geometry and oscillator coherence.
"""

__version__ = "0.1.0"
__author__ = "Kundai Farai Sachikonye"
__email__ = "kundai.sachikonye@wzw.tum.de"

from syndrome.core.coherence import coherence_index, cellular_coherence
from syndrome.core.disease import disease_vector, classify_disease, disease_severity
from syndrome.core.partition import PartitionCoord, partition_capacity, categorical_distance
from syndrome.core.s_entropy import SEntropyPoint

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    # Core functions
    "coherence_index",
    "cellular_coherence",
    "disease_vector",
    "classify_disease",
    "disease_severity",
    "partition_capacity",
    "categorical_distance",
    # Core types
    "PartitionCoord",
    "SEntropyPoint",
]
