# Paper Artifact Templates

## Experiment Ledger Template

```markdown
## Experiment: <name>

- Purpose:
- Script/command:
- Source code files:
- Base config:
- Scenario variants:
- Seeds:
- Years / population / other scale:
- Raw outputs:
- Summary outputs:
- Figures:
- Verification:
- Archive status: Green / Yellow / Red
- Reproducibility gaps:
```

## Figure Ledger Template

```markdown
| Figure | Claim supported | Source data | Script | Seeds | Status |
|---|---|---|---|---|---|
| Figure 1 | ... | `paper/data/...csv` | `scripts/...py` | `0,1,2` | Green |
```

## Methods Paragraph Template

```markdown
Simulations were run with Python <version> using `uv` for dependency management.
The core implementation is in `src/<package>/`. Stochastic runs used seeds
<seed list>. Unless otherwise stated, scenarios used <base config>. Raw outputs
are archived under `<path>`, summary tables under `<path>`, and figures under
`<path>`. The test suite was checked with `<command>` and returned `<result>`.
```

## Reproducibility Gap Wording

```markdown
This result is retained as an archived exploratory output. The data and figure
are included, but the exact generating script was not preserved as a standalone
versioned artifact. The result should be treated as hypothesis-generating until
the scenario family is promoted into a committed script or CLI command and
rerun with recorded seeds and parameters.
```

## Sensitive Interpretation Wording

```markdown
This model parameter should be read as an abstract selection mechanism, not as a
claim about any real demographic group. The simulation tests whether changing
the retained candidate set changes mutual pair formation under the specified
rules. It does not establish real-world causality.
```

