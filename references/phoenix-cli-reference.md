# Phoenix Protocol CLI 工具集参考

## 概述

20个Python脚本，填补 `hermes fact-store` / `hermes cron runs` 等不存在的 CLI 空白。
路径：`~/.hermes/scripts/`
一键安装：`bash ~/.hermes/scripts/install_phoenix_fixes.sh`
同步到IA：`python3 ~/.hermes/scripts/phoenix_collab.py sync-scripts`

## 工具列表

### 基础工具（2个）

| 脚本 | 功能 | 用法 |
|------|------|------|
| `fact_store_cli.py` | 命令行访问 fact_store | `stats / list [limit] / search <query> / add <content> [--category CAT] [--tags TAGS] / remove <fact_id>` |
| `cron_history_cli.py` | Cron 运行历史 | `stats [job_id] / list [job_id] [--limit N] / add <job_id> <status> [--duration S] [--error MSG] / failures [job_id]` |

### 诊断工具（3个）

| 脚本 | 功能 | 用法 |
|------|------|------|
| `phoenix_diagnose.py` | 系统健康检查 | `health / diagnose <symptom> / check-cron / check-memory / check-skills` |
| `phoenix_ai_diagnose.py` | AI辅助诊断 | `analyze-logs [days] / analyze-cron / analyze-memory / suggest-fix` |
| `phoenix_advanced_diagnose.py` | 增强诊断 | `network / performance / security / dependency / full` |

### 修复工具（3个）

| 脚本 | 功能 | 用法 |
|------|------|------|
| `phoenix_rollback.py` | 修复备份回滚 | `backup <file> / restore <file> / list / rollback <backup_id>` |
| `phoenix_auto_rollback.py` | 自动回滚触发 | `monitor / auto-rollback <file> / check-health` |
| `phoenix_remote.py` | 远程修复 | `diagnose [host] / repair [host] / sync-all [host] / status [host]` |

### 评估工具（3个）

| 脚本 | 功能 | 用法 |
|------|------|------|
| `phoenix_evaluate.py` | 修复效果评估 | `test <test_name> / evaluate <repair_id> / list-tests` |
| `phoenix_enhanced_eval.py` | 增强评估（21测试） | `test-all / test-category <cat> / list-categories / report` |
| `phoenix_benchmark.py` | 性能基准测试 | `run / test <test_name> / list / compare` |

### 学习工具（3个）

| 脚本 | 功能 | 用法 |
|------|------|------|
| `phoenix_lesson_graph.py` | 教训知识图谱 | `add <lesson> [--category CAT] [--severity SEV] / list / show <id> / relate <id1> <id2> / search <query>` |
| `phoenix_auto_lesson.py` | 自动提取教训 | `extract-logs / extract-cron / extract-memory / auto-extract` |
| `phoenix_lesson_analysis.py` | 教训关联分析 | `analyze / cluster / root-cause / recommend` |

### 预防工具（3个）

| 脚本 | 功能 | 用法 |
|------|------|------|
| `phoenix_preventive.py` | 预防性维护 | `predict / analyze / recommend` |
| `phoenix_scheduled.py` | 定时预测 | `run / schedule / report` |
| `phoenix_scheduler.py` | 智能调度 | `schedule / add <task> <cron> / remove <task_id> / run <task_id> / status` |

### 协同工具（2个）

| 脚本 | 功能 | 用法 |
|------|------|------|
| `phoenix_collab.py` | 多Agent协同 | `sync-scripts / sync-skills / remote-diagnose [host] / remote-repair [host]` |
| `phoenix_task_distributor.py` | 任务分发 | `distribute <task> / status / collect / list` |

### 版本管理工具（1个）

| 脚本 | 功能 | 用法 |
|------|------|------|
| `phoenix_version.py` | 文件版本管理 | `commit <file> [msg] / history <file> / diff <file> [ver] / restore <file> [ver] / tag <file> <tag>` |

## 常用命令

```bash
# 系统健康检查
python3 ~/.hermes/scripts/phoenix_diagnose.py health

# 生成修复建议
python3 ~/.hermes/scripts/phoenix_ai_diagnose.py suggest-fix

# 运行所有测试
python3 ~/.hermes/scripts/phoenix_enhanced_eval.py test-all

# 性能基准测试
python3 ~/.hermes/scripts/phoenix_benchmark.py run

# 预测潜在故障
python3 ~/.hermes/scripts/phoenix_preventive.py predict

# 全面诊断（网络/性能/安全/依赖）
python3 ~/.hermes/scripts/phoenix_advanced_diagnose.py full

# 版本管理
python3 ~/.hermes/scripts/phoenix_version.py commit ~/.hermes/memories/MEMORY.md "备份"
python3 ~/.hermes/scripts/phoenix_version.py history ~/.hermes/memories/MEMORY.md

# 教训关联分析
python3 ~/.hermes/scripts/phoenix_lesson_analysis.py analyze

# 智能调度
python3 ~/.hermes/scripts/phoenix_scheduler.py status

# 任务分发到IA
python3 ~/.hermes/scripts/phoenix_task_distributor.py distribute health_check

# 同步到IA
python3 ~/.hermes/scripts/phoenix_collab.py sync-scripts

# 远程诊断
python3 ~/.hermes/scripts/phoenix_remote.py diagnose 192.168.3.88
```

## 数据库

| 数据库 | 路径 | 用途 |
|--------|------|------|
| `memory_store.db` | `~/.hermes/memory_store.db` | fact_store（127条fact） |
| `cron_history.db` | `~/.hermes/cron_history.db` | Cron运行历史 |
| `phoenix_eval.db` | `~/.hermes/phoenix_eval.db` | 评估结果 |
| `phoenix_lessons.db` | `~/.hermes/phoenix_lessons.db` | 教训知识图谱 |
| `phoenix_predictions.db` | `~/.hermes/phoenix_predictions.db` | 预测记录 |
| `phoenix_benchmark.db` | `~/.hermes/phoenix_benchmark.db` | 性能基准数据 |
| `phoenix_scheduler.db` | `~/.hermes/phoenix_scheduler.db` | 调度任务 |
| `phoenix_tasks.db` | `~/.hermes/phoenix_tasks.db` | 分发任务 |

## 与 Hermes CLI 的关系

| Hermes CLI | 状态 | Phoenix CLI 替代 |
|------------|------|-----------------|
| `hermes fact-store` | ❌ 不存在 | `fact_store_cli.py` |
| `hermes cron runs/history` | ❌ 不存在 | `cron_history_cli.py` |
| `hermes cron list` | ✅ 可用 | 无替代 |
| `hermes cron edit` | ✅ 可用 | 无替代 |
| `hermes cron run` | ✅ 可用 | 无替代 |
