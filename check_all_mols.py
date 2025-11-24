#!/usr/bin/env python3
"""
检查all_mols字段，找出GA_optimized的问题
"""
import pickle
import sys
import statistics

def check_all_mols(filepath, name):
    """检查all_mols中的数据"""
    
    print("="*80)
    print(f"检查 {name}")
    print("="*80)
    
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    
    if 'all_mols' not in data:
        print("⚠️  没有all_mols字段")
        return
    
    all_mols = data['all_mols']
    print(f"\nall_mols类型: {type(all_mols)}, 长度: {len(all_mols)}")
    
    # 检查第一个元素的结构
    if all_mols:
        first = all_mols[0]
        print(f"第一个元素类型: {type(first)}")
        if isinstance(first, tuple):
            print(f"元组长度: {len(first)}")
            if len(first) >= 1:
                item = first[0]
                print(f"Item类型: {type(item)}")
                print(f"Item属性: total={getattr(item, 'total', 'N/A')}, scores={getattr(item, 'scores', 'N/A')}")
        elif hasattr(first, '__dict__'):
            print(f"对象属性: {list(first.__dict__.keys())}")
    
    # 提取有效Items (不要求total不为None，因为all_mols可能包含未评估的)
    items = []
    for entry in all_mols:
        if isinstance(entry, tuple) and len(entry) >= 1:
            item = entry[0]
            items.append(item)
        elif hasattr(entry, 'value'):
            items.append(entry)
    
    print(f"总Items: {len(items)}")
    
    # 统计有total的数量
    items_with_total = [item for item in items if hasattr(item, 'total') and item.total is not None]
    print(f"有total的Items: {len(items_with_total)}")
    
    if not items_with_total:
        print("⚠️  没有有效的评估结果")
        return
    
    items = items_with_total
    
    # 按total排序
    items_sorted = sorted(items, key=lambda x: x.total, reverse=True)
    top10 = items_sorted[:10]
    
    print(f"\n【Top 10解】")
    print(f"{'Rank':<6} {'Total':<12} {'Score[0]':<12} {'Score[1]':<12} {'Score[2]':<12}")
    print("-"*70)
    
    for i, item in enumerate(top10, 1):
        if hasattr(item, 'scores') and item.scores is not None:
            scores = item.scores
            if len(scores) >= 3:
                print(f"{i:<6} {item.total:<12.6f} {scores[0]:<12.6f} {scores[1]:<12.6f} {scores[2]:<12.6f}")
    
    # 统计scores[0] (Weight)的分布
    weight_scores = []
    for item in items:
        if hasattr(item, 'scores') and item.scores is not None and len(item.scores) >= 1:
            weight_scores.append(item.scores[0])
    
    if weight_scores:
        print(f"\n【Weight Score统计】")
        print(f"  数量: {len(weight_scores)}")
        print(f"  范围: [{min(weight_scores):.6f}, {max(weight_scores):.6f}]")
        print(f"  均值: {statistics.mean(weight_scores):.6f}")
        print(f"  中位数: {statistics.median(weight_scores):.6f}")
        
        # 检查是否有异常值
        if min(weight_scores) < 0.01:
            print(f"  ⚠️  发现异常低的Weight score: {min(weight_scores):.6f}")
            # 找出异常值的数量
            abnormal = [s for s in weight_scores if s < 0.01]
            print(f"  ⚠️  异常值数量: {len(abnormal)} ({100*len(abnormal)/len(weight_scores):.1f}%)")

if __name__ == '__main__':
    files = {
        'GA_optimized': 'moo_results/zgca,gemini-2.5-flash-nothinking/mols/weight_axial_uc_max_bending_uc_max_sacs_geo_jk_baseline_GA_optimized_101.pkl',
        'NSGA2': 'moo_results/zgca,gemini-2.5-flash-nothinking/mols/weight_axial_uc_max_bending_uc_max_sacs_geo_jk_baseline_NSGA2_101.pkl',
        'SMSEMOA': 'moo_results/zgca,gemini-2.5-flash-nothinking/mols/weight_axial_uc_max_bending_uc_max_sacs_geo_jk_baseline_SMSEMOA_101.pkl'
    }
    
    for name, filepath in files.items():
        try:
            check_all_mols(filepath, name)
            print("\n")
        except Exception as e:
            print(f"❌ 检查{name}时出错: {e}")
            import traceback
            traceback.print_exc()
