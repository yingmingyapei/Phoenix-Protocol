#!/usr/bin/env python3
"""
Phoenix Protocol 版本管理CLI - 文件版本管理
用法: python3 phoenix_version.py <command> [args...]

命令:
  commit <file> [message]  提交文件版本
  history <file>           查看文件历史
  diff <file> [version]    比较版本差异
  restore <file> [version] 恢复到指定版本
  tag <file> <tag>         添加标签
"""

import sys
import os
import hashlib
import json
import shutil
from datetime import datetime

HERMES_HOME = os.path.expanduser("~/.hermes")
VERSION_DIR = os.path.join(HERMES_HOME, "versions")
VERSION_INDEX = os.path.join(VERSION_DIR, "index.json")

def ensure_version_dir():
    """确保版本目录存在"""
    os.makedirs(VERSION_DIR, exist_ok=True)
    if not os.path.exists(VERSION_INDEX):
        with open(VERSION_INDEX, 'w') as f:
            json.dump({}, f)

def load_version_index():
    """加载版本索引"""
    ensure_version_dir()
    try:
        with open(VERSION_INDEX, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_version_index(index):
    """保存版本索引"""
    ensure_version_dir()
    with open(VERSION_INDEX, 'w') as f:
        json.dump(index, f, indent=2)

def get_file_hash(file_path):
    """计算文件哈希"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def commit_file(file_path, message=None):
    """提交文件版本"""
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 {file_path}")
        return
    
    # 计算文件哈希
    file_hash = get_file_hash(file_path)
    if not file_hash:
        print(f"错误: 无法读取文件 {file_path}")
        return
    
    # 加载版本索引
    index = load_version_index()
    
    # 获取文件的版本历史
    if file_path not in index:
        index[file_path] = []
    
    # 检查是否与上一版本相同
    if index[file_path]:
        last_version = index[file_path][-1]
        if last_version["hash"] == file_hash:
            print(f"文件未变化，跳过提交")
            return
    
    # 创建版本
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    version_id = f"{timestamp}_{file_hash[:8]}"
    version_path = os.path.join(VERSION_DIR, version_id)
    
    # 备份文件
    shutil.copy2(file_path, version_path)
    
    # 更新索引
    version_info = {
        "version_id": version_id,
        "hash": file_hash,
        "timestamp": timestamp,
        "message": message or "自动提交",
        "file_size": os.path.getsize(file_path)
    }
    index[file_path].append(version_info)
    save_version_index(index)
    
    print(f"✅ 已提交版本: {version_id}")
    print(f"   文件: {file_path}")
    print(f"   消息: {message or '自动提交'}")

def show_history(file_path):
    """查看文件历史"""
    index = load_version_index()
    
    if file_path not in index:
        print(f"文件 {file_path} 没有版本历史")
        return
    
    versions = index[file_path]
    print(f"=== 文件历史: {file_path} ===")
    print(f"版本数量: {len(versions)}")
    
    for i, version in enumerate(versions):
        print(f"\n版本 {i+1}: {version['version_id']}")
        print(f"  时间: {version['timestamp']}")
        print(f"  消息: {version['message']}")
        print(f"  大小: {version['file_size']} 字节")
        print(f"  哈希: {version['hash']}")

def diff_versions(file_path, version_num=None):
    """比较版本差异"""
    index = load_version_index()
    
    if file_path not in index:
        print(f"文件 {file_path} 没有版本历史")
        return
    
    versions = index[file_path]
    if len(versions) < 2:
        print("版本数量不足，无法比较")
        return
    
    # 获取要比较的版本
    if version_num:
        if version_num < 1 or version_num > len(versions):
            print(f"错误: 版本号 {version_num} 无效")
            return
        version = versions[version_num - 1]
    else:
        version = versions[-1]
    
    version_path = os.path.join(VERSION_DIR, version["version_id"])
    
    if not os.path.exists(version_path):
        print(f"错误: 版本文件不存在 {version_path}")
        return
    
    # 比较文件
    try:
        with open(file_path, 'r') as f:
            current_content = f.read()
        with open(version_path, 'r') as f:
            version_content = f.read()
        
        if current_content == version_content:
            print("文件内容相同")
        else:
            print("文件内容不同")
            print(f"当前文件大小: {len(current_content)} 字符")
            print(f"版本文件大小: {len(version_content)} 字符")
    except Exception as e:
        print(f"错误: 无法比较文件 {e}")

def restore_version(file_path, version_num=None):
    """恢复到指定版本"""
    index = load_version_index()
    
    if file_path not in index:
        print(f"文件 {file_path} 没有版本历史")
        return
    
    versions = index[file_path]
    if not versions:
        print("没有可用版本")
        return
    
    # 获取要恢复的版本
    if version_num:
        if version_num < 1 or version_num > len(versions):
            print(f"错误: 版本号 {version_num} 无效")
            return
        version = versions[version_num - 1]
    else:
        version = versions[-1]
    
    version_path = os.path.join(VERSION_DIR, version["version_id"])
    
    if not os.path.exists(version_path):
        print(f"错误: 版本文件不存在 {version_path}")
        return
    
    # 恢复文件
    try:
        # 先备份当前版本
        if os.path.exists(file_path):
            commit_file(file_path, "恢复前自动备份")
        
        # 恢复
        shutil.copy2(version_path, file_path)
        print(f"✅ 已恢复到版本: {version['version_id']}")
        print(f"   文件: {file_path}")
    except Exception as e:
        print(f"错误: 恢复失败 {e}")

def add_tag(file_path, tag):
    """添加标签"""
    index = load_version_index()
    
    if file_path not in index:
        print(f"文件 {file_path} 没有版本历史")
        return
    
    versions = index[file_path]
    if not versions:
        print("没有可用版本")
        return
    
    # 添加标签到最后一个版本
    versions[-1]["tag"] = tag
    save_version_index(index)
    
    print(f"✅ 已添加标签: {tag}")
    print(f"   文件: {file_path}")
    print(f"   版本: {versions[-1]['version_id']}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "commit":
        if len(sys.argv) < 3:
            print("错误: commit 需要文件路径")
            sys.exit(1)
        file_path = sys.argv[2]
        message = sys.argv[3] if len(sys.argv) > 3 else None
        commit_file(file_path, message)
    elif command == "history":
        if len(sys.argv) < 3:
            print("错误: history 需要文件路径")
            sys.exit(1)
        show_history(sys.argv[2])
    elif command == "diff":
        if len(sys.argv) < 3:
            print("错误: diff 需要文件路径")
            sys.exit(1)
        file_path = sys.argv[2]
        version_num = int(sys.argv[3]) if len(sys.argv) > 3 else None
        diff_versions(file_path, version_num)
    elif command == "restore":
        if len(sys.argv) < 3:
            print("错误: restore 需要文件路径")
            sys.exit(1)
        file_path = sys.argv[2]
        version_num = int(sys.argv[3]) if len(sys.argv) > 3 else None
        restore_version(file_path, version_num)
    elif command == "tag":
        if len(sys.argv) < 4:
            print("错误: tag 需要文件路径和标签")
            sys.exit(1)
        add_tag(sys.argv[2], sys.argv[3])
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
