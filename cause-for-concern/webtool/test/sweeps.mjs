import { SWEEPS } from "../src/cfc/sweeps.js";
for (const s of Object.values(SWEEPS)) {
  const t0 = Date.now();
  const r = s.run();
  const ms = Date.now() - t0;
  let summary = "";
  if (r.kind === "noise") summary = `violations=${r.violations}/${r.trials} medianSlack=${r.medianSlack.toFixed(0)} max=${r.maxObserved.toExponential(2)}`;
  if (r.kind === "fixed") summary = r.strata.map(x=>`${x.fp64.toFixed(2)}/${x.fp32.toFixed(2)}`).join(" ") + ` unwarr=${r.strata[0].unwarranted.toFixed(2)}`;
  if (r.kind === "trichotomy") summary = `U=${(r.fractions.UNDECIDABLE*100).toFixed(1)}% gap=${r.gapOrders.toFixed(1)} orders`;
  if (r.kind === "basis") summary = `verdictDisagree=${r.verdictDisagree} flaggedRate=${(r.flaggedDisagreeRate*100).toFixed(1)}% hit=${r.witnessHitMcb.toFixed(2)} |W|=${r.meanWitnessMcb.toFixed(2)}`;
  if (r.kind === "detection") summary = `violations=${r.violations}/${r.evaluations} ratio=${r.minRatio.toFixed(2)}..${r.maxRatio.toFixed(2)}`;
  console.log(`${s.label.padEnd(24)} ${String(ms).padStart(5)}ms  ${summary}`);
}
