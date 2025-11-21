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

def _parse_and_modify_line(line: str, block_name: str) -> str:
    try:
        keyword = block_name.split()[0]
        original_line_stripped = line.rstrip()

        if keyword == "GRUP" and re.search(r'(W\d+X\d+)', line):
            match = re.search(r'(W\d+X\d+)', line)
            current_section = match.group(1)
            try:
                current_index = W_SECTIONS_LIBRARY.index(current_section)
            except ValueError:
                logging.warning(f"Section '{current_section}' for GRUP '{block_name}' not in library. Skipping.")
                return original_line_stripped

            step = random.randint(1, 3) * random.choice([-1, 1])
            new_index = np.clip(current_index + step, 0, len(W_SECTIONS_LIBRARY) - 1)
            new_section = W_SECTIONS_LIBRARY[new_index]
            
            return original_line_stripped.replace(current_section, new_section, 1)

        elif keyword == "GRUP":
            if 'CONE' in line: return original_line_stripped

            try:
                od_val, wt_val = float(line[18:24]), float(line[25:30])
            except (ValueError, IndexError):
                logging.warning(f"Could not parse OD/WT for GRUP '{block_name}': '{line.strip()}'. Skipping.")
                return original_line_stripped

            if random.choice([True, False]):
                od_val *= random.uniform(0.9, 1.1)
            else:
                wt_val *= random.uniform(0.9, 1.1)

            od_val = np.clip(od_val, 10.0, 99.999)
            wt_val = np.clip(wt_val, 0.5, 9.999)
            
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
        num_modifications = random.randint(1, len(optimizable_blocks) // 2)
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

                filtered_blocks = self._apply_coupled_joint_constraints(filtered_blocks)

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
        
        # --- 1. Weight Transformation (Correct) ---
        w_min, w_max = 50, 5000   
        w = np.clip(penalized_results.get('weight', w_max), w_min, w_max)
        if self.obj_directions.get('weight') == 'min':
            # This correctly maps low weight to a low score [0, 1]
            transformed['weight'] = (w - w_min) / (w_max - w_min)
        else:
            # This correctly maps high weight to a low score [0, 1]
            transformed['weight'] = (w_max - w) / (w_max - w_min)

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

    def _apply_coupled_joint_constraints(self, candidate_blocks: dict) -> dict:
        """
        Section problems seldom edit joints, but if coupled joint definitions exist we keep
        master/slave nodes synchronized so future JSON payloads cannot desync them.
        """
        if not candidate_blocks or not self.coupled_joints:
            return candidate_blocks

        enforced_blocks = dict(candidate_blocks)
        required_joint_keys = {
            f"JOINT_{joint_id}"
            for ids in self.coupled_joints.items()
            for joint_id in ids
        }
        missing_keys = [k for k in required_joint_keys if k not in enforced_blocks]
        baseline_lines = self._load_joint_lines_from_file(missing_keys)

        for master_id, slave_id in self.coupled_joints.items():
            master_key = f"JOINT_{master_id}"
            slave_key = f"JOINT_{slave_id}"

            master_line = enforced_blocks.get(master_key) or baseline_lines.get(master_key)
            slave_line = enforced_blocks.get(slave_key) or baseline_lines.get(slave_key)

            if not master_line:
                continue

            master_coords = _get_coords_from_modified_line(master_line)
            if not master_coords:
                continue

            base_slave_line = slave_line or master_line
            enforced_blocks[slave_key] = _build_slave_joint_line(base_slave_line, master_coords)

        return enforced_blocks

    def _load_joint_lines_from_file(self, joint_keys) -> dict:
        if not joint_keys:
            return {}

        input_path = getattr(self.modifier, "input_file", Path(self.sacs_project_path) / "sacinp.demo13")
        try:
            with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
        except FileNotFoundError:
            return {}

        joint_line_map = {}
        for joint_key in joint_keys:
            parts = joint_key.split('_')
            if len(parts) != 2:
                continue
            joint_id = parts[1]
            pattern = re.compile(r"^\s*JOINT\s+" + re.escape(joint_id))
            for line in all_lines:
                if pattern.search(line):
                    joint_line_map[joint_key] = line.rstrip('\n')
                    break
        return joint_line_map
