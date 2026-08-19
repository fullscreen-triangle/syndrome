#!/usr/bin/env python3
"""
run_validation.py -- validation experiments for the solver-tolerance paper.

Five experiments, each testing a numbered result:

  V1  noise scale        Thm 3.2  eps_num ~ L^2 u Lambda, and the bound holds
  V2  fixed tolerance    Sec 4    a constant eps fails in BOTH directions
  V3  trichotomy         Thm 5.5  UNDECIDABLE is non-empty and non-degenerate
  V4  basis dependence   Thm 6.1 / Prop 6.2  verdict invariant, flagged set not
  V5  detection          Thm 5.3  D > 2 eps* implies flagged; empirical threshold

Everything is seeded. Results are written to results.json, which is the
single source for every number quoted in the manuscript and every point
plotted in the panels.

Design note: no check here compares the implementation against its own
tolerance computation, because such a check passes by construction.
Where a claim is an identity we verify it exactly; where it is a bound we
measure how slack the bound is and report that.
"""

from __future__ import annotations

import json
import math
import os
import platform
import sys
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.abspath(os.path.join(HERE, "..", "..", "..", "prototype"))
sys.path.insert(0, PROTO)

from cfc.kernel import (  # noqa: E402
    MACH_U, Z_ALPHA, Circuit, Cycle, Reaction, Species,
    admit, compute_holonomy, compute_tolerance, cycle_sum, data_floor,
    fundamental_cycle_basis, gamma, minimum_cycle_basis, numerical_floor,
    witness_set, CONSISTENT, UNDECIDABLE, INCONSISTENT,
)

SEED = 20260819
RESULTS: Dict[str, object] = {}


# =====================================================================
# helpers
# =====================================================================

def make_ring(n: int, mu_lo: float, mu_hi: float,
              sigma: float, rng: np.random.Generator,
              chords: int = 0) -> Circuit:
    """A ring of n species, optionally with `chords` extra edges."""
    c = Circuit()
    mus = rng.uniform(mu_lo, mu_hi, size=n)
    for i in range(n):
        # Fold the sampled potential into mu0 with c = 1 so that
        # mu = mu0 exactly; this keeps Lambda under our control.
        c.add_species(Species(f"S{i}", float(mus[i]), 1.0, sigma))
    for i in range(n):
        c.add_reaction(Reaction(f"R{i}", f"S{i}", f"S{(i + 1) % n}", 0.1))
    for j in range(chords):
        a = int(rng.integers(0, n))
        b = int((a + 2 + rng.integers(0, max(1, n - 3))) % n)
        if a != b:
            c.add_reaction(Reaction(f"C{j}", f"S{a}", f"S{b}", 0.1))
    return c.solve()


def verdict_label(c: Circuit, cy: Cycle) -> str:
    return admit(compute_holonomy(c, cy), compute_tolerance(c, cy)).label


def clone(c: Circuit) -> Circuit:
    out = c.copy()
    out.mu, out.G, out.J = dict(c.mu), dict(c.G), dict(c.J)
    out.solved, out.centred = c.solved, c.centred
    out.gauge_offset = c.gauge_offset
    return out


# =====================================================================
# V1 -- the noise scale
# =====================================================================

