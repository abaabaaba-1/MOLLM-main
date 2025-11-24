# problem/sacs_section_pf/evaluator.py (Platform Section Optimization Version)
import numpy as np
import json
import logging
import random
import copy
import re
from pathlib import Path

from .sacs_file_modifier import SacsFileModifier
from .sacs_runner import SacsRunner
from .sacs_interface_uc import get_sacs_uc_summary
from .sacs_interface_weight_improved import calculate_sacs_weight_from_db

# --- START: 种子定义区 (基于新架构 sacinp13 - 副本.txt) ---

# 种子 1: 均衡型基准 (基于新架构文件)
SEED_BASELINE = {
    "new_code_blocks": {
        "GRUP_DUM": "GRUP DUM         12.000 1.000 29.0011.6036.00 9    1.001.00     0.500N490.00",
        "GRUP_LG6": "GRUP LG6         36.000 0.750 29.0011.0036.00 1    1.001.00     0.500N490.003.25",
        "GRUP_LG6_2": "GRUP LG6         26.000 0.750 29.0011.6036.00 1    1.001.00     0.500N490.00",
        "GRUP_LG7": "GRUP LG7         26.000 0.750 29.0011.6036.00 1    1.001.00     0.500N490.00",
        "GRUP_SHF": "GRUP SHF          4.000 1.000 29.0011.6036.00 1    1.001.00     0.500N490.00",
        "GRUP_SK2": "GRUP SK2 W8X24                29.0011.6036.00 1    1.001.00     0.500N1.00-2",
        "GRUP_SKD": "GRUP SKD W12X30               29.0011.6036.00 1    1.001.00     0.500N1.00-2",
        "GRUP_STB": "GRUP STB          6.000 1.000 29.0011.6036.00 9    1.001.00     0.500N1.00-2",
        "GRUP_VB1": "GRUP VB1         12.750 0.625 29.0011.6036.00 1    1.001.00     0.500N490.00",
        "GRUP_VB2": "GRUP VB2          8.825 0.500 29.0011.6036.00 1    1.001.00     0.500N490.00",
        "GRUP_VBS": "GRUP VBS         12.750 0.625 29.0011.6036.00 1    1.001.00     0.500N490.00",
        "GRUP_W01": "GRUP W01 W24X162              29.0111.2035.97 1    1.001.00     0.500 490.00",
        "GRUP_W02": "GRUP W02 W24X131              29.0111.2035.97 1    1.001.00     0.500 490.00",
        "PGRUP_P01": "PGRUP P01 0.3750I29.000 0.25036.000                                     490.0000",
        "PGRUP_PLT": "PGRUP PLT 0.2500 29.000 0.25036.000                                     490.0000"
    }
}

# --- END: 种子定义区 ---

INITIAL_SEEDS = [
    SEED_BASELINE,
]
logging.info(f"成功加载并定义了 {len(INITIAL_SEEDS)} 个基准种子（基于新架构 sacinp13）。")

W_SECTIONS_LIBRARY = [
    "W24X55", "W24X62", "W24X68", "W24X76", "W24X84", "W24X94", "W24X103",
    "W24X104", "W24X117", "W24X131", "W24X146", "W24X162", "W24X176",
    "W24X192", "W24X207", "W24X229"
]

# 为不同尺寸系列建立独立库，避免跨系列混用
W8_SECTIONS_LIBRARY = [
    "W8X10", "W8X13", "W8X15", "W8X18", "W8X21", "W8X24", "W8X28",
    "W8X31", "W8X35", "W8X40", "W8X48", "W8X58", "W8X67"
]

W12_SECTIONS_LIBRARY = [
    "W12X14", "W12X16", "W12X19", "W12X22", "W12X26", "W12X30", "W12X35",
    "W12X40", "W12X45", "W12X50", "W12X53", "W12X58", "W12X65", "W12X72",
    "W12X79", "W12X87", "W12X96", "W12X106", "W12X120", "W12X136", "W12X152",
    "W12X170", "W12X190", "W12X210", "W12X230", "W12X252", "W12X279", "W12X305", "W12X336"
]

# 汇总所有 I-beam 库的字典，按系列名称索引
I_BEAM_LIBRARIES = {
    "W8": W8_SECTIONS_LIBRARY,
    "W12": W12_SECTIONS_LIBRARY,
    "W24": W_SECTIONS_LIBRARY
}

