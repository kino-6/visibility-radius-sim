# Visibility Radius Working Paper Bundle

This directory is a self-contained paper bundle for the visibility-radius simulation.

## Main Papers

- `visibility_radius_working_paper_ja.md`: Japanese working paper with embedded figures.
- `visibility_radius_working_paper.md`: English working paper with embedded figures.
- `drafts/`: older text-only drafts kept for comparison; use the root-level papers above as canonical versions.
- `appendix_followups/`: follow-up appendix figures, summaries, and report for robustness checks A-G.
  - `appendix_followups_report.md`: English appendix report.
  - `appendix_followups_report_ja.md`: Japanese appendix report with term notes.

## Figures

Figures are stored under `figures/` and linked with relative paths from the papers.

- `sns_2000s_simple.png`: baseline SNS 2000s trajectory.
- `actionable_attention_comparison.png`: phantom candidates vs actionable reserve.
- `reserve_threshold_slots_multiseed.png`: protected actionable-slot threshold.
- `civilizational_adaptation_longrun.png`: long-run culture scenarios.
- `regional_culture_crossing_comparison.png`: cross-region pairing comparison.
- `regional_culture_trajectories_by_culture.png`: culture-by-culture regional trajectories.
- `behavioral_action_interventions.png`: behavioral action intervention comparison.
- `appendix_followups/figures/`: figures for follow-up robustness checks A-G.

## Data

Summary CSV files used by the paper are stored under `data/`.

- `actionable_attention_comparison_summary.csv`
- `civilizational_adaptation_longrun_summary.csv`
- `regional_culture_crossing_summary.csv`
- `reserve_threshold_slots_multiseed_summary.csv`
- `behavioral_action_interventions_summary.csv`
- `behavioral_action_interventions_seed42_summary.csv`
- `appendix_followups/data/`: summary CSV files for follow-up robustness checks A-G.

## Notes

Supporting analysis notes are stored under `notes/`.

- `behavioral_action_interventions_report.md`: action-level intervention report.
- `reserve_threshold_report.md`: protected-slot threshold report.
- `factor_analysis.md`: earlier extinction-driver ablation notes.
- `appendix_followups_report.md`: short copy of the follow-up robustness report.

## Note

This bundle is a working-paper artifact, not a publication-ready reproducibility package. Some exploratory results were generated during interactive analysis. For publication-grade reproducibility, promote those scenario scripts into versioned CLI commands or notebooks.