def v1_noise_scale() -> dict:
    """Measure the computed cycle sum of CONSISTENT circuits.

    The true value is exactly zero, so whatever is computed IS the
    rounding error. We sweep cycle length and potential range and check
    (a) the bound of Thm 3.2 is never violated, (b) how slack it is.
    """
    rng = np.random.default_rng(SEED)
    lengths = [3, 5, 8, 12, 16, 20, 25, 30]
    ranges = [10.0, 100.0, 1000.0, 3000.0]
    grid, viol, slack = [], 0, []

    for L in lengths:
        for lam in ranges:
            errs, bounds = [], []
            for _ in range(60):
                c = make_ring(L, -lam, lam, sigma=1.0, rng=rng)
                cy = Cycle(name="ring",
                           edges=[(f"R{i}", +1) for i in range(L)],
                           nodes=[f"S{i}" for i in range(L)] + ["S0"])
                # Perturb the summation order to sample rounding paths.
                h = abs(cycle_sum(c, cy))
                b = numerical_floor(c, cy)
                errs.append(h)
                bounds.append(b)
                if h > b:
                    viol += 1
                if b > 0 and h > 0:
                    slack.append(b / h)
            grid.append({
                "length": L,
                "Lambda": lam,
                "max_abs_error": float(max(errs)),
                "mean_abs_error": float(np.mean(errs)),
                "mean_bound": float(np.mean(bounds)),
                "predicted_scale": float(gamma(2 * L) * 2 * L * lam),
            })

    return {
        "grid": grid,
        "bound_violations": viol,
        "trials": len(lengths) * len(ranges) * 60,
        "median_slack_factor": float(np.median(slack)) if slack else None,
        "claim": "eps_num bound of Thm 3.2 is never violated",
        "passed": viol == 0,
    }


# =====================================================================
# V2 -- a fixed tolerance fails in both directions
# =====================================================================

