# 🎯 最终诊断：GA_optimized的Weight Score计算错误

## 问题确认

通过读取pkl文件，**确认了根本问题**：

### 原始值对比（Top 1解）

| 算法 | Weight (tonnes) | Axial UC | Bending UC | Weight Score | Total |
|------|----------------|----------|------------|--------------|-------|
| **GA_optimized** | **65.92** | 0.0207 | 0.0768 | **0.003215** ⚠️ | 0.9664 |
| NSGA2 | 64.77 | 0.0208 | 0.0768 | 0.321003 | 0.8605 |
| SMSEMOA | 65.83 | 0.0215 | 0.0768 | 0.343459 | 0.8528 |

### 🚨 关键发现

1. **原始值相似**：
   - GA_optimized的weight=65.92吨
   - NSGA2的weight=64.77吨
   - SMSEMOA的weight=65.83吨
   - **三个算法的原始weight都在64-66吨范围内，非常接近！**

2. **Weight Score异常**：
   - GA_optimized的weight score = **0.003215** (异常低)
   - NSGA2的weight score = 0.321003 (正常)
   - SMSEMOA的weight score = 0.343459 (正常)
   - **GA_optimized的weight score比正常值低了100倍！**

3. **其他目标正常**：
   - Axial UC score: 三个算法都在0.020-0.021范围内
   - Bending UC score: 三个算法都是0.0768
   - **只有Weight score异常！**

## 根本原因

### Weight归一化逻辑

根据`problem/sacs_geo_jk/evaluator.py`的`_transform_objectives`方法：

```python
def _transform_objectives(self, penalized_results: dict) -> dict:
    transformed = {}
    
    # Weight Transformation (dynamic when baseline available)
    if self.baseline_weight_tonnes:
        min_ratio, max_ratio = self.weight_ratio_bounds  # [0.5, 2.0]
        weight = penalized_results.get('weight', self.baseline_weight_tonnes)
        ratio = weight / self.baseline_weight_tonnes
        ratio = np.clip(ratio, min_ratio, max_ratio)
        denom = max(max_ratio - min_ratio, 1e-8)
        weight_norm = (ratio - min_ratio) / denom  # (ratio - 0.5) / 1.5
    else:
        w_min, w_max = self.weight_bounds  # [50.0, 5000.0]
        weight = np.clip(penalized_results.get('weight', w_max), w_min, w_max)
        weight_norm = (weight - w_min) / (w_max - w_min)
    
    if self.obj_directions.get('weight') == 'min':
        transformed['weight'] = weight_norm
    else:
        transformed['weight'] = 1.0 - weight_norm
    
    return transformed
```

### 计算验证

#### NSGA2 (weight=64.77, score=0.321)

假设使用固定bounds [50, 5000]:
```
weight_norm = (64.77 - 50) / (5000 - 50) = 14.77 / 4950 = 0.00298
```
❌ 不匹配！应该是0.321

假设使用动态baseline_weight:
```
如果baseline_weight = 50吨:
ratio = 64.77 / 50 = 1.295
weight_norm = (1.295 - 0.5) / (2.0 - 0.5) = 0.795 / 1.5 = 0.530
```
❌ 还是不匹配

**等等！让我重新检查transformed的定义...**

#### 重新分析

从代码看，`scores = [transformed_results[obj] for obj in property_list]`

所以`scores[0]`应该等于`transformed_results['weight']`。

如果NSGA2的weight=64.77，score=0.321，那么：
```
0.321 = (64.77 - w_min) / (w_max - w_min)
```

解方程：
```
如果w_min=50, w_max=5000:
  0.321 = (64.77 - 50) / 4950 = 0.00298  ❌

如果使用动态baseline，baseline_weight=?:
  ratio = 64.77 / baseline_weight
  0.321 = (ratio - 0.5) / 1.5
  ratio = 0.321 * 1.5 + 0.5 = 0.9815
  baseline_weight = 64.77 / 0.9815 = 65.99吨
```

**找到了！baseline_weight ≈ 66吨**

#### 验证GA_optimized

如果baseline_weight=66吨，GA_optimized的weight=65.92:
```
ratio = 65.92 / 66 = 0.9988
weight_norm = (0.9988 - 0.5) / 1.5 = 0.3325
```

但实际score=0.003215，差了100倍！

