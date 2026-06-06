---
name: paper-artifact-reproducibility
description: Use when creating, revising, or reviewing a computational paper, working paper, simulation report, appendix, or research artifact that needs reproducible methods, parameter/seed disclosure, figure-data traceability, archive structure, limitations, and careful claim wording.
---

# Paper Artifact Reproducibility

## Core Rule

Treat every paper claim as a bundle of four linked artifacts:

```text
claim -> figure/table -> data/output file -> script/config/seed
```

If any link is missing, either add it, weaken the claim, or mark it as an archived exploratory result.

## Workflow

1. **Frame the claim.**
   - State the research question and hypothesis before presenting results.
   - Separate mechanism claims from empirical-world claims.
   - Flag toy-model, exploratory, non-calibrated, or non-forecast status early.

2. **Create an experiment ledger.**
   - Record scripts or CLI commands used.
   - Record seeds, seed ranges, run counts, and whether results are fixed-seed or multi-seed.
   - Record parameters that can materially affect results.
   - Record output paths for raw CSVs, summary CSVs, figures, and reports.
   - Mark any result that cannot be regenerated from committed code as `archived exploratory output`.

3. **Make figures auditable.**
   - Every figure must have an adjacent or discoverable source data file.
   - Captions should explain what comparison is being shown, not just name the plot.
   - Avoid relying on visually impressive curves without reporting the metrics used to interpret them.
   - When possible, include min/mean/max or seed count for stochastic results.

4. **Write methods so another agent can rerun them.**
   - Include environment, package manager, language/runtime, dependency lockfile, and key source files.
   - Include representative rerun commands.
   - Include exact scenario constructors or config files when available.
   - Include limitations of reproducibility, such as missing scripts or ad hoc exploratory generation.

5. **Constrain interpretation.**
   - Distinguish repeatability, reproducibility, and replication when relevant.
   - Do not let a simulation result imply a real-world causal claim without calibration and external evidence.
   - Name denominator artifacts, selection effects, stochastic variance, and model constraints.
   - Use neutral language for sensitive social claims; describe model mechanisms before labels.

6. **Archive before finalizing.**
   - Put paper-ready figures and summary data under `paper/`.
   - Keep generated bulk outputs under `outputs/`.
   - Add an appendix or reproducibility archive when a paper has more than one experiment family.
   - Update the paper README or index so future readers know which file is canonical.

## Minimum Paper Artifact Checklist

Before calling a paper/report complete, verify:

- [ ] Research question and non-claims are explicit.
- [ ] Each major figure/table maps to a data file.
- [ ] Each major result maps to a script, CLI command, or archived exploratory note.
- [ ] Seeds and stochastic run counts are listed.
- [ ] Parameters and scenario variants are listed.
- [ ] Environment and dependency strategy are listed.
- [ ] Tests or smoke checks are reported.
- [ ] Limitations include both model limitations and reproducibility gaps.
- [ ] Claims are no stronger than the experiment design supports.
- [ ] Paper bundle has stable paths independent of `outputs/` churn.

## Suggested Directory Pattern

```text
paper/
  README.md
  working_paper.md
  working_paper_ja.md
  figures/
  data/
  appendices/
    reproducibility_archive.md
    reproducibility_archive_ja.md
  notes/
outputs/
  scenario_family/
docs/
  plan_or_progress_notes.md
scripts/
  run_named_experiment.py
```

## When To Read References

- Read `references/reproducibility_standards.md` when strengthening the checklist, writing a reproducibility appendix, or justifying why seeds/scripts/data availability matter.
- Read `references/templates.md` when drafting a methods section, figure ledger, or reproducibility archive.

