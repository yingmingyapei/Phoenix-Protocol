---
name: evolution-engine
description: Phoenix Protocol 凤凰协议——闭环自进化引擎。自动检测故障→诊断根因→应用修复→验证结果→沉淀教训。每次故障都是一场火，烧完之后更强。
version: 1.0.0
author: yingming
tags: [evolution, self-healing, auto-repair, watchdog, closed-loop, hermes-core]
category: hermes
created: 2026-06-08
---

# Phoenix Protocol — 凤凰协议

```
    ╔═══════════════════════════════════════════════════════════╗
    ║            🔥  P H O E N I X   P R O T O C O L  🔥       ║
    ║                  ─── 凤 凰 协 议 ───                       ║
    ║                          .                                 ║
    ║                         /|\                                ║
    ║                        / | \                               ║
    ║                       /  |  \                              ║
    ║                      /   |   \                             ║
    ║                     🔥   🔥   🔥                           ║
    ║                      \   |   /                             ║
    ║                       \  |  /                              ║
    ║                        \ | /                               ║
    ║                         \|/                                ║
    ║                        .~.                                 ║
    ║                       /   \                                ║
    ║                      /     \                               ║
    ║                                                               ║
    ║          "每次故障都是一场火，烧完之后更强"                     ║
    ╚═══════════════════════════════════════════════════════════╝
```

## 触发条件

当用户说以下关键词时加载此技能：
- "凤凰协议" / "Phoenix Protocol"
- "自愈" / "自动修复" / "auto-repair"
- "健康检查" / "健康扫描" / "health check"
- "系统巡检" / "自动进化"

## 核心理念

**凤凰涅槃，浴火重生。每次故障都是一场火，烧完之后更强。**

传统模式：
```
故障 → 报错 → 人发现 → 人修复 → 人验证 → 费时费力
```

凤凰协议：
```
故障 → 🔥燃烧（检测+诊断）→ 🦅重生（修复+验证）→ 💎沉淀（学习）
 ↑                                                        │
 └────────── 教训反哺，同类故障不再发生 ────────────────────┘
```

## 五阶段闭环

### ① 检测 (Detect)

**检测什么**：

| 检测项 | 方法 | 频率 |
|--------|------|------|
| Cron 连续失败 | `cronjob list` → 检查 last_status | 每6小时 |
| Cron 超时率 | 统计 recent_runs 中 timeout 占比 | 每6小时 |
| Skills 过时 | 检查 SKILL.md 中的日期/版本/pitfalls | 每日 |
| 记忆矛盾 | `fact_store contradict` | 每日 |
| Hermes 版本 | `git log --oneline -1` vs upstream | 每日 |
| 依赖完整性 | numpy/uv 关键包检查 | 每日 |

**检测输出格式**：
```json
{
  "timestamp": "2026-06-08T14:00:00",
  "health_score": 85,
  "issues": [
    {
      "id": "CRON-001",
      "type": "cron_consecutive_failure",
      "severity": "high",
      "target": "75b38298aa5e",
      "detail": "热点刀锋连续失败3次",
      "auto_fixable": true
    }
  ]
}
```

### ② 诊断 (Diagnose)

**诊断流程**：
1. 搜索 `fact_store(action='search', query='故障关键词')` → 查找已知解法
2. 分析错误信息 → 提取根因关键词
3. 判断置信度：
   - **高** (>0.8)：fact_store 有精确匹配的已知解法 → 可自动修复
   - **中** (0.5-0.8)：有相关线索但不确定 → 生成修复方案，人工确认
   - **低** (<0.5)：无已知解法 → 记录问题，人工处理

**置信度评分规则**：
```
基础分 = fact_store 最高匹配分
+ 0.1 如果有历史修复记录
+ 0.1 如果修复方案涉及 skill patch（非破坏性）
- 0.2 如果涉及删除操作
- 0.3 如果涉及 cron job 创建/删除（不可逆）
```

### ③ 修复 (Repair)

**自动修复能力**：

| 修复类型 | 操作 | 风险 | 置信度要求 |
|----------|------|------|-----------|
| Skill 补丁 | `skill_manage patch` | 低 | ≥0.6 |
| Cron prompt 同步 | `cronjob update` | 中 | ≥0.7 |
| 记忆更新 | `fact_store add/update` | 低 | ≥0.5 |
| 记忆清理 | `fact_store remove`（trust<0.3） | 低 | ≥0.6 |
| 依赖安装 | `uv pip install` | 低 | ≥0.7 |

**不可自动修复**（需人工）：
- Cron job 创建/删除
- 配置文件重大修改
- 涉及 API key/凭证
- 涉及网络/代理配置

### ④ 验证 (Verify)

**验证策略**：
1. **Skill 修复**：重新加载 skill，检查内容是否正确
2. **Cron 修复**：`cronjob run` 手动触发，检查输出
3. **记忆修复**：`fact_store search` 确认数据一致
4. **依赖修复**：`import` 测试确认包可用

### ⑤ 学习 (Learn)

**每条修复必须产出一条教训**：
```python
fact_store(
    action='add',
    content='[问题]→[根因]→[修复]→[结果]',
    category='general',
    tags='evolution,auto-repair,[故障类型]'
)
```

