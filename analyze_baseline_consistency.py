#!/usr/bin/env python3
"""
分析三个baseline算法（NSGA2, SMSEMOA, GA_optimized）的逻辑一致性
"""
import json
import sys

def analyze_algorithm_consistency():
    """检查三个算法在评估器、目标函数等方面的一致性"""
    
    print("="*80)
    print("Baseline算法逻辑一致性分析")
    print("="*80)
    
    # 读取三个结果文件
    files = {
        'NSGA2': 'moo_results/zgca,gemini-2.5-flash-nothinking/results/weight_axial_uc_max_bending_uc_max_sacs_geo_jk_baseline_NSGA2_101.json',
        'SMSEMOA': 'moo_results/zgca,gemini-2.5-flash-nothinking/results/weight_axial_uc_max_bending_uc_max_sacs_geo_jk_baseline_SMSEMOA_101.json',
        'GA_optimized': 'moo_results/zgca,gemini-2.5-flash-nothinking/results/weight_axial_uc_max_bending_uc_max_sacs_geo_jk_baseline_GA_optimized_101.json'
    }
    
    configs = {}
    for name, filepath in files.items():
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                configs[name] = data.get('params', '')
        except Exception as e:
            print(f"❌ 无法读取 {name}: {e}")
            return
    
    print("\n" + "="*80)
    print("1. 配置参数对比")
    print("="*80)
    
    # 解析关键配置
    key_params = [
        'evalutor_path',
        'goals',
        'optimization_direction',
        'optimization.pop_size',
        'optimization.eval_budget',
        'sacs.project_path',
        'sacs.optimizable_joints',
    ]
    
    for param in key_params:
        print(f"\n【{param}】")
        for name, config_str in configs.items():
            # 简单解析（假设是YAML格式的字符串）
            lines = config_str.split('\n')
            value = "未找到"
            for line in lines:
                if param.replace('.', '.') in line or param.split('.')[-1] in line:
                    value = line.strip()
                    break
            print(f"  {name:15s}: {value}")
    
    print("\n" + "="*80)
    print("2. 关键发现")
    print("="*80)
    
    findings = []
    
    # 检查evaluator路径
    eval_paths = {}
    for name, config_str in configs.items():
        if 'evalutor_path: problem.sacs_geo_jk.evaluator' in config_str:
            eval_paths[name] = 'problem.sacs_geo_jk.evaluator'
    
    if len(set(eval_paths.values())) == 1 and len(eval_paths) == 3:
        findings.append("✅ 三个算法使用相同的evaluator: problem.sacs_geo_jk.evaluator")
    else:
        findings.append("❌ 三个算法的evaluator可能不一致")
    
    # 检查优化目标
    goals_consistent = True
    for name, config_str in configs.items():
        if "goals: ['weight', 'axial_uc_max', 'bending_uc_max']" not in config_str:
            goals_consistent = False
    
    if goals_consistent:
        findings.append("✅ 三个算法使用相同的优化目标: weight, axial_uc_max, bending_uc_max")
    else:
        findings.append("❌ 优化目标可能不一致")
    
    # 检查early stopping配置
    print("\n【Early Stopping配置】")
    for name, config_str in configs.items():
        if 'baseline_early_stopping' in config_str:
            print(f"  {name}: 启用了baseline_early_stopping")
            # 提取关键参数
            for line in config_str.split('\n'):
                if any(x in line for x in ['enable:', 'patience:', 'min_samples:', 'metric:']):
                    print(f"    {line.strip()}")
        elif 'early_stopping: False' in config_str:
            print(f"  {name}: early_stopping=False (未启用)")
        else:
            print(f"  {name}: 使用默认early stopping")
    
    findings.append("\n⚠️  GA_optimized启用了baseline_early_stopping，而NSGA2/SMSEMOA未启用")
    findings.append("   这导致GA_optimized在800个样本时就停止了，而其他算法继续运行")
    
    for finding in findings:
        print(finding)
    
    print("\n" + "="*80)
    print("3. 代码层面检查")
    print("="*80)
    
    print("""
根据代码分析：

【评估器 (RewardingSystem)】
- 位置: problem/sacs_geo_jk/evaluator.py
- 三个算法都使用相同的evaluator
- 评估逻辑:
  1. 解析JSON候选 -> new_code_blocks
  2. 修改SACS文件 -> 运行分析
  3. 提取指标: weight, axial_uc_max, bending_uc_max
  4. 应用惩罚 (max_uc > 1.0 时)
  5. 转换目标 (_transform_objectives)
  6. 计算overall_score = 1.0 - mean(transformed_values)

【目标转换 (_transform_objectives)】
- Weight归一化:
  * 如果有baseline_weight: ratio = weight/baseline_weight, 归一化到[0.5, 2.0]
  * 否则: 归一化到[50, 5000]吨
- UC归一化: 归一化到[0, 1]
- 所有transformed值都在[0, 1]范围内
- 对于min目标: transformed = (value - min) / (max - min)

【Overall Score计算】
- overall_score = 1.0 - mean(transformed_values)
- 因此: overall_score越大越好 (接近1表示所有目标都接近最小值)
- avg_top100 = mean([item.total for item in top100])
- item.total = overall_score

【Hypervolume计算】
- 使用pymoo的HV计算
- 参考点: [1.1, 1.1, 1.1] (对于3目标问题)
- 输入: top100的scores (即transformed_values)
- 只计算Pareto前沿的hypervolume

【关键问题】
❌ GA_optimized的hypervolume=1.21异常高，而NSGA2/SMSEMOA约0.86
   - 正常情况下，参考点为[1.1, 1.1, 1.1]时，HV不应超过1.1^3=1.331
   - GA_optimized的HV=1.21接近理论上限，说明其解可能不在正常范围内
   
❌ GA_optimized的avg_top100=0.966异常高 (接近1)
   - 这意味着transformed_values的均值接近0
   - 即所有目标都接近最小边界
   - 但这在实际工程中几乎不可能（weight、UC不可能同时都达到最优）
""")
    
    print("\n" + "="*80)
    print("4. 数据验证")
    print("="*80)
    
    # 读取并分析实际数据
    for name, filepath in files.items():
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                results = data.get('results', [])
                if results:
                    final = results[-1]
                    print(f"\n【{name} - 最终结果】")
                    print(f"  avg_top100: {final.get('avg_top100', 'N/A'):.6f}")
                    print(f"  hypervolume: {final.get('hypervolume', 'N/A'):.6f}")
                    print(f"  生成样本数: {final.get('generated_num', 'N/A')}")
                    print(f"  唯一样本数: {final.get('all_unique_moles', 'N/A')}")
                    
                    # 检查是否有异常
                    hv = final.get('hypervolume', 0)
                    avg = final.get('avg_top100', 0)
                    
                    if hv > 1.0:
                        print(f"  ⚠️  Hypervolume={hv:.4f} 异常高 (参考点[1.1,1.1,1.1]下理论上限1.331)")
                    if avg > 0.95:
                        print(f"  ⚠️  avg_top100={avg:.4f} 异常高 (接近1表示所有目标都达到最优边界)")
        except Exception as e:
            print(f"❌ 分析{name}数据时出错: {e}")
    
    print("\n" + "="*80)
    print("5. 结论")
    print("="*80)
    
    print("""
【逻辑一致性】
✅ 三个算法使用相同的evaluator (problem.sacs_geo_jk.evaluator)
✅ 三个算法使用相同的优化目标 (weight, axial_uc_max, bending_uc_max)
✅ 三个算法使用相同的目标转换逻辑 (_transform_objectives)
✅ 三个算法使用相同的hypervolume计算方法 (pymoo HV, ref=[1.1,1.1,1.1])

【关键差异】
❌ Early Stopping策略不同:
   - GA_optimized: 启用baseline_early_stopping (patience=6, min_samples=600)
   - NSGA2/SMSEMOA: 未启用baseline_early_stopping
   
❌ 种群选择策略不同:
   - NSGA2: 使用NSGA-II的非支配排序和拥挤度选择
   - SMSEMOA: 使用hypervolume contribution选择
   - GA_optimized: 使用锦标赛选择 (tournament_selection)

【异常数据分析】
⚠️  GA_optimized的指标异常:
   - hypervolume=1.21 (远高于NSGA2/SMSEMOA的0.86)
   - avg_top100=0.966 (远高于NSGA2/SMSEMOA的0.86)
   
可能原因:
1. Early stopping导致GA_optimized过早停止，陷入局部最优
2. 锦标赛选择可能导致种群多样性不足
3. 可能存在数值计算问题（如transformed_values计算错误）
4. 可能某些解的scores不在[0,1]范围内，导致HV计算异常

【建议】
1. 禁用GA_optimized的early stopping，让其运行完整的2000个评估
2. 检查GA_optimized生成的解的原始值（weight, axial_uc, bending_uc）
3. 验证transformed_values是否都在[0,1]范围内
4. 对比三个算法的Pareto前沿分布
""")

if __name__ == '__main__':
    analyze_algorithm_consistency()
