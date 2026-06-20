#!/usr/bin/env python3
"""
Phoenix Protocol 修复回滚CLI - 修复前备份和修复失败自动回滚
用法: python3 phoenix_rollback.py <command> [args...]

命令:
  backup <file>           备份文件
  restore <file>          恢复文件
  list                    列出备份
  rollback <backup_id>    回滚到指定备份
"""

import sys
import os
import shutil
import json
from datetime import datetime

HERMES_HOME = os.path.expanduser("~/.hermes")
BACKUP_DIR = os.path.join(HERMES_HOME, "backups")
BACKUP_INDEX = os.path.join(BACKUP_DIR, "index.json")

def ensure_backup_dir():
    """确保备份目录存在"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if not os.path.exists(BACKUP_INDEX):
        with open(BACKUP_INDEX, 'w') as f:
            json.dump([], f)

def load_backup_index():
    """加载备份索引"""
    ensure_backup_dir()
    try:
        with open(BACKUP_INDEX, 'r') as f:
            return json.load(f)
    except:
        return []

def save_backup_index(index):
    """保存备份索引"""
    ensure_backup_dir()
    with open(BACKUP_INDEX, 'w') as f:
        json.dump(index, f, indent=2)

def backup_file(file_path):
    """备份文件"""
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 {file_path}")
        return
    
    ensure_backup_dir()
    
    # 生成备份ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = os.path.basename(file_path)
    backup_id = f"{timestamp}_{file_name}"
    backup_path = os.path.join(BACKUP_DIR, backup_id)
    
    # 备份文件
    shutil.copy2(file_path, backup_path)
    
    # 更新索引
    index = load_backup_index()
    index.append({
        "backup_id": backup_id,
        "original_path": file_path,
        "backup_path": backup_path,
        "timestamp": timestamp,
        "file_size": os.path.getsize(file_path)
    })
    save_backup_index(index)
    
    print(f"✅ 已备份: {file_path}")
    print(f"   备份ID: {backup_id}")
    print(f"   备份路径: {backup_path}")

def restore_file(file_path):
    """恢复文件（从最新备份）"""
    index = load_backup_index()
    
    # 查找最新的备份
    backups = [b for b in index if b["original_path"] == file_path]
    if not backups:
        print(f"错误: 没有找到 {file_path} 的备份")
        return
    
    latest = max(backups, key=lambda x: x["timestamp"])
    backup_path = latest["backup_path"]
    
    if not os.path.exists(backup_path):
        print(f"错误: 备份文件不存在 {backup_path}")
        return
    
    # 恢复文件
    shutil.copy2(backup_path, file_path)
    
    print(f"✅ 已恢复: {file_path}")
    print(f"   从备份: {latest['backup_id']}")

def list_backups():
    """列出所有备份"""
    index = load_backup_index()
    
    if not index:
        print("没有备份记录")
        return
    
    print("=== 备份列表 ===")
    for backup in index:
        print(f"ID: {backup['backup_id']}")
        print(f"  原文件: {backup['original_path']}")
        print(f"  备份时间: {backup['timestamp']}")
        print(f"  文件大小: {backup['file_size']} 字节")
        print()

def rollback_to_backup(backup_id):
    """回滚到指定备份"""
    index = load_backup_index()
    
    # 查找备份
    backup = None
    for b in index:
        if b["backup_id"] == backup_id:
            backup = b
            break
    
    if not backup:
        print(f"错误: 未找到备份ID {backup_id}")
        return
    
    backup_path = backup["backup_path"]
    original_path = backup["original_path"]
    
    if not os.path.exists(backup_path):
        print(f"错误: 备份文件不存在 {backup_path}")
        return
    
    # 回滚前先备份当前状态
    if os.path.exists(original_path):
        backup_file(original_path)
    
    # 回滚
    shutil.copy2(backup_path, original_path)
    
    print(f"✅ 已回滚到备份: {backup_id}")
    print(f"   恢复文件: {original_path}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "backup":
        if len(sys.argv) < 3:
            print("错误: backup 需要文件路径")
            sys.exit(1)
        backup_file(sys.argv[2])
    elif command == "restore":
        if len(sys.argv) < 3:
            print("错误: restore 需要文件路径")
            sys.exit(1)
        restore_file(sys.argv[2])
    elif command == "list":
        list_backups()
    elif command == "rollback":
        if len(sys.argv) < 3:
            print("错误: rollback 需要备份ID")
            sys.exit(1)
        rollback_to_backup(sys.argv[2])
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