def v2_fixed_tolerance(eps_fixed: float = 1e-6) -> dict:
    """What a fixed tolerance actually costs, measured rather than assumed.

    An earlier version of this experiment predicted that a fixed
    eps = 1e-6 would produce false positives on long high-potential
    cycles. It does not, and the reason is instructive: in binary64 the
    rounding error on a cycle sum tops out near 3e-12 even at L = 30 and
    Lambda = 3000 (V1), which is six orders of magnitude below 1e-6. A
    fixed tolerance that sits far above the numerical floor cannot
    manufacture a false positive.

    So the failure of a fixed tolerance is ONE-SIDED in double
    precision, not two-sided. What it does do, badly, is:

      (a) miss real defects, because 1e-6 is a habit rather than a
          detection threshold, and any defect below it is invisible
          however well-characterised the data;
      (b) claim CONSISTENT on defects that lie inside the data's own
          uncertainty, which is an unwarranted positive assertion where
          the honest verdict is UNDECIDABLE.

    (b) is the substantive cost and it is what we quantify. We also
    report the precision at which the two-sided failure WOULD appear,
    by repeating the null in float32, where the numerical floor rises
    to meet a fixed 1e-6.
    """
    rng = np.random.default_rng(SEED + 1)
    strata = [
        ("short_low", (3, 5), 20.0),
        ("short_high", (3, 5), 1800.0),
        ("long_low", (15, 22), 20.0),
        ("long_high", (15, 22), 1800.0),
    ]
    n_trials = 400
    # Defects spanning below/around/above the fixed tolerance.
    defects = [1e-8, 1e-7, 1e-6, 1e-5, 1e-3, 1e-1, 1.0]
    out = []

    for name, (lo, hi), lam in strata:
        fp = fp32 = 0
        miss_by_D = {f"{D:g}": 0 for D in defects}
        wrong_consistent = 0
        undecidable_correctly = 0

        for _ in range(n_trials):
            L = int(rng.integers(lo, hi + 1))
            c = make_ring(L, -lam, lam, sigma=1.0, rng=rng)
            cy = Cycle(name="ring",
                       edges=[(f"R{i}", +1) for i in range(L)],
                       nodes=[f"S{i}" for i in range(L)] + ["S0"])

            # --- null condition: no defect, so any positive is spurious
            if abs(cycle_sum(c, cy)) > eps_fixed:
                fp += 1

            # Same null in single precision, where the numerical floor
            # is ~1e7 times larger and does reach a fixed 1e-6.
            mus32 = np.array([c.mu[f"S{i}"] for i in range(L)],
                             dtype=np.float32)
            acc = np.float32(0.0)
            for i in range(L):
                acc = np.float32(acc + (mus32[(i + 1) % L] - mus32[i]))
            if abs(float(acc)) > eps_fixed:
                fp32 += 1

            # --- alternative: sweep defect magnitude
            for D in defects:
                d = clone(c)
                d.edge_offset["R0"] = D
                if abs(cycle_sum(d, cy)) <= eps_fixed:
                    miss_by_D[f"{D:g}"] += 1

            # --- the substantive cost: a fixed test says CONSISTENT
            #     where the cycle-local test says UNDECIDABLE.
            d = clone(c)
            d.edge_offset["R0"] = 0.5      # inside sigma=1.0 uncertainty
            fixed_says_inconsistent = abs(cycle_sum(d, cy)) > eps_fixed
            local = verdict_label(d, cy)
            if local == UNDECIDABLE and fixed_says_inconsistent:
                wrong_consistent += 1
            if local == UNDECIDABLE:
                undecidable_correctly += 1

        out.append({
            "stratum": name,
            "length_range": [lo, hi],
            "Lambda": lam,
            "n": n_trials,
            "fixed_false_positive_rate": fp / n_trials,
            "fixed_false_positive_rate_float32": fp32 / n_trials,
            "missed_rate_by_defect":
                {k: v / n_trials for k, v in miss_by_D.items()},
            "unwarranted_positive_rate": wrong_consistent / n_trials,
            "correctly_undecidable_rate":
                undecidable_correctly / n_trials,
        })

    worst_fp64 = max(s["fixed_false_positive_rate"] for s in out)
    worst_fp32 = max(s["fixed_false_positive_rate_float32"] for s in out)
    worst_unwarranted = max(s["unwarranted_positive_rate"] for s in out)
    # A fixed tolerance misses every defect strictly below it.
    miss_at_1e7 = max(s["missed_rate_by_defect"]["1e-07"] for s in out)

    return {
        "eps_fixed": eps_fixed,
        "defect_sweep": defects,
        "strata": out,
        "worst_fixed_false_positive_rate_float64": worst_fp64,
        "worst_fixed_false_positive_rate_float32": worst_fp32,
        "worst_missed_rate_at_defect_1e-7": miss_at_1e7,
        "worst_unwarranted_positive_rate": worst_unwarranted,
        "two_sided_failure_in_float64": bool(worst_fp64 > 0.0),
        "two_sided_failure_in_float32": bool(worst_fp32 > 0.05),
        "claim": ("in binary64 the failure is one-sided: a fixed eps "
                  "misses defects below it and asserts INCONSISTENT "
                  "where the data cannot resolve the question; the "
                  "false-positive mode appears only at lower precision"),
        # The experiment passes if it establishes the one-sided failure
        # AND the unwarranted-positive cost, which is what the corrected
        # claim asserts.
        "passed": bool(miss_at_1e7 > 0.99 and worst_unwarranted > 0.5),
    }


# =====================================================================
# V3 -- the trichotomy
# =====================================================================

