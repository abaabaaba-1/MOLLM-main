# SACS 批量实验运行器使用指南

## 概述

`run_all_baselines.py` 支持四种 SACS 优化问题的批量实验运行，自动管理种子文件重置。

## 四种优化问题

| 问题 ID | 名称 | 模型 | 种子文件 | 描述 |
|---------|------|------|----------|------|
| `section_jk` | Section Optimization (JK) | Demo06 | sacinp.demo06 | 截面优化（导管架模型） |
| `section_pf` | Section Optimization (PF) | Demo13 | sacinp.demo13 | 截面优化（平台模型） |
| `geo_jk` | Geometry Optimization (JK) | Demo06 | sacinp.demo06 | 几何优化（导管架模型） |
| `geo_pf` | Geometry Optimization (PF) | Demo13 | sacinp.demo13 | 几何优化（平台模型） |

## 基本用法

### 1. 运行单个问题的所有 baseline

```bash
# 截面优化（JK 模型）
python run_all_baselines.py --problem section_jk

# 几何优化（JK 模型）
python run_all_baselines.py --problem geo_jk

# 截面优化（PF 模型）
python run_all_baselines.py --problem section_pf

# 几何优化（PF 模型）
python run_all_baselines.py --problem geo_pf
```

### 2. 运行特定 baseline

```bash
# 只运行 GA 和 NSGA-II
python run_all_baselines.py --problem section_jk --baselines ga nsga2

# 只运行 SMS-EMOA
python run_all_baselines.py --problem geo_jk --baselines sms
```

### 3. 使用多个随机种子

```bash
# 用 5 个不同的种子运行 GA
python run_all_baselines.py --problem section_jk --baselines ga --seeds 42 43 44 45 46

# 用 3 个种子运行所有 baseline
python run_all_baselines.py --problem geo_jk --seeds 42 100 200
```

### 4. 运行所有问题（警告：运行时间很长）

```bash
# 运行所有 4 个问题 × 5 个 baseline × 1 个种子 = 20 个实验
python run_all_baselines.py --problem all

# 运行所有问题，但只用 GA
python run_all_baselines.py --problem all --baselines ga
```

### 5. 测试运行（不实际执行）

```bash
# 查看会运行哪些实验，但不实际执行
python run_all_baselines.py --problem section_jk --dry-run

# 测试所有问题的配置
python run_all_baselines.py --problem all --dry-run
```

### 6. 跳过种子文件重置

```bash
# 使用现有的 SACS 文件状态，不重置
python run_all_baselines.py --problem geo_jk --skip-reset
```

## 可用的 Baseline 算法

- `ga` - Genetic Algorithm (遗传算法)
- `nsga2` - NSGA-II (非支配排序遗传算法 II)
- `sms` - SMS-EMOA (S-Metric Selection)
- `moead` - MOEA/D (基于分解的多目标进化算法)
- `rs` - Random Search (随机搜索)

## 输出文件

### 日志文件

- **主日志**：`baseline_experiments.log` - 所有实验的汇总日志
- **单独日志**：`logs/{problem}_{baseline}_seed{seed}_{timestamp}.log` - 每个实验的详细输出

例如：
```
logs/section_jk_ga_seed42_20251122_183000.log
logs/geo_jk_nsga2_seed42_20251122_190000.log
logs/section_pf_sms_seed43_20251122_193000.log
```

### 结果文件

每个实验的结果保存在对应的 `moo_results/` 目录下，由各 baseline 脚本自动管理。

## 实验时间估算

假设单个实验运行 2 小时（`eval_budget=2000`）：

| 场景 | 实验数 | 预计时间 |
|------|--------|----------|
| 单问题 + 所有 baseline | 5 | ~10 小时 |
| 单问题 + 单 baseline + 5 种子 | 5 | ~10 小时 |
| 所有问题 + 所有 baseline | 20 | ~40 小时 |
| 所有问题 + 单 baseline | 4 | ~8 小时 |

## 高级示例

### 完整的对比实验

```bash
# 对比 section_jk 和 geo_jk 在 GA 和 NSGA-II 上的表现
# 每个算法运行 3 次（不同种子）
# 总共：2 问题 × 2 算法 × 3 种子 = 12 个实验

python run_all_baselines.py \
    --problem section_jk \
    --baselines ga nsga2 \
    --seeds 42 43 44

python run_all_baselines.py \
    --problem geo_jk \
    --baselines ga nsga2 \
    --seeds 42 43 44
```

### 快速原型测试

```bash
# 用小 budget 快速测试所有问题的配置是否正确
# 需要先修改各 config.yaml 中的 eval_budget 为 100

python run_all_baselines.py --problem all --baselines ga --dry-run  # 先测试
python run_all_baselines.py --problem all --baselines ga            # 实际运行
```

## 故障排查

### 问题：种子文件未找到

```
ERROR: Source seed file not found: /mnt/d/wsl_sacs_exchange/sacs_project/sacinp.demo06
```

**解决**：检查 `SACS_PROBLEMS` 中的 `seed_backup` 路径是否正确。

### 问题：工作目录不存在

```
ERROR: Failed to reset SACS seed file
```

**解决**：确保 `working_dir` 路径存在，或脚本会自动创建。

### 问题：配置文件未找到

```
ERROR: Baseline script not found
```

**解决**：检查 `config_path` 是否指向正确的 `config.yaml` 文件。

## 注意事项

1. **种子文件管理**：每次实验前会自动从备份恢复种子文件，确保初始状态一致
2. **并行运行**：脚本按顺序运行实验，不支持并行（避免 SACS 文件冲突）
3. **实验间隔**：每个实验之间有 5 秒暂停，防止文件系统冲突
4. **中断恢复**：如果中途中断，需要手动重新运行（不支持断点续传）
5. **磁盘空间**：确保有足够空间存储所有日志和结果文件

## 配置修改

如需修改问题配置，编辑 `run_all_baselines.py` 中的 `SACS_PROBLEMS` 字典：

```python
SACS_PROBLEMS = {
    'section_jk': {
        'name': 'Section Optimization (JK Model)',
        'seed_backup': r"D:\wsl_sacs_exchange\sacs_project\sacinp.demo06",
        'working_dir': r"D:\wsl_sacs_exchange\sacs_project\Demo06_Section",
        'target_file': "sacinp.demo06",
        'config_path': "problem/sacs_section_jk/config.yaml",
        'description': '截面优化（导管架模型，Demo06）'
    },
    # ... 其他问题
}
```

## 总结

这个脚本简化了批量实验管理，支持：
- ✅ 四种 SACS 优化问题
- ✅ 五种 baseline 算法
- ✅ 多随机种子重复实验
- ✅ 自动种子文件重置
- ✅ 实时输出和日志记录
- ✅ 实验结果汇总

**推荐工作流**：
1. 先用 `--dry-run` 测试配置
2. 用小 `eval_budget` 快速验证
3. 正式运行完整实验
4. 分析 `moo_results/` 中的结果
