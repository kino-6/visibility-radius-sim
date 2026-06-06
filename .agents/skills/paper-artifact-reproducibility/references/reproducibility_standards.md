# Reproducibility Standards Reference

Use this as background when writing or reviewing computational papers. Keep the paper practical; do not overfit to any single venue.

## External Anchors

### ACM Artifact Review and Badging

Source: <https://www.acm.org/publications/policies/artifact-review-and-badging-current>

Useful takeaways:

- Separate artifact availability/evaluation from result validation.
- Treat documentation, consistency with the paper, completeness, exercisability, and verification evidence as artifact quality dimensions.
- Distinguish:
  - repeatability: same team, same setup
  - reproducibility: different team, same artifacts/setup
  - replicability: different team, independently developed artifacts/setup

Apply to this project:

- Mark whether a result is rerunnable from committed scripts or only archived.
- Do not call something "replicated" because it was rerun with the same code.

### JOSS Review Checklist

Source: <https://joss.readthedocs.io/en/latest/review_checklist.html>

Useful takeaways:

- Review is checklist-driven.
- Check repository availability, license, scope/significance, installation, functionality, documentation, example usage, and tests.
- A software paper should explain purpose to non-specialists.

Apply to this project:

- Include installation and rerun commands.
- Keep the README and paper bundle index current.
- Mention tests and smoke checks in final reports.

### PLOS Ten Simple Rules for Reproducible Computational Research

Source: <https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003285>

Useful takeaways:

- For every result, track how it was produced.
- Record program names, versions, parameters, and inputs.
- Random seeds matter for exact reproduction.
- Store raw data behind figures so figures can be regenerated or adjusted without rerunning everything.

Apply to this project:

- For simulation outputs, record `SimulationConfig`, seed(s), script, raw CSV, summary CSV, and plot path.
- If a figure lacks a raw source file, treat it as a reproducibility gap.

### Nature Portfolio Reporting and Availability

Source: <https://www.nature.com/natmachintell/editorial-policies/reporting-standards>

Useful takeaways:

- Published claims should be replicable/buildable by readers.
- Manuscripts should disclose material, data, code, protocols, and restrictions.
- Data availability statements should explain access to the minimum dataset needed to verify and extend claims.

Apply to this project:

- Add a data/code availability section when making a public-facing paper.
- Explain any restrictions or missing generation scripts.

### PLOS Computational Modeling Reproducibility

Source: <https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1007881>

Useful takeaways:

- Common failures include incomplete simulation descriptions, missing software versions, missing run instructions, and missing code.
- Good practice includes stating software and versions, providing machine-readable code, and having a third party test whether the methods are sufficient.

Apply to this project:

- Prefer named scripts over ad hoc notebook/session generation.
- Add a future task when an experiment family is archived but not scripted.

## Practical Severity Levels

- **Green**: committed script + raw data + summary data + figure + seeds + parameters + tests.
- **Yellow**: output/data archived and parameters partly known, but generation script incomplete.
- **Red**: figure or claim exists without source data, parameters, seed, or script.

