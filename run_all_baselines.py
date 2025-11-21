#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Batch Baseline Runner with Seed Reset
批量运行所有baseline实验，每次运行前自动重置SACS初始种子文件

Usage:
    # Run all baselines with default seeds
    python run_all_baselines.py
    
    # Run specific baselines
    python run_all_baselines.py --baselines ga nsga2 sms
    
    # Run one baseline with multiple seeds
    python run_all_baselines.py --baselines ga --seeds 42 43 44 45 46
    
    # Dry run (test without actually running)
    python run_all_baselines.py --dry-run
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

# SACS seed file paths (Windows paths for WSL)
SACS_SEED_BACKUP = r"D:\wsl_sacs_exchange\sacs_project\sacinp.demo06"
SACS_WORKING_DIR = r"D:\wsl_sacs_exchange\sacs_project\Demo06_Section"
SACS_TARGET_FILE = "sacinp.demo06"  # filename in working directory

# Project configuration
CONFIG_PATH = "problem/sacs_section_jk/config.yaml"
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

def reset_sacs_seed():
    """Reset SACS seed file from backup"""
    try:
        # Convert paths to WSL format
        source = convert_to_wsl_path(SACS_SEED_BACKUP)
        target_dir = convert_to_wsl_path(SACS_WORKING_DIR)
        target = f"{target_dir}/{SACS_TARGET_FILE}"
        
        log_message(f"Resetting SACS seed file...")
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

def run_baseline(baseline_name, seed, dry_run=False):
    """Run a single baseline experiment"""
    if baseline_name not in BASELINES:
        log_message(f"ERROR: Unknown baseline '{baseline_name}'", "ERROR")
        return False
    
    script = BASELINES[baseline_name]
    script_path = PROJECT_ROOT / script
    
    if not script_path.exists():
        log_message(f"ERROR: Baseline script not found: {script_path}", "ERROR")
        return False
    
    log_message(f"="*80)
    log_message(f"Starting: {baseline_name.upper()} (seed={seed})")
    log_message(f"Script: {script}")
    log_message(f"="*80)
    
    if dry_run:
        log_message(f"[DRY RUN] Would execute: python {script} {CONFIG_PATH} --seed {seed}", "DRY_RUN")
        time.sleep(1)  # Simulate some work
        return True
    
    # Reset seed file before each run
    if not reset_sacs_seed():
        log_message(f"ERROR: Failed to reset seed file, skipping {baseline_name}", "ERROR")
        return False
    
    # Run the baseline
    cmd = [sys.executable, str(script_path), CONFIG_PATH, "--seed", str(seed)]
    log_message(f"Executing: {' '.join(cmd)}")
    
    start_time = time.time()
    
    # Create output log file
    output_log = PROJECT_ROOT / f"logs/{baseline_name}_seed{seed}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
        description="Batch runner for SACS baseline experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all baselines with default seed
  python run_all_baselines.py
  
  # Run specific baselines
  python run_all_baselines.py --baselines ga sms
  
  # Run GA with multiple seeds
  python run_all_baselines.py --baselines ga --seeds 42 43 44 45 46
  
  # Test without actually running
  python run_all_baselines.py --dry-run
        """
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
    
    # Determine which baselines to run
    if 'all' in args.baselines:
        baselines_to_run = list(BASELINES.keys())
    else:
        baselines_to_run = args.baselines
    
    # Print configuration
    log_message("="*80)
    log_message("Baseline Experiment Batch Runner")
    log_message("="*80)
    log_message(f"Baselines: {', '.join(baselines_to_run)}")
    log_message(f"Seeds: {args.seeds}")
    log_message(f"Config: {CONFIG_PATH}")
    log_message(f"Dry run: {args.dry_run}")
    log_message(f"Skip seed reset: {args.skip_reset}")
    log_message(f"Log file: {LOG_FILE}")
    log_message("="*80)
    
    # Calculate total experiments
    total_experiments = len(baselines_to_run) * len(args.seeds)
    log_message(f"Total experiments to run: {total_experiments}")
    
    if not args.dry_run:
        response = input("\nProceed? [y/N]: ")
        if response.lower() != 'y':
            log_message("Aborted by user")
            return
    
    # Run experiments
    start_time = time.time()
    results = []
    
    for baseline in baselines_to_run:
        for seed in args.seeds:
            success = run_baseline(baseline, seed, dry_run=args.dry_run)
            results.append((baseline, seed, success))
            
            # Brief pause between experiments
            if not args.dry_run:
                time.sleep(5)
    
    # Summary
    total_time = time.time() - start_time
    log_message("="*80)
    log_message("EXPERIMENT SUMMARY")
    log_message("="*80)
    
    success_count = sum(1 for _, _, success in results if success)
    fail_count = len(results) - success_count
    
    log_message(f"Total experiments: {len(results)}")
    log_message(f"Successful: {success_count}")
    log_message(f"Failed: {fail_count}")
    log_message(f"Total time: {total_time/3600:.2f} hours")
    log_message("="*80)
    
    # Detailed results
    log_message("\nDetailed Results:")
    for baseline, seed, success in results:
        status = "✓" if success else "✗"
        log_message(f"  {status} {baseline.upper()} (seed={seed})")
    
    log_message("="*80)
    log_message(f"All experiments completed. Check {LOG_FILE} for details.")
    
    sys.exit(0 if fail_count == 0 else 1)

if __name__ == "__main__":
    main()