#!/usr/bin/env python3
"""
run_cfc.py -- run .cfc programs and store results as JSON.

    python run_cfc.py examples/kcl_tolerance.cfc
    python run_cfc.py examples/*.cfc --outdir results
    python run_cfc.py examples/kcl_tolerance.cfc --tokens

Exit status is 0 when every program reaches status OK, 1 otherwise, so
the script is usable in a CI gate. Note that a NEGATIVE run exits 1 but
is a legitimate scientific outcome, while an INVALID run means the
experiment licensed no conclusion at all -- the two are distinguished in
the output rather than collapsed.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cfc import run_file, tokenize  # noqa: E402
from cfc.parser import parse  # noqa: E402


STATUS_NOTE = {
    "OK": "all assertions held",
    "NEGATIVE": "an assertion failed or declined -- a real result",
    "INVALID": "a reference check failed -- no conclusion licensed",
    "ERROR": "the program could not be run",
}


def summarise(rec_json: dict) -> str:
    st = rec_json["status"]
    lines = [
        f"  status      : {st}  ({STATUS_NOTE.get(st, '')})",
        f"  clock       : {rec_json['committed_measurements']} "
        f"committed measurement(s)",
    ]
    if rec_json.get("floor") is not None:
        lines.append(f"  floor       : {rec_json['floor']:g}")

    verdicts = rec_json.get("verdicts", [])
    if verdicts:
        tally = {}
        for v in verdicts:
            tally[v["verdict"]] = tally.get(v["verdict"], 0) + 1
        parts = ", ".join(f"{k}={v}" for k, v in sorted(tally.items()))
        lines.append(f"  verdicts    : {len(verdicts)} ({parts})")

    tols = rec_json.get("tolerances", [])
    if tols:
        n_missing = sum(1 for t in tols if not t["data_available"])
        lines.append(f"  tolerances  : {len(tols)} computed"
                     + (f", {n_missing} without uncertainty data"
                        if n_missing else ""))

    w = rec_json.get("witness_set")
    if w is not None:
        shown = ", ".join(w[:6]) + ("..." if len(w) > 6 else "")
        lines.append(f"  witness set : {len(w)} edge(s) [{shown}]")

    for e in rec_json.get("emissions", []):
        lines.append(f"  emit L{e['line']:<4}: {e['message']}")

    if rec_json.get("error"):
        lines.append(f"  error       : {rec_json['error']}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run CFC programs.")
    ap.add_argument("paths", nargs="+", help=".cfc files or globs")
    ap.add_argument("--outdir", default="results",
                    help="directory for JSON output (default: results)")
    ap.add_argument("--tokens", action="store_true",
                    help="dump the token stream and exit")
    ap.add_argument("--ast", action="store_true",
                    help="dump the parsed AST and exit")
    ap.add_argument("--quiet", action="store_true",
                    help="write JSON only, no summary")
    args = ap.parse_args()

    files: list[str] = []
    for p in args.paths:
        hits = glob.glob(p)
        files.extend(hits if hits else [p])
    if not files:
        print("no input files", file=sys.stderr)
        return 2

    if args.tokens or args.ast:
        for path in files:
            with open(path, encoding="utf-8") as f:
                src = f.read()
            print(f"=== {path} ===")
            if args.tokens:
                for t in tokenize(src):
                    print(f"  {t}")
            else:
                prog = parse(src)
                for s in prog.stmts:
                    print(f"  {type(s).__name__:16s} line {s.line}")
        return 0

    os.makedirs(args.outdir, exist_ok=True)
    worst = 0
    for path in files:
        rec = run_file(path).to_json()
        base = os.path.splitext(os.path.basename(path))[0]
        out = os.path.join(args.outdir, base + ".json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=2)
        if not args.quiet:
            print(f"=== {path} ===")
            print(summarise(rec))
            print(f"  json        -> {out}\n")
        if rec["status"] != "OK":
            worst = 1
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
