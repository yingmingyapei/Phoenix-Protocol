#!/usr/bin/env python3
"""
Phoenix Protocol AI辅助诊断CLI - 使用AI分析错误日志和系统状态
用法: python3 phoenix_ai_diagnose.py <command> [args...]

命令:
  analyze-logs [days]     分析最近N天的错误日志
  analyze-cron            分析Cron运行模式
  analyze-memory          分析记忆系统健康
  suggest-fix             生成修复建议
"""

import sys
import os
import sqlite3
import json
from datetime import datetime, timedelta

HERMES_HOME = os.path.expanduser("~/.hermes")
ERROR_LOG = os.path.join(HERMES_HOME, "errors.log")
CRON_DB = os.path.join(HERMES_HOME, "cron_history.db")
MEMORY_DB = os.path.join(HERMES_HOME, "memory_store.db")

def analyze_error_logs(days=7):
    """分析错误日志"""
    print(f"=== 分析最近 {days} 天的错误日志 ===")
    
    if not os.path.exists(ERROR_LOG):
        print("错误日志文件不存在")
        return []
    
    errors = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    with open(ERROR_LOG, 'r') as f:
        for line in f:
            # 简单的日期提取（假设格式为 YYYY-MM-DD HH:MM:SS）
            try:
                if len(line) > 19:
                    date_str = line[:19]
                    log_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    if log_date >= cutoff_date:
                        errors.append({
                            "timestamp": date_str,
                            "message": line[20:].strip()
                        })
            except:
                continue
    
    print(f"找到 {len(errors)} 条错误日志")
    
    # 分析错误模式
    error_patterns = {}
    for error in errors:
        # 提取关键词
        keywords = ["timeout", "failed", "error", "exception", "connection"]
        for keyword in keywords:
            if keyword in error["message"].lower():
                if keyword not in error_patterns:
                    error_patterns[keyword] = 0
                error_patterns[keyword] += 1
    
    if error_patterns:
        print("\n错误模式统计:")
        for pattern, count in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True):
            print(f"  {pattern}: {count} 次")
    
    return errors

def analyze_cron_patterns():
    """分析Cron运行模式"""
    print("=== 分析Cron运行模式 ===")
    
    if not os.path.exists(CRON_DB):
        print("Cron历史数据库不存在")
        return {}
    
    conn = sqlite3.connect(CRON_DB)
    cursor = conn.cursor()
    
    # 分析每个job的运行模式
    cursor.execute("""
        SELECT job_id, 
               COUNT(*) as total_runs,
               SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_runs,
               SUM(CASE WHEN status = 'failure' THEN 1 ELSE 0 END) as failure_runs,
               AVG(duration) as avg_duration,
               MIN(created_at) as first_run,
               MAX(created_at) as last_run
        FROM cron_runs
        GROUP BY job_id
    """)
    
    patterns = {}
    for row in cursor.fetchall():
        job_id = row[0]
        patterns[job_id] = {
            "total_runs": row[1],
            "success_runs": row[2],
            "failure_runs": row[3],
            "avg_duration": row[4],
            "first_run": row[5],
            "last_run": row[6],
            "success_rate": row[2] / row[1] * 100 if row[1] > 0 else 0
        }
    
    conn.close()
    
    # 输出分析结果
    for job_id, pattern in patterns.items():
        print(f"\nJob: {job_id}")
        print(f"  总运行: {pattern['total_runs']}")
        print(f"  成功: {pattern['success_runs']}")
        print(f"  失败: {pattern['failure_runs']}")
        print(f"  成功率: {pattern['success_rate']:.1f}%")
        print(f"  平均耗时: {pattern['avg_duration']:.1f}s" if pattern['avg_duration'] else "  平均耗时: N/A")
        print(f"  首次运行: {pattern['first_run']}")
        print(f"  最后运行: {pattern['last_run']}")
    
    return patterns

def analyze_memory_health():
    """分析记忆系统健康"""
    print("=== 分析记忆系统健康 ===")
    
    if not os.path.exists(MEMORY_DB):
        print("记忆数据库不存在")
        return {}
    
    conn = sqlite3.connect(MEMORY_DB)
    cursor = conn.cursor()
    
    # 分析fact使用情况
    cursor.execute("SELECT COUNT(*) FROM facts")
    total_facts = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM facts WHERE trust_score < 0.3")
    low_trust = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM facts WHERE retrieval_count = 0")
    never_retrieved = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(trust_score) FROM facts")
    avg_trust = cursor.fetchone()[0]
    
    # 分析category分布
    cursor.execute("SELECT category, COUNT(*) FROM facts GROUP BY category")
    categories = cursor.fetchall()
    
    conn.close()
    
    print(f"总fact数: {total_facts}")
    print(f"低信任 (<0.3): {low_trust}")
    print(f"从未检索: {never_retrieved}")
    print(f"平均信任分: {avg_trust:.2f}")
    
    print("\nCategory分布:")
    for cat, count in categories:
        print(f"  {cat}: {count}")
    
    return {
        "total_facts": total_facts,
        "low_trust": low_trust,
        "never_retrieved": never_retrieved,
        "avg_trust": avg_trust,
        "categories": dict(categories)
    }

def generate_fix_suggestions():
    """生成修复建议"""
    print("=== 生成修复建议 ===")
    
    suggestions = []
    
    # 分析错误日志
    errors = analyze_error_logs(7)
    if errors:
        suggestions.append({
            "priority": "high",
            "category": "logs",
            "description": f"最近7天有 {len(errors)} 条错误日志",
            "action": "检查错误日志，修复常见问题"
        })
    
    # 分析Cron模式
    cron_patterns = analyze_cron_patterns()
    for job_id, pattern in cron_patterns.items():
        if pattern["success_rate"] < 80:
            suggestions.append({
                "priority": "high",
                "category": "cron",
                "description": f"Job {job_id} 成功率低 ({pattern['success_rate']:.1f}%)",
                "action": "检查job配置，修复失败原因"
            })
    
    # 分析记忆系统
    memory_health = analyze_memory_health()
    if memory_health.get("low_trust", 0) > 10:
        suggestions.append({
            "priority": "medium",
            "category": "memory",
            "description": f"低信任fact过多 ({memory_health['low_trust']} 条)",
            "action": "清理低信任fact"
        })
    
    # 输出建议
    if suggestions:
        print(f"\n生成 {len(suggestions)} 条修复建议:")
        for i, suggestion in enumerate(suggestions, 1):
            priority_icon = "🔴" if suggestion["priority"] == "high" else "🟡" if suggestion["priority"] == "medium" else "🟢"
            print(f"\n{priority_icon} 建议 {i}: {suggestion['description']}")
            print(f"   类别: {suggestion['category']}")
            print(f"   操作: {suggestion['action']}")
    else:
        print("\n✅ 无需修复")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "analyze-logs":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        analyze_error_logs(days)
    elif command == "analyze-cron":
        analyze_cron_patterns()
    elif command == "analyze-memory":
        analyze_memory_health()
    elif command == "suggest-fix":
        generate_fix_suggestions()
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
