#!/usr/bin/env python3
"""
Cron运行历史CLI - 记录和查询cron job运行历史
用法: python3 cron_history_cli.py <command> [args...]

命令:
  list [job_id]           列出运行历史
  add <job_id> <status> [--duration DURATION] [--error ERROR]  添加运行记录
  stats [job_id]          统计信息
  failures [job_id]       列出失败记录
"""

import sys
import os
import sqlite3

DB_PATH = os.path.expanduser("~/.hermes/cron_history.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cron_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            status TEXT NOT NULL,
            duration INTEGER,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_id ON cron_runs(job_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON cron_runs(created_at)")
    conn.commit()
    return conn

def list_history(job_id=None, limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    if job_id:
        cursor.execute("SELECT run_id, job_id, status, duration, error_message, created_at FROM cron_runs WHERE job_id = ? ORDER BY created_at DESC LIMIT ?", (job_id, limit))
    else:
        cursor.execute("SELECT run_id, job_id, status, duration, error_message, created_at FROM cron_runs ORDER BY created_at DESC LIMIT ?", (limit,))
    runs = cursor.fetchall()
    conn.close()
    print(f"=== Cron运行历史 (最近 {len(runs)} 条) ===")
    for run in runs:
        status_icon = "✅" if run[2] == "success" else "❌"
        duration_str = f"{run[3]}s" if run[3] else "N/A"
        error_str = f" error={run[4][:50]}..." if run[4] else ""
        print(f"{status_icon} ID {run[0]}: job={run[1]} status={run[2]} duration={duration_str}{error_str} ({run[5]})")

def add_run(job_id, status, duration=None, error=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO cron_runs (job_id, status, duration, error_message, created_at) VALUES (?, ?, ?, ?, datetime('now'))", (job_id, status, duration, error))
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    print(f"✅ 已添加运行记录 ID {run_id}: job={job_id} status={status}")

def show_stats(job_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    if job_id:
        cursor.execute("SELECT COUNT(*) FROM cron_runs WHERE job_id = ?", (job_id,))
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM cron_runs WHERE job_id = ? AND status = 'success'", (job_id,))
        success = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM cron_runs WHERE job_id = ? AND status = 'failure'", (job_id,))
        failure = cursor.fetchone()[0]
        cursor.execute("SELECT AVG(duration) FROM cron_runs WHERE job_id = ? AND duration IS NOT NULL", (job_id,))
        avg_duration = cursor.fetchone()[0]
        cursor.execute("SELECT MAX(created_at) FROM cron_runs WHERE job_id = ?", (job_id,))
        last_run = cursor.fetchone()[0]
        cursor.execute("SELECT status FROM cron_runs WHERE job_id = ? ORDER BY created_at DESC LIMIT 10", (job_id,))
        recent_runs = [r[0] for r in cursor.fetchall()]
        consecutive_failures = 0
        for status in recent_runs:
            if status == "failure":
                consecutive_failures += 1
            else:
                break
        conn.close()
        print(f"=== Cron统计信息 (job_id: {job_id}) ===")
        print(f"总运行次数: {total}")
        print(f"成功: {success}")
        print(f"失败: {failure}")
        print(f"成功率: {success/total*100:.1f}%" if total > 0 else "成功率: N/A")
        print(f"平均耗时: {avg_duration:.1f}s" if avg_duration else "平均耗时: N/A")
        print(f"连续失败: {consecutive_failures} 次")
        print(f"最后运行: {last_run}")
    else:
        cursor.execute("SELECT COUNT(*) FROM cron_runs")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM cron_runs WHERE status = 'success'")
        success = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM cron_runs WHERE status = 'failure'")
        failure = cursor.fetchone()[0]
        cursor.execute("SELECT job_id, COUNT(*) FROM cron_runs GROUP BY job_id ORDER BY COUNT(*) DESC LIMIT 10")
        top_jobs = cursor.fetchall()
        conn.close()
        print("=== Cron统计信息 (全局) ===")
        print(f"总运行次数: {total}")
        print(f"成功: {success}")
        print(f"失败: {failure}")
        print(f"成功率: {success/total*100:.1f}%" if total > 0 else "成功率: N/A")
        print("\n运行次数最多的job:")
        for job in top_jobs:
            print(f"  {job[0]}: {job[1]} 次")

def list_failures(job_id=None, limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    if job_id:
        cursor.execute("SELECT run_id, job_id, status, duration, error_message, created_at FROM cron_runs WHERE job_id = ? AND status = 'failure' ORDER BY created_at DESC LIMIT ?", (job_id, limit))
    else:
        cursor.execute("SELECT run_id, job_id, status, duration, error_message, created_at FROM cron_runs WHERE status = 'failure' ORDER BY created_at DESC LIMIT ?", (limit,))
    failures = cursor.fetchall()
    conn.close()
    print(f"=== Cron失败记录 (最近 {len(failures)} 条) ===")
    for fail in failures:
        error_str = f" error={fail[4][:80]}..." if fail[4] else "无错误信息"
        print(f"❌ ID {fail[0]}: job={fail[1]} duration={fail[3]}s{error_str} ({fail[5]})")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    command = sys.argv[1]
    if command == "list":
        job_id = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None
        limit = 20
        if "--limit" in sys.argv:
            idx = sys.argv.index("--limit")
            if idx + 1 < len(sys.argv):
                limit = int(sys.argv[idx + 1])
        list_history(job_id, limit)
    elif command == "add":
        if len(sys.argv) < 4:
            print("错误: add 需要 job_id 和 status 参数")
            sys.exit(1)
        job_id = sys.argv[2]
        status = sys.argv[3]
        duration = None
        error = None
        i = 4
        while i < len(sys.argv):
            if sys.argv[i] == "--duration" and i + 1 < len(sys.argv):
                duration = int(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--error" and i + 1 < len(sys.argv):
                error = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        add_run(job_id, status, duration, error)
    elif command == "stats":
        job_id = sys.argv[2] if len(sys.argv) > 2 else None
        show_stats(job_id)
    elif command == "failures":
        job_id = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None
        limit = 10
        if "--limit" in sys.argv:
            idx = sys.argv.index("--limit")
            if idx + 1 < len(sys.argv):
                limit = int(sys.argv[idx + 1])
        list_failures(job_id, limit)
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
