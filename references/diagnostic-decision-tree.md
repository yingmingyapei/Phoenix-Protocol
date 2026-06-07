# 诊断决策树

## 故障分类与处理路径

```
故障检测到
    │
    ├─ Cron 连续失败
    │   ├─ 错误含 "timeout"/"超时" → WSL 网络问题
    │   │   └─ 检查代理配置 → 更新 skill pitfall
    │   ├─ 错误含 "401"/"403" → API key 过期
    │   │   └─ 报告用户（不可自动修复）
    │   ├─ 错误含 "tool not found" → 工具名变更
    │   │   └─ skill_manage patch 更新工具名
    │   ├─ 错误含 "command not found" → 命令过时
    │   │   └─ 搜索正确命令 → skill_manage patch
    │   └─ 其他 → 记录到 fact_store，报告用户
    │
    ├─ Skill 过时
    │   ├─ pitfalls 缺少已知故障 → 补充 pitfall
    │   ├─ 命令/URL 变更 → 更新内容
    │   ├─ 版本号过旧 → 标记待更新
    │   └─ 内容完整 → 跳过
    │
    ├─ 记忆矛盾
    │   ├─ 两条事实冲突 → 检查哪条更准确
    │   │   ├─ 新事实正确 → 标记旧事实 unhelpful
    │   │   └─ 旧事实正确 → 标记新事实 unhelpful
    │   └─ 事实过时 → 更新或删除
    │
    ├─ 依赖缺失
    │   ├─ numpy → uv pip install numpy
    │   ├─ 其他 pip 包 → uv pip install {包名}
    │   └─ 系统包 → 报告用户
    │
    └─ 数据源故障
        ├─ API 返回 404 → URL 变更，更新 skill
        ├─ API 返回 403/401 → 认证问题，报告用户
        ├─ API 超时 → 网络问题，检查代理
        └─ API 返回空 → 数据源可能下线，切换备用源
```

## 已知故障模式库

### CRON-001: opencli daemon start 不存在
- **症状**: cron job 报 "opencli daemon start: command not found"
- **根因**: Agent 照搬 skill 中的代码示例
- **修复**: 正确命令是 `opencli daemon restart`，物理删除 start 代码
- **教训**: 弱模型会照搬代码，必须物理删除而非声明禁止

### CRON-002: Cron prompt 与 skill 不同步
- **症状**: cron job 行为与 skill 描述不一致
- **根因**: skill 更新后未同步到 cron job
- **修复**: `cronjob update` 同步最新 prompt
- **教训**: 修改 skill 后必须同步 cron job

### CRON-003: WSL 网络超时
- **症状**: cron job 随机超时，尤其海外 API
- **根因**: Gateway 和 cron 走不同网络路径
- **修复**: 确保代理配置正确（127.0.0.1:10808）
- **教训**: cron job 超时 40% 根因是 WSL 网络

### SKILL-001: FTS5 中文搜索返回空
- **症状**: fact_store search 对中文关键词返回空
- **根因**: FTS5 unicode61 分词器合并中英文为一个 token
- **修复**: 已修复（前缀通配符 + LIKE 降级）
- **教训**: 搜索系统必须有中文兜底机制

### SKILL-002: numpy 缺失导致向量检索断裂
- **症状**: probe/related/reason 降级为 search
- **根因**: numpy 未安装时 HRR 向量静默跳过
- **修复**: `uv pip install numpy` + `store.backfill_all()`
- **教训**: 关键依赖缺失应报错而非静默跳过

### DEP-001: MiMo 长 token 性能瓶颈
- **症状**: 输入 >28K tokens 时 API 响应显著变慢
- **根因**: MiMo 服务器 KV-cache 处理能力不足
- **修复**: context_length=50000, compression.threshold=0.25
- **教训**: 不同模型的 token 承载能力差异巨大

### NET-001: Groq API 被 Cloudflare 封锁
- **症状**: Groq API 直连返回 403
- **根因**: Cloudflare 封锁 WSL IP
- **修复**: 配置 SOCKS5 代理 127.0.0.1:10808
- **教训**: 海外 API 在 WSL 中基本都需要代理
