"""
Oscillator Classes Module

Provides implementations of the eight oscillator classes:
- P: Protein folding oscillators
- E: Enzyme catalytic oscillators
- C: Ion channel gating oscillators
- M: Membrane potential oscillators
- A: ATP synthesis oscillators
- G: Gene expression oscillators
- Ca: Calcium signaling oscillators
- R: Circadian rhythm oscillators
"""

from syndrome.core.coherence import (
    Oscillator,
    coherence_from_folding_cycles,
    coherence_from_turnover,
    coherence_from_open_probability,
    coherence_from_membrane_amplitude,
    coherence_from_period_stability,
)

__all__ = [
    "Oscillator",
    "coherence_from_folding_cycles",
    "coherence_from_turnover",
    "coherence_from_open_probability",
    "coherence_from_membrane_amplitude",
    "coherence_from_period_stability",
]
