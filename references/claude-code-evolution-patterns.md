# Claude Code 自进化模式研究

> 来源：Claude Code 系统提示词源码分析（319 个文件），2026-06-08

## 1. Dream 记忆整合（最有借鉴价值）

**文件**: `agent-prompt-dream-memory-consolidation.md`

四阶段流程：

```
Phase 1 — Orient（定位）
  └─ ls 记忆目录 + 读索引 + 扫描现有主题文件 + 最近日志

Phase 2 — Gather（采集）
  └─ 优先级：session logs > 代码变更 > transcript 搜索
  └─ 不要穷尽读取 transcript，只找已经怀疑重要的东西

Phase 3 — Consolidate（整合）
  └─ 合并新信号到现有主题文件（不是创建近似副本）
  └─ 相对日期→绝对日期（"昨天"→"2026-06-07"）
  └─ 删除矛盾事实（今天的调查推翻了旧记忆→直接修复）

Phase 4 — Prune & Index（修剪+索引）
  └─ 索引 ≤25KB，每条 ≤150 字符
  └─ 格式：`- [Title](file.md) — 一行钩子`
  └─ 删除过时指针，缩短过长条目
  └─ 解决矛盾——两个文件不一致时修复错误的那个
```

**关键设计**：记忆文件不可原地编辑（immutable），只能删除旧文件+创建新文件。防止"记忆漂移"。

### 对 Phoenix Protocol 的启示

我们的 fact_store 只会 append，没有整合机制。应该：
- 定期（每周）运行"记忆整合"：合并重复事实、删除矛盾、更新过时信息
- fact_store 的 `contradict` 操作已有矛盾检测，但没有自动修复流程
- 需要一个"记忆整合"定时任务

---

## 2. Dream 记忆修剪

**文件**: `agent-prompt-dream-memory-pruning.md`

```
对每条记忆判断：
├─ 过时/失效 → 删除
├─ 重复/近似 → 合并为一条新文件（保留最早的 created 日期）
└─ 仍然有效 → 保留
```

**关键规则**：
- `team/` 子目录的记忆要保守——别人的记忆不能随便删
- 记忆文件不可原地编辑，合并=删旧+建新

### 对 Phoenix Protocol 的启示

fact_store 的 `remove` 操作可以清理低信任记忆，但缺少"合并重复"能力。应该：
- 在深度进化任务中增加"合并重复事实"步骤
- 信任分数 <0.3 且 >30 天的事实自动清理

---

## 3. 记忆选择性注入（节省 token）

**文件**: `agent-prompt-determine-which-memory-files-to-attach.md`

不是全量注入，而是子 agent 选 ≤5 条最相关记忆。

**选择标准**：
- 避免重复提问（路径、配置、已做决定）
- 应用用户偏好（风格、工具选择）
- 维持连续性（项目状态、进行中的工作）
- 避免已知陷阱（过去的纠正）

**关键规则**：
- 对 user-profile 和 project-overview 记忆要特别保守
- "works on DB performance" ≠ 每个包含 "performance" 的问题都相关
- 匹配问题内容，不是匹配用户画像关键词

### 对 Phoenix Protocol 的启示

当前 Hermes 全量注入 memory 到 system prompt（60+ 条，13K+ 字符）。应该：
- 用 fact_store 的 search/probe 做按需检索
- 对每个查询只注入最相关的 ≤5 条
- 大幅减少 token 浪费

---

## 4. 记忆合成子 Agent

**文件**: `agent-prompt-memory-synthesis.md`

专门的子 agent，读取所有记忆文件，对每个查询提取 ≤7 条相关事实：

```json
{
  "relevant_facts": ["fact1", "fact2"],
  "cited_memories": ["file1.md", "file2.md"]
}
```

**规则**：
- 每条事实 1-2 句话，独立可理解
- 只命名路径/标识符当它是必须使用或避免的东西
- 不要自己推理——只从事实中提取
- 如果之前的轮次已经返回了相关事实，返回空

---

## 5. 用户反馈记忆（成功+失败）

**文件**: `system-prompt-memory-description-of-user-feedback-with-explicit-save.md`

> "如果只保存纠正，你会避免过去的错误，但会偏离用户已经验证过的方法，变得过于谨慎。"

**规则**：
- 记录成功 AND 失败
- 保存新反馈前检查是否与已有反馈矛盾
- 矛盾时要么不保存，要么保存一条明确标注覆盖的记录

### 对 Phoenix Protocol 的启示

当前 agent-self-evolution 主要关注"发现错误"。应该：
- 同样记录"做得好的地方"和"用户认可的方法"
- 防止"过度矫正"——修了一个问题反而丢了之前的好做法

---

## 6. 自主循环持久化

**文件**: `system-prompt-autonomous-loop-persistence-guidance.md`

两版本：

**基础版**：用户离开时继续完成已建立的工作
- 最强信号：进行中的 PR（review comments、CI 失败、merge conflicts）
- 次强：未完成的实现、未兑现的承诺
- 3 次无事可做→停止

**持久版**：停止前先扩大范围
- 重新审视原始任务
- 检查兄弟 PR/分支
- 只有任务证明完成才停止

**设计哲学**：
> "你是一个管家（steward），不是发起者（initiator）。价值来自于可靠地推进用户已启动的工作。"

**可逆性判断**：
- 可逆操作（本地编辑、测试）→ 倾向执行
- 不可逆操作（push、delete、send）→ 需要明确授权

### 对 Phoenix Protocol 的启示

当前健康扫描发现问题后，如果置信度不够就报告用户。应该：
- 对可逆修复（skill patch、fact_store 更新）更积极
- 对不可逆修复（cron create/delete）更保守
- 连续空扫描时扩大检查范围，而不是停止

---

## 7. 自调度循环

**文件**: `skill-loop-self-pacing-mode.md`

Agent 自己决定下次运行的时间或事件：

- **事件驱动**：arm 一个 monitor（CI 完成、日志匹配、文件变更、PR 评论）
  - `persistent: true` 保持监听
  - `<task-notification>` 消息唤醒循环
- **时间驱动**：fallback heartbeat（1200-1800 秒）
- 唤醒后执行任务，然后再次调度

### 对 Phoenix Protocol 的启示

当前只有 cron 时间驱动。可以增加：
- 事件驱动：cron job 失败时立即触发健康扫描
- 自适应频率：问题多时扫描更频繁，稳定时降低频率

---

## 8. 自动模式规则审查

**文件**: `agent-prompt-auto-mode-rule-reviewer.md`

自动审查用户的自动模式规则：
- 清晰度（是否有歧义）
- 完整性（是否有边界情况遗漏）
- 冲突（规则之间是否矛盾）
- 可操作性（是否足够具体）

### 对 Phoenix Protocol 的启示

可以增加"安全规则审查"：定期检查 Phoenix Protocol 的安全边界是否合理、是否有遗漏。

---

## 总结：优先借鉴顺序

| 优先级 | 模式 | 实施难度 | 价值 |
|--------|------|----------|------|
| P0 | 记忆整合（Dream） | 中 | 防止记忆膨胀和矛盾 |
| P0 | 记录成功+失败 | 低 | 防止过度矫正 |
| P1 | 记忆选择性注入 | 中 | 节省 token，提高精准度 |
| P1 | 自主循环持久化 | 低 | 减少"无事可做"停止 |
| P2 | 记忆修剪自动化 | 低 | fact_store 已有基础 |
| P2 | 自调度循环 | 中 | 事件驱动+自适应频率 |
| P3 | 规则审查 | 低 | 安全边界自检 |
