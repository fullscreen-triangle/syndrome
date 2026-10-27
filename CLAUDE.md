# syndrome — working notes for agents

A paper repository. The LaTeX is the content; code (`syndrome-rs/`, `syndrome/`,
`cause-for-concern/prototype/`) supports it.

| Where | What |
|---|---|
| `publication/*/` | standalone papers headed for submission |
| `docs/*/`, `cause-for-concern/docs/*/`, `diseases/` | further papers and source drafts |
| `monograph/chapters/ch*.tex` | the monograph — **consolidates** the papers above, so most chapters restate a paper |
| `tools/*.md` | docs for the research tools below (global notes in `~/.claude/CLAUDE.md`) |

## Reviewing and correcting papers — which tool for which step

Tested on this repo 2026-10-21.

| Step | Tool | Notes |
|---|---|---|
| Find a section / theorem by name | `purpose ask "<stem>"` | `\section` titles are indexed (3,797 of 5,329 symbols are from 109 `.tex` files). One stem, never a question. 0.1 s. |
| Find where an *argument* is made, in words you don't know | `mcp__tracker__repo_search` with `scenes` | **Always pass** `scenes: ["publication","docs","monograph","cause-for-concern","diseases"]` — without it `.claude/worktrees/` copies eat the budget and come back withheld. Dry run by default. |
| Check a paper against its monograph chapter | same `repo_search` | It returns the paper and the chapter side by side when they share a passage (e.g. the holonomy remark: fuzzy-circuits paper ≈ `ch08-fuzzy-circuits.tex`). A correction to one usually needs the other. |
| Exact tokens: `\label`, `\cite` keys, `\ref`, constants | Grep | Neither purpose nor spraypaint is for literals. |
| What else depends on a paper I'm changing | `purpose ckg why <path>` | Lens `.purpose/lens.toml` keeps `section` kinds and **excludes `monograph/`** on purpose (see its comments). **~3 min per query** (`ckg ask "holonomy"`: 194 s) — always run in the background. Act on the NECESSARY list (14 modules for holonomy); the 100+ "reachable but redundant" are noise. |
| What a paper directory contains | `okgg scan <dir>` | Lists `.tex`, `.bib`, captions, figure scripts as entities. No generator call. |
| Which repo / what this repo is about | `mcp__tracker__repo_sense` | χ=6, one fragment; heaviest files are all papers. |

Not useful for paper work here: `wt` (only `syndrome-rs/` is code), `smith`, `srn-fleet`.

## Hygiene

- `.claude/settings.local.json` holds credentials. Never run raw `spraypaint ask` with
  credential-shaped terms in this repo; use tracker's `repo_search`, which withholds it.
- `wt` writes `.wt/` beside what it analyses and it is not gitignored — delete it after.
- `.spraypaint/` is excluded via `.git/info/exclude`. `.purpose/index.json` is currently
  tracked even though it is a cache — leave it to the user to untrack.
- Build check for a paper: run `pdflatex`/`bibtex` in the paper's own directory and read
  the `.log` for `^!` errors and undefined references before reporting it compiles.
