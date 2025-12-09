# Baseline实验批量运行命令手册

## 📋 可用配置

### 问题类型 (--problem)
- `section_jk` - 截面优化（导管架模型，Demo06）
- `section_pf` - 截面优化（平台模型，Demo13）
- `geo_jk` - 几何优化（导管架模型，Demo06）
- `geo_pf` - 几何优化（平台模型，Demo13）
- `all` - 所有问题

### Baseline算法 (--baselines)
- `ga` - 遗传算法
- `sms` - SMS-EMOA
- `nsga2` - NSGA-II
- `moead` - MOEA/D
- `rs` - 随机搜索
- `all` - 所有算法（默认）

### 随机种子 (--seeds)
- 默认: `42`
- 可指定多个，如: `42 43 44 45 46`

---

## 🚀 常用命令

### 1. 测试运行（不实际执行）
```bash
# 测试geo_jk问题的所有baseline
python run_all_baselines.py --problem geo_jk --dry-run

# 测试特定baseline
python run_all_baselines.py --problem geo_jk --baselines ga --dry-run
```

---

## 📦 单个问题运行

### 2. 运行单个问题的所有baseline（默认seed=42）
```bash
# 几何优化（导管架）
python run_all_baselines.py --problem geo_jk

# 几何优化（平台）
python run_all_baselines.py --problem geo_pf

# 截面优化（导管架）
python run_all_baselines.py --problem section_jk

# 截面优化（平台）
python run_all_baselines.py --problem section_pf
```

### 3. 运行单个问题的特定baseline
```bash
# 只运行GA
python run_all_baselines.py --problem geo_jk --baselines ga

# 运行GA和NSGA2
python run_all_baselines.py --problem geo_jk --baselines ga nsga2

# 运行SMS-EMOA和MOEA/D
python run_all_baselines.py --problem section_jk --baselines sms moead
```

---

## 🎲 多随机种子运行

### 4. 单个baseline，多个种子
```bash
# GA运行5个不同种子
python run_all_baselines.py --problem geo_jk --baselines ga --seeds 42 43 44 45 46

# NSGA2运行3个种子
python run_all_baselines.py --problem section_jk --baselines nsga2 --seeds 42 101 202
```

### 5. 多个baseline，多个种子
```bash
# GA和SMS各运行5个种子
python run_all_baselines.py --problem geo_jk --baselines ga sms --seeds 42 43 44 45 46

# 所有baseline各运行3个种子
python run_all_baselines.py --problem geo_jk --seeds 42 43 44
```

---

## 🌍 多问题运行

### 6. 所有问题，所有baseline（⚠️ 运行时间很长）
```bash
# 运行所有组合（4个问题 × 5个baseline × 1个种子 = 20次实验）
python run_all_baselines.py --problem all

# 所有问题，特定baseline
python run_all_baselines.py --problem all --baselines ga nsga2

# 所有问题，所有baseline，多个种子（⚠️ 超长时间）
python run_all_baselines.py --problem all --seeds 42 43 44
```

---

## 🔧 高级选项

### 7. 跳过SACS种子文件重置
```bash
# 使用现有的SACS状态，不重置种子文件
python run_all_baselines.py --problem geo_jk --skip-reset
```

### 8. 组合使用
```bash
# 测试 + 跳过重置
python run_all_baselines.py --problem geo_jk --dry-run --skip-reset

# 特定baseline + 多种子 + 跳过重置
python run_all_baselines.py --problem section_jk --baselines ga --seeds 42 43 --skip-reset
```

---

## 📊 实际使用场景

### 场景1：快速测试单个算法
```bash
# 测试GA是否能正常运行
python run_all_baselines.py --problem geo_jk --baselines ga --dry-run
python run_all_baselines.py --problem geo_jk --baselines ga
```

### 场景2：对比不同算法（单次运行）
```bash
# 对比GA、NSGA2、SMS三种算法
python run_all_baselines.py --problem geo_jk --baselines ga nsga2 sms
```

### 场景3：统计显著性测试（多次运行）
```bash
# 每个算法运行5次不同种子
python run_all_baselines.py --problem geo_jk --baselines ga nsga2 sms --seeds 42 43 44 45 46
```

### 场景4：完整实验（所有算法，多次运行）
```bash
# 所有baseline，每个5次
python run_all_baselines.py --problem geo_jk --seeds 42 43 44 45 46
```

### 场景5：多问题对比
```bash
# 在两个几何优化问题上对比GA
python run_all_baselines.py --problem geo_jk --baselines ga --seeds 42 43 44
python run_all_baselines.py --problem geo_pf --baselines ga --seeds 42 43 44
```

### 场景6：继续之前中断的实验
```bash
# 如果之前运行了部分实验，继续运行剩余的（使用不同种子）
python run_all_baselines.py --problem geo_jk --baselines ga --seeds 101 102 103
```

---

## 📈 预估运行时间

基于单次实验约2-3小时的估算：

| 命令 | 实验次数 | 预估时间 |
|------|---------|---------|
| `--problem geo_jk` | 5 (所有baseline×1种子) | ~10-15小时 |
| `--problem geo_jk --baselines ga` | 1 | ~2-3小时 |
| `--problem geo_jk --baselines ga --seeds 42 43 44 45 46` | 5 | ~10-15小时 |
| `--problem geo_jk --seeds 42 43 44 45 46` | 25 (5个baseline×5种子) | ~50-75小时 |
| `--problem all` | 20 (4问题×5baseline×1种子) | ~40-60小时 |
| `--problem all --seeds 42 43 44 45 46` | 100 | ~200-300小时 |

---

## 💡 最佳实践

1. **先测试**: 使用 `--dry-run` 确认配置正确
2. **从小到大**: 先运行单个baseline，再扩展到多个
3. **分批运行**: 避免一次性运行所有组合，建议分批进行
4. **检查日志**: 查看 `baseline_experiments.log` 了解进度
5. **结果备份**: 定期备份 `moo_results/` 和 `logs/` 文件夹

---

## 🔍 查看结果

运行完成后，结果保存在：
- **日志文件**: `baseline_experiments.log`
- **结果文件**: `moo_results/zgca,gemini-2.5-flash-nothinking/`
- **详细日志**: `logs/`

查看实验总结：
```bash
tail -50 baseline_experiments.log
```

---

## ⚠️ 注意事项

1. **确保SACS环境正常**: 运行前确认SACS可以正常执行
2. **磁盘空间**: 每次实验约产生几百MB数据，确保有足够空间
3. **不要中断**: 尽量让脚本完整运行，中断可能导致数据不完整
4. **Git同步**: 运行前先 `git pull` 获取最新代码
5. **Early Stopping**: 如果禁用了early stopping，确保有足够时间运行完整的2000次评估

---

## 🆘 故障排查

### 问题1: SACS文件找不到
```bash
# 检查SACS路径是否正确
ls /mnt/d/wsl_sacs_exchange/sacs_project/
```

### 问题2: 实验中断
```bash
# 查看日志找到最后成功的实验
tail -100 baseline_experiments.log

# 继续运行剩余实验（使用不同种子或跳过已完成的baseline）
```

### 问题3: 结果文件冲突
```bash
# 备份现有结果
cp -r moo_results moo_results_backup_$(date +%Y%m%d)

# 清理后重新运行
```