def _parse_and_modify_line(line: str, block_name: str) -> str:
    try:
        keyword = block_name.split()[0]
        original_line_stripped = line.rstrip()

        if keyword == "GRUP" and re.search(r'(W\d+X\d+)', line):
            match = re.search(r'(W\d+X\d+)', line)
            current_section = match.group(1)
            
            # 自动识别系列（W8, W12, W24 等）
            series_match = re.match(r'(W\d+)X', current_section)
            if not series_match:
                logging.warning(f"Cannot parse series from '{current_section}'. Skipping.")
                return original_line_stripped
            
            series_name = series_match.group(1)
            section_library = I_BEAM_LIBRARIES.get(series_name)
            
            if not section_library:
                logging.warning(f"No library found for series '{series_name}'. Skipping.")
                return original_line_stripped
            
            try:
                current_index = section_library.index(current_section)
            except ValueError:
                logging.warning(f"Section '{current_section}' not in {series_name} library. Skipping.")
                return original_line_stripped

            step = random.randint(1, 3) * random.choice([-1, 1])
            new_index = np.clip(current_index + step, 0, len(section_library) - 1)
            new_section = section_library[new_index]
            
            return original_line_stripped.replace(current_section, new_section, 1)

        elif keyword == "GRUP":
            if 'CONE' in line: return original_line_stripped

            try:
                od_val, wt_val = float(line[18:24]), float(line[25:30])
            except (ValueError, IndexError):
                logging.warning(f"Could not parse OD/WT for GRUP '{block_name}': '{line.strip()}'. Skipping.")
                return original_line_stripped

            # 保存原始值作为下界参考，允许向下探索更轻的截面
            original_od, original_wt = od_val, wt_val
            
            if random.choice([True, False]):
                od_val *= random.uniform(0.9, 1.1)
            else:
                wt_val *= random.uniform(0.9, 1.1)

            # 使用更宽松的边界：允许缩小到原值的 50%，扩大到 2 倍（或 99.999 上限）
            od_val = np.clip(od_val, max(2.0, original_od * 0.5), min(99.999, original_od * 2.0))
            wt_val = np.clip(wt_val, max(0.25, original_wt * 0.5), min(9.999, original_wt * 2.0))
            
            new_od_str = f"{od_val:6.3f}"
            new_wt_str = f"{wt_val:5.3f}"
            
            new_line = line[:18] + new_od_str + " " + new_wt_str + line[30:]
            return new_line.rstrip()

        elif keyword == "PGRUP":
            thick_match = re.search(r"(\d+\.\d+)", line[10:])
            if not thick_match:
                logging.warning(f"Cannot parse PGRUP thickness: {line.strip()}")
                return original_line_stripped

            thick_str = thick_match.group(1)
            thick_val = float(thick_str) * random.uniform(0.8, 1.2)
            thick_val = np.clip(thick_val, 0.250, 2.000)
            
            num_decimals = len(thick_str.split('.')[1])
            new_thick_str = f"{thick_val:.{num_decimals}f}"
            new_line = line.replace(thick_str, new_thick_str, 1)
            return new_line.rstrip()

    except Exception as e:
        logging.error(f"Error in _parse_and_modify_line for '{block_name}': {e}", exc_info=True)
        return line.rstrip()
        
    return line.rstrip()


def _get_coords_from_modified_line(modified_line: str) -> dict:
    """Extracts XYZ coordinates from a JOINT* line; used when enforcing couplings."""
    try:
        num_pattern = re.compile(r'-?\d+\.\d*(?:[eE][-+]?\d+)?')
        all_numbers = [float(n) for n in num_pattern.findall(modified_line)]
        if len(all_numbers) < 3:
            return None
        return {'x': all_numbers[0], 'y': all_numbers[1], 'z': all_numbers[2]}
    except Exception:
        return None


