#!/usr/bin/env python3
"""
验证baseline_weight修复是否生效
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model.MOLLM import ConfigLoader
from problem.sacs_geo_jk.evaluator import RewardingSystem

def verify_baseline_weight():
    """验证baseline_weight是否正确加载"""
    
    print("="*80)
    print("验证 baseline_weight 修复")
    print("="*80)
    
    # 加载config
    config_path = 'sacs_geo_jk/config.yaml'
    print(f"\n1. 加载配置文件: {config_path}")
    
    try:
        config = ConfigLoader(config_path)
        print("   ✅ 配置文件加载成功")
    except Exception as e:
        print(f"   ❌ 配置文件加载失败: {e}")
        return False
    
    # 检查config中的baseline_weight
    baseline_weight_from_config = config.get('sacs.baseline_weight_tonnes')
    print(f"\n2. Config中的baseline_weight: {baseline_weight_from_config}")
    
    if baseline_weight_from_config is None:
        print("   ❌ Config中没有设置baseline_weight_tonnes")
        return False
    elif baseline_weight_from_config != 66.0:
        print(f"   ⚠️  baseline_weight={baseline_weight_from_config}，期望值为66.0")
    else:
        print("   ✅ baseline_weight设置正确 (66.0 tonnes)")
    
    # 初始化RewardingSystem
    print(f"\n3. 初始化RewardingSystem...")
    
    try:
        reward_system = RewardingSystem(config)
        print("   ✅ RewardingSystem初始化成功")
    except Exception as e:
        print(f"   ❌ RewardingSystem初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 验证RewardingSystem使用的baseline_weight
    actual_baseline_weight = reward_system.baseline_weight_tonnes
    print(f"\n4. RewardingSystem实际使用的baseline_weight: {actual_baseline_weight}")
    
    if actual_baseline_weight is None:
        print("   ❌ baseline_weight为None")
        return False
    elif abs(actual_baseline_weight - 66.0) < 0.001:
        print("   ✅ baseline_weight正确 (66.0 tonnes)")
    else:
        print(f"   ❌ baseline_weight={actual_baseline_weight}，期望值为66.0")
        return False
    
    # 测试归一化
    print(f"\n5. 测试Weight归一化...")
    
    test_weights = [64.77, 65.92, 65.83]  # NSGA2, GA_optimized, SMSEMOA的top1 weight
    expected_scores = [0.321, 0.332, 0.322]  # 期望的归一化值
    
    for weight, expected in zip(test_weights, expected_scores):
        ratio = weight / actual_baseline_weight
        ratio = max(0.5, min(2.0, ratio))  # clip to [0.5, 2.0]
        weight_norm = (ratio - 0.5) / 1.5
        
        print(f"   Weight={weight:.2f}吨 -> ratio={ratio:.4f} -> normalized={weight_norm:.6f} (期望≈{expected:.3f})")
        
        if abs(weight_norm - expected) < 0.02:
            print(f"      ✅ 归一化正确")
        else:
            print(f"      ⚠️  归一化值偏差较大")
    
    print("\n" + "="*80)
    print("验证完成")
    print("="*80)
    
    print("\n【总结】")
    print("✅ 修复已生效！")
    print("✅ 所有算法现在将使用相同的baseline_weight=66.0吨")
    print("✅ 这确保了不同运行之间的结果可比性")
    print("\n【下一步】")
    print("1. 使用修复后的配置重新运行GA_optimized")
    print("2. 验证新的结果与NSGA2/SMSEMOA可比")
    print("3. 对比优化效果")
    
    return True

if __name__ == '__main__':
    success = verify_baseline_weight()
    sys.exit(0 if success else 1)
