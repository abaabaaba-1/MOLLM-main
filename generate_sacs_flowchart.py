#!/usr/bin/env python3
"""
生成 SACS 优化项目的流程图
用于论文中的流程图绘制
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, ConnectionPatch
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_sacs_flowchart():
    """创建 SACS 优化流程图"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 20))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 25)
    ax.axis('off')
    
    # 定义颜色
    color_start = '#90EE90'  # 浅绿色 - 开始
    color_process = '#87CEEB'  # 天蓝色 - 处理
    color_decision = '#FFD700'  # 金色 - 决策
    color_eval = '#FFA500'  # 橙色 - 评估
    color_output = '#98FB98'  # 浅绿色 - 输出
    color_end = '#FF6347'  # 番茄红 - 结束
    
    # 定义框的样式
    box_style = dict(boxstyle="round,pad=0.5", edgecolor='black', linewidth=1.5)
    
    # 1. 开始
    start_box = FancyBboxPatch((4, 23.5), 2, 0.8, facecolor=color_start, **box_style)
    ax.add_patch(start_box)
    ax.text(5, 24, 'Start', ha='center', va='center', fontsize=12, weight='bold')
    
    # 2. 加载配置和初始化
    init_box = FancyBboxPatch((3, 21.5), 4, 1, facecolor=color_process, **box_style)
    ax.add_patch(init_box)
    ax.text(5, 22, 'Load Configuration\n(Config YAML)', ha='center', va='center', fontsize=10)
    
    # 3. 生成初始种群
    init_pop_box = FancyBboxPatch((3, 19.5), 4, 1, facecolor=color_process, **box_style)
    ax.add_patch(init_pop_box)
    ax.text(5, 20, 'Generate Initial Population\n(From SACS file or seeds)', ha='center', va='center', fontsize=10)
    
    # 4. 评估初始种群
    eval_init_box = FancyBboxPatch((3, 17.5), 4, 1, facecolor=color_eval, **box_style)
    ax.add_patch(eval_init_box)
    ax.text(5, 18, 'Evaluate Initial Population', ha='center', va='center', fontsize=10)
    
    # 5. 优化循环开始
    loop_start_box = FancyBboxPatch((3, 15.5), 4, 1, facecolor=color_decision, **box_style)
    ax.add_patch(loop_start_box)
    ax.text(5, 16, 'Optimization Loop\n(While budget > 0)', ha='center', va='center', fontsize=10)
    
    # 6. 选择父代
    select_box = FancyBboxPatch((0.5, 13), 3, 1, facecolor=color_process, **box_style)
    ax.add_patch(select_box)
    ax.text(2, 13.5, 'Select Parents\n(NSGA-II Selection)', ha='center', va='center', fontsize=9)
    
    # 7. LLM 生成新候选
    llm_box = FancyBboxPatch((3.5, 13), 3, 1, facecolor=color_process, **box_style)
    ax.add_patch(llm_box)
    ax.text(5, 13.5, 'LLM Generate\n(Mutation/Crossover)', ha='center', va='center', fontsize=9)
    
    # 8. 解析 JSON
    parse_box = FancyBboxPatch((6.5, 13), 3, 1, facecolor=color_process, **box_style)
    ax.add_patch(parse_box)
    ax.text(8, 13.5, 'Parse Candidate\n(Extract code blocks)', ha='center', va='center', fontsize=9)
    
    # 9. 修改 SACS 文件
    modify_box = FancyBboxPatch((0.5, 10.5), 3, 1, facecolor=color_eval, **box_style)
    ax.add_patch(modify_box)
    ax.text(2, 11, 'Modify SACS File\n(Replace GRUP/PGRUP)', ha='center', va='center', fontsize=9)
    
    # 10. 运行 SACS 分析
    run_box = FancyBboxPatch((3.5, 10.5), 3, 1, facecolor=color_eval, **box_style)
    ax.add_patch(run_box)
    ax.text(5, 11, 'Run SACS Analysis\n(WSL Environment)', ha='center', va='center', fontsize=9)
    
    # 11. 提取结果
    extract_box = FancyBboxPatch((6.5, 10.5), 3, 1, facecolor=color_eval, **box_style)
    ax.add_patch(extract_box)
    ax.text(8, 11, 'Extract Results\n(Weight, UC values)', ha='center', va='center', fontsize=9)
    
    # 12. 计算目标值
    obj_box = FancyBboxPatch((3.5, 8.5), 3, 1, facecolor=color_eval, **box_style)
    ax.add_patch(obj_box)
    ax.text(5, 9, 'Calculate Objectives\n(Weight, Axial_UC, Bending_UC)', ha='center', va='center', fontsize=9)
    
    # 13. 更新种群
    update_box = FancyBboxPatch((3.5, 7), 3, 1, facecolor=color_process, **box_style)
    ax.add_patch(update_box)
    ax.text(5, 7.5, 'Update Population\n(NSGA-II)', ha='center', va='center', fontsize=9)
    
    # 14. 检查预算
    budget_box = FancyBboxPatch((3.5, 5.5), 3, 1, facecolor=color_decision, **box_style)
    ax.add_patch(budget_box)
    ax.text(5, 6, 'Budget > 0?', ha='center', va='center', fontsize=10, weight='bold')
    
    # 15. 输出结果
    output_box = FancyBboxPatch((3, 3.5), 4, 1, facecolor=color_output, **box_style)
    ax.add_patch(output_box)
    ax.text(5, 4, 'Save Results\n(PKL, JSON, Model Files)', ha='center', va='center', fontsize=10)
    
    # 16. 结束
    end_box = FancyBboxPatch((4, 1.5), 2, 0.8, facecolor=color_end, **box_style)
    ax.add_patch(end_box)
    ax.text(5, 2, 'End', ha='center', va='center', fontsize=12, weight='bold')
    
    # 绘制箭头
    arrows = [
        # 主流程箭头
        ((5, 23.5), (5, 22.5)),  # Start -> Load Config
        ((5, 21.5), (5, 20.5)),  # Load Config -> Init Pop
        ((5, 19.5), (5, 18.5)),  # Init Pop -> Eval Init
        ((5, 17.5), (5, 16.5)),  # Eval Init -> Loop Start
        ((5, 15.5), (5, 14)),    # Loop Start -> Select/LLM/Parse
        ((2, 13), (2, 11.5)),    # Select -> Modify
        ((5, 13), (5, 11.5)),   # LLM -> Run
        ((8, 13), (8, 11.5)),   # Parse -> Extract
        ((2, 10.5), (3.5, 9.5)), # Modify -> Calculate Obj
        ((5, 10.5), (5, 9.5)),   # Run -> Calculate Obj
        ((8, 10.5), (6.5, 9.5)), # Extract -> Calculate Obj
        ((5, 8.5), (5, 8)),      # Calculate Obj -> Update
        ((5, 7), (5, 6.5)),     # Update -> Budget Check
        ((5, 5.5), (5, 4.5)),    # Budget Check -> Output (Yes)
        ((5, 3.5), (5, 2.3)),    # Output -> End
    ]
    
    for (x1, y1), (x2, y2) in arrows:
        arrow = FancyArrowPatch((x1, y1), (x2, y2),
                               arrowstyle='->', lw=2, color='black',
                               connectionstyle="arc3,rad=0")
        ax.add_patch(arrow)
    
    # 循环箭头（预算未用完时返回）
    loop_arrow = FancyArrowPatch((2, 6), (2, 15),
                                 arrowstyle='->', lw=2, color='red',
                                 connectionstyle="arc3,rad=0.3", linestyle='--')
    ax.add_patch(loop_arrow)
    ax.text(1.5, 10.5, 'Continue', ha='center', va='center', fontsize=9, 
            color='red', rotation=90, weight='bold')
    
    # 添加标题
    ax.text(5, 24.8, 'SACS Multi-Objective Optimization Workflow', 
            ha='center', va='center', fontsize=16, weight='bold')
    
    # 添加图例
    legend_elements = [
        mpatches.Patch(facecolor=color_start, label='Start/End'),
        mpatches.Patch(facecolor=color_process, label='Process'),
        mpatches.Patch(facecolor=color_decision, label='Decision'),
        mpatches.Patch(facecolor=color_eval, label='Evaluation'),
        mpatches.Patch(facecolor=color_output, label='Output'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('sacs_optimization_flowchart.png', dpi=300, bbox_inches='tight')
    plt.savefig('sacs_optimization_flowchart.pdf', bbox_inches='tight')
    print("流程图已保存为:")
    print("  - sacs_optimization_flowchart.png (高分辨率)")
    print("  - sacs_optimization_flowchart.pdf (矢量图)")
    plt.close()

def create_detailed_evaluation_flowchart():
    """创建详细的评估流程图"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis('off')
    
    color_process = '#87CEEB'
    color_eval = '#FFA500'
    color_success = '#90EE90'
    color_fail = '#FF6347'
    
    box_style = dict(boxstyle="round,pad=0.5", edgecolor='black', linewidth=1.5)
    
    # 标题
    ax.text(5, 13.5, 'SACS Candidate Evaluation Process', 
            ha='center', va='center', fontsize=14, weight='bold')
    
    # 1. 接收候选
    start_box = FancyBboxPatch((3.5, 11.5), 3, 0.8, facecolor=color_process, **box_style)
    ax.add_patch(start_box)
    ax.text(5, 12, 'Receive Candidate\n(JSON string)', ha='center', va='center', fontsize=10)
    
    # 2. 解析 JSON
    parse_box = FancyBboxPatch((3.5, 10), 3, 0.8, facecolor=color_process, **box_style)
    ax.add_patch(parse_box)
    ax.text(5, 10.5, 'Parse JSON\n(Extract code blocks)', ha='center', va='center', fontsize=10)
    
    # 3. 过滤代码块
    filter_box = FancyBboxPatch((3.5, 8.5), 3, 0.8, facecolor=color_process, **box_style)
    ax.add_patch(filter_box)
    ax.text(5, 9, 'Filter Code Blocks\n(GRUP/PGRUP only)', ha='center', va='center', fontsize=10)
    
    # 4. 备份原文件
    backup_box = FancyBboxPatch((0.5, 7), 3, 0.8, facecolor=color_eval, **box_style)
    ax.add_patch(backup_box)
    ax.text(2, 7.5, 'Backup Original\nSACS File', ha='center', va='center', fontsize=9)
    
    # 5. 修改 SACS 文件
    modify_box = FancyBboxPatch((3.5, 7), 3, 0.8, facecolor=color_eval, **box_style)
    ax.add_patch(modify_box)
    ax.text(5, 7.5, 'Modify SACS File\n(Replace blocks)', ha='center', va='center', fontsize=9)
    
    # 6. 运行 SACS
    run_box = FancyBboxPatch((6.5, 7), 3, 0.8, facecolor=color_eval, **box_style)
    ax.add_patch(run_box)
    ax.text(8, 7.5, 'Run SACS Analysis\n(WSL)', ha='center', va='center', fontsize=9)
    
    # 7. 检查成功
    check_box = FancyBboxPatch((3.5, 5.5), 3, 0.8, facecolor='#FFD700', **box_style)
    ax.add_patch(check_box)
    ax.text(5, 6, 'Analysis\nSuccessful?', ha='center', va='center', fontsize=10, weight='bold')
    
    # 8. 提取重量
    weight_box = FancyBboxPatch((0.5, 4), 3, 0.8, facecolor=color_eval, **box_style)
    ax.add_patch(weight_box)
    ax.text(2, 4.5, 'Extract Weight\n(From DB)', ha='center', va='center', fontsize=9)
    
    # 9. 提取 UC
    uc_box = FancyBboxPatch((3.5, 4), 3, 0.8, facecolor=color_eval, **box_style)
    ax.add_patch(uc_box)
    ax.text(5, 4.5, 'Extract UC Values\n(From DB)', ha='center', va='center', fontsize=9)
    
    # 10. 计算目标
    obj_box = FancyBboxPatch((6.5, 4), 3, 0.8, facecolor=color_eval, **box_style)
    ax.add_patch(obj_box)
    ax.text(8, 4.5, 'Calculate Objectives\n(Weight, UC_max)', ha='center', va='center', fontsize=9)
    
    # 11. 成功输出
    success_box = FancyBboxPatch((3.5, 2.5), 3, 0.8, facecolor=color_success, **box_style)
    ax.add_patch(success_box)
    ax.text(5, 3, 'Return Results\n(Weight, Axial_UC, Bending_UC)', ha='center', va='center', fontsize=9)
    
    # 12. 失败输出
    fail_box = FancyBboxPatch((3.5, 1), 3, 0.8, facecolor=color_fail, **box_style)
    ax.add_patch(fail_box)
    ax.text(5, 1.5, 'Assign Penalty\n(Invalid/Failed)', ha='center', va='center', fontsize=9)
    
    # 绘制箭头
    arrows = [
        ((5, 11.5), (5, 10.8)),
        ((5, 10), (5, 9.3)),
        ((5, 8.5), (5, 7.8)),
        ((2, 7), (2, 4.8)),
        ((5, 7), (5, 6.3)),
        ((8, 7), (8, 4.8)),
        ((5, 5.5), (2, 4.8)),  # Success -> Weight
        ((5, 5.5), (5, 4.8)),  # Success -> UC
        ((5, 5.5), (8, 4.8)),  # Success -> Obj
        ((2, 4), (3.5, 3.3)),
        ((5, 4), (5, 3.3)),
        ((8, 4), (6.5, 3.3)),
        ((5, 5.5), (5, 1.8)),  # Fail -> Penalty
    ]
    
    for (x1, y1), (x2, y2) in arrows:
        arrow = FancyArrowPatch((x1, y1), (x2, y2),
                               arrowstyle='->', lw=1.5, color='black',
                               connectionstyle="arc3,rad=0")
        ax.add_patch(arrow)
    
    # 添加 Yes/No 标签
    ax.text(6.5, 6, 'Yes', ha='left', va='center', fontsize=9, weight='bold', color='green')
    ax.text(3, 6, 'No', ha='right', va='center', fontsize=9, weight='bold', color='red')
    
    plt.tight_layout()
    plt.savefig('sacs_evaluation_flowchart.png', dpi=300, bbox_inches='tight')
    plt.savefig('sacs_evaluation_flowchart.pdf', bbox_inches='tight')
    print("\n详细评估流程图已保存为:")
    print("  - sacs_evaluation_flowchart.png")
    print("  - sacs_evaluation_flowchart.pdf")
    plt.close()

if __name__ == '__main__':
    print("正在生成 SACS 优化流程图...")
    create_sacs_flowchart()
    print("\n正在生成详细评估流程图...")
    create_detailed_evaluation_flowchart()
    print("\n✅ 所有流程图生成完成！")

