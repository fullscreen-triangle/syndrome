/**
 * End-to-end: examples, sweep lab, docs, inspector.
 */
import { chromium } from "playwright";

const URL = process.env.CFC_URL || "http://localhost:4173/";
const OUT = "test/shots";

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1680, height: 1020 } });
const errors = [];
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
page.on("pageerror", (e) => errors.push(String(e)));

await page.goto(URL, { waitUntil: "networkidle" });
await page.waitForTimeout(600);

let bad = 0;
const check = (ok, msg) => { console.log(`  ${ok ? "PASS" : "FAIL"}  ${msg}`); if (!ok) bad++; };

// ---- landing --------------------------------------------------------
// The app opens here, so this also covers the default view.
const landed = await page.$eval("body", (b) =>
  // The masthead is uppercased by CSS, so innerText is not the source casing.
  /Cause-for-Concern . Workbench/i.test(b.innerText) &&
  /Two floors, neither of them constant/i.test(b.innerText) &&
  /UNDECIDABLE/.test(b.innerText));
check(landed, "landing page renders on load");

// Its file links are the intended way in.
await page.click("[data-testid=landing-start]");
await page.waitForTimeout(250);
const inEditor = await page.$("[data-testid=run]");
check(!!inEditor, "landing opens the first experiment in the editor");

// ---- examples -------------------------------------------------------
const expect = {
  "01_validity_gate.cfc": "OK",
  "02_undecidable.cfc": "OK",
  "03_invalid_reference.cfc": "INVALID",
  "04_rejected.cfc": "ERROR",
  "05_node_vs_edge.cfc": "OK",
};
for (const [f, want] of Object.entries(expect)) {
  await page.locator(`div[title='${f}']`).first().click();
  await page.waitForTimeout(180);
  await page.click("[data-testid=run]");
  await page.waitForTimeout(800);
  const st = await page.$eval("body", (b) => {
    const m = b.innerText.match(/●\s+(OK|NEGATIVE|INVALID|ERROR)/);
    return m ? m[1] : "none";
  });
  check(st === want, `${f.padEnd(26)} → ${st}`);
  await page.screenshot({ path: `${OUT}/${f.replace(".cfc", "")}.png` });
}

// ---- charts + inspector --------------------------------------------
await page.locator("div[title='01_validity_gate.cfc']").first().click();
await page.waitForTimeout(150);
await page.click("[data-testid=run]");
await page.waitForTimeout(1100);
const svgs = await page.$$eval("svg", (n) => n.length);
const canv = await page.$$eval("canvas", (n) => n.length);
check(svgs >= 4 && canv >= 1, `charts rendered: ${svgs} svg, ${canv} webgl`);
await page.screenshot({ path: `${OUT}/charts.png` });

await page.click("text=Inspector");
await page.waitForTimeout(350);
const rows = await page.$$eval("tbody tr", (n) => n.length);
check(rows === 4, `inspector rows = ${rows} (expected 4)`);
await page.screenshot({ path: `${OUT}/inspector.png` });

// ---- keyboard shortcut ---------------------------------------------
await page.keyboard.press("Control+Enter");
await page.waitForTimeout(700);
const stillOk = await page.$eval("body", (b) => /●\s+OK/.test(b.innerText));
check(stillOk, "Ctrl+Enter re-runs");

// ---- sweep lab ------------------------------------------------------
await page.click("button[title='Validation lab']");
await page.waitForTimeout(400);
await page.click("text=Run all sweeps");
await page.waitForTimeout(3000);
const done = await page.$$eval("div", (ns) =>
  ns.filter((n) => /^\d+ ms$/.test(n.textContent.trim())).length);
check(done >= 5, `sweeps completed: ${done}/5`);
await page.screenshot({ path: `${OUT}/lab-noise.png` });

for (const [label, shot] of [["V3 · Trichotomy", "lab-trichotomy"],
                             ["V4 · Basis dependence", "lab-basis"],
                             ["V5 · Detection", "lab-detection"]]) {
  await page.click(`text=${label}`);
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${OUT}/${shot}.png` });
}

// ---- docs -----------------------------------------------------------
await page.click("button[title='Reference']");
await page.waitForTimeout(350);
const hasRef = await page.$eval("body", (b) => b.innerText.includes("CFC language reference"));
check(hasRef, "reference pane renders");
await page.screenshot({ path: `${OUT}/docs.png` });

check(errors.length === 0, `console errors: ${errors.length}`);
for (const e of errors.slice(0, 4)) console.log("     ", e.slice(0, 170));

await browser.close();
process.exit(bad ? 1 : 0);
