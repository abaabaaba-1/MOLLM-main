#!/usr/bin/env python3
"""
简单对比三个算法的优化过程
"""
import json

def analyze_optimization_process():
    """分析优化过程的演化"""
    
    print("="*80)
    print("优化过程对比分析")
    print("="*80)
    
    files = {
        'NSGA2': 'moo_results/zgca,gemini-2.5-flash-nothinking/results/weight_axial_uc_max_bending_uc_max_sacs_geo_jk_baseline_NSGA2_101.json',
        'SMSEMOA': 'moo_results/zgca,gemini-2.5-flash-nothinking/results/weight_axial_uc_max_bending_uc_max_sacs_geo_jk_baseline_SMSEMOA_101.json',
        'GA_optimized': 'moo_results/zgca,gemini-2.5-flash-nothinking/results/weight_axial_uc_max_bending_uc_max_sacs_geo_jk_baseline_GA_optimized_101.json'
    }
    
    all_data = {}
    for name, filepath in files.items():
        with open(filepath, 'r') as f:
            all_data[name] = json.load(f)
    
    # 对比优化轨迹
    print("\n【优化轨迹对比】")
    print(f"{'Gen':<6} {'NSGA2_avg':<12} {'NSGA2_hv':<12} {'SMS_avg':<12} {'SMS_hv':<12} {'GA_avg':<12} {'GA_hv':<12}")
    print("-"*90)
    
    max_len = max(len(all_data[name]['results']) for name in all_data)
    
    for i in range(min(15, max_len)):  # 只显示前15代
        row = f"{i+1:<6}"
        
        for name in ['NSGA2', 'SMSEMOA', 'GA_optimized']:
            results = all_data[name]['results']
            if i < len(results):
                avg = results[i].get('avg_top100', 0)
                hv = results[i].get('hypervolume', 0)
                row += f" {avg:<12.6f} {hv:<12.6f}"
            else:
                row += f" {'---':<12} {'---':<12}"
        
        print(row)
    
    print("\n【关键观察】")
    
    # 分析初始种群
    print("\n1. 初始种群质量:")
    for name in ['NSGA2', 'SMSEMOA', 'GA_optimized']:
        results = all_data[name]['results']
        if results:
            first = results[0]
            print(f"  {name:15s}: avg_top100={first['avg_top100']:.6f}, hv={first['hypervolume']:.6f}")
    
    # 分析收敛速度
    print("\n2. 收敛分析:")
    for name in ['NSGA2', 'SMSEMOA', 'GA_optimized']:
        results = all_data[name]['results']
        if len(results) >= 2:
            first_avg = results[0]['avg_top100']
            last_avg = results[-1]['avg_top100']
            improvement = last_avg - first_avg
            print(f"  {name:15s}: 初始={first_avg:.6f}, 最终={last_avg:.6f}, 提升={improvement:.6f} ({100*improvement/first_avg:.1f}%)")
    
    # 分析样本效率
    print("\n3. 样本效率:")
    for name in ['NSGA2', 'SMSEMOA', 'GA_optimized']:
        results = all_data[name]['results']
        if results:
            last = results[-1]
            samples = last['generated_num']
            final_score = last['avg_top100']
            print(f"  {name:15s}: {samples}样本 -> avg_top100={final_score:.6f} (效率={final_score/samples*1000:.3f}/千样本)")
    
    # 检查是否有异常跳跃
    print("\n4. 异常检测:")
    for name in ['NSGA2', 'SMSEMOA', 'GA_optimized']:
        results = all_data[name]['results']
        max_jump = 0
        jump_gen = -1
        
        for i in range(1, len(results)):
            prev_avg = results[i-1]['avg_top100']
            curr_avg = results[i]['avg_top100']
            jump = abs(curr_avg - prev_avg)
            
            if jump > max_jump:
                max_jump = jump
                jump_gen = i
        
        if max_jump > 0.01:  # 如果有超过1%的跳跃
            print(f"  {name:15s}: 第{jump_gen+1}代有{max_jump:.6f}的跳跃")
        else:
            print(f"  {name:15s}: 平滑收敛，无异常跳跃")
    
    print("\n" + "="*80)
    print("核心发现")
    print("="*80)
    
    # 对比NSGA2和GA_optimized的差异
    nsga2_results = all_data['NSGA2']['results']
    ga_results = all_data['GA_optimized']['results']
    
    print(f"""
【数据异常】
GA_optimized的指标远高于NSGA2/SMSEMOA:
- avg_top100: GA={ga_results[-1]['avg_top100']:.6f} vs NSGA2={nsga2_results[-1]['avg_top100']:.6f}
- hypervolume: GA={ga_results[-1]['hypervolume']:.6f} vs NSGA2={nsga2_results[-1]['hypervolume']:.6f}

【可能原因】
1. ❌ 评估器不同？
   - 已验证：三个算法使用相同的evaluator (problem.sacs_geo_jk.evaluator)
   
2. ❌ 目标函数不同？
   - 已验证：三个算法使用相同的goals和optimization_direction
   
3. ✅ Early Stopping导致过早停止
   - GA_optimized在800样本时停止
   - NSGA2运行了1600样本
   - 但这不能解释为什么GA的指标反而更高
   
4. ⚠️  可能的真正原因：
   a) GA_optimized的初始种群质量异常高
      - 需要检查generate_initial_population是否被修改
      - 或者初始种群是否使用了不同的策略
   
   b) 锦标赛选择导致种群快速收敛到局部最优
      - 种群多样性丧失
      - 所有个体都非常相似
      - avg_top100高是因为top100都是相似的"局部最优"解
   
   c) 数值计算问题
      - transformed_values计算可能有bug
      - 或者某些解的原始值异常（需要查看pkl文件）

【下一步调查】
1. 检查GA_optimized的初始种群生成逻辑
2. 查看GA_optimized的种群多样性（unique top 100数量）
3. 提取实际的原始值（weight, axial_uc, bending_uc）进行对比
""")
    
    # 检查种群多样性
    print("\n【种群多样性检查】")
    for name in ['NSGA2', 'SMSEMOA', 'GA_optimized']:
        results = all_data[name]['results']
        if results:
            last = results[-1]
            unique_moles = last.get('all_unique_moles', 0)
            generated = last.get('generated_num', 1)
            uniqueness = last.get('Uniqueness', 0)
            print(f"  {name:15s}: 唯一样本={unique_moles}, 生成样本={generated}, 唯一性={uniqueness:.4f}")

if __name__ == '__main__':
    analyze_optimization_process()
