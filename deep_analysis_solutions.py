#!/usr/bin/env python3
"""
深入分析三个算法生成的实际解，检查原始值和transformed值
"""
import json
import pickle
import numpy as np

def analyze_solutions():
    """分析实际解的数据"""
    
    print("="*80)
    print("深入分析：检查实际解的原始值和转换值")
    print("="*80)
    
    # 读取pkl文件（包含实际的Item对象）
    pkl_files = {
        'NSGA2': 'moo_results/zgca,gemini-2.5-flash-nothinking/mols/weight_axial_uc_max_bending_uc_max_sacs_geo_jk_baseline_NSGA2_101.pkl',
        'SMSEMOA': 'moo_results/zgca,gemini-2.5-flash-nothinking/mols/weight_axial_uc_max_bending_uc_max_sacs_geo_jk_baseline_SMSEMOA_101.pkl',
        'GA_optimized': 'moo_results/zgca,gemini-2.5-flash-nothinking/mols/weight_axial_uc_max_bending_uc_max_sacs_geo_jk_baseline_GA_optimized_101.pkl'
    }
    
    for name, filepath in pkl_files.items():
        try:
            print(f"\n{'='*80}")
            print(f"【{name}】")
            print('='*80)
            
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            # data应该是一个包含(Item, info)元组的列表
            if not data:
                print("  ⚠️  数据为空")
                continue
            
            # 提取所有有效的Item
            items = []
            for entry in data:
                if isinstance(entry, tuple) and len(entry) >= 1:
                    item = entry[0]
                    if hasattr(item, 'total') and item.total is not None:
                        items.append(item)
            
            if not items:
                print("  ⚠️  没有有效的Item")
                continue
            
            print(f"\n总样本数: {len(items)}")
            
            # 按total排序，取top 10
            items_sorted = sorted(items, key=lambda x: x.total, reverse=True)
            top10 = items_sorted[:10]
            
            print(f"\n【Top 10解的详细信息】")
            print(f"{'Rank':<6} {'Total':<10} {'Weight':<12} {'Axial_UC':<12} {'Bending_UC':<12} {'Feasible':<10}")
            print("-"*80)
            
            for i, item in enumerate(top10, 1):
                # 提取原始结果
                if hasattr(item, 'property') and isinstance(item.property, dict):
                    orig = item.property.get('original_results', {})
                    weight = orig.get('weight', 'N/A')
                    axial = orig.get('axial_uc_max', 'N/A')
                    bending = orig.get('bending_uc_max', 'N/A')
                    
                    # 提取约束结果
                    constr = item.property.get('constraint_results', {})
                    feasible = "Yes" if constr.get('is_feasible', 0) > 0.5 else "No"
                    
                    # 格式化输出
                    weight_str = f"{weight:.2f}" if isinstance(weight, (int, float)) else str(weight)
                    axial_str = f"{axial:.4f}" if isinstance(axial, (int, float)) else str(axial)
                    bending_str = f"{bending:.4f}" if isinstance(bending, (int, float)) else str(bending)
                    
                    print(f"{i:<6} {item.total:<10.6f} {weight_str:<12} {axial_str:<12} {bending_str:<12} {feasible:<10}")
            
            # 统计分析
            print(f"\n【统计分析】")
            
            # 提取所有原始值
            weights = []
            axials = []
            bendings = []
            feasible_count = 0
            
            for item in items:
                if hasattr(item, 'property') and isinstance(item.property, dict):
                    orig = item.property.get('original_results', {})
                    constr = item.property.get('constraint_results', {})
                    
                    w = orig.get('weight')
                    a = orig.get('axial_uc_max')
                    b = orig.get('bending_uc_max')
                    
                    if isinstance(w, (int, float)) and w < 90000:  # 排除惩罚值
                        weights.append(w)
                    if isinstance(a, (int, float)) and a < 900:
                        axials.append(a)
                    if isinstance(b, (int, float)) and b < 900:
                        bendings.append(b)
                    
                    if constr.get('is_feasible', 0) > 0.5:
                        feasible_count += 1
            
            if weights:
                print(f"  Weight (tonnes):")
                print(f"    范围: [{min(weights):.2f}, {max(weights):.2f}]")
                print(f"    均值: {np.mean(weights):.2f}")
                print(f"    中位数: {np.median(weights):.2f}")
            
            if axials:
                print(f"  Axial UC:")
                print(f"    范围: [{min(axials):.4f}, {max(axials):.4f}]")
                print(f"    均值: {np.mean(axials):.4f}")
                print(f"    中位数: {np.median(axials):.4f}")
            
            if bendings:
                print(f"  Bending UC:")
                print(f"    范围: [{min(bendings):.4f}, {max(bendings):.4f}]")
                print(f"    均值: {np.mean(bendings):.4f}")
                print(f"    中位数: {np.median(bendings):.4f}")
            
            print(f"  可行解比例: {feasible_count}/{len(items)} ({100*feasible_count/len(items):.1f}%)")
            
            # 检查transformed_results
            print(f"\n【Transformed Values检查 (Top 10)】")
            print(f"{'Rank':<6} {'Weight_T':<12} {'Axial_T':<12} {'Bending_T':<12} {'Mean_T':<12}")
            print("-"*80)
            
            for i, item in enumerate(top10, 1):
                if hasattr(item, 'property') and isinstance(item.property, dict):
                    trans = item.property.get('transformed_results', {})
                    w_t = trans.get('weight', 'N/A')
                    a_t = trans.get('axial_uc_max', 'N/A')
                    b_t = trans.get('bending_uc_max', 'N/A')
                    
                    if all(isinstance(x, (int, float)) for x in [w_t, a_t, b_t]):
                        mean_t = np.mean([w_t, a_t, b_t])
                        expected_total = 1.0 - mean_t
                        
                        print(f"{i:<6} {w_t:<12.6f} {a_t:<12.6f} {b_t:<12.6f} {mean_t:<12.6f}")
                        
                        # 验证total计算
                        if abs(item.total - expected_total) > 0.001:
                            print(f"  ⚠️  Total不匹配: actual={item.total:.6f}, expected={expected_total:.6f}")
            
            # 检查scores（用于hypervolume计算）
            print(f"\n【Scores检查 (用于Hypervolume计算)】")
            if hasattr(top10[0], 'scores'):
                print(f"{'Rank':<6} {'Score[0]':<12} {'Score[1]':<12} {'Score[2]':<12}")
                print("-"*80)
                for i, item in enumerate(top10, 1):
                    if hasattr(item, 'scores') and item.scores is not None:
                        scores = item.scores
                        if len(scores) >= 3:
                            print(f"{i:<6} {scores[0]:<12.6f} {scores[1]:<12.6f} {scores[2]:<12.6f}")
                            
                            # 检查是否在[0,1]范围内
                            if any(s < 0 or s > 1 for s in scores):
                                print(f"  ⚠️  Scores超出[0,1]范围!")
            else:
                print("  ⚠️  Items没有scores属性")
            
        except FileNotFoundError:
            print(f"  ❌ 文件不存在: {filepath}")
        except Exception as e:
            print(f"  ❌ 分析出错: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("结论")
    print("="*80)
    print("""
根据上述分析，可以判断：

1. 如果GA_optimized的原始值（weight, axial_uc, bending_uc）与NSGA2/SMSEMOA
   相似，但avg_top100和hypervolume差异巨大，则问题出在：
   - Transformed values计算错误
   - Scores计算错误
   - Hypervolume计算使用了错误的输入

2. 如果GA_optimized的原始值本身就异常（如weight极小，UC极小），则问题出在：
   - 评估器计算错误
   - SACS分析结果提取错误
   - 或者GA_optimized确实找到了"假"的优秀解（数值上看起来好，但实际不可行）

3. 如果GA_optimized的可行解比例很低，说明：
   - 算法陷入了不可行区域
   - 惩罚机制没有起作用
   - Early stopping过早停止，没有足够时间探索可行域
""")

if __name__ == '__main__':
    analyze_solutions()
