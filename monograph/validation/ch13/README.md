# Chapter 13 checks

The checks behind the `[C]` labels of `chapters/ch13-social-mechanics.tex`.

| Script | Needs | Writes |
|---|---|---|
| `coordination.py` | numpy | `results.json` |

```
python coordination.py
```

Everything here is a computation on **contact structure alone**. A single
per-contact transmission probability `tau` is fixed by hand and held
constant; no environmental variable, no climate series, and no
pathogen-specific parameter is fitted or used. That is deliberate: the
chapter's claim is that coordination structure moves the epidemic threshold
*by itself*, so a check that smuggled in a temperature term would not test
it. Equally, these checks say nothing about whether temperature matters —
that question is answered from the literature in the chapter text, not here.

Seed `20261027`; `numpy` version recorded in `results.json`.

## What each check establishes

**C1 — degree heterogeneity at fixed mean (positive).** Three contact
distributions with the *same* mean degree (8) and the same `tau` (0.08)
differ in `R0 = tau * <k²>/<k>` by a factor of about 6, and the simulated
final outbreak size follows: 0.003 for the regular graph against 0.203 for
the bimodal one. The mean number of contacts per person does not determine
the threshold; the second moment does. Final sizes come from bond
percolation on sampled configuration-model graphs, so they are a check on
the formula, not a restatement of it.

**C2a — assortativity at fixed row sums (negative).** Reallocating each
group's contacts between inside and outside the group, holding every
group's total fixed and all groups symmetric, leaves the dominant
eigenvalue of the next-generation matrix *exactly* unchanged (0.5000 in
every row). This is Perron–Frobenius: a non-negative matrix with constant
row sums `s` has dominant eigenvalue `s` with the uniform vector as
eigenvector, however the mass within each row is arranged.

This check was written expecting a rise and found none. It is reported
because it constrains what "coordination" can mean: assortative mixing
*per se*, at fixed contact budget and symmetric groups, is not a
vulnerability mechanism.

**C2b — activity heterogeneity at fixed population mean (positive).**
Letting the five groups differ in activity under proportionate mixing,
`C_ij = k_i k_j / (g <k>)`, raises the dominant eigenvalue from 0.5000 to
0.7025 at constant population mean contact. The `predicted_tau_times_excess`
column confirms the eigenvalue equals `tau <k²>/<k>` to the printed digits.
This is C1 in matrix form, and it is the mechanism C2a lacks.

**C3 — group size at fixed mean degree (positive, non-monotone).** With mean
degree held at 40, concentrating the contact budget into larger fully-mixed
groups raises `R*`, the number of outside infections produced by one
introduction plus every case it causes inside its own group, from 2.00 at
`s=1` to 6.19 at `s=30`. Within-group spread is a Reed–Frost chain binomial
compounded over generations, which is what makes group size bite: a
single-generation count misses it.

Two effects oppose each other — local amplification rises superlinearly as
`(s-1) tau` approaches 1, while the contact budget reaching other groups
falls linearly — so `R*` is non-monotone in general and self-limiting in
the extreme: a group that absorbs a person's whole budget can infect no one
outside. Over the range checked here the first effect dominates.

**C4 — the source paper's weighting function (refuted).** The paper that
this chapter replaces posits a monotone step function
`f = 0.2, 0.4, 0.6, 0.8, 1.0` over five coordination regimes, giving a 5×
phase-locked-to-turbulent vulnerability ratio. Computing `<k²>/<k>` for a
two-level contact family parametrised by the same order parameter at fixed
mean degree gives a **U-shaped**, not increasing, function: 38.7, 9.3, 11.2,
46.7, 250.9 as `r` runs 0.15 → 0.97, minimised near `r = 0.4`.

The reason is in the `core_degree` and `periphery_degree` columns.
`<k²>/<k>` at fixed mean is minimised by a *uniform* distribution and rises
in both directions away from it: at `r = 0.15` a small periphery carries
degree 45 while 85% of the population carries 1.4; at `r = 0.97` a 3% core
carries degree 259. Both are concentrated, and concentration is what the
second moment measures.

So a single scalar order parameter from 0 to 1 does not order populations by
vulnerability unless one also fixes which tail is heavy, and the posited
monotone `f` does not follow from the contact structure it summarises. The
chapter states the second-moment result instead and does not use `f` or its
numerical values for any claim.

## What these checks do not show

- Nothing here is calibrated against observed incidence anywhere. `tau` is
  stipulated. The absolute numbers have no epidemiological meaning; only the
  ratios at fixed mean do.
- C3's `R*` uses a households approximation (one level of grouping,
  fully-mixed groups, proportionate mixing outside). Real contact networks
  have overlapping groups.
- The configuration model of C1 has no clustering and no degree
  correlations, both of which are present in measured contact networks and
  both of which move the threshold.
- No check here bears on co-evolution time, template convergence, or
  geographic prevalence. Those claims are cited to the literature in the
  chapter or dropped.
