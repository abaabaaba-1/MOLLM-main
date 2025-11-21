# 测试运行（不实际执行）
python run_all_baselines.py --dry-run

# 运行所有baseline，使用默认seed=42
python run_all_baselines.py

# 运行特定的baseline
python run_all_baselines.py --baselines ga sms nsga2

# 运行GA的多个seed
python run_all_baselines.py --baselines ga --seeds 42 43 44 45 46

# 运行所有baseline，每个5个不同的seed
python run_all_baselines.py --seeds 42 43 44 45 46