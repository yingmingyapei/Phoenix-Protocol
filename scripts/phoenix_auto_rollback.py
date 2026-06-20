#!/usr/bin/env python3
"""
Phoenix Protocol 自动回滚CLI - 修复失败自动回滚
用法: python3 phoenix_auto_rollback.py <command> [args...]

命令:
  monitor                 监控修复状态
  auto-rollback <file>    自动回滚（修复失败时）
  check-health            检查系统健康
"""

import sys
import os
import sqlite3
import shutil
from datetime import datetime

HERMES_HOME = os.path.expanduser("~/.hermes")
BACKUP_DIR = os.path.join(HERMES_HOME, "backups")
BACKUP_INDEX = os.path.join(BACKUP_DIR, "index.json")
CRON_DB = os.path.join(HERMES_HOME, "cron_history.db")

def load_backup_index():
    """加载备份索引"""
    import json
    if not os.path.exists(BACKUP_INDEX):
        return []
    try:
        with open(BACKUP_INDEX, 'r') as f:
            return json.load(f)
    except:
        return []

def get_latest_backup(file_path):
    """获取文件的最新备份"""
    index = load_backup_index()
    backups = [b for b in index if b["original_path"] == file_path]
    if not backups:
        return None
    return max(backups, key=lambda x: x["timestamp"])

def auto_rollback(file_path):
    """自动回滚（修复失败时）"""
    print(f"=== 自动回滚: {file_path} ===")
    
    # 获取最新备份
    backup = get_latest_backup(file_path)
    if not backup:
        print(f"错误: 没有找到 {file_path} 的备份")
        return False
    
    backup_path = backup["backup_path"]
    if not os.path.exists(backup_path):
        print(f"错误: 备份文件不存在 {backup_path}")
        return False
    
    # 检查当前文件是否损坏
    if os.path.exists(file_path):
        try:
            # 简单检查：文件是否可读
            with open(file_path, 'r') as f:
                content = f.read()
            print(f"当前文件可读，内容长度: {len(content)}")
        except Exception as e:
            print(f"当前文件损坏: {e}")
            print("执行自动回滚...")
            shutil.copy2(backup_path, file_path)
            print(f"✅ 已回滚到备份: {backup['backup_id']}")
            return True
    else:
        print(f"当前文件不存在，执行自动回滚...")
        shutil.copy2(backup_path, file_path)
        print(f"✅ 已回滚到备份: {backup['backup_id']}")
        return True
    
    print("当前文件正常，无需回滚")
    return False

def monitor_repair_status():
    """监控修复状态"""
    print("=== 监控修复状态 ===")
    
    # 检查Cron运行状态
    if os.path.exists(CRON_DB):
        conn = sqlite3.connect(CRON_DB)
        cursor = conn.cursor()
        
        # 获取最近的失败记录
        cursor.execute("""
            SELECT job_id, status, error_message, created_at 
            FROM cron_runs 
            WHERE status = 'failure'
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        failures = cursor.fetchall()
        conn.close()
        
        if failures:
            print(f"\n最近 {len(failures)} 次失败:")
            for fail in failures:
                print(f"  ❌ {fail[0]}: {fail[2][:50] if fail[2] else '无错误信息'} ({fail[3]})")
        else:
            print("\n✅ 最近没有失败记录")
    
    # 检查备份状态
    index = load_backup_index()
    if index:
        print(f"\n备份状态: {len(index)} 个备份")
        for backup in index[-3:]:  # 显示最近3个备份
            print(f"  - {backup['backup_id']}: {backup['original_path']}")
    else:
        print("\n备份状态: 无备份")

def check_health():
    """检查系统健康"""
    print("=== 检查系统健康 ===")
    
    # 检查关键文件
    critical_files = [
        ("MEMORY.md", os.path.join(HERMES_HOME, "memories", "MEMORY.md")),
        ("USER.md", os.path.join(HERMES_HOME, "memories", "USER.md")),
        ("config.yaml", os.path.join(HERMES_HOME, "config.yaml")),
    ]
    
    for name, path in critical_files:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    content = f.read()
                print(f"✓ {name}: 正常 ({len(content)} 字符)")
            except Exception as e:
                print(f"✗ {name}: 损坏 ({e})")
                # 尝试回滚
                backup = get_latest_backup(path)
                if backup and os.path.exists(backup["backup_path"]):
                    print(f"  尝试回滚到备份 {backup['backup_id']}...")
                    shutil.copy2(backup["backup_path"], path)
                    print(f"  ✅ 回滚成功")
        else:
            print(f"✗ {name}: 不存在")
            # 尝试回滚
            backup = get_latest_backup(path)
            if backup and os.path.exists(backup["backup_path"]):
                print(f"  尝试回滚到备份 {backup['backup_id']}...")
                shutil.copy2(backup["backup_path"], path)
                print(f"  ✅ 回滚成功")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "monitor":
        monitor_repair_status()
    elif command == "auto-rollback":
        if len(sys.argv) < 3:
            print("错误: auto-rollback 需要文件路径")
            sys.exit(1)
        auto_rollback(sys.argv[2])
    elif command == "check-health":
        check_health()
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
