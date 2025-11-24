#!/usr/bin/env python3
"""
读取pkl文件并分析实际解的数据
"""
import pickle
import sys

def inspect_pkl(filepath):
    """检查pkl文件中的数据"""
    
    print("="*80)
    print(f"检查文件: {filepath}")
    print("="*80)
    
    try:
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        print(f"\n数据类型: {type(data)}")
        
        # 处理字典格式（新版本）
        if isinstance(data, dict):
            print(f"字典键: {list(data.keys())}")
            
            # 尝试找到mol_buffer
            if 'mol_buffer' in data:
                mol_buffer = data['mol_buffer']
                print(f"mol_buffer类型: {type(mol_buffer)}, 长度: {len(mol_buffer)}")
            elif 'final_pops' in data:
                mol_buffer = data['final_pops']
                print(f"final_pops类型: {type(mol_buffer)}, 长度: {len(mol_buffer)}")
            else:
                print("⚠️  未找到mol_buffer或final_pops")
                return
        else:
            mol_buffer = data
            print(f"数据长度: {len(data)}")
        
        if not mol_buffer:
            print("⚠️  数据为空")
            return
        
        # 检查第一个元素的结构
        print(f"\n第一个元素类型: {type(mol_buffer[0])}")
        if isinstance(mol_buffer[0], tuple):
            print(f"元组长度: {len(mol_buffer[0])}")
            item = mol_buffer[0][0]
            print(f"Item类型: {type(item)}")
        
        # 提取所有有效的Item
        items = []
        for entry in mol_buffer:
            if isinstance(entry, tuple) and len(entry) >= 1:
                item = entry[0]
                if hasattr(item, 'total') and item.total is not None:
                    items.append(item)
            elif hasattr(entry, 'total'):
                # 直接是Item对象
                if entry.total is not None:
                    items.append(entry)
        
        print(f"\n有效Item数量: {len(items)}")
        
        if not items:
            print("⚠️  没有有效的Item")
            return
        
        # 按total排序
        items_sorted = sorted(items, key=lambda x: x.total, reverse=True)
        top10 = items_sorted[:10]
        
        print(f"\n{'='*80}")
        print("Top 10解的详细信息")
        print('='*80)
        print(f"{'Rank':<6} {'Total':<12} {'Weight':<12} {'Axial_UC':<12} {'Bending_UC':<12} {'Feasible':<10}")
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
                
                print(f"{i:<6} {item.total:<12.6f} {weight_str:<12} {axial_str:<12} {bending_str:<12} {feasible:<10}")
        
        # 统计分析
        print(f"\n{'='*80}")
        print("统计分析")
        print('='*80)
        
        weights = []
        axials = []
        bendings = []
        feasible_count = 0
        penalty_count = 0
        
        for item in items:
            if hasattr(item, 'property') and isinstance(item.property, dict):
                orig = item.property.get('original_results', {})
                constr = item.property.get('constraint_results', {})
                
                w = orig.get('weight')
                a = orig.get('axial_uc_max')
                b = orig.get('bending_uc_max')
                
                if isinstance(w, (int, float)):
                    if w < 90000:  # 排除惩罚值
                        weights.append(w)
                    else:
                        penalty_count += 1
                
                if isinstance(a, (int, float)) and a < 900:
                    axials.append(a)
                if isinstance(b, (int, float)) and b < 900:
                    bendings.append(b)
                
                if constr.get('is_feasible', 0) > 0.5:
                    feasible_count += 1
        
        if weights:
            import statistics
            print(f"\nWeight (tonnes):")
            print(f"  范围: [{min(weights):.2f}, {max(weights):.2f}]")
            print(f"  均值: {statistics.mean(weights):.2f}")
            print(f"  中位数: {statistics.median(weights):.2f}")
        
        if axials:
            print(f"\nAxial UC:")
            print(f"  范围: [{min(axials):.4f}, {max(axials):.4f}]")
            print(f"  均值: {statistics.mean(axials):.4f}")
            print(f"  中位数: {statistics.median(axials):.4f}")
        
        if bendings:
            print(f"\nBending UC:")
            print(f"  范围: [{min(bendings):.4f}, {max(bendings):.4f}]")
            print(f"  均值: {statistics.mean(bendings):.4f}")
            print(f"  中位数: {statistics.median(bendings):.4f}")
        
        print(f"\n可行解比例: {feasible_count}/{len(items)} ({100*feasible_count/len(items):.1f}%)")
        print(f"惩罚解数量: {penalty_count}")
        
        # 检查transformed_results和scores
        print(f"\n{'='*80}")
        print("Transformed Values和Scores检查 (Top 10)")
        print('='*80)
        print(f"{'Rank':<6} {'Weight_T':<12} {'Axial_T':<12} {'Bending_T':<12} {'Mean_T':<12} {'1-Mean_T':<12}")
        print("-"*90)
        
        for i, item in enumerate(top10, 1):
            if hasattr(item, 'property') and isinstance(item.property, dict):
                trans = item.property.get('transformed_results', {})
                w_t = trans.get('weight', 'N/A')
                a_t = trans.get('axial_uc_max', 'N/A')
                b_t = trans.get('bending_uc_max', 'N/A')
                
                if all(isinstance(x, (int, float)) for x in [w_t, a_t, b_t]):
                    mean_t = (w_t + a_t + b_t) / 3
                    expected_total = 1.0 - mean_t
                    
                    print(f"{i:<6} {w_t:<12.6f} {a_t:<12.6f} {b_t:<12.6f} {mean_t:<12.6f} {expected_total:<12.6f}")
                    
                    # 验证total计算
                    if abs(item.total - expected_total) > 0.001:
                        print(f"  ⚠️  Total不匹配: actual={item.total:.6f}, expected={expected_total:.6f}")
        
        # 检查scores
        print(f"\n{'='*80}")
        print("Scores检查 (用于Hypervolume计算)")
        print('='*80)
        
        if hasattr(top10[0], 'scores'):
            print(f"{'Rank':<6} {'Score[0]':<12} {'Score[1]':<12} {'Score[2]':<12} {'In [0,1]':<10}")
            print("-"*70)
            for i, item in enumerate(top10, 1):
                if hasattr(item, 'scores') and item.scores is not None:
                    scores = item.scores
                    if len(scores) >= 3:
                        in_range = "Yes" if all(0 <= s <= 1 for s in scores) else "No"
                        print(f"{i:<6} {scores[0]:<12.6f} {scores[1]:<12.6f} {scores[2]:<12.6f} {in_range:<10}")
                        
                        if not all(0 <= s <= 1 for s in scores):
                            print(f"  ⚠️  Scores超出[0,1]范围!")
        else:
            print("⚠️  Items没有scores属性")
        
    except FileNotFoundError:
        print(f"❌ 文件不存在: {filepath}")
    except Exception as e:
        print(f"❌ 读取出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = 'moo_results/zgca,gemini-2.5-flash-nothinking/mols/weight_axial_uc_max_bending_uc_max_sacs_geo_jk_baseline_GA_optimized_101.pkl'
    
    inspect_pkl(filepath)
