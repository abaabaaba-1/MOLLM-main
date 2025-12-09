# evaluator.py (Definitive Fix - Employs a robust, context-aware line modification strategy)
import numpy as np
import json
import logging
import random
import copy
import re
from pathlib import Path

# --- 【已修正】使用相对路径导入，以匹配您的项目结构 ---
from .sacs_file_modifier import SacsFileModifier
from .sacs_runner import SacsRunner
from .sacs_interface_uc import get_sacs_uc_summary
from .sacs_interface_weight_improved import calculate_sacs_weight_from_db
# --- 修正结束 ---

# REWRITTEN: _parse_and_modify_line - The core of the new robust solution.
# This function no longer uses separate get/build helpers. It performs a minimal, in-place modification.
def _parse_and_modify_line(original_line: str, block_name: str, config=None) -> str:
    """
    Parses and modifies a JOINT line using a robust, surgical replacement strategy
    that preserves the original file's exact formatting, including spacing and precision.
    """
    try:
        keyword = block_name.split()[0]
        if keyword != "JOINT":
            return original_line.rstrip()

        # 1. Find all numbers and their precise start/end positions in the string.
        # This pattern finds numbers with or without decimals, handling scientific notation.
        num_pattern = re.compile(r'-?\d+\.\d*(?:[eE][-+]?\d+)?')
        matches = list(num_pattern.finditer(original_line))

        if len(matches) < 3:
            logging.warning(f"Could not find at least 3 coordinates in JOINT line: {original_line.rstrip()}")
            return original_line.rstrip()

        # 2. Get random mutation parameters
        amplitude_range = 2.0
        if config:
            amplitudes = config.get('optimization.mutation_strategy.joint_mutation_amplitudes', {})
            if amplitudes:
                chosen_amplitude_key = random.choice(list(amplitudes.keys()))
                amplitude_range = amplitudes.get(chosen_amplitude_key, 2.0)
        
        max_steps = int(amplitude_range / 0.01)
        num_steps = random.randint(-max_steps, max_steps) if max_steps > 0 else 0
        if num_steps == 0: num_steps = 1 # Ensure some change
        change = num_steps * 0.01

        # 3. Select which coordinate (X, Y, or Z) to modify
        coord_indices = {'x': 0, 'y': 1, 'z': 2}
        coord_to_change_name = random.choice(['x', 'y', 'z'])
        target_match_index = coord_indices[coord_to_change_name]
        target_match = matches[target_match_index]

        # 4. Perform the mutation
        original_value = float(target_match.group(0))
        new_value = original_value + change

        # 5. Dynamically format the new value to perfectly match the old value's format
        original_text = target_match.group(0)
        original_len = len(original_text)
        
        # Determine original precision
        if '.' in original_text:
            precision = len(original_text.split('.')[1])
        else:
            precision = 0
        
        # Create a dynamic format specifier: e.g., ">10.2f" for right-align, 10 chars, 2 decimals
        format_spec = f">{original_len}.{precision}f"
        new_text = format(new_value, format_spec)

        # Prevent overflow from breaking the format. Truncate if necessary.
        if len(new_text) > original_len:
            new_text = new_text[:original_len]

        # 6. Surgically replace the old number text with the new formatted text
        start, end = target_match.span()
        new_line = original_line[:start] + new_text + original_line[end:]
        
        return new_line.rstrip()

    except Exception as e:
        logging.error(f"CRITICAL error in _parse_and_modify_line for '{block_name}': {e}", exc_info=True)
        return original_line.rstrip()

# ADDED: A new, simple coordinate getter needed for coupled joints.
def _get_coords_from_modified_line(modified_line: str) -> dict:
    """A simple parser to get the first three float values from a line."""
    try:
        num_pattern = re.compile(r'-?\d+\.\d*(?:[eE][-+]?\d+)?')
        all_numbers = [float(n) for n in num_pattern.findall(modified_line)]
        if len(all_numbers) < 3: return None
        return {'x': all_numbers[0], 'y': all_numbers[1], 'z': all_numbers[2]}
    except Exception:
        return None