def _build_slave_joint_line(original_slave_line: str, master_coords: dict) -> str:
    """Rebuilds a slave joint line so it matches master coordinates while preserving formatting."""
    try:
        num_pattern = re.compile(r'-?\d+\.\d*(?:[eE][-+]?\d+)?')
        matches = list(num_pattern.finditer(original_slave_line))
        if len(matches) < 3:
            return original_slave_line.rstrip()

        replacements = [
            {'match': matches[0], 'value': master_coords['x']},
            {'match': matches[1], 'value': master_coords['y']},
            {'match': matches[2], 'value': master_coords['z']},
        ]

        line_editor = list(original_slave_line)
        for rep in reversed(replacements):
            match = rep['match']
            value = rep['value']
            original_text = match.group(0)
            original_len = len(original_text)
            precision = len(original_text.split('.')[1]) if '.' in original_text else 0
            format_spec = f">{original_len}.{precision}f"
            new_text = format(value, format_spec)
            if len(new_text) > original_len:
                new_text = new_text[:original_len]
            start, end = match.span()
            line_editor[start:end] = list(new_text)

        return "".join(line_editor).rstrip()
    except Exception:
        return original_slave_line.rstrip()

def generate_initial_population(config, seed):
    np.random.seed(seed)
    random.seed(seed)
    population_size = config.get('optimization.pop_size')
    optimizable_blocks = config.get('sacs.optimizable_blocks')
    initial_population_jsons = []
    seen_candidates = set()
    max_tries = population_size * 10

    logging.info(f"正在生成大小为 {population_size} 的初始种群...")
    
    for seed_candidate in INITIAL_SEEDS:
        candidate_str = json.dumps(seed_candidate, sort_keys=True)
        if candidate_str not in seen_candidates:
            initial_population_jsons.append(candidate_str)
            seen_candidates.add(candidate_str)
    
    try_count = 0
    while len(initial_population_jsons) < population_size and try_count < max_tries:
        base_candidate = copy.deepcopy(random.choice(INITIAL_SEEDS))
        num_modifications = random.randint(1, max(1, len(optimizable_blocks) // 2))
        blocks_to_modify_names = random.sample(optimizable_blocks, min(num_modifications, len(optimizable_blocks)))

        for block_name in blocks_to_modify_names:
            block_key = block_name.replace(" ", "_")
            if block_key in base_candidate["new_code_blocks"]:
                original_sacs_line = base_candidate["new_code_blocks"][block_key]
                modified_sacs_line = _parse_and_modify_line(original_sacs_line, block_name)
                base_candidate["new_code_blocks"][block_key] = modified_sacs_line
        
        candidate_str = json.dumps(base_candidate, sort_keys=True)
        if candidate_str not in seen_candidates:
            initial_population_jsons.append(candidate_str)
            seen_candidates.add(candidate_str)
        try_count += 1

    if len(initial_population_jsons) < population_size:
        logging.warning(f"仅生成了 {len(initial_population_jsons)}/{population_size} 个初始候选体。")

    logging.info(f"成功生成 {len(initial_population_jsons)} 个初始候选体。")
    return initial_population_jsons


class RewardingSystem:
    def __init__(self, config):
        self.config = config
        self.sacs_project_path = config.get('sacs.project_path')
        self.logger = logging.getLogger(self.__class__.__name__)
        self.modifier = SacsFileModifier(self.sacs_project_path)
        self.runner = SacsRunner(project_path=self.sacs_project_path, sacs_install_path=config.get('sacs.install_path'))
        self.objs = config.get('goals', [])
        self.obj_directions = {obj: config.get('optimization_direction')[i] for i, obj in enumerate(self.objs)}
        self.coupled_joints = config.get('sacs.coupled_joints', {}) or {}
        
        # 动态归一化参数（与 sacs_section_jk 一致）
        self.baseline_weight_tonnes = None
        self.weight_ratio_bounds = config.get('sacs.weight_ratio_bounds', [0.5, 2.0])
        if not (isinstance(self.weight_ratio_bounds, (list, tuple)) and len(self.weight_ratio_bounds) == 2):
            self.weight_ratio_bounds = [0.5, 2.0]
        self.weight_bounds = config.get('sacs.weight_bounds', [50.0, 5000.0])
        if not (isinstance(self.weight_bounds, (list, tuple)) and len(self.weight_bounds) == 2):
            self.weight_bounds = [50.0, 5000.0]
        
        try:
            base_weight_res = calculate_sacs_weight_from_db(self.sacs_project_path)
            if base_weight_res.get('status') == 'success':
                self.baseline_weight_tonnes = max(1e-6, float(base_weight_res['total_weight_tonnes']))
                self.logger.info(f"Baseline weight for normalization: {self.baseline_weight_tonnes:.3f} tonnes")
        except Exception as exc:
            self.logger.warning(f"Failed to read baseline weight for normalization: {exc}")

    def evaluate(self, items):
        invalid_num = 0
        for item in items:
            wrote_candidate = False
            try:
                try:
                    self.modifier.restore_baseline()
                except Exception as baseline_err:
                    self.logger.error(f"Failed to restore baseline before evaluation: {baseline_err}")
                    self._assign_penalty(item, "Baseline_Restore_Fail")
                    invalid_num += 1
                    continue

                raw_value = item.value
                try:
                    if 'candidate' in raw_value:
                        raw_value = raw_value.split('<candidate>', 1)[1].rsplit('</candidate>', 1)[0].strip()
                    modifications = json.loads(raw_value)
                    new_code_blocks = modifications.get("new_code_blocks")
                except (json.JSONDecodeError, IndexError, AttributeError) as e:
                    self.logger.warning(f"Failed to parse candidate JSON: {raw_value}. Error: {e}")
                    self._assign_penalty(item, "Invalid JSON format from LLM")
                    invalid_num += 1
                    continue

                if not new_code_blocks or not isinstance(new_code_blocks, dict):
                    self._assign_penalty(item, "Invalid candidate structure (no new_code_blocks)")
                    invalid_num += 1
                    continue
                
                # 对于截面优化，只允许修改 GRUP 和 PGRUP，不允许修改 JOINT（几何优化）
                filtered_blocks = {}
                for key, value in new_code_blocks.items():
                    # 只允许 GRUP_* 和 PGRUP_* 开头的块
                    if key.startswith('GRUP_') or key.startswith('PGRUP_'):
                        filtered_blocks[key] = value
                    else:
                        self.logger.warning(f"过滤掉非截面优化块: {key} (截面优化只允许 GRUP/PGRUP)")
                
                if not filtered_blocks:
                    self._assign_penalty(item, "No valid section blocks (GRUP/PGRUP) found in candidate")
                    invalid_num += 1
                    continue

                # 截面优化不涉及 coupled joints，无需调用约束同步
                if not self.modifier.replace_code_blocks(filtered_blocks):
                    self._assign_penalty(item, "SACS file modification failed")
                    invalid_num += 1
                    try:
                        self.modifier.restore_baseline()
                    except Exception as cleanup_err:
                        self.logger.error(f"Failed to restore baseline after modification failure: {cleanup_err}")
                    continue

                wrote_candidate = True
                analysis_result = self.runner.run_analysis(timeout=300)
                
                if not analysis_result.get('success'):
                    error_msg = analysis_result.get('error', 'Unknown SACS execution error')
                    self.logger.warning(f"SACS analysis failed for a candidate. Reason: {error_msg}")
                    self._assign_penalty(item, f"SACS_Run_Fail: {str(error_msg)[:100]}")
                    invalid_num += 1
                    continue
                
                weight_res = calculate_sacs_weight_from_db(self.sacs_project_path)
                uc_res = get_sacs_uc_summary(self.sacs_project_path)

                if not (weight_res.get('status') == 'success' and uc_res.get('status') == 'success'):
                    self.logger.warning("Metric extraction failed after successful SACS run.")
                    error_msg = f"W:{weight_res.get('error', 'OK')}|UC:{uc_res.get('message', 'OK')}"
                    self._assign_penalty(item, f"Metric_Extraction_Fail: {error_msg}")
                    invalid_num += 1
                    continue

                max_uc_overall = uc_res.get('max_uc', 999.0)
                is_feasible = max_uc_overall <= 1.0
                
                raw_results = {
                    'weight': weight_res['total_weight_tonnes'],
                    'axial_uc_max': uc_res.get('axial_uc_max', 999.0),
                    'bending_uc_max': uc_res.get('bending_uc_max', 999.0)
                }

                penalized_results = self._apply_penalty(raw_results, max_uc_overall)
                transformed = self._transform_objectives(penalized_results)
                overall_score = 1.0 - np.mean(list(transformed.values()))

                results_dict = {
                    'original_results': raw_results,
                    'transformed_results': transformed,
                    'overall_score': overall_score,
                    'constraint_results': {'is_feasible': 1.0 if is_feasible else 0.0, 'max_uc': max_uc_overall}
                }
                item.assign_results(results_dict)

            except Exception as e:
                self.logger.critical(f"Unhandled exception during item evaluation: {e}", exc_info=True)
                self._assign_penalty(item, f"Critical_Eval_Error: {e}")
                invalid_num += 1
            finally:
                if wrote_candidate:
                    try:
                        self.modifier.restore_baseline()
                    except Exception as cleanup_err:
                        self.logger.error(f"Failed to restore baseline after evaluation: {cleanup_err}")

        return items, { "invalid_num": invalid_num, "repeated_num": 0 }

    def _apply_penalty(self, results: dict, max_uc: float) -> dict:
        penalized_results = results.copy()
        if max_uc > 1.0:
            penalty_factor = 1.0 + (max_uc - 1.0) * 5.0
            self.logger.warning(f"Infeasible design: max_uc={max_uc:.3f}. Applying penalty factor {penalty_factor:.2f}.")
            if self.obj_directions['weight'] == 'min':
                penalized_results['weight'] *= penalty_factor
        return penalized_results

    def _assign_penalty(self, item, reason=""):
        penalty_score = 99999
        original = {obj: penalty_score if self.obj_directions[obj] == 'min' else -penalty_score for obj in self.objs}
        results = {
            'original_results': original,
            'transformed_results': {obj: 1.0 for obj in self.objs},
            'overall_score': -1.0,
            'constraint_results': {'is_feasible': 0.0, 'max_uc': 999.0},
            'error_reason': reason
        }
        item.assign_results(results)

    def _transform_objectives(self, penalized_results: dict) -> dict:
        """
        Transforms raw, penalized objective values into normalized scores for the optimizer.
        The optimizer's goal is to MINIMIZE the mean of these transformed scores.
        Therefore, a better raw value (e.g., lower weight) must correspond to a lower transformed score.
        """
        transformed = {}
        
        # --- 1. Weight Transformation (dynamic when baseline available) ---
        if self.baseline_weight_tonnes:
            min_ratio, max_ratio = self.weight_ratio_bounds
            weight = penalized_results.get('weight', self.baseline_weight_tonnes)
            ratio = weight / self.baseline_weight_tonnes
            ratio = np.clip(ratio, min_ratio, max_ratio)
            denom = max(max_ratio - min_ratio, 1e-8)
            weight_norm = (ratio - min_ratio) / denom
        else:
            w_min, w_max = self.weight_bounds
            w_min, w_max = float(w_min), float(w_max)
            if w_min >= w_max:
                w_min, w_max = 50.0, 5000.0
            weight = np.clip(penalized_results.get('weight', w_max), w_min, w_max)
            weight_norm = (weight - w_min) / (w_max - w_min)
        
        if self.obj_directions.get('weight') == 'min':
            transformed['weight'] = weight_norm
        else:
            transformed['weight'] = 1.0 - weight_norm

        # --- 2. Stress (UC) Transformations (Normalized to [0, 1] for fair comparison) ---
        # Normalize UC values to [0, 1] to match geometric optimization and enable fair hypervolume comparison
        
        uc_min, uc_max = 0.0, 1.0
        axial_uc = np.clip(penalized_results.get('axial_uc_max', uc_max), uc_min, uc_max)
        if self.obj_directions.get('axial_uc_max') == 'min':
            transformed['axial_uc_max'] = (axial_uc - uc_min) / (uc_max - uc_min)
        else:
            transformed['axial_uc_max'] = (uc_max - axial_uc) / (uc_max - uc_min)

        bending_uc = np.clip(penalized_results.get('bending_uc_max', uc_max), uc_min, uc_max)
        if self.obj_directions.get('bending_uc_max') == 'min':
            transformed['bending_uc_max'] = (bending_uc - uc_min) / (uc_max - uc_min)
        else:
            transformed['bending_uc_max'] = (uc_max - bending_uc) / (uc_max - uc_min)
        
        # Ensure all transformed values are in [0, 1]
        for key, val in transformed.items():
            transformed[key] = np.clip(val, 0.0, 1.0)
            
        return transformed
