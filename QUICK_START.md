# 快速开始 - 批量实验运行

## 🚀 最常用的命令

### 1. 运行 MOLLM（推荐用于新实验）

```bash
# 对 PF 平台截面优化运行 MOLLM
python run_all_baselines.py --problem section_pf --algorithms mollm

# 对 JK 导管架几何优化运行 MOLLM
python run_all_baselines.py --problem geo_jk --algorithms mollm
```

### 2. 对比 MOLLM 和所有 baseline

```bash
# 运行所有算法（6个：5个baseline + MOLLM）
python run_all_baselines.py --problem section_pf --algorithms all
```

### 3. 测试运行（不实际执行）

```bash
# 查看将要执行什么命令
python run_all_baselines.py --problem section_pf --algorithms mollm --dry-run
```

---

## 📋 支持的算法

| 算法 | 类型 | 说明 |
|------|------|------|
| `mollm` | MOLLM | 多目标大语言模型优化器 ⭐ |
| `ga` | Baseline | 遗传算法 |
| `sms` | Baseline | SMS-EMOA |
| `nsga2` | Baseline | NSGA-II |
| `moead` | Baseline | MOEA/D |
| `rs` | Baseline | 随机搜索 |

---

## 🎯 支持的问题

| 代码 | 描述 |
|------|------|
| `section_jk` | JK 导管架截面优化 |
| `section_pf` | PF 平台截面优化 |
| `geo_jk` | JK 导管架几何优化 |
| `geo_pf` | PF 平台几何优化 |

---

## 💡 实用技巧

### 使用多个随机种子

```bash
python run_all_baselines.py --problem section_pf --algorithms mollm --seeds 42 43 44
```

### 只运行特定算法

```bash
# 只运行 GA 和 MOLLM
python run_all_baselines.py --problem geo_jk --algorithms ga mollm
```

### 运行所有问题

```bash
# 对所有 4 个问题运行 MOLLM
python run_all_baselines.py --problem all --algorithms mollm
```

---

## 📊 查看结果

- **主日志**: `baseline_experiments.log`
- **详细日志**: `logs/{problem}_{algorithm}_seed{seed}_{timestamp}.log`

---

## ⚠️ 注意事项

1. **运行时间**: MOLLM 通常需要数小时，请合理安排时间
2. **确认提示**: 非 dry-run 模式会要求确认，输入 `y` 继续
3. **自动重置**: 每次运行前会自动重置 SACS 种子文件

---

**详细文档**: 查看 `RUN_ALL_EXPERIMENTS_GUIDE.md`