# ADDED: A new, robust builder for coupled (slave) joints.
def _build_slave_joint_line(original_slave_line: str, master_coords: dict) -> str:
    """
    Rebuilds a slave joint line using the coordinates from its master.
    It uses the same robust, format-preserving logic as _parse_and_modify_line.
    """
    try:
        num_pattern = re.compile(r'-?\d+\.\d*(?:[eE][-+]?\d+)?')
        matches = list(num_pattern.finditer(original_slave_line))
        if len(matches) < 3: return original_slave_line.rstrip()

        x_match, y_match, z_match = matches[0], matches[1], matches[2]
        
        # This list makes it easy to iterate and replace
        replacements = [
            {'match': x_match, 'value': master_coords['x']},
            {'match': y_match, 'value': master_coords['y']},
            {'match': z_match, 'value': master_coords['z']}
        ]
        
        # Apply replacements from right to left to not mess up indices
        line_editor = list(original_slave_line)
        for rep in reversed(replacements):
            match = rep['match']
            value = rep['value']
            
            original_text = match.group(0)
            original_len = len(original_text)
            precision = len(original_text.split('.')[1]) if '.' in original_text else 0
            
            format_spec = f">{original_len}.{precision}f"
            new_text = format(value, format_spec)
            if len(new_text) > original_len: new_text = new_text[:original_len]
            
            start, end = match.span()
            line_editor[start:end] = list(new_text)
            
        return "".join(line_editor).rstrip()

    except Exception as e:
        logging.error(f"CRITICAL error in _build_slave_joint_line: {e}", exc_info=True)
        return original_slave_line.rstrip()

