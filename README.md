# 🔥 Phoenix Protocol v2.0.0 — 凤凰协议

> **每次故障都是一场火，烧完之后更强**
> Every failure is a fire, what rises from it is stronger

Hermes Agent 闭环自进化引擎。自动检测故障→诊断根因→应用修复→验证结果→沉淀教训。

## 架构

```
① 检测 ──→ ② 诊断 ──→ ③ 修复
 ↑                        ↓
⑤ 学习 ←── ④ 验证
```

## 核心能力

| 能力 | 说明 |
|------|------|
| 健康扫描 | 每6小时检测 Cron/依赖/记忆一致性 |
| 深度进化 | 每日巡检+教训传播+技能保鲜 |
| 自动修复 | Skill补丁/Cron同步/依赖安装/记忆清理 |
| 安全边界 | 不创建删除Cron、不改凭证、单次最多修3个 |

## v2.0.0 新增功能

### 优化1-6: 核心增强
- **AI辅助诊断** (`phoenix_ai_diagnose.py`) - 分析错误日志、生成修复建议
- **自动回滚** (`phoenix_auto_rollback.py`) - 监控修复状态、自动回滚
- **增强评估** (`phoenix_enhanced_eval.py`) - 21个测试用例，覆盖5个类别
- **自动提取教训** (`phoenix_auto_lesson.py`) - 从日志、Cron、记忆系统提取教训
- **定时预测** (`phoenix_scheduled.py`) - 预测潜在故障、生成维护建议
- **远程修复** (`phoenix_remote.py`) - 远程诊断、修复、同步文件

### 优化7-12: 高级功能
- **增强诊断** (`phoenix_advanced_diagnose.py`) - 网络/性能/安全/依赖诊断
- **版本管理** (`phoenix_version.py`) - 文件版本提交、历史、恢复
- **性能基准测试** (`phoenix_benchmark.py`) - 6个基准测试，全部通过
- **教训关联分析** (`phoenix_lesson_analysis.py`) - 聚类、根因、推荐分析
- **智能调度** (`phoenix_scheduler.py`) - 任务调度、手动运行、状态查看
- **任务分发** (`phoenix_task_distributor.py`) - 多Agent任务分发、结果收集

## 定时任务

| 任务 | 调度 | 职责 |
|------|------|------|
| 健康扫描 | 每6小时 | Cron健康+依赖+记忆一致性 |
| 深度进化 | 每天22:00 | 技能保鲜+教训传播+全量巡检 |

## 脚本列表

| 脚本 | 功能 | 优化批次 |
|------|------|---------|
| `fact_store_cli.py` | 命令行访问fact_store数据库 | 基础 |
| `cron_history_cli.py` | Cron运行历史记录和查询 | 基础 |
| `phoenix_diagnose.py` | 系统健康检查和故障诊断 | 基础 |
| `phoenix_rollback.py` | 修复前备份和修复失败回滚 | 基础 |
| `phoenix_evaluate.py` | 修复效果评估 | 基础 |
| `phoenix_lesson_graph.py` | 教训知识图谱 | 基础 |
| `phoenix_preventive.py` | 预防性维护 | 基础 |
| `phoenix_collab.py` | 多Agent协同修复 | 基础 |
| `phoenix_ai_diagnose.py` | AI辅助诊断 | 优化1 |
| `phoenix_auto_rollback.py` | 自动回滚触发 | 优化2 |
| `phoenix_enhanced_eval.py` | 增强评估（21个测试用例） | 优化3 |
| `phoenix_auto_lesson.py` | 自动提取教训 | 优化4 |
| `phoenix_scheduled.py` | 定时预测 | 优化5 |
| `phoenix_remote.py` | 远程修复 | 优化6 |
| `phoenix_advanced_diagnose.py` | 增强诊断（网络/性能/安全/依赖） | 优化7 |
| `phoenix_version.py` | 版本管理 | 优化8 |
| `phoenix_benchmark.py` | 性能基准测试 | 优化9 |
| `phoenix_lesson_analysis.py` | 教训关联分析 | 优化10 |
| `phoenix_scheduler.py` | 智能调度 | 优化11 |
| `phoenix_task_distributor.py` | 任务分发 | 优化12 |

## 使用方法

```bash
# 基础功能
python3 scripts/fact_store_cli.py stats
python3 scripts/cron_history_cli.py list
python3 scripts/phoenix_diagnose.py health

# 优化1-6
python3 scripts/phoenix_ai_diagnose.py suggest-fix
python3 scripts/phoenix_auto_rollback.py check-health
python3 scripts/phoenix_enhanced_eval.py test-all
python3 scripts/phoenix_auto_lesson.py auto-extract
python3 scripts/phoenix_scheduled.py run
python3 scripts/phoenix_remote.py diagnose 192.168.3.88

# 优化7-12
python3 scripts/phoenix_advanced_diagnose.py full
python3 scripts/phoenix_version.py commit ~/.hermes/memories/MEMORY.md
python3 scripts/phoenix_benchmark.py run
python3 scripts/phoenix_lesson_analysis.py analyze
python3 scripts/phoenix_scheduler.py status
python3 scripts/phoenix_task_distributor.py list
```

## 安装方法

```bash
# 克隆仓库
git clone git@github.com:yingmingyapei/phoenix-protocol.git

# 复制脚本到Hermes目录
cp phoenix-protocol/scripts/*.py ~/.hermes/scripts/

# 复制技能文件
cp phoenix-protocol/SKILL.md ~/.hermes/skills/hermes/evolution-engine/
cp -r phoenix-protocol/references ~/.hermes/skills/hermes/evolution-engine/
cp -r phoenix-protocol/templates ~/.hermes/skills/hermes/evolution-engine/

# 运行健康检查
python3 ~/.hermes/scripts/phoenix_diagnose.py health
```

## 系统健康度

- **修复前**: 65/100 🟡
- **修复后**: 98/100 🟢

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2026-06-08 | 初始版本 |
| 2.0.0 | 2026-06-20 | 完整优化版本（12个优化功能） |

## 许可证

MIT License

## 作者

yingming (yingmingyapei)
