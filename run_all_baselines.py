#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Batch Baseline Runner with Seed Reset (Multi-Problem Support)
批量运行所有baseline实验，支持四种SACS优化问题，每次运行前自动重置SACS初始种子文件

Usage:
    # Run all baselines for section_jk problem
    python run_all_baselines.py --problem section_jk
    
    # Run specific baselines for geo_jk problem
    python run_all_baselines.py --problem geo_jk --baselines ga nsga2
    
    # Run one baseline with multiple seeds for section_pf
    python run_all_baselines.py --problem section_pf --baselines ga --seeds 42 43 44
    
    # Run all problems with all baselines (WARNING: very long runtime)
    python run_all_baselines.py --problem all
    
    # Dry run (test without actually running)
    python run_all_baselines.py --problem geo_jk --dry-run
"""

import os
import sys
import shutil
import subprocess
import argparse
import time
from datetime import datetime
from pathlib import Path

# ==================== Configuration ====================

# SACS Problems Configuration
# 每个问题包含：种子备份路径、工作目录、目标文件名、配置文件路径
SACS_PROBLEMS = {
    'section_jk': {
        'name': 'Section Optimization (JK Model)',
        'seed_backup': r"D:\wsl_sacs_exchange\sacs_project\sacinp.demo06",
        'working_dir': r"D:\wsl_sacs_exchange\sacs_project\Demo06_Section",
        'target_file': "sacinp.demo06",
        'config_path': "problem/sacs_section_jk/config.yaml",
        'description': '截面优化（导管架模型，Demo06）'
    },
    'section_pf': {
        'name': 'Section Optimization (PF Model)',
        'seed_backup': r"D:\wsl_sacs_exchange\sacs_project\sacinp.demo13",
        'working_dir': r"D:\wsl_sacs_exchange\sacs_project\Demo13_Section",
        'target_file': "sacinp.demo13",
        'config_path': "problem/sacs_section_pf/config.yaml",
        'description': '截面优化（平台模型，Demo13）'
    },
    'geo_jk': {
        'name': 'Geometry Optimization (JK Model)',
        'seed_backup': r"D:\wsl_sacs_exchange\sacs_project\sacinp.demo06",
        'working_dir': r"D:\wsl_sacs_exchange\sacs_project\Demo06_Geo",
        'target_file': "sacinp.demo06",
        'config_path': "problem/sacs_geo_jk/config.yaml",
        'description': '几何优化（导管架模型，Demo06）'
    },
    'geo_pf': {
        'name': 'Geometry Optimization (PF Model)',
        'seed_backup': r"D:\wsl_sacs_exchange\sacs_project\sacinp.demo13",
        'working_dir': r"D:\wsl_sacs_exchange\sacs_project\Demo13_Geo",
        'target_file': "sacinp.demo13",
        'config_path': "problem/sacs_geo_pf/config.yaml",
        'description': '几何优化（平台模型，Demo13）'
    }
}

PROJECT_ROOT = Path(__file__).parent.absolute()

# Available baselines
BASELINES = {
    'ga': 'baseline_ga.py',
    'sms': 'baseline_sms.py',
    'nsga2': 'baseline_nsga2.py',
    'moead': 'baseline_moead.py',
    'rs': 'baseline_rs.py',
}

# Default random seeds
DEFAULT_SEEDS = [42]

# Log file
LOG_FILE = PROJECT_ROOT / "baseline_experiments.log"

# ==================== Helper Functions ====================

def log_message(msg, level="INFO"):
    """Write message to both console and log file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] [{level}] {msg}"
    print(formatted_msg)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(formatted_msg + "\n")

def convert_to_wsl_path(windows_path):
    """Convert Windows path to WSL path"""
    # D:\folder\file -> /mnt/d/folder/file
    if ':' in windows_path:
        drive = windows_path[0].lower()
        path = windows_path[2:].replace('\\', '/')
        return f"/mnt/{drive}{path}"
    return windows_path