def _get_initial_joint_definitions(config: dict) -> dict:
    sacs_file_path = config.get('sacs.project_path')
    if not sacs_file_path:
        logging.error("Config missing 'sacs.project_path'.")
        return {}

    # 自动检测文件格式：优先查找 demo13，然后是 demo06
    project_path = Path(sacs_file_path)
    if (project_path / "sacinp.demo13").exists():
        sacs_file = project_path / "sacinp.demo13"
    elif (project_path / "sacinp.demo06").exists():
        sacs_file = project_path / "sacinp.demo06"
    else:
        sacs_file = project_path / "sacinp.demo13"  # 默认使用 demo13
        logging.warning(f"未找到 sacinp.demo13 或 sacinp.demo06，使用默认: {sacs_file}")

    optimizable_joints_list = config.get('sacs.optimizable_joints', [])
    coupled_joints_map = config.get('sacs.coupled_joints', {})
    slave_joints_list = [f"JOINT {v}" for v in coupled_joints_map.values()]
    joint_lines, all_target_joints = {}, set(optimizable_joints_list + slave_joints_list)

    try:
        with open(sacs_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        for joint_prefix in all_target_joints:
            parts = joint_prefix.split()
            if len(parts) != 2: continue
            keyword, id_val = parts
            pattern = re.compile(r"^\s*" + re.escape(keyword) + r"\s+" + re.escape(id_val))
            for line in lines:
                if pattern.search(line):
                    key = joint_prefix.replace(" ", "_")
                    joint_lines[key] = line.rstrip('\n')
                    break
    except FileNotFoundError:
        logging.error(f"SACS input file not found at {sacs_file} for seed generation.")

    return joint_lines


# 基线种子（空字典，节点定义将从 SACS 文件中自动读取）
SEED_BASELINE = {
    "new_code_blocks": {}
}

def generate_initial_population(config, seed):
    np.random.seed(seed); random.seed(seed)
    population_size = config.get('optimization.pop_size')
    optimizable_joints = config.get('sacs.optimizable_joints', [])
    coupled_joints_map = config.get('sacs.coupled_joints', {})
    initial_joint_lines = _get_initial_joint_definitions(config)

    if not initial_joint_lines:
        logging.critical("FATAL: Could not load any JOINT definitions from the SACS input file.");
        return [json.dumps(SEED_BASELINE, sort_keys=True)]

    logging.info(f"Successfully loaded {len(initial_joint_lines)} initial JOINT definitions from SACS file.")
    master_seed = copy.deepcopy(SEED_BASELINE)
    master_seed["new_code_blocks"].update(initial_joint_lines)
    initial_population_jsons, seen_candidates = [], set()
    master_seed_str = json.dumps(master_seed, sort_keys=True)
    initial_population_jsons.append(master_seed_str)
    seen_candidates.add(master_seed_str)
    logging.info(f"Starting generation of initial population of size {population_size}...")
    max_tries, try_count = population_size * 10, 0

    while len(initial_population_jsons) < population_size and try_count < max_tries:
        base_candidate = copy.deepcopy(master_seed)
        if not optimizable_joints:
            logging.error("No optimizable joints defined in config; cannot generate new candidates.")
            break

        num_modifications = random.randint(1, max(1, len(optimizable_joints) // 2))
        items_to_modify = random.sample(optimizable_joints, min(num_modifications, len(optimizable_joints)))

        for item_name in items_to_modify:
            item_key = item_name.replace(" ", "_")
            original_sacs_line = base_candidate["new_code_blocks"][item_key]
            # Use the new robust modification function
            modified_sacs_line = _parse_and_modify_line(original_sacs_line, item_name, config=config)
            base_candidate["new_code_blocks"][item_key] = modified_sacs_line

            if item_name.startswith("JOINT"):
                joint_id = item_name.split(" ")[1]
                if joint_id in coupled_joints_map:
                    slave_id = coupled_joints_map[joint_id]
                    slave_key = f"JOINT_{slave_id}"
                    # Get the new master coordinates and update the slave
                    master_coords = _get_coords_from_modified_line(modified_sacs_line)
                    if master_coords and slave_key in base_candidate["new_code_blocks"]:
                        original_slave_line = base_candidate["new_code_blocks"][slave_key]
                        # Use the new robust slave line builder
                        new_slave_line = _build_slave_joint_line(original_slave_line, master_coords)
                        base_candidate["new_code_blocks"][slave_key] = new_slave_line

        candidate_str = json.dumps(base_candidate, sort_keys=True)
        if candidate_str not in seen_candidates:
            initial_population_jsons.append(candidate_str)
            seen_candidates.add(candidate_str)
        try_count += 1

    if len(initial_population_jsons) < population_size:
        logging.warning(f"Only generated {len(initial_population_jsons)}/{population_size} initial candidates.")

    logging.info(f"Successfully generated {len(initial_population_jsons)} initial candidates.")
    return initial_population_jsons


class RewardingSystem:
    def __init__(self, config):
        self.config = config
        self.sacs_project_path = config.get('sacs.project_path')
        self.logger = logging.getLogger(self.__class__.__name__)
        self.modifier = SacsFileModifier(self.sacs_project_path)
        self.runner = SacsRunner(
            project_path=self.sacs_project_path,
            sacs_install_path=config.get('sacs.install_path')
        )
        self.objs = config.get('goals', [])
        self.obj_directions = {
            obj: config.get('optimization_direction')[i]
            for i, obj in enumerate(self.objs)
        }
        self.coupled_joints = config.get('sacs.coupled_joints', {}) or {}

        # Weight normalization configuration
        self.baseline_weight_tonnes = config.get('sacs.baseline_weight_tonnes')
        self.weight_ratio_bounds = config.get('sacs.weight_ratio_bounds', [0.5, 2.0])
        if not (isinstance(self.weight_ratio_bounds, (list, tuple)) and len(self.weight_ratio_bounds) == 2):
            self.weight_ratio_bounds = [0.5, 2.0]
        self.weight_bounds = config.get('sacs.weight_bounds', [50.0, 5000.0])
        if not (isinstance(self.weight_bounds, (list, tuple)) and len(self.weight_bounds) == 2):
            self.weight_bounds = [50.0, 5000.0]

        # Prefer config-provided baseline if available; otherwise, read once from SACS DB
        if self.baseline_weight_tonnes is None:
            try:
                base_weight_res = calculate_sacs_weight_from_db(self.sacs_project_path)
                if base_weight_res.get('status') == 'success':
                    self.baseline_weight_tonnes = max(
                        1e-6, float(base_weight_res['total_weight_tonnes'])
                    )
                    self.logger.info(
                        f"Baseline weight for normalization: {self.baseline_weight_tonnes:.3f} tonnes"
                    )
            except Exception as exc:
                self.logger.warning(f"Failed to read baseline weight for normalization: {exc}")

    def evaluate(self, items):
        invalid_num = 0
        if not items: return [], {"invalid_num": 0, "repeated_num": 0}

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
                    json_match = re.search(r'{\s*"new_code_blocks":\s*{.*?}\s*}', raw_value, re.DOTALL)
                    if json_match: raw_value = json_match.group(0)
                    elif 'candidate' in raw_value: raw_value = raw_value.split('<candidate>', 1)[1].rsplit('</candidate>', 1)[0].strip()
                    modifications = json.loads(raw_value)
                    new_code_blocks = modifications.get("new_code_blocks")
                except (json.JSONDecodeError, IndexError, AttributeError) as e:
                    self.logger.warning(f"Could not parse candidate JSON: {raw_value[:200]}... Error: {e}")
                    self._assign_penalty(item, "Invalid JSON format from LLM")
                    invalid_num += 1
                    continue

                if not new_code_blocks or not isinstance(new_code_blocks, dict):
                    self._assign_penalty(item, "Invalid candidate structure (no new_code_blocks)")
                    invalid_num += 1
                    continue

                # 对于几何优化，只允许修改配置中声明的 JOINT 及其耦合节点
                opt_joints = self.config.get('sacs.optimizable_joints', []) or []
                coupled_map = self.coupled_joints or {}
                allowed_keys = set()

                for j in opt_joints:
                    parts = j.split()
                    if len(parts) == 2 and parts[0] == 'JOINT':
                        joint_id = parts[1]
                        allowed_keys.add(f"JOINT_{joint_id}")
                        if joint_id in coupled_map:
                            allowed_keys.add(f"JOINT_{coupled_map[joint_id]}")

                for master_id, slave_id in coupled_map.items():
                    allowed_keys.add(f"JOINT_{master_id}")
                    allowed_keys.add(f"JOINT_{slave_id}")

                filtered_blocks = {}
                for key, value in new_code_blocks.items():
                    if not key.startswith('JOINT_'):
                        self.logger.warning(f"过滤掉非几何优化块: {key} (几何优化只允许 JOINT)")
                        continue
                    if allowed_keys and key not in allowed_keys:
                        self.logger.warning(f"过滤掉未在 optimizable_joints 白名单中的 JOINT: {key}")
                        continue
                    filtered_blocks[key] = value

                if not filtered_blocks:
                    self._assign_penalty(item, "No valid joint blocks (JOINT) found in candidate")
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
                    self.logger.warning(f"SACS analysis failed. Reason: {error_msg}")
                    self._assign_penalty(item, f"SACS_Run_Fail: {str(error_msg)[:100]}")
                    invalid_num += 1
                    continue

                weight_res = calculate_sacs_weight_from_db(self.sacs_project_path)
                uc_res = get_sacs_uc_summary(self.sacs_project_path)

                if not (weight_res.get('status') == 'success' and uc_res.get('status') == 'success'):
                    error_msg = f"W:{weight_res.get('error', 'OK')}|UC:{uc_res.get('message', 'OK')}"
                    self.logger.warning("Metric extraction failed after successful SACS run.")
                    self._assign_penalty(item, f"Metric_Extraction_Fail: {error_msg}")
                    invalid_num += 1
                    continue

                max_uc_overall = uc_res.get('max_uc', 999.0)
                is_feasible = max_uc_overall <= 1.0
                raw_results = {'weight': weight_res['total_weight_tonnes'], 'axial_uc_max': uc_res.get('axial_uc_max', 999.0), 'bending_uc_max': uc_res.get('bending_uc_max', 999.0)}
                penalized_results = self._apply_penalty(raw_results, max_uc_overall)
                transformed = self._transform_objectives(penalized_results)
                overall_score = 1.0 - np.mean(list(transformed.values()))
                results_dict = {'original_results': raw_results, 'transformed_results': transformed, 'overall_score': overall_score, 'constraint_results': {'is_feasible': 1.0 if is_feasible else 0.0, 'max_uc': max_uc_overall}}
                item.assign_results(results_dict)
            except Exception as e:
                self.logger.critical(f"Unhandled exception during evaluation: {e}", exc_info=True)
                self._assign_penalty(item, f"Critical_Eval_Error: {e}")
                invalid_num += 1
            finally:
                if wrote_candidate:
                    try:
                        self.modifier.restore_baseline()
                    except Exception as cleanup_err:
                        self.logger.error(f"Failed to restore baseline after evaluation: {cleanup_err}")
        return items, {"invalid_num": invalid_num, "repeated_num": 0}

    def _apply_penalty(self, results: dict, max_uc: float) -> dict:
        """Apply penalty to infeasible designs (UC > 1.0).
        
        Following JK model's approach: only penalize weight, not UC values.
        This avoids double-penalization and maintains physical meaning of UC.
        """
        penalized_results = results.copy()
        if max_uc > 1.0:
            penalty_factor = 1.0 + (max_uc - 1.0) * 5.0
            self.logger.warning(f"Infeasible design: max_uc={max_uc:.3f}. Applying penalty factor {penalty_factor:.2f}.")
            # Only penalize weight, following JK model's approach
            if self.obj_directions['weight'] == 'min':
                penalized_results['weight'] *= penalty_factor
        return penalized_results

    def _assign_penalty(self, item, reason=""):
        penalty_score = 99999
        original = {obj: penalty_score if self.obj_directions[obj] == 'min' else -penalty_score for obj in self.objs}
        results = {'original_results': original, 'transformed_results': {obj: 1.0 for obj in self.objs}, 'overall_score': -1.0, 'constraint_results': {'is_feasible': 0.0, 'max_uc': 999.0}, 'error_reason': reason}
        item.assign_results(results)

    def _transform_objectives(self, penalized_results: dict) -> dict:
        transformed = {}

        # --- 1. Weight Transformation (prefer ratio to a baseline weight) ---
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
                # 默认范围基于实际几何优化数据: [54.2, 55.2] tonnes
                w_min, w_max = 54.0, 56.0
            weight = np.clip(penalized_results.get('weight', w_max), w_min, w_max)
            weight_norm = (weight - w_min) / (w_max - w_min)

        if self.obj_directions.get('weight') == 'min':
            transformed['weight'] = weight_norm
        else:
            transformed['weight'] = 1.0 - weight_norm

        # --- 2. UC Transformations ---
        # Following JK model's strict constraint approach:
        # - UC range [0, 1] enforces feasibility requirement (UC ≤ 1.0)
        # - Values > 1.0 are clipped, discouraging infeasible designs
        # - Combined with weight penalty, this guides optimizer toward feasible solutions
        # This ensures all optimized designs are engineering-viable.
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

        for key, val in transformed.items():
            transformed[key] = np.clip(val, 0.0, 1.0)

        return transformed

    def _apply_coupled_joint_constraints(self, candidate_blocks: dict) -> dict:
        """
        Ensures declared coupled joints stay coincident by rebuilding slave joint lines
        using their master's coordinates.
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
                self.logger.warning(f"Missing master joint {master_key}; cannot enforce coupling.")
                if slave_line:
                    enforced_blocks[slave_key] = slave_line
                continue

            master_coords = _get_coords_from_modified_line(master_line)
            if not master_coords:
                self.logger.warning(f"Failed to parse coordinates for {master_key}; skipping coupling.")
                continue

            base_slave_line = slave_line or master_line
            new_slave_line = _build_slave_joint_line(base_slave_line, master_coords)
            enforced_blocks[slave_key] = new_slave_line

        return enforced_blocks

    def _load_joint_lines_from_file(self, joint_keys) -> dict:
        """Loads JOINT lines from the current sacinp file for keys missing in the candidate."""
        if not joint_keys:
            return {}

        input_path = getattr(self.modifier, "input_file", None)
        if input_path is None:
            # Fallback: auto-detect file format
            project_path = Path(self.sacs_project_path)
            if (project_path / "sacinp.demo13").exists():
                input_path = project_path / "sacinp.demo13"
            elif (project_path / "sacinp.demo06").exists():
                input_path = project_path / "sacinp.demo06"
            else:
                input_path = project_path / "sacinp.demo13"
        try:
            with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
        except FileNotFoundError:
            self.logger.error(f"Cannot open SACS input file {input_path}; coupled joints may desync.")
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
