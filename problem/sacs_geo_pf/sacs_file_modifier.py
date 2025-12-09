# problem/sacs/sacs_file_modifier.py (V2 - 增加对目标文件的支持)
import re
import shutil
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import logging

class SacsFileModifier:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        # 支持多种文件格式：优先查找 demo13，然后是 demo06
        if (self.project_path / "sacinp.demo13").exists():
            self.input_file = self.project_path / "sacinp.demo13"
        elif (self.project_path / "sacinp.demo06").exists():
            self.input_file = self.project_path / "sacinp.demo06"
        else:
            self.input_file = self.project_path / "sacinp.demo13"  # 默认使用 demo13
        self.backup_dir = self.project_path / "backups"
        self.logger = logging.getLogger(self.__class__.__name__)
        # 确保项目目录存在，然后创建备份目录
        self.project_path.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        if not self.input_file.exists():
            raise FileNotFoundError(f"SACS input file not found: {self.input_file}")
        self.master_backup_path = self._ensure_master_backup()

    def _ensure_master_backup(self) -> Optional[Path]:
        """确保存在一个稳定的基线备份，用于在每个候选评估前恢复。"""
        suffix = self.input_file.suffix
        baseline_name = f"sacinp_master_baseline{suffix}"
        baseline_path = self.backup_dir / baseline_name
        if not baseline_path.exists():
            shutil.copy2(self.input_file, baseline_path)
            self.logger.info(f"Created master baseline backup: {baseline_name}")
        return baseline_path

    def _create_backup(self) -> Optional[Path]:
        """Creates a backup of the current input file."""
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            # 根据输入文件扩展名确定备份文件扩展名
            file_ext = self.input_file.suffix
            backup_path = self.backup_dir / f"sacinp_pre_eval_{ts}{file_ext}"
            shutil.copy2(self.input_file, backup_path)
            self.logger.info(f"Created backup: {backup_path.name}")
            return backup_path
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None

    def _restore_from_backup(self, backup_path: Path):
        """Restores the input file from a backup."""
        try:
            shutil.copy2(backup_path, self.input_file)
            self.logger.warning(f"Restored file from backup: {backup_path.name}")
        except Exception as e:
            self.logger.error(f"Failed to restore from backup {backup_path.name}: {e}")

    def restore_baseline(self):
        """Restores the SACS input file back to the master baseline snapshot."""
        if not self.master_backup_path or not self.master_backup_path.exists():
            raise FileNotFoundError("Master baseline backup is missing; cannot restore.")
        shutil.copy2(self.master_backup_path, self.input_file)
        self.logger.debug("Restored SACS input file from master baseline.")

    def extract_code_blocks(self, block_prefixes: List[str]) -> Dict[str, str]:
        code_blocks = {}
        try:
            with open(self.input_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            for prefix in block_prefixes:
                found = False
                for line in lines:
                    if line.strip().startswith(prefix):
                        key = prefix.replace(" ", "_")
                        code_blocks[key] = line.rstrip('\n')
                        found = True
                        break
                if not found:
                    self.logger.warning(f"Could not find a unique code block for prefix: '{prefix}'")
        except Exception as e:
            self.logger.error(f"Error extracting code blocks: {e}")
        return code_blocks

    def replace_code_blocks(self, new_code_blocks: Dict[str, str], target_file: Optional[Path] = None) -> bool:
        """
        Replaces entire lines in a SACS file with new code blocks.
        
        Args:
            new_code_blocks: A dictionary of code blocks to replace.
            target_file (Optional): If provided, modifications are written to this file.
                                    If None, the default input file is modified in place.
        """
        file_to_modify = target_file if target_file is not None else self.input_file
        is_in_place_modification = (target_file is None)

        if not file_to_modify.exists():
            self.logger.error(f"Target file for modification does not exist: {file_to_modify}")
            return False

        backup_path = None
        if is_in_place_modification:
            backup_path = self._create_backup()
            if not backup_path:
                return False

        try:
            with open(file_to_modify, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            lines_replaced = 0
            for identifier, new_line in new_code_blocks.items():
                parts = identifier.split('_')
                if len(parts) < 2:
                    self.logger.warning(f"Invalid identifier format '{identifier}'. Expected format: 'GRUP_ID' or 'PGRUP_ID'. Skipping.")
                    continue
                
                # 对于多部分标识符（如 GRUP_LG6_2），合并后面的部分
                keyword = parts[0]  # GRUP 或 PGRUP
                id_val = '_'.join(parts[1:])  # 处理 ID 中可能包含下划线的情况
                
                # 如果 id_val 包含数字后缀（如 "LG6_2"），需要特殊处理匹配
                # 对于 "GRUP_LG6_2"，匹配 "GRUP LG6" 的第二个出现
                if '_' in id_val and id_val.split('_')[-1].isdigit():
                    # 分离基础ID和序号
                    base_id = '_'.join(id_val.split('_')[:-1])
                    match_index = int(id_val.split('_')[-1]) - 1  # 转换为0-based索引
                    
                    # 查找所有匹配的行
                    pattern = re.compile(r"^\s*" + re.escape(keyword) + r"\s+" + re.escape(base_id))
                    matches = []
                    for i, line in enumerate(lines):
                        if pattern.search(line) and 'CONE' not in line:  # 排除 CONE 类型
                            matches.append(i)
                    
                    # 选择指定索引的匹配行
                    if 0 <= match_index < len(matches):
                        line_idx = matches[match_index]
                        self.logger.info(f"Replacing block '{identifier}' (match #{match_index + 1}) in {file_to_modify.name}:\n  OLD: {lines[line_idx].strip()}\n  NEW: {new_line.strip()}")
                        lines[line_idx] = new_line + '\n'
                        lines_replaced += 1
                        continue
                    else:
                        self.logger.warning(f"Identifier '{identifier}' - match index {match_index} out of range (found {len(matches)} matches). Skipping.")
                        continue
                
                # 标准匹配：关键词后跟空格，然后是ID
                pattern = re.compile(r"^\s*" + re.escape(keyword) + r"\s+" + re.escape(id_val))
                
                line_found_and_replaced = False
                for i, line in enumerate(lines):
                    if pattern.search(line):
                        self.logger.info(f"Replacing block '{identifier}' in {file_to_modify.name}:\n  OLD: {line.strip()}\n  NEW: {new_line.strip()}")
                        lines[i] = new_line + '\n'
                        lines_replaced += 1
                        line_found_and_replaced = True
                        break

                if not line_found_and_replaced:
                    self.logger.warning(f"Identifier '{identifier}' from LLM not found in SACS file. Skipping.")

            with open(file_to_modify, 'w', encoding='utf-8', errors='ignore') as f:
                f.writelines(lines)

            if lines_replaced == 0:
                self.logger.warning(f"No code blocks were replaced in {file_to_modify.name}.")
                if is_in_place_modification and backup_path:
                    self._restore_from_backup(backup_path)
                return False

            self.logger.info(f"Successfully replaced {lines_replaced} code blocks in {file_to_modify.name}.")
            return True

        except Exception as e:
            self.logger.critical(f"Fatal error during code block replacement on {file_to_modify.name}: {e}")
            if is_in_place_modification and backup_path:
                self._restore_from_backup(backup_path)
            return False
