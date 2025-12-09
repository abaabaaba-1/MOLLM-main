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


python main.py sacs_section_jk/config.yaml --seed 43

# 1️⃣ 测试运行（1分钟）
python run_all_baselines.py --problem geo_jk --baselines ga --dry-run

# 2️⃣ 单个baseline（2-3小时）
python run_all_baselines.py --problem geo_jk --baselines ga

# 3️⃣ 对比多个算法（6-9小时）
python run_all_baselines.py --problem geo_jk --baselines ga nsga2 sms

# 4️⃣ 所有baseline（10-15小时）
python run_all_baselines.py --problem geo_jk

# 5️⃣ 多随机种子统计（50-75小时）
python run_all_baselines.py --problem geo_jk --seeds 42 43 44 45 46