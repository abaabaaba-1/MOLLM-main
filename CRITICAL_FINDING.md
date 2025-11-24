# 🔴 关键发现：GA_optimized的Scores异常

## 问题确认

通过读取pkl文件，发现了**根本问题**：

### Scores对比 (Top 1解)

| 算法 | Score[0] (Weight) | Score[1] (Axial UC) | Score[2] (Bending UC) | Total | Hypervolume |
|------|------------------|---------------------|----------------------|-------|-------------|
| **GA_optimized** | **0.003215** | 0.020701 | 0.076832 | 0.9664 | 1.2112 |
| NSGA2 | 0.321003 | 0.020816 | 0.076830 | 0.8605 | 0.8605 |
| SMSEMOA | 0.343459 | 0.021457 | 0.076830 | 0.8528 | 0.8352 |

### 🚨 异常点

**GA_optimized的Score[0] (Weight) = 0.003215，比NSGA2/SMSEMOA低了100倍！**

- NSGA2的Weight score: ~0.32
- SMSEMOA的Weight score: ~0.34
- **GA_optimized的Weight score: ~0.003** ⚠️

这导致：
1. GA_optimized的解在目标空间中非常接近原点
2. Hypervolume计算时，这些解占据了更大的体积
3. avg_top100虚高（因为mean(scores)很小，1-mean(scores)就很大）

## 根本原因

### 问题出在哪里？

有两种可能：

#### 可能1: Property字段缺失

从pkl数据看，所有算法的Items都**没有property字段**（显示为N/A）：
- `original_results` 缺失
- `transformed_results` 缺失
- 但`scores`字段存在

这说明：
- **final_pops只保存了最终种群的40个个体**
- 这些个体的详细property信息可能没有被保存
- 但scores（用于选择和HV计算）被保存了

#### 可能2: Scores计算错误

**关键问题**：GA_optimized的Weight score为什么这么小？

正常情况下，对于minimization问题：
```python
# transformed_results['weight'] 应该在[0, 1]范围内
# scores应该等于transformed_results

# 如果weight很小（接近最优），transformed应该接近0
# 但NSGA2/SMSEMOA的weight score都在0.32左右
# 说明它们的weight都在中等水平

# GA_optimized的weight score=0.003
# 意味着它的weight非常接近最小边界
```

## 检查all_mols

让我检查`all_mols`字段，看是否能找到完整的评估历史：

```python
# pkl文件结构
{
    'history': ...,
    'init_pops': ...,
    'final_pops': [40个Item],  # 只有最终种群
    'all_mols': ...,  # 可能包含所有评估过的解
    'properties': ...,
    'evaluation': ...,
    'running_time': ...
}
```

## 下一步调查

1. ✅ **已确认**: GA_optimized的Weight score异常低（0.003 vs 0.32）
2. ⏳ **待检查**: 查看`all_mols`字段，找到完整的评估历史
3. ⏳ **待检查**: 检查baseline_ga.py中scores的赋值逻辑
4. ⏳ **待检查**: 对比NSGA2和GA_optimized的Item.scores赋值过程

## 可能的Bug位置

### 假设1: BaselineMOO没有正确设置scores

在`baseline_ga.py`中，可能没有正确调用父类的scores赋值逻辑。

需要检查：
- `MOO.evaluate()` 如何设置`item.scores`
- `BaselineMOO` 是否覆盖了这个逻辑
- NSGA2/SMSEMOA的`select_next_population`是否修改了scores

### 假设2: 不同算法使用了不同的scores定义

- NSGA2: 使用`item.scores`进行非支配排序
- SMSEMOA: 使用`item.scores`计算HV贡献
- GA_optimized: 使用`item.total`进行锦标赛选择

**关键问题**：GA_optimized的scores是如何被设置的？

## 临时结论

**GA_optimized的优化效果"看起来"好，是因为它的Weight score异常低（0.003），导致：**

1. **Hypervolume虚高**: 解集非常接近原点，占据更大体积
2. **avg_top100虚高**: mean(scores)小 → 1-mean(scores)大 → total大

**这不是真正的优化成功，而是数值计算错误！**

需要找出为什么GA_optimized的Weight score会是0.003而不是0.32。
