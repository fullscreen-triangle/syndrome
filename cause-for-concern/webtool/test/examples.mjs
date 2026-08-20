import { runSource } from "../src/cfc/interpreter.js";
import { EXAMPLES } from "../src/data/examples.js";
let bad = 0;
for (const [name, src] of Object.entries(EXAMPLES)) {
  const r = runSource(src, name);
  const nV = r.verdicts.length;
  const tally = {};
  for (const v of r.verdicts) tally[v.verdict] = (tally[v.verdict]||0)+1;
  console.log(`${name.padEnd(26)} ${r.status.padEnd(9)} clock=${String(r.committedMeasurements).padStart(2)} verdicts=${nV} ${JSON.stringify(tally)} W=${JSON.stringify(r.witnessSet)}`);
  if (r.error) console.log(`   -> ${r.error}`);
  const expected = { "04_rejected.cfc":"ERROR", "03_invalid_reference.cfc":"INVALID" };
  const want = expected[name] || "OK";
  if (r.status !== want) { console.log(`   !! expected ${want}`); bad++; }
}
process.exit(bad ? 1 : 0);