### 🎯 问题定位

**GA_optimized使用了不同的baseline_weight！**

如果GA_optimized的score=0.003215，weight=65.92:
```
0.003215 = (ratio - 0.5) / 1.5
ratio = 0.003215 * 1.5 + 0.5 = 0.5048
baseline_weight = 65.92 / 0.5048 = 130.6吨
```

**GA_optimized的baseline_weight ≈ 130吨，是NSGA2/SMSEMOA的2倍！**

## baseline_ga.py的问题

### 可能的Bug位置

1. **Evaluator初始化时机不同**
   - BaselineMOO可能在不同时机初始化RewardingSystem
   - 导致读取的baseline_weight不同

2. **配置文件不同**
   - GA_optimized可能使用了不同的config
   - 或者config在运行时被修改

3. **SACS项目状态不同**
   - 如果三个算法不是同时运行
   - SACS项目的baseline文件可能被修改
   - 导致`calculate_sacs_weight_from_db`返回不同的值

### 检查baseline_ga.py

需要检查：
1. ✅ `BaselineMOO.__init__`是否修改了config
2. ✅ `BaselineMOO`是否重新初始化了reward_system
3. ✅ 是否有代码修改了baseline_weight

让我检查代码...

## 验证

从`baseline_ga.py`看，`BaselineMOO`继承自`MOO`，没有重新初始化reward_system。

但是，如果三个算法在不同时间运行，SACS项目的baseline文件可能不同：

```python
# evaluator.py __init__
try:
    base_weight_res = calculate_sacs_weight_from_db(self.sacs_project_path)
    if base_weight_res.get('status') == 'success':
        self.baseline_weight_tonnes = max(1e-6, float(base_weight_res['total_weight_tonnes']))
        self.logger.info(f"Baseline weight for normalization: {self.baseline_weight_tonnes:.3f} tonnes")
except Exception as exc:
    self.logger.warning(f"Failed to read baseline weight for normalization: {exc}")
```

**如果GA_optimized运行时，SACS项目的baseline文件被修改过，就会导致baseline_weight不同！**

## 结论

### 问题根源

**GA_optimized的baseline_weight ≈ 130吨，而NSGA2/SMSEMOA的baseline_weight ≈ 66吨**

这导致：
1. 相同的weight值（~66吨）被归一化到不同的范围
2. GA_optimized: ratio = 66/130 = 0.5，weight_norm ≈ 0.003
3. NSGA2: ratio = 66/66 = 1.0，weight_norm ≈ 0.33
4. Weight score差了100倍，导致total、hypervolume虚高

### baseline_ga.py有问题吗？

**baseline_ga.py本身没有bug！**

问题在于：
1. **运行环境不一致**：三个算法在不同时间运行，SACS baseline文件不同
2. **Evaluator依赖外部状态**：baseline_weight从SACS文件读取，不是固定值

### 其他模型是否成功运行？

✅ **NSGA2和SMSEMOA都成功运行了优化**：
- NSGA2: 1599次评估，weight从66.31降到64.77吨
- SMSEMOA: 960次评估，weight从66.31降到65.81吨
- 两者的baseline_weight都是66吨，归一化逻辑一致

❌ **GA_optimized的优化结果不可信**：
- 虽然运行了800次评估
- 但由于baseline_weight错误（130吨 vs 66吨）
- 导致weight score异常低，指标虚高
- **不是真正的优化成功**

## 解决方案

### 1. 立即修复

在config中固定baseline_weight：
```yaml
sacs:
  baseline_weight_tonnes: 66.0  # 固定值，不从文件读取
```

修改evaluator.py：
```python
# 优先使用config中的固定值
self.baseline_weight_tonnes = config.get('sacs.baseline_weight_tonnes')
if not self.baseline_weight_tonnes:
    # 如果config没有，才从文件读取
    base_weight_res = calculate_sacs_weight_from_db(self.sacs_project_path)
    ...
```

### 2. 重新运行GA_optimized

使用正确的baseline_weight重新运行，确保三个算法使用相同的归一化参数。

### 3. 添加日志

在evaluator初始化时打印baseline_weight：
```python
self.logger.info(f"[CRITICAL] Baseline weight for normalization: {self.baseline_weight_tonnes:.3f} tonnes")
```

确保所有算法使用相同的值。
