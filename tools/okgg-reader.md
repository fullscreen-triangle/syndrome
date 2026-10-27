# okgg-reader

Read a repository through its okgg graph until what you understand matches what the graph
separates. Every explanation it took to get there is kept, per triple.

```bash
okgg run  ../dcat-ap-plus --all-branches --base main --skip-rev gh-pages   # the graph + reading.json
node dist/cli.js ../dcat-ap-plus/.okgg --receiver <you>                     # the tutor
okgg read ../dcat-ap-plus --receiver <you>                                  # your progress, from Rust
```

## How it works

`okgg` writes `reading.json`: the descent tree of the graph as ranked **lessons**. A lesson
says *these files are split by this facet into these groups*, and names the words that
decided each file's group. The tutor takes the first required lesson you have not understood
and runs this loop:

1. **Explain.** It prints the evidence block: the groups, the words that decide them, and some
   example files. It is deterministic and taken verbatim from the graph. A local model
   (Ollama, `llama3.2` by default) turns the evidence into prose.
2. **Check.** You sort a sample of the lesson's files into the groups; open them and read
   them if you need to. The sample never includes a file just listed as an example.
3. **Compare, blindly.** Your grouping and the graph's are compared by which pairs each
   separates, and by nothing else. This is the translation test of the manuscript (Part III),
   with you in the generator's place.
   - Understood means **quiescent**. No pair the graph witnesses as different is joined by
     you, and no pair it gives the same witnessed value is split by you.
   - Pairs with an undetermined side are **open**. The graph does not know how they resolve,
     so you are not judged on them.
4. **Re-explain.** If you are not quiescent, the tutor names each misplaced file's group and
   the evidence for it, asks the model to explain the difference, and checks again on files
   you have not yet been shown. After `--max-tries` it records the lesson as contested,
   reveals the groups, and moves on.

The model explains, but it never judges whether you understood; that is the check's job.

## What is kept

- **`understanding.jsonl`**, beside `reading.json`, is an append-only record of acts:
  `explain`, `check`, `understood`, `contested`. Each act names its lesson, the triples it
  covers, and what was said or answered. Nothing is ever rewritten. Understanding a lesson
  and later failing it is a further act, not a deletion.
- **The metadata of a triple** is a fold over that record:
  `UnderstandingStore.metadataFor(tid, reader)` returns the explanations it took, the number
  of checks, and when it was understood. It is recomputed on read and never stored.
- **`receiver-<you>.json`** is your own graph, a `ReceiverGraph` from
  `@four-sided-triangle/individuate`. Each understood lesson is fixed as a distinction, in
  contact with the lesson it refines, so it grows in the shape of the descent tree.

None of this reaches the committed graph. The explanations are the virtual stratum: they can
complete what you hold, but the graph's values come only from the witness (manuscript,
thm:reach).

## Options

| flag | default | |
|---|---|---|
| `--receiver <id>` | required | whose understanding this is; readers are kept apart |
| `--model` | `llama3.2` | Ollama model for explanations |
| `--no-llm` | | show the evidence only, with no prose |
| `--max-tries` | 3 | checks per lesson before it is left contested |
| `--sample` | 6 | files per check |
| `--lessons N` | | stop after N lessons |
| `--ollama-url` | `$OLLAMA_HOST` | |

To require fewer lessons, choose your own sufficiency: write a reading order with
`okgg read <dir> --theta 0.8 --json > reading-0.8.json` and pass that file to the tutor.

## Build and test

```bash
npm run build --prefix ../../../../semantics/four-sided-triangle/sdk-ts   # the SDK's dist/, once
npm install && npm run build && npm test
```

The library is exported from `src/index.ts`. `OkggSource` adapts the lessons to the SDK's
`SourceAdapter`, so `createIndividuator` can answer free questions over the same graph.
