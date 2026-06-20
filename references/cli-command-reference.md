# Hermes CLI 命令参考（健康扫描上下文）

> 基于 2026-06-10 实际验证。CLI 版本可能更新，定期验证。

## hermes cron

可用子命令：
```
list      列出所有 job（含 last_run 状态）
create    创建新 job
add       同 create
edit      修改已有 job
pause     暂停 job
resume    恢复 job
run       手动触发 job
remove    删除 job
rm        同 remove
delete    同 remove
status    无参数，显示 cron 系统状态
tick      立即触发一次 cron tick
```

### hermes cron list 输出格式
```
┌────────────────────────────────────────────────────────┐
│                    Scheduled Jobs                       │
└────────────────────────────────────────────────────────┘

  <job_id> [active]
    Name:      <name>
    Schedule:  <cron_expr or interval>
    Repeat:    ∞
    Next run:  <ISO datetime>
    Deliver:   <destination>
    Script:    <script_name>      # 仅 no-agent mode
    Mode:      no-agent           # 仅 script job
    Skills:    <skill1, skill2>   # 仅 agent job
    Last run:  <ISO datetime>  ok/error: <message>
```

### 限制
- ❌ 无 `runs` / `history` 子命令 → 无法查看运行历史
- ❌ `status` 不接受 job_id 参数 → 无法查单个 job 状态
- `list` 仅显示 last_run，无法判断连续失败次数

### 替代方案：用 logs 推断
```bash
hermes logs errors --since "3d" | grep -i "<job_id or keyword>"
hermes logs agent -n 500 --since "2d" | grep -i "<keyword>"
```
注意：`--since` 格式为 `1h`, `30m`, `2d`，不接受 ISO 日期。

## hermes memory

可用子命令：
```
setup     交互式选择外部 memory provider
status    显示当前 memory provider 配置
off       禁用外部 provider（仅保留 built-in）
reset     清空 built-in memory（MEMORY.md + USER.md）
```

### 限制
- ❌ 无 `fact-store` / `fact` 命令
- ❌ 无 `contradict` / `search` / `add` / `remove` 操作
- 外部 provider 支持：honcho, openviking, mem0, hindsight, holographic, retaindb, byterover
- Built-in memory：MEMORY.md / USER.md（文件系统）

### 2026-06-20 更新：CLI 空白已填补

上述 `hermes fact-store` 和 `hermes cron runs/history` 的空白已通过自定义脚本填补：
- `~/.hermes/scripts/fact_store_cli.py` — 替代 `hermes fact-store`
- `~/.hermes/scripts/cron_history_cli.py` — 替代 `hermes cron runs/history`

详见 [phoenix-cli-reference.md](phoenix-cli-reference.md)。

### 记忆数据库
- SQLite 文件：`~/.hermes/memory_store.db`
- WAL 文件：`~/.hermes/memory_store.db-wal`, `~/.hermes/memory_store.db-shm`
- ~~无 CLI 工具直接查询，需 python3 + sqlite3 模块~~ → 现有 `fact_store_cli.py`

## hermes logs

```bash
hermes logs [log_name]           # 默认 agent.log
hermes logs errors               # errors.log
hermes logs gateway              # gateway.log
hermes logs list                 # 列出所有可用 log 文件
hermes logs -n <N>               # 最近 N 行
hermes logs --since "<time>"     # 如 1h, 30m, 2d
hermes logs --level <LEVEL>      # 过滤日志级别
hermes logs --component <NAME>   # 过滤组件
hermes logs --session <ID>       # 过滤 session
hermes logs -f                   # 实时跟踪
```

### 日志文件位置
`~/.hermes/logs/` 下：
- agent.log — agent 主日志
- errors.log — 错误和警告
- gateway.log — gateway 运行日志
- mcp-stderr.log — MCP server stderr
- update.log — 更新日志
