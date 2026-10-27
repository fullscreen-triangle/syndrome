Kundai Farai Sachikonye
Experimental Bioinformatics, TUM School of Life Sciences
AIMe Registry for Artificial Intelligence
Maximus-von-Imhof-Forum 3, 85354 Freising, Germany
kundai.sachikonye@bitspark.com

Professor Hao Lin
Editor-in-Chief, *Medinformatics*
Bon View Publishing

Dear Professor Lin,

I am pleased to submit the enclosed manuscript, **"Disease Metabolic Network
Modelling: Separating Numerical Noise from Thermodynamic Inconsistency in
Cycle-Consistency Tests on Metabolic Circuits,"** for consideration as an
Original Research article in *Medinformatics*.

**What the paper addresses.** Metabolic network reconstructions are routinely
checked for thermodynamic consistency using cycle sums, which vanish
identically for a consistent network by the Wegscheider condition. Any such
check needs a tolerance below which a computed cycle sum counts as zero, and
near-universal practice is to fix that tolerance at a round number — 1e-6 is
typical — and describe it as a solver setting. This paper shows that framing is
a category error with a measurable cost, and replaces it with a tolerance
computed per cycle from the arithmetic and from the reported uncertainty of the
underlying thermodynamic annotations.

**Key findings.**

1. The rounding-error scale of a cycle sum is derived rather than assumed.
   Measuring the cost of a fixed tolerance corrected a prediction we had made:
   in double precision the rounding error never comes within six orders of
   magnitude of the customary threshold, so a fixed tolerance produces no false
   positives from rounding. The two-sided failure we predicted appears only in
   single precision.

2. Only uncertainty in the edge data reaches a cycle sum: errors in the species
   potentials, including all concentration error, cancel around every cycle.
   Under simulated noise the resulting tolerance gives false positives at 0.009
   against a nominal 0.01 and detects defects of twice its value with
   probability at least 0.993.

3. On experimental data the cost of a fixed tolerance is total. Of the 67
   independent cycles among 418 reactions whose equilibrium constants were
   measured (3,276 measurements in the NIST TECRDB), every cycle sum exceeds
   the customary 1e-6 kJ/mol, so a fixed test declares all 67 inconsistent.
   The cycle-local tolerance flags 7 and returns UNDECIDABLE on 60; its two
   floors lie 14 orders of magnitude apart.

4. The real data also corrected the method. Repeated measurements of one
   reaction are cycles whose sum is known to be zero, and they show
   measurement errors heavier-tailed than the Gaussian the data floor assumes;
   calibrated on them, the test flags 3 cycles. The data hold several
   inconsistencies at once, so localisation is by how often a reaction lies on
   a flagged cycle rather than by a single witness set.

5. In the human erythrocyte network, assembled from UniProt and Rhea,
   pyruvate kinase lies on no cycle, and none of the network's seven cycles
   has a measured equilibrium constant on every edge. A cycle-consistency test
   therefore cannot address erythrocyte enzymopathies on present data; two
   further measurements, of the Rapoport-Luebering shunt, would make one cycle
   testable.

**Fit to the journal.** The work sits in *Medinformatics*' Integrative and
Computational Biology area, specifically computational modelling of biological
systems, and speaks to the journal's stated aim of connecting biomedical
scientists with mathematicians and computer scientists. Its practical
contribution is directed at anyone running consistency checks on metabolic
reconstructions: the paper shows that a parameter widely treated as an
implementation detail is silently encoding a detection threshold, and gives a
computable replacement together with the conditions under which a result may
be claimed at all.

**Scope of the claims.** I want to be explicit about what the manuscript does
not show. The diagnostic protocol, specified with pre-registered criteria, was
run on the real erythrocyte network and stopped at its own pre-registered check,
because the target reaction lies on no cycle; the paper reports this as an
invalid experiment, not a negative result. The paper also states what the test
cannot see: a loss of enzyme activity that leaves equilibrium constants
unchanged preserves every cycle sum. Whether disease produces edge data that
fail the test remains open, and the present data cannot settle it.

**Declarations.** This manuscript is original, is not under consideration
elsewhere, and has not been published previously. There are no conflicts of
interest to declare. The validation suite, the snapshot of public experimental data
it analyses, and the complete numerical record are openly available. Use of generative AI in preparing the manuscript is disclosed
in Materials and Methods, as the journal requires.

The submission comprises the manuscript, a supplementary file containing the
proofs of all numbered results, the typed language, the full protocol and the
details of the experimental-data analysis, five figures, and a graphical
abstract.

Thank you for your consideration. I would be glad to respond to any questions.

Yours sincerely,

Kundai Farai Sachikonye
