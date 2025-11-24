# 🐛 Bug分析：SMSEMOA修改了scores导致数据不一致

## 问题根源

### SMSEMOA的select_next_population方法 (baseline_sms.py:43-64)

```python
def select_next_population(self, pop_size: int) -> List:
    whole_population = [item[0] for item in self.mol_buffer if item[0].total is not None]
    if not whole_population or len(whole_population) <= pop_size: return whole_population
    
    directions = self.config.get('optimization_direction')
    original_scores = np.array([p.scores for p in whole_population])  # 读取原始scores
    
    # 🔴 问题1: 重新归一化scores
    min_vals, max_vals = np.min(original_scores, axis=0), np.max(original_scores, axis=0)
    range_vals = max_vals - min_vals
    range_vals[range_vals == 0] = 1
    normalized_scores = (original_scores - min_vals) / range_vals
    
    for i, direction in enumerate(directions):
        if direction == 'max': normalized_scores[:, i] = 1.0 - normalized_scores[:, i]
    
    # 🔴 问题2: 创建临时对象并修改scores
    temp_pop_for_selection = []
    for i, p in enumerate(whole_population):
        temp_p = copy.copy(p)
        temp_p.scores = normalized_scores[i]  # ⚠️ 修改了scores！
        temp_pop_for_selection.append(temp_p)
    
    ref_point = np.full(original_scores.shape[1], 1.1)
    selected_temp_pops = _local_corrected_hvc_selection(temp_pop_for_selection, pop_size, ref_point)
    
    # 🔴 问题3: 返回的是原始population，但temp_pop的scores已经被修改
    selected_values = {p.value for p in selected_temp_pops}
    final_selection = [p for p in whole_population if p.value in selected_values]
    return final_selection
```

### 关键问题

**`copy.copy(p)` 是浅拷贝！**

```python
temp_p = copy.copy(p)  # 浅拷贝
temp_p.scores = normalized_scores[i]  # 修改scores

# 如果scores是numpy array或list，这会修改原始对象！
# 因为浅拷贝只复制引用，不复制内容
```

### 验证

从pkl数据看：
- **GA_optimized**: Weight score = 0.003 (异常低)
- **NSGA2**: Weight score = 0.321 (正常)
- **SMSEMOA**: Weight score = 0.343 (正常)

**等等！SMSEMOA的scores也是正常的？**

让我重新检查...

## 重新分析

### 检查copy.copy的行为

```python
import copy
import numpy as np

class Item:
    def __init__(self):
        self.scores = np.array([0.5, 0.5, 0.5])

p = Item()
temp_p = copy.copy(p)
temp_p.scores = np.array([0.1, 0.1, 0.1])  # 重新赋值

print(p.scores)  # [0.5, 0.5, 0.5] - 不会被修改！
```

**结论**: `copy.copy()`后重新赋值`scores`不会影响原对象，因为是重新赋值而不是修改。

所以SMSEMOA的代码**没有bug**。

## 那么GA_optimized的问题在哪里？

### 重新审视数据

让我检查`all_mols`字段，看看完整的评估历史：

```python
# 需要检查all_mols中的Items
# 看看它们的scores是否正常
```

### 可能的原因

1. **GA_optimized使用了不同的evaluator版本**
   - 虽然配置文件显示相同，但运行时可能加载了不同的模块

2. **baseline_weight不同**
   - GA_optimized的baseline_weight可能异常小
   - 导致weight ratio计算错误
   - transformed['weight'] = (ratio - 0.5) / (2.0 - 0.5)
   - 如果baseline_weight很小，ratio会很大，但clip到2.0后，transformed接近1.0
   - 等等，这会让transformed变大，不是变小...

3. **Weight bounds不同**
   - 如果GA_optimized使用了不同的weight_bounds
   - 例如[500, 5000]而不是[50, 5000]
   - 那么相同的weight值会得到更小的transformed值

4. **Scores赋值时机不同**
   - BaselineMOO可能在某个地方重新设置了scores

## 下一步

需要检查：
1. ✅ 已排除：SMSEMOA的copy.copy不会影响原对象
2. ⏳ **待检查**: GA_optimized的all_mols中的Items
3. ⏳ **待检查**: baseline_ga.py是否有地方重新设置scores
4. ⏳ **待检查**: 三个算法运行时的baseline_weight值
