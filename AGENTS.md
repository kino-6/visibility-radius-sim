# Agent Notes

This repository is an abstract agent-based simulation for visibility radius, phantom comparison candidates, actionable attention, and cultural adaptation. It is not a demographic forecast and should not be framed as a claim about real human behavior.

## Current Research State

The main branch contains the current working-paper bundle and appendix outputs.

The core model now has:

- `phantom_candidate_mode=sampled`: perceived non-pairable candidates can consume top-k selection slots.
- `actionable_selection_reserve_fraction`: a global share of top-k slots reserved for real candidates inside action radius.
- `regional_actionable_reserve_fractions`: place-held culture values for clustered regions.
- `allow_cross_region_pairing`: whether region boundaries block pair formation across clusters.
- `Agent.region_id`: clustered locations can be treated as regions/countries.
- optional abstract `Agent.gender`: A/B labels for mechanism-only gendered aspiration follow-ups.

## Project Skills

- `paper-artifact-reproducibility`: use when creating or reviewing working papers, appendices, reports, figure bundles, or simulation artifacts that need traceable claims, parameter/seed disclosure, figure-data links, reproducibility archives, and careful limitation wording.

## Main Findings So Far

1. **Phantom candidates make candidate-pool expansion causal.**

   Without phantom candidates, `candidate_pool_multiplier` mostly acts as a diagnostic metric. With sampled phantom candidates, non-pairable comparison candidates can win attention and reduce actionable pair formation.

2. **The collapse mechanism is attention displacement.**

   The severe failure mode is:

   ```text
   global visibility + local action radius + bounded top-k attention
   -> top-k slots filled by phantom/non-actionable candidates
   -> real actionable mutual selection collapses
   -> births collapse
   ```

3. **Actionable reserve is a strong avoidance mechanism.**

   Reserving part of top-k for real/actionable candidates prevents phantom candidates from taking every attention slot. In seed-42 outputs:

   ```text
   current phantom: final ratio 0.415
   actionable reserve 50%: final ratio 0.945
   actionable reserve 75%: final ratio 0.941
   ```

4. **The reserve effect is threshold-like and slot-based.**

   With `top_k=16`, reserve fractions become integer protected slots. Multi-seed results show:

   ```text
   0 protected slots: final ratio ~0.001
   1 protected slot:  final ratio ~0.094
   2 protected slots: final ratio ~0.390
   4 protected slots: final ratio ~0.735
   8 protected slots: final ratio ~0.983
   ```

   The key condition is not just late birth recovery. The system must avoid a deep demographic bottleneck early enough.

5. **Place-held culture matters.**

   Region-level reserve cultures show that no-reserve regions are selected out, while weak/balanced/strong reserve regions survive. In the current regional experiment:

   ```text
   No reserve regions: near extinction
   Weak reserve regions: survive
   Balanced reserve regions: survive
   Strong reserve regions: survive
   ```

6. **Cross-region pairing changes culture shares more than survival itself.**

   Blocking cross-region pair formation slightly improves total population in the current regional run, while allowing cross-region pairing lets strong reserve cultures gain somewhat more share. This is not yet robustly explored.

## Important Outputs

- `paper/visibility_radius_working_paper_ja.md`: Japanese working paper with figures.
- `paper/visibility_radius_working_paper.md`: English working paper with figures.
- `outputs/phantom_candidates/phantom_candidate_comparison_seed42.csv`: phantom vs no-phantom comparison.
- `outputs/actionable_attention/actionable_attention_comparison.png`: collapse vs actionable reserve comparison.
- `outputs/civilizational_adaptation/civilizational_adaptation_longrun.png`: fixed-culture long-run comparison.
- `outputs/regional_culture/regional_culture_crossing_comparison.png`: cross-region pairing allow vs block.
- `outputs/regional_culture/regional_culture_trajectories_by_culture.png`: culture-by-culture trajectories.
- `outputs/reserve_threshold/reserve_threshold_slots_multiseed.png`: protected slot threshold curve.
- `outputs/reserve_threshold/reserve_threshold_report.md`: short threshold report.
- `outputs/factor_analysis/factor_analysis.md`: earlier ablation notes.
- `outputs/behavioral_interventions/behavioral_action_interventions.png`: behavior intervention comparison.
- `docs/appendix_followups_plan.md`: plan for follow-up robustness checks A-G.
- `docs/appendix_followups_results.md`: results report for follow-up robustness checks A-G.
- `outputs/appendix_followups/appendix_followups_overview.png`: visual overview of follow-up checks.
- `paper/appendices/reproducibility_archive_ja.md`: Japanese reproducibility archive with scripts, seeds, parameters, output paths, and known gaps.
- `paper/appendices/reproducibility_archive.md`: English reproducibility archive.
- `outputs/gendered_aspiration/gendered_aspiration_summary.png`: abstract A/B gendered aspirational selectivity follow-up.
- `paper/notes/gendered_aspiration_report_ja.md`: Japanese note for the gendered aspiration follow-up.

## Modeling Caveats

- Most cultural experiments are still fixed-culture models. Region culture does not yet adapt, imitate successful cultures, or diffuse.
- `regional_actionable_reserve_fractions` are configured programmatically in exploratory scripts rather than exposed through the CLI.
- Long-run outputs can become hard to interpret after near-extinction because some rates become artifacts of tiny denominators.
- Generated outputs are useful for research traceability but can grow quickly.

## Next Useful Experiments

- Add cultural diffusion or institutional learning at the Region level.
- Add migration between regions separately from cross-region pair formation.
- Track births and pair formation per region/culture directly in metrics.
- Sweep `regional_actionable_reserve_fractions` and `allow_cross_region_pairing` across more seeds.
- Test whether moderate reserve cultures outperform strong reserve cultures under higher migration or cultural homogenization.
