# Run Commands and Early-Stopping Notes

## Primary Runs (LLM-driven MOO) — only missing seeds
- `python3 main.py problem/sacs_geo_jk/config.yaml --seed 42`   # 重跑并跑满预算
- `python3 main.py problem/sacs_geo_jk/config.yaml --seed 60`
- `python3 main.py problem/sacs_geo_jk/config.yaml --seed 62`
- `python3 main.py problem/sacs_geo_jk/config.yaml --seed 101`
- `python3 main.py problem/sacs_geo_pf/config.yaml --seed 90`
- `python3 main.py problem/sacs_geo_pf/config.yaml --seed 101`
- `python3 main.py problem/sacs_section_pf/config.yaml --seed 90`  # mollm 补 seed 90

## Baseline Comparisons (only missing seeds)
- GA: `python3 baseline_ga.py --config problem/sacs_geo_pf/config.yaml --seed 90`
- GA: `python3 baseline_ga.py --config problem/sacs_geo_pf/config.yaml --seed 101`
- GA: `python3 baseline_ga.py --config problem/sacs_section_pf/config.yaml --seed 80`
- GA: `python3 baseline_ga.py --config problem/sacs_section_pf/config.yaml --seed 101`
- NSGA2: 将上述命令中的 `baseline_ga.py` 替换为 `baseline_nsga2.py`
- SMSEMOA: 将上述命令中的 `baseline_ga.py` 替换为 `baseline_sms.py`

## Notes
- `sacs_geo_jk`, `sacs_section_jk`: `early_stopping: False`，应跑满预算。
- `sacs_section_pf`, `sacs_geo_pf`: 请在 config 中设 `early_stopping: False` 确保跑满 2000 预算。
- Baseline 早停取决于 config 的 `baseline_early_stopping`；如需全程，设为 `False`。
