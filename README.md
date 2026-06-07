# 🔥 Phoenix Protocol — 凤凰协议

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

## 定时任务

| 任务 | 调度 | 职责 |
|------|------|------|
| 健康扫描 | 每6小时 | Cron健康+依赖+记忆一致性 |
| 深度进化 | 每天22:00 | 技能保鲜+教训传播+全量巡检 |

## 联动

```
agent-self-evolution (21:00) → 发现教训
Phoenix Protocol (22:00) → 自动修复
fact_store → 记录修复结果 → 下次故障自动检索
```

## 文件结构

```
├── SKILL.md                          # 核心技能文档
├── templates/
│   ├── health-scan.md                # 健康扫描 prompt
│   └── deep-evolution.md             # 深度进化 prompt
└── references/
    ├── diagnostic-decision-tree.md   # 诊断决策树+故障模式库
    └── confidence-scoring.md         # 置信度评分规则
```

---

*Phoenix Protocol — 不是运维，是涅槃。*
