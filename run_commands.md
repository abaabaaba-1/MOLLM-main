# Run Commands and Early-Stopping Notes

## Primary Runs (LLM-driven MOO)
- `python3 main.py problem/sacs_geo_jk/config.yaml --seed 42`
- `python3 main.py problem/sacs_geo_pf/config.yaml --seed 80`
- `python3 main.py problem/sacs_section_pf/config.yaml --seed 90`
- (optional robustness) `python3 main.py problem/sacs_section_jk/config.yaml --seed 42`

## Baseline Comparisons (optional)
Use the same config paths as above, replacing the command as needed:
- `python3 baseline_ga.py --config problem/sacs_section_pf/config.yaml --seed 90`
- `python3 baseline_nsga2.py --config problem/sacs_section_pf/config.yaml --seed 90`
- `python3 baseline_sms.py --config problem/sacs_section_pf/config.yaml --seed 90`
- Repeat for `sacs_geo_pf`, `sacs_geo_jk`, `sacs_section_jk` with desired seeds.

## Early-Stopping Behavior
- `sacs_geo_jk`, `sacs_section_jk`: `early_stopping: False` in config; will run to `optimization.eval_budget` unless externally interrupted.
- `sacs_section_pf`, `sacs_geo_pf`: default early stopping is enabled in `MOO` (stops if `avg_top100` improves < 1e-4 for 6 consecutive logs and old score > 0.05). To force full budget, add `early_stopping: False` to their configs before running.
- Baseline scripts honor `baseline_early_stopping` in configs (e.g., jk configs set it to `False`).
