#!/usr/bin/env python3
"""
Phoenix Protocol 智能调度CLI - 智能调度维护任务
用法: python3 phoenix_scheduler.py <command> [args...]

命令:
  schedule                显示调度计划
  add <task> <cron>       添加调度任务
  remove <task_id>        删除调度任务
  run <task_id>           手动运行任务
  status                  显示任务状态
"""

import sys
import os
import sqlite3
import subprocess
from datetime import datetime

HERMES_HOME = os.path.expanduser("~/.hermes")
SCHEDULER_DB = os.path.join(HERMES_HOME, "phoenix_scheduler.db")

def get_connection():
    conn = sqlite3.connect(SCHEDULER_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            task_command TEXT NOT NULL,
            cron_expression TEXT,
            last_run TIMESTAMP,
            next_run TIMESTAMP,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

# 预定义的调度任务
DEFAULT_TASKS = [
    {
        "name": "每日健康检查",
        "command": "python3 ~/.hermes/scripts/phoenix_diagnose.py health",
        "cron": "0 8 * * *",
        "description": "每天早上8:00运行健康检查"
    },
    {
        "name": "每日预测",
        "command": "python3 ~/.hermes/scripts/phoenix_scheduled.py run",
        "cron": "0 9 * * *",
        "description": "每天早上9:00运行预测"
    },
    {
        "name": "每周基准测试",
        "command": "python3 ~/.hermes/scripts/phoenix_benchmark.py run",
        "cron": "0 10 * * 0",
        "description": "每周日早上10:00运行基准测试"
    },
    {
        "name": "每月教训提取",
        "command": "python3 ~/.hermes/scripts/phoenix_auto_lesson.py auto-extract",
        "cron": "0 11 1 * *",
        "description": "每月1日早上11:00运行教训提取"
    },
    {
        "name": "每日版本提交",
        "command": "python3 ~/.hermes/scripts/phoenix_version.py commit ~/.hermes/memories/MEMORY.md '每日自动提交'",
        "cron": "0 23 * * *",
        "description": "每天晚上23:00提交MEMORY.md版本"
    }
]

def show_schedule():
    """显示调度计划"""
    print("=== 调度计划 ===")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT task_id, task_name, cron_expression, last_run, status FROM scheduled_tasks ORDER BY task_id")
    tasks = cursor.fetchall()
    
    conn.close()
    
    if not tasks:
        print("没有调度任务")
        return
    
    print(f"\n任务总数: {len(tasks)}")
    for task in tasks:
        status_icon = "✅" if task[4] == "active" else "⏸️"
        print(f"\n{status_icon} 任务 {task[0]}: {task[1]}")
        print(f"   Cron: {task[2]}")
        print(f"   上次运行: {task[3] or '从未运行'}")

def add_task(task_name, cron_expression):
    """添加调度任务"""
    # 查找预定义任务
    task_command = None
    for default_task in DEFAULT_TASKS:
        if default_task["name"] == task_name:
            task_command = default_task["command"]
            break
    
    if not task_command:
        print(f"错误: 未知任务 '{task_name}'")
        print("可用任务:")
        for task in DEFAULT_TASKS:
            print(f"  - {task['name']}: {task['description']}")
        return
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO scheduled_tasks (task_name, task_command, cron_expression, status, created_at)
        VALUES (?, ?, ?, 'active', datetime('now'))
    """, (task_name, task_command, cron_expression))
    
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"✅ 已添加任务: {task_name}")
    print(f"   任务ID: {task_id}")
    print(f"   Cron: {cron_expression}")

def remove_task(task_id):
    """删除调度任务"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT task_name FROM scheduled_tasks WHERE task_id = ?", (task_id,))
    task = cursor.fetchone()
    
    if not task:
        print(f"错误: 任务ID {task_id} 不存在")
        conn.close()
        return
    
    cursor.execute("DELETE FROM scheduled_tasks WHERE task_id = ?", (task_id,))
    conn.commit()
    conn.close()
    
    print(f"✅ 已删除任务: {task[0]} (ID: {task_id})")

def run_task(task_id):
    """手动运行任务"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT task_name, task_command FROM scheduled_tasks WHERE task_id = ?", (task_id,))
    task = cursor.fetchone()
    
    if not task:
        print(f"错误: 任务ID {task_id} 不存在")
        conn.close()
        return
    
    print(f"=== 运行任务: {task[0]} ===")
    
    try:
        result = subprocess.run(task[1], shell=True, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ 任务执行成功")
            print(result.stdout)
        else:
            print(f"❌ 任务执行失败")
            print(result.stderr)
        
        # 更新上次运行时间
        cursor.execute("UPDATE scheduled_tasks SET last_run = datetime('now') WHERE task_id = ?", (task_id,))
        conn.commit()
    except subprocess.TimeoutExpired:
        print(f"❌ 任务执行超时")
    except Exception as e:
        print(f"❌ 任务执行异常: {e}")
    
    conn.close()

def show_status():
    """显示任务状态"""
    print("=== 任务状态 ===")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT task_id, task_name, status, last_run FROM scheduled_tasks ORDER BY task_id")
    tasks = cursor.fetchall()
    
    conn.close()
    
    if not tasks:
        print("没有调度任务")
        return
    
    print(f"\n任务总数: {len(tasks)}")
    
    active_tasks = sum(1 for t in tasks if t[2] == "active")
    print(f"活跃任务: {active_tasks}")
    
    for task in tasks:
        status_icon = "✅" if task[2] == "active" else "⏸️"
        print(f"\n{status_icon} 任务 {task[0]}: {task[1]}")
        print(f"   状态: {task[2]}")
        print(f"   上次运行: {task[3] or '从未运行'}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "schedule":
        show_schedule()
    elif command == "add":
        if len(sys.argv) < 4:
            print("错误: add 需要任务名称和Cron表达式")
            sys.exit(1)
        add_task(sys.argv[2], sys.argv[3])
    elif command == "remove":
        if len(sys.argv) < 3:
            print("错误: remove 需要任务ID")
            sys.exit(1)
        remove_task(int(sys.argv[2]))
    elif command == "run":
        if len(sys.argv) < 3:
            print("错误: run 需要任务ID")
            sys.exit(1)
        run_task(int(sys.argv[2]))
    elif command == "status":
        show_status()
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
