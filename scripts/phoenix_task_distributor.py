#!/usr/bin/env python3
"""
Phoenix Protocol 任务分发CLI - 多Agent任务分发
用法: python3 phoenix_task_distributor.py <command> [args...]

命令:
  distribute <task>       分发任务到远程Agent
  status                  显示任务状态
  collect                 收集任务结果
  list                    列出可用任务
"""

import sys
import os
import sqlite3
import subprocess
import json
from datetime import datetime

HERMES_HOME = os.path.expanduser("~/.hermes")
TASK_DB = os.path.join(HERMES_HOME, "phoenix_tasks.db")
IA_HOST = "192.168.3.88"
IA_USER = "root"

def get_connection():
    conn = sqlite3.connect(TASK_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS distributed_tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            task_command TEXT NOT NULL,
            target_host TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    conn.commit()
    return conn

# 可分发的任务
DISTRIBUTABLE_TASKS = {
    "health_check": {
        "name": "健康检查",
        "command": "python3 ~/.hermes/scripts/phoenix_diagnose.py health",
        "description": "在远程Agent运行健康检查"
    },
    "benchmark": {
        "name": "基准测试",
        "command": "python3 ~/.hermes/scripts/phoenix_benchmark.py run",
        "description": "在远程Agent运行基准测试"
    },
    "lesson_extract": {
        "name": "教训提取",
        "command": "python3 ~/.hermes/scripts/phoenix_auto_lesson.py auto-extract",
        "description": "在远程Agent提取教训"
    },
    "memory_sync": {
        "name": "记忆同步",
        "command": "python3 ~/.hermes/scripts/phoenix_version.py commit ~/.hermes/memories/MEMORY.md '远程同步'",
        "description": "同步记忆文件"
    }
}

def run_ssh_command(host, user, command, timeout=60):
    """执行SSH命令"""
    try:
        ssh_cmd = f"ssh {user}@{host} '{command}'"
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "SSH命令超时", 1
    except Exception as e:
        return "", str(e), 1

def distribute_task(task_name):
    """分发任务到远程Agent"""
    if task_name not in DISTRIBUTABLE_TASKS:
        print(f"错误: 未知任务 '{task_name}'")
        print("可用任务:")
        for name, task in DISTRIBUTABLE_TASKS.items():
            print(f"  - {name}: {task['description']}")
        return
    
    task = DISTRIBUTABLE_TASKS[task_name]
    print(f"=== 分发任务: {task['name']} ===")
    
    # 保存任务到数据库
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO distributed_tasks (task_name, task_command, target_host, status, created_at)
        VALUES (?, ?, ?, 'running', datetime('now'))
    """, (task_name, task["command"], IA_HOST))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # 执行远程命令
    print(f"正在分发到 {IA_HOST}...")
    stdout, stderr, returncode = run_ssh_command(IA_HOST, IA_USER, task["command"])
    
    # 更新任务状态
    conn = get_connection()
    cursor = conn.cursor()
    if returncode == 0:
        cursor.execute("""
            UPDATE distributed_tasks 
            SET status = 'completed', result = ?, completed_at = datetime('now')
            WHERE task_id = ?
        """, (stdout, task_id))
        print(f"✅ 任务执行成功")
        print(f"结果: {stdout[:200]}...")
    else:
        cursor.execute("""
            UPDATE distributed_tasks 
            SET status = 'failed', result = ?, completed_at = datetime('now')
            WHERE task_id = ?
        """, (stderr, task_id))
        print(f"❌ 任务执行失败")
        print(f"错误: {stderr[:200]}...")
    
    conn.commit()
    conn.close()

def show_status():
    """显示任务状态"""
    print("=== 任务状态 ===")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT task_id, task_name, target_host, status, created_at, completed_at 
        FROM distributed_tasks 
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    tasks = cursor.fetchall()
    conn.close()
    
    if not tasks:
        print("没有分发任务")
        return
    
    print(f"\n最近 {len(tasks)} 个任务:")
    for task in tasks:
        status_icon = "✅" if task[3] == "completed" else "❌" if task[3] == "failed" else "⏳"
        print(f"\n{status_icon} 任务 {task[0]}: {task[1]}")
        print(f"   目标: {task[2]}")
        print(f"   状态: {task[3]}")
        print(f"   创建: {task[4]}")
        if task[5]:
            print(f"   完成: {task[5]}")

def collect_results():
    """收集任务结果"""
    print("=== 收集任务结果 ===")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT task_id, task_name, result 
        FROM distributed_tasks 
        WHERE status = 'completed'
        ORDER BY completed_at DESC
        LIMIT 5
    """)
    
    tasks = cursor.fetchall()
    conn.close()
    
    if not tasks:
        print("没有已完成的任务")
        return
    
    print(f"\n最近 {len(tasks)} 个已完成任务:")
    for task in tasks:
        print(f"\n任务 {task[0]}: {task[1]}")
        print(f"结果: {task[2][:200] if task[2] else '无结果'}...")

def list_tasks():
    """列出可用任务"""
    print("=== 可用任务 ===")
    for name, task in DISTRIBUTABLE_TASKS.items():
        print(f"  - {name}: {task['description']}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "distribute":
        if len(sys.argv) < 3:
            print("错误: distribute 需要任务名称")
            sys.exit(1)
        distribute_task(sys.argv[2])
    elif command == "status":
        show_status()
    elif command == "collect":
        collect_results()
    elif command == "list":
        list_tasks()
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