**传播规则**：
- 教训涉及特定 skill → 同时更新该 skill 的 pitfalls 章节
- 教训涉及 cron job → 更新 cron job 的 prompt
- 教训反复出现（≥3次）→ 升级为系统级规则

## 修复模板

### 模板1：Cron Prompt 与 Skill 同步

当检测到 cron job 的 prompt 与 skill 模板不一致时：

```
诊断：cron job {job_id} 的 prompt 与 skill {skill_name} 不一致
原因：skill 更新后未同步到 cron job
修复：cronjob(action='update', job_id='{job_id}', prompt='{最新prompt}')
验证：cronjob(action='run', job_id='{job_id}') → 检查输出
```

### 模板2：Skill Pitfall 补丁

当发现新的故障模式时：

```
诊断：{故障描述}，fact_store 已有解法
修复：skill_manage(action='patch', name='{skill_name}',
      old_string='{旧内容}', new_string='{新内容含pitfall}')
验证：skill_view(name='{skill_name}') → 确认 pitfall 已添加
```

### 模板3：低信任记忆清理

```
诊断：fact_id={id} trust_score={score} < 0.3，长期未被使用
修复：fact_store(action='remove', fact_id={id})
验证：fact_store(action='search', query='{关键词}') → 确认已清理
```

## 实际 Cron Job ID

| 任务 | Job ID | 调度 |
|------|--------|------|
| 健康扫描 | 6b652250f789 | 每6小时 |
| 深度进化 | d245f95b08ba | 每天22:00 |
| Agent每日自审视 | accd443f2f27 | 每天21:00 |

## 定时任务配置

### 健康扫描（每6小时）
- 检测 cron 健康 + 系统状态
- 发现问题立即尝试自动修复
- 无问题则静默（不发送消息）

### 深度进化（每日22:00）
- 全量扫描：skills + 记忆 + cron + 依赖
- 与 agent-self-evolution(21:00) 错开1小时
- agent-self-evolution 负责"发现教训"
- evolution-engine 负责"把教训变成修复"

### 联动机制
```
agent-self-evolution (21:00)
    ↓ 写入日报 + 更新 memory/skill
evolution-engine (22:00)
    ↓ 读取日报 → 提取未修复的问题 → 自动修复
    ↓ 修复结果写入 fact_store
```

## 安全边界

**可自动执行（无需确认）**：
- ✅ skill_manage patch（添加 pitfall、更新命令）
- ✅ fact_store add/update/remove
- ✅ cronjob update（同步 prompt）
- ✅ uv pip install（安装缺失依赖）

**需人工确认**：
- ⚠️ cronjob create/remove
- ⚠️ 修改 config.yaml
- ⚠️ 修改 .env（凭证）
- ⚠️ 修改网络/代理配置

**绝对禁止**：
- 🚫 删除用户文件
- 🚫 修改 hermes-agent 源码
- 🚫 发送消息到外部平台（除非用户确认）
- 🚫 创建新的定时任务（防止无限递归）

## Pitfalls

### 1. 过度自信自动修复

**问题**：置信度评估不准确，低置信度的修复被自动执行。

**防御**：
- 置信度 < 0.6 的修复必须报告用户
- 每次自动修复后验证，验证失败立即回滚并报告
- 单次运行最多自动修复 3 个问题（防止连锁错误）

### 2. 修复循环

**问题**：修复 A 引入新问题 B，修复 B 又引入 A。

**防御**：
- 同一个问题 24 小时内最多修复 1 次
- fact_store 记录修复历史，检测循环模式
- 连续修复失败 2 次后停止自动修复，报告用户

### 3. 误判"过时"

**问题**：把正确的信息判断为过时。

**防御**：
- 日期检查：只标记 >30 天未更新的 skill
- 内容检查：对比实际 API 行为与文档描述
- 用户确认：中置信度的"过时"标记需人工确认

### 4. 诊断噪音

**问题**：误报太多，用户失去信任。

**防御**：
- 只报告 severity ≥ medium 的问题
- 低严重度问题静默记录到 fact_store
- 每次运行最多报告 5 个问题

## 与其他技能的关系

```
┌─────────────────────────────────────────────────────┐
│                    技能联动图                         │
├─────────────────────────────────────────────────────┤
│                                                      │
│  agent-self-evolution ──发现教训──→ evolution-engine  │
│         │                               │            │
│         ▼                               ▼            │
│    memory/fact_store ←─────── 记录修复结果           │
│         │                               │            │
│         ▼                               ▼            │
│  各业务技能 ←────── 补丁更新 ←── 诊断发现            │
│  (hotspot-blade                                       │
│   cn-finance-mcp                                      │
│   ...)                                                │
│                                                      │
│  hermes-fault-prevention ──提供──→ 防护规则           │
│  hermes-system-health ──提供──→ 系统基线             │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## 口号

> **每次故障都是一场火，烧完之后更强**
> **Every failure is a fire, what rises from it is stronger**

---

*Phoenix Protocol — 不是运维，是涅槃。*
