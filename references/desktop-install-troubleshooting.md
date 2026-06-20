# 桌面版安装故障排查

## Git Merge Conflict 导致安装失败

### 症状

桌面版安装程序在 `repository` 阶段失败：

```
bootstrap FAILED stage=Some("repository") error=git checkout main failed (exit 1)
```

日志关键行（`C:\Users\yingm\AppData\Local\hermes\logs\bootstrap-installer.log`）：
```
stderr: error: could not write index
stderr: error: you need to resolve your current index first
```

### 根因

安装程序检测到本地有修改，尝试 stash 但失败，Git 处于未完成的合并状态。

冲突文件示例：`toolsets.py`、`tui_gateway/server.py`（带有 `<<<<<<< Updated upstream` 标记）。

### 诊断步骤

```bash
# 1. 检查日志
cat /mnt/c/Users/yingm/AppData/Local/hermes/logs/bootstrap-installer.log | tail -50

# 2. 检查Git状态
cd /mnt/c/Users/yingm/AppData/Local/hermes/hermes-agent
git status --short

# 3. 检查冲突文件
git diff --name-only --diff-filter=U

# 4. 检查合并状态文件
cat .git/AUTO_MERGE 2>/dev/null
cat .git/ORIG_HEAD 2>/dev/null
```

### 修复步骤

```bash
cd /mnt/c/Users/yingm/AppData/Local/hermes/hermes-agent

# 方案1：使用upstream版本解决冲突（推荐）
git checkout --theirs <冲突文件1> <冲突文件2>
git add <冲突文件1> <冲突文件2>
git commit -m "Resolve merge conflicts: use upstream versions"
git checkout -- .  # 清理工作目录

# 方案2：完全重置（会丢失本地修改）
git reset --hard HEAD
git clean -fd

# 方案3：删除仓库重新安装（最后手段）
rm -rf /mnt/c/Users/yingm/AppData/Local/hermes/hermes-agent
# 然后重新运行安装程序
```

### 验证

```bash
git status  # 应显示 "nothing to commit, working tree clean"
git log --oneline -3  # 确认提交历史正常
```

### 防御

- 安装前检查 Git 状态：`git status`
- 如有本地修改，先备份或提交
- 使用 `git stash` 保存临时修改

## 常见安装阶段

桌面版安装包含 16 个阶段：

| 阶段 | 名称 | 常见失败原因 |
|------|------|-------------|
| prereqs | uv, python, git, node, system-packages | 缺少依赖 |
| install | repository, venv, dependencies, node-deps, desktop | Git冲突、网络超时 |
| finalize | path, config-templates, platform-sdks, bootstrap-marker | 权限问题 |
| post-install | configure, gateway | API key配置 |