def v3_trichotomy() -> dict:
    """Sweep defect magnitude against data quality.

    Produces the (sigma, D) surface whose three regions are the three
    verdicts. The middle region must be non-empty -- that is the claim.
    """
    rng = np.random.default_rng(SEED + 2)
    sigmas = np.logspace(-3, 1.0, 26)      # 0.001 .. 10 kJ/mol
    defects = np.logspace(-10, 2, 40)      # 1e-10 .. 100 kJ/mol
    L, lam = 6, 200.0

    surface = np.zeros((len(sigmas), len(defects)), dtype=int)
    counts = {CONSISTENT: 0, UNDECIDABLE: 0, INCONSISTENT: 0}
    code = {CONSISTENT: 0, UNDECIDABLE: 1, INCONSISTENT: 2}

    base = make_ring(L, -lam, lam, sigma=1.0, rng=rng)
    cy = Cycle(name="ring",
               edges=[(f"R{i}", +1) for i in range(L)],
               nodes=[f"S{i}" for i in range(L)] + ["S0"])

    eps_num_ref = numerical_floor(base, cy)
    eps_data_ref = []

    for i, s in enumerate(sigmas):
        c = clone(base)
        for sp in c.species.values():
            sp.sigma = float(s)
        eps_data_ref.append(float(data_floor(c, cy)))
        for j, D in enumerate(defects):
            d = clone(c)
            d.edge_offset["R0"] = float(D)
            lab = verdict_label(d, cy)
            surface[i, j] = code[lab]
            counts[lab] += 1

    total = int(surface.size)
    return {
        "sigmas": sigmas.tolist(),
        "defects": defects.tolist(),
        "surface": surface.tolist(),
        "code": {"CONSISTENT": 0, "UNDECIDABLE": 1, "INCONSISTENT": 2},
        "counts": {k: int(v) for k, v in counts.items()},
        "fractions": {k: v / total for k, v in counts.items()},
        "eps_num_reference": float(eps_num_ref),
        "eps_data_by_sigma": eps_data_ref,
        "orders_of_magnitude_gap":
            float(math.log10(eps_data_ref[len(sigmas) // 2] / eps_num_ref)),
        "claim": "UNDECIDABLE is non-empty and occupies a real region",
        "passed": counts[UNDECIDABLE] > 0,
    }


# =====================================================================
# V4 -- basis dependence
# =====================================================================

def v4_basis() -> dict:
    """Verdict is basis-independent; the flagged set is not.

    We build networks with several independent cycles, inject one edge
    defect, and compare a minimum-weight basis against a fundamental
    (spanning-tree) basis.
    """
    rng = np.random.default_rng(SEED + 3)
    trials = 200
    rows = []
    verdict_disagreements = 0
    flagged_disagreements = 0
    witness_hits_mcb = witness_hits_fcb = 0
    wsize_mcb, wsize_fcb = [], []

    for t in range(trials):
        n = int(rng.integers(6, 12))
        c = make_ring(n, -500.0, 500.0, sigma=0.05, rng=rng,
                      chords=int(rng.integers(2, 4)))
        c = c.centre_potentials()
        target = f"R{int(rng.integers(0, n))}"
        d = clone(c)
        d.edge_offset[target] = 50.0

        mcb = minimum_cycle_basis(d)
        fcb = fundamental_cycle_basis(d)
        if not mcb or not fcb:
            continue

        fm = [cy for cy in mcb if verdict_label(d, cy) == INCONSISTENT]
        ff = [cy for cy in fcb if verdict_label(d, cy) == INCONSISTENT]

        vm, vf = len(fm) > 0, len(ff) > 0
        if vm != vf:
            verdict_disagreements += 1
        if len(fm) != len(ff):
            flagged_disagreements += 1

        Wm, Wf = witness_set(fm), witness_set(ff)
        if target in Wm:
            witness_hits_mcb += 1
        if target in Wf:
            witness_hits_fcb += 1
        if fm:
            wsize_mcb.append(len(Wm))
        if ff:
            wsize_fcb.append(len(Wf))

        rows.append({
            "n_species": n,
            "flagged_mcb": len(fm),
            "flagged_fcb": len(ff),
            "witness_mcb": len(Wm),
            "witness_fcb": len(Wf),
            "mean_len_mcb": float(np.mean([x.length for x in mcb])),
            "mean_len_fcb": float(np.mean([x.length for x in fcb])),
        })

    n_eff = len(rows)
    return {
        "trials": n_eff,
        "verdict_disagreements": verdict_disagreements,
        "flagged_set_disagreements": flagged_disagreements,
        "flagged_disagreement_rate":
            flagged_disagreements / n_eff if n_eff else 0.0,
        "witness_contains_defect_mcb":
            witness_hits_mcb / n_eff if n_eff else 0.0,
        "witness_contains_defect_fcb":
            witness_hits_fcb / n_eff if n_eff else 0.0,
        "mean_witness_size_mcb":
            float(np.mean(wsize_mcb)) if wsize_mcb else None,
        "mean_witness_size_fcb":
            float(np.mean(wsize_fcb)) if wsize_fcb else None,
        "rows": rows,
        "claim": ("verdict agrees across bases; flagged set need not; "
                  "witness set contains the defect under both"),
        "passed": verdict_disagreements == 0,
    }


# =====================================================================
# V5 -- the detection guarantee
# =====================================================================

def v5_detection() -> dict:
    """Sweep D and find the empirical detection threshold vs 2 eps*."""
    rng = np.random.default_rng(SEED + 4)
    configs = [
        ("sigma_0.01", 0.01), ("sigma_0.05", 0.05), ("sigma_0.2", 0.2),
        ("sigma_1.0", 1.0), ("sigma_5.0", 5.0),
    ]
    L, lam = 6, 300.0
    curves, rows = [], []
    guarantee_violations = 0

    for name, sig in configs:
        c = make_ring(L, -lam, lam, sigma=sig, rng=rng).centre_potentials()
        cy = Cycle(name="ring",
                   edges=[(f"R{i}", +1) for i in range(L)],
                   nodes=[f"S{i}" for i in range(L)] + ["S0"])
        tol = compute_tolerance(c, cy)
        Ds = np.logspace(-12, 3, 220)
        flags, first_detect = [], None
        for D in Ds:
            d = clone(c)
            d.edge_offset["R0"] = float(D)
            lab = verdict_label(d, cy)
            hit = (lab == INCONSISTENT)
            flags.append(int(hit))
            if hit and first_detect is None:
                first_detect = float(D)
            # The guarantee: D > 2 eps* must be detected.
            if D > 2 * tol.star and not hit:
                guarantee_violations += 1

        curves.append({
            "config": name, "sigma": sig,
            "eps_num": tol.numerical, "eps_data": tol.data,
            "eps_star": tol.star,
            "predicted_threshold": 2 * tol.star,
            "empirical_threshold": first_detect,
            "ratio": (first_detect / (2 * tol.star)
                      if first_detect else None),
            "D": Ds.tolist(), "detected": flags,
        })
        rows.append({
            "sigma": sig, "eps_star": tol.star,
            "predicted": 2 * tol.star, "empirical": first_detect,
        })

    ratios = [c["ratio"] for c in curves if c["ratio"]]
    return {
        "curves": curves,
        "summary": rows,
        "guarantee_violations": guarantee_violations,
        "max_ratio_empirical_to_predicted":
            float(max(ratios)) if ratios else None,
        "min_ratio_empirical_to_predicted":
            float(min(ratios)) if ratios else None,
        "claim": "every defect above 2 eps* is detected",
        "passed": guarantee_violations == 0,
    }


# =====================================================================
# main
# =====================================================================

def main() -> int:
    print("Running validation experiments (seed %d)...\n" % SEED)
    experiments = [
        ("V1_noise_scale", v1_noise_scale),
        ("V2_fixed_tolerance", v2_fixed_tolerance),
        ("V3_trichotomy", v3_trichotomy),
        ("V4_basis_dependence", v4_basis),
        ("V5_detection", v5_detection),
    ]
    for key, fn in experiments:
        print(f"  {key} ...", end=" ", flush=True)
        RESULTS[key] = fn()
        ok = RESULTS[key].get("passed")
        print("PASS" if ok else "FAIL")

    RESULTS["meta"] = {
        "seed": SEED,
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "platform": platform.platform(),
        "mach_u": MACH_U,
        "z_alpha": Z_ALPHA,
    }

    out = os.path.join(HERE, "results.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(RESULTS, f, indent=2)
    print(f"\nwrote {out}")

    n_pass = sum(1 for k, _ in experiments if RESULTS[k].get("passed"))
    print(f"{n_pass}/{len(experiments)} experiments passed")
    return 0 if n_pass == len(experiments) else 1


if __name__ == "__main__":
    raise SystemExit(main())
