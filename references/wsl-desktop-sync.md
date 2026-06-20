# WSL-Desktop Hermes 同步指南

> 2026-06-11 验证。适用于 WSL2 + Windows Hermes Desktop 共存环境。

## 架构说明

WSL 和 Desktop 是两个独立的 Hermes 实例：
- **WSL**: `~/.hermes/`（通过 systemd 运行 gateway）
- **Desktop**: `C:\Users\<user>\AppData\Local\hermes\`（Electron 应用）

两者共享相同的配置格式，但运行环境独立。需要手动同步配置。

## 同步清单

| 优先级 | 文件/目录 | 说明 | 大小参考 |
|--------|-----------|------|----------|
| P0 | `config.yaml` | provider、model、工具配置 | ~20K |
| P0 | `.env` | API Key、密钥 | ~20K |
| P0 | `auth.json` | 认证令牌 | ~8K |
| P1 | `memory_store.db` | 结构化记忆（fact_store） | ~520K |
| P1 | `skills/` | 技能库 | 128个技能 |
| P1 | `memories/` | 文件模式记忆 | 127个文件 |
| P2 | `scripts/` | 自动化脚本 | 14个 |
| P2 | `cron/` | 定时任务配置 | 2个文件 |

## 同步脚本

```bash
#!/bin/bash
# hermes-sync-wsl-to-desktop.sh
# 从 WSL 同步到 Windows Desktop

set -eo pipefail

WIN_HERMES="/mnt/c/Users/yingm/AppData/Local/hermes"
WSL_HERMES="$HOME/.hermes"

# 检查目标目录
if [ ! -d "$WIN_HERMES" ]; then
    echo "ERROR: Desktop Hermes 目录不存在: $WIN_HERMES"
    echo "请先安装 Hermes Desktop"
    exit 1
fi

echo "=== 开始同步 ==="
echo "源: $WSL_HERMES"
echo "目标: $WIN_HERMES"
echo ""

# 备份原配置
echo "1. 备份原配置..."
cp "$WIN_HERMES/config.yaml" "$WIN_HERMES/config.yaml.bak" 2>/dev/null || true
cp "$WIN_HERMES/.env" "$WIN_HERMES/.env.bak" 2>/dev/null || true

# P0: 核心配置
echo "2. 同步核心配置..."
cp "$WSL_HERMES/config.yaml" "$WIN_HERMES/config.yaml"
cp "$WSL_HERMES/.env" "$WIN_HERMES/.env"
cp "$WSL_HERMES/auth.json" "$WIN_HERMES/auth.json" 2>/dev/null || echo "   - auth.json 不存在，跳过"

# P1: 记忆和技能
echo "3. 同步记忆数据库..."
cp "$WSL_HERMES/memory_store.db" "$WIN_HERMES/memory_store.db"

echo "4. 同步技能目录..."
mkdir -p "$WIN_HERMES/skills"
cp -r "$WSL_HERMES/skills/"* "$WIN_HERMES/skills/" 2>/dev/null || true

echo "5. 同步记忆文件..."
mkdir -p "$WIN_HERMES/memories"
cp -r "$WSL_HERMES/memories/"* "$WIN_HERMES/memories/" 2>/dev/null || true

# P2: 脚本和定时任务
echo "6. 同步脚本..."
mkdir -p "$WIN_HERMES/scripts"
cp -r "$WSL_HERMES/scripts/"* "$WIN_HERMES/scripts/" 2>/dev/null || true

echo "7. 同步定时任务配置..."
mkdir -p "$WIN_HERMES/cron"
cp -r "$WSL_HERMES/cron/"* "$WIN_HERMES/cron/" 2>/dev/null || true

# 验证
echo ""
echo "=== 同步完成 ==="
echo "config.yaml:     $(du -h "$WIN_HERMES/config.yaml" | cut -f1)"
echo ".env:            $(du -h "$WIN_HERMES/.env" | cut -f1)"
echo "memory_store.db: $(du -h "$WIN_HERMES/memory_store.db" | cut -f1)"
echo "skills/:         $(find "$WIN_HERMES/skills" -name "SKILL.md" | wc -l) 个技能"
echo "memories/:       $(find "$WIN_HERMES/memories" -name "*.md" | wc -l) 个文件"
```

## 反向同步（Desktop → WSL）

如果在 Desktop 中修改了配置，需要反向同步：

```bash
WIN_HERMES="/mnt/c/Users/yingm/AppData/Local/hermes"
WSL_HERMES="$HOME/.hermes"

cp "$WIN_HERMES/config.yaml" "$WSL_HERMES/config.yaml"
cp "$WIN_HERMES/.env" "$WSL_HERMES/.env"
cp "$WIN_HERMES/auth.json" "$WSL_HERMES/auth.json"
cp "$WIN_HERMES/memory_store.db" "$WSL_HERMES/memory_store.db"
```

## 注意事项

1. **Cron 任务只在 WSL 运行** - Desktop 不支持后台定时任务
2. **Gateway 独立** - WSL 和 Desktop 各自有独立的 gateway 进程
3. **避免同时运行** - 两个实例同时运行可能导致端口冲突
4. **备份优先** - 同份前先备份目标目录的配置
5. **路径差异** - WSL 用 `/home/yingming/`，Desktop 用 `C:\Users\yingm\`

## 常见问题

### Q: 同步后 Desktop 启动失败？
A: 检查 `.env` 中的路径是否需要调整（WSL 路径 vs Windows 路径）

### Q: 记忆数据库冲突？
A: 以最后一次同步的版本为准。建议定期同步，避免分叉。

### Q: 技能版本不一致？
A: 同步 `skills/` 目录会覆盖目标版本。如需合并，手动处理。