def reset_sacs_seed(problem_key):
    """Reset SACS seed file from backup for specified problem"""
    try:
        if problem_key not in SACS_PROBLEMS:
            log_message(f"ERROR: Unknown problem '{problem_key}'", "ERROR")
            return False
        
        problem = SACS_PROBLEMS[problem_key]
        
        # Convert paths to WSL format
        source = convert_to_wsl_path(problem['seed_backup'])
        target_dir = convert_to_wsl_path(problem['working_dir'])
        target = f"{target_dir}/{problem['target_file']}"
        
        log_message(f"Resetting SACS seed file for {problem['name']}...")
        log_message(f"  Source: {source}")
        log_message(f"  Target: {target}")
        
        # Check if source exists
        if not os.path.exists(source):
            log_message(f"ERROR: Source seed file not found: {source}", "ERROR")
            return False
        
        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)
        
        # Copy file
        shutil.copy2(source, target)
        log_message(f"✓ SACS seed file reset successfully", "SUCCESS")
        return True
        
    except Exception as e:
        log_message(f"ERROR: Failed to reset SACS seed file: {e}", "ERROR")
        return False

def run_baseline(baseline_name, problem_key, seed, dry_run=False, skip_reset=False):
    """Run a single baseline experiment for specified problem"""
    if baseline_name not in BASELINES:
        log_message(f"ERROR: Unknown baseline '{baseline_name}'", "ERROR")
        return False
    
    if problem_key not in SACS_PROBLEMS:
        log_message(f"ERROR: Unknown problem '{problem_key}'", "ERROR")
        return False
    
    script = BASELINES[baseline_name]
    script_path = PROJECT_ROOT / script
    problem = SACS_PROBLEMS[problem_key]
    config_path = problem['config_path']
    
    if not script_path.exists():
        log_message(f"ERROR: Baseline script not found: {script_path}", "ERROR")
        return False
    
    log_message(f"="*80)
    log_message(f"Starting: {baseline_name.upper()} | {problem['name']} (seed={seed})")
    log_message(f"Script: {script}")
    log_message(f"Config: {config_path}")
    log_message(f"="*80)
    
    if dry_run:
        log_message(f"[DRY RUN] Would execute: python {script} {config_path} --seed {seed}", "DRY_RUN")
        time.sleep(1)  # Simulate some work
        return True
    
    # Reset seed file before each run (unless skipped)
    if not skip_reset:
        if not reset_sacs_seed(problem_key):
            log_message(f"ERROR: Failed to reset seed file, skipping {baseline_name}", "ERROR")
            return False
    
    # Run the baseline
    cmd = [sys.executable, str(script_path), config_path, "--seed", str(seed)]
    log_message(f"Executing: {' '.join(cmd)}")
    
    start_time = time.time()
    
    # Create output log file with problem identifier
    output_log = PROJECT_ROOT / f"logs/{problem_key}_{baseline_name}_seed{seed}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    output_log.parent.mkdir(exist_ok=True)
    
    try:
        # Use Popen for real-time output
        process = subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1  # Line buffered
        )
        
        # Stream output to both console and log file
        with open(output_log, 'w', encoding='utf-8') as f:
            for line in process.stdout:
                print(line, end='')  # Real-time console output
                f.write(line)        # Save to log file
                f.flush()            # Force write to disk
        
        # Wait for process to complete
        return_code = process.wait()
        elapsed = time.time() - start_time
        
        if return_code == 0:
            log_message(f"✓ {baseline_name.upper()} completed successfully in {elapsed/3600:.2f} hours", "SUCCESS")
            log_message(f"  Output saved to: {output_log}")
            return True
        else:
            log_message(f"✗ {baseline_name.upper()} failed with return code {return_code}", "ERROR")
            log_message(f"  Check log for details: {output_log}")
            return False
            
    except Exception as e:
        elapsed = time.time() - start_time
        log_message(f"✗ Exception occurred: {e}", "ERROR")
        log_message(f"  Runtime before error: {elapsed/3600:.2f} hours")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Batch runner for SACS baseline experiments (Multi-Problem Support)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all baselines for section_jk problem
  python run_all_baselines.py --problem section_jk
  
  # Run specific baselines for geo_jk problem
  python run_all_baselines.py --problem geo_jk --baselines ga sms
  
  # Run GA with multiple seeds for section_pf
  python run_all_baselines.py --problem section_pf --baselines ga --seeds 42 43 44
  
  # Run all problems with all baselines (WARNING: very long runtime)
  python run_all_baselines.py --problem all
  
  # Test without actually running
  python run_all_baselines.py --problem geo_jk --dry-run
        """
    )
    
    parser.add_argument(
        '--problem',
        choices=list(SACS_PROBLEMS.keys()) + ['all'],
        required=True,
        help='Which SACS problem to run (section_jk, section_pf, geo_jk, geo_pf, or all)'
    )
    
    parser.add_argument(
        '--baselines',
        nargs='+',
        choices=list(BASELINES.keys()) + ['all'],
        default=['all'],
        help='Which baselines to run (default: all)'
    )
    
    parser.add_argument(
        '--seeds',
        nargs='+',
        type=int,
        default=DEFAULT_SEEDS,
        help=f'Random seeds to use (default: {DEFAULT_SEEDS})'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test run without actually executing experiments'
    )
    
    parser.add_argument(
        '--skip-reset',
        action='store_true',
        help='Skip SACS seed file reset (use existing state)'
    )
    
    args = parser.parse_args()
    
    # Determine which problems to run
    if args.problem == 'all':
        problems_to_run = list(SACS_PROBLEMS.keys())
    else:
        problems_to_run = [args.problem]
    
    # Determine which baselines to run
    if 'all' in args.baselines:
        baselines_to_run = list(BASELINES.keys())
    else:
        baselines_to_run = args.baselines
    
    # Print configuration
    log_message("="*80)
    log_message("SACS Baseline Experiment Batch Runner (Multi-Problem)")
    log_message("="*80)
    log_message(f"Problems: {', '.join(problems_to_run)}")
    for prob in problems_to_run:
        log_message(f"  - {prob}: {SACS_PROBLEMS[prob]['description']}")
    log_message(f"Baselines: {', '.join(baselines_to_run)}")
    log_message(f"Seeds: {args.seeds}")
    log_message(f"Dry run: {args.dry_run}")
    log_message(f"Skip seed reset: {args.skip_reset}")
    log_message(f"Log file: {LOG_FILE}")
    log_message("="*80)
    
    # Calculate total experiments
    total_experiments = len(problems_to_run) * len(baselines_to_run) * len(args.seeds)
    log_message(f"Total experiments to run: {total_experiments}")
    
    if not args.dry_run:
        response = input("\nProceed? [y/N]: ")
        if response.lower() != 'y':
            log_message("Aborted by user")
            return
    
    # Run experiments
    start_time = time.time()
    results = []
    
    for problem in problems_to_run:
        log_message(f"\n{'='*80}")
        log_message(f"Starting experiments for problem: {SACS_PROBLEMS[problem]['name']}")
        log_message(f"{'='*80}\n")
        
        for baseline in baselines_to_run:
            for seed in args.seeds:
                success = run_baseline(
                    baseline, 
                    problem, 
                    seed, 
                    dry_run=args.dry_run,
                    skip_reset=args.skip_reset
                )
                results.append((problem, baseline, seed, success))
                
                # Brief pause between experiments
                if not args.dry_run:
                    time.sleep(5)
    
    # Summary
    total_time = time.time() - start_time
    log_message("="*80)
    log_message("EXPERIMENT SUMMARY")
    log_message("="*80)
    
    success_count = sum(1 for _, _, _, success in results if success)
    fail_count = len(results) - success_count
    
    log_message(f"Total experiments: {len(results)}")
    log_message(f"Successful: {success_count}")
    log_message(f"Failed: {fail_count}")
    log_message(f"Total time: {total_time/3600:.2f} hours")
    log_message("="*80)
    
    # Detailed results
    log_message("\nDetailed Results:")
    for problem, baseline, seed, success in results:
        status = "✓" if success else "✗"
        log_message(f"  {status} {problem} | {baseline.upper()} (seed={seed})")
    
    log_message("="*80)
    log_message(f"All experiments completed. Check {LOG_FILE} for details.")
    
    sys.exit(0 if fail_count == 0 else 1)

if __name__ == "__main__":
    main()