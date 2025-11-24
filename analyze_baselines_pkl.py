#!/usr/bin/env python3
"""
使用read_checkpoint.py的方法分析三个baseline算法的pkl文件
"""
import pickle
import pandas as pd
import numpy as np
import sys

# 导入Item类
try:
    from algorithm.base import Item
except ImportError:
    class Item:
        def __init__(self):
            self.value = ""
            self.property = {}
            self.total = 0.0
            self.scores = None

def analyze_baseline_pkl(filepath, name):
    """分析baseline算法的pkl文件"""
    
    print("="*80)
    print(f"分析 {name}")
    print("="*80)
    
    try:
        with open(filepath, 'rb') as f:
            data = pickle.load(f, encoding='latin1')
    except Exception as e:
        print(f"❌ 读取文件出错: {e}")
        return None
    
    print(f"\n文件包含的键: {list(data.keys())}")
    
    # 1. 分析final_pops
    if 'final_pops' in data:
        final_pops = data['final_pops']
        print(f"\n【Final Pops】")
        print(f"  数量: {len(final_pops)}")
        
        if final_pops and hasattr(final_pops[0], 'total'):
            # 按total排序
            sorted_pops = sorted(final_pops, key=lambda x: x.total if x.total is not None else -999, reverse=True)
            top5 = sorted_pops[:5]
            
            print(f"\n  Top 5解:")
            print(f"  {'Rank':<6} {'Total':<12} {'Score[0]':<12} {'Score[1]':<12} {'Score[2]':<12}")
            print("  " + "-"*70)
            
            for i, item in enumerate(top5, 1):
                if hasattr(item, 'scores') and item.scores is not None and len(item.scores) >= 3:
                    print(f"  {i:<6} {item.total:<12.6f} {item.scores[0]:<12.6f} {item.scores[1]:<12.6f} {item.scores[2]:<12.6f}")
                else:
                    print(f"  {i:<6} {item.total:<12.6f} {'N/A':<12} {'N/A':<12} {'N/A':<12}")
            
            # 统计scores[0]的分布
            weight_scores = [item.scores[0] for item in final_pops if hasattr(item, 'scores') and item.scores is not None and len(item.scores) >= 1]
            if weight_scores:
                print(f"\n  Weight Score (scores[0]) 统计:")
                print(f"    范围: [{min(weight_scores):.6f}, {max(weight_scores):.6f}]")
                print(f"    均值: {np.mean(weight_scores):.6f}")
                print(f"    中位数: {np.median(weight_scores):.6f}")
                
                if min(weight_scores) < 0.01:
                    print(f"    ⚠️  发现异常低的Weight score!")
    
    # 2. 分析all_mols
    if 'all_mols' in data:
        all_mols = data['all_mols']
        print(f"\n【All Mols】")
        print(f"  总数: {len(all_mols)}")
        
        # 提取数据
        extracted_data = []
        for candidate_entry in all_mols:
            item = candidate_entry[0] if isinstance(candidate_entry, (list, tuple)) and candidate_entry else candidate_entry
            if not hasattr(item, 'value') or not hasattr(item, 'property'): 
                continue
            
            prop = item.property or {}
            info = {
                'total_score': item.total,
                'scores': item.scores if hasattr(item, 'scores') else None
            }
            
            # 解析property
            if 'original_results' in prop:
                original_results = prop.get('original_results', {})
                constraint_results = prop.get('constraint_results', {})
                info.update({
                    'weight': original_results.get('weight'),
                    'axial_uc_max': original_results.get('axial_uc_max'),
                    'bending_uc_max': original_results.get('bending_uc_max'),
                    'is_feasible': constraint_results.get('is_feasible'),
                    'max_uc': constraint_results.get('max_uc'),
                })
            else:
                info.update({
                    'weight': prop.get('weight'),
                    'axial_uc_max': prop.get('axial_uc_max'),
                    'bending_uc_max': prop.get('bending_uc_max'),
                })
            
            extracted_data.append(info)
        
        if extracted_data:
            df = pd.DataFrame(extracted_data)
            
            # 统计有效数据
            valid_df = df.dropna(subset=['weight', 'axial_uc_max', 'bending_uc_max'], how='all')
            print(f"  有效评估数: {len(valid_df)}")
            
            if len(valid_df) > 0:
                print(f"\n  原始值统计:")
                print(f"    Weight: [{valid_df['weight'].min():.2f}, {valid_df['weight'].max():.2f}], 均值={valid_df['weight'].mean():.2f}")
                print(f"    Axial UC: [{valid_df['axial_uc_max'].min():.4f}, {valid_df['axial_uc_max'].max():.4f}], 均值={valid_df['axial_uc_max'].mean():.4f}")
                print(f"    Bending UC: [{valid_df['bending_uc_max'].min():.4f}, {valid_df['bending_uc_max'].max():.4f}], 均值={valid_df['bending_uc_max'].mean():.4f}")
                
                # 可行解比例
                if 'is_feasible' in valid_df.columns:
                    feasible_count = (valid_df['is_feasible'] == 1.0).sum()
                    print(f"    可行解: {feasible_count}/{len(valid_df)} ({100*feasible_count/len(valid_df):.1f}%)")
                
                # Top 10的原始值
                top10_df = valid_df.nlargest(10, 'total_score')
                print(f"\n  Top 10解的原始值:")
                print(f"    {'Rank':<6} {'Total':<10} {'Weight':<10} {'Axial_UC':<10} {'Bending_UC':<10}")
                print("    " + "-"*60)
                for i, (idx, row) in enumerate(top10_df.iterrows(), 1):
                    print(f"    {i:<6} {row['total_score']:<10.4f} {row['weight']:<10.2f} {row['axial_uc_max']:<10.4f} {row['bending_uc_max']:<10.4f}")
    
    return data

def compare_baselines():
    """对比三个baseline算法"""
    
    files = {
        'GA_optimized': 'moo_results/zgca,gemini-2.5-flash-nothinking/mols/weight_axial_uc_max_bending_uc_max_sacs_geo_jk_baseline_GA_optimized_101.pkl',
        'NSGA2': 'moo_results/zgca,gemini-2.5-flash-nothinking/mols/weight_axial_uc_max_bending_uc_max_sacs_geo_jk_baseline_NSGA2_101.pkl',
        'SMSEMOA': 'moo_results/zgca,gemini-2.5-flash-nothinking/mols/weight_axial_uc_max_bending_uc_max_sacs_geo_jk_baseline_SMSEMOA_101.pkl'
    }
    
    results = {}
    for name, filepath in files.items():
        data = analyze_baseline_pkl(filepath, name)
        results[name] = data
        print("\n")
    
    # 对比分析
    print("="*80)
    print("对比分析")
    print("="*80)
    
    print("\n【关键发现】")
    
    # 提取final_pops的weight scores
    for name, data in results.items():
        if data and 'final_pops' in data:
            final_pops = data['final_pops']
            weight_scores = [item.scores[0] for item in final_pops if hasattr(item, 'scores') and item.scores is not None and len(item.scores) >= 1]
            if weight_scores:
                print(f"\n{name}:")
                print(f"  Final Pops Weight Score范围: [{min(weight_scores):.6f}, {max(weight_scores):.6f}]")
                print(f"  均值: {np.mean(weight_scores):.6f}")
                
                if min(weight_scores) < 0.01:
                    print(f"  🚨 异常: Weight score异常低 (< 0.01)")
                    print(f"  这会导致hypervolume和avg_top100虚高!")

if __name__ == '__main__':
    compare_baselines()
