#!/usr/bin/env python3
"""
Phoenix Protocol 定时预测CLI - 定时运行预测和维护建议
用法: python3 phoenix_scheduled.py <command> [args...]

命令:
  run                     运行定时预测
  schedule                显示定时任务
  report                  生成预测报告
"""

import sys
import os
import sqlite3
import json
from datetime import datetime, timedelta

HERMES_HOME = os.path.expanduser("~/.hermes")
PREDICT_DB = os.path.join(HERMES_HOME, "phoenix_predictions.db")
CRON_DB = os.path.join(HERMES_HOME, "cron_history.db")
MEMORY_DB = os.path.join(HERMES_HOME, "memory_store.db")

def get_predict_connection():
    conn = sqlite3.connect(PREDICT_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT NOT NULL,
            recommendation TEXT,
            confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def analyze_cron_health():
    """分析Cron健康状态"""
    if not os.path.exists(CRON_DB):
        return []
    
    conn = sqlite3.connect(CRON_DB)
    cursor = conn.cursor()
    
    # 分析每个job的运行模式
    cursor.execute("""
        SELECT job_id, 
               COUNT(*) as total_runs,
               SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_runs,
               SUM(CASE WHEN status = 'failure' THEN 1 ELSE 0 END) as failure_runs,
               AVG(duration) as avg_duration
        FROM cron_runs
        GROUP BY job_id
    """)
    
    predictions = []
    for row in cursor.fetchall():
        job_id = row[0]
        total_runs = row[1]
        success_runs = row[2]
        failure_runs = row[3]
        avg_duration = row[4]
        
        success_rate = success_runs / total_runs * 100 if total_runs > 0 else 0
        
        # 预测潜在问题
        if success_rate < 80:
            predictions.append({
                "type": "cron_failure",
                "severity": "high",
                "description": f"Job {job_id} 成功率低 ({success_rate:.1f}%)",
                "recommendation": "检查job配置，修复失败原因",
                "confidence": 0.9
            })
        
        if failure_runs >= 3:
            predictions.append({
                "type": "cron_consecutive_failure",
                "severity": "high",
                "description": f"Job {job_id} 连续失败 {failure_runs} 次",
                "recommendation": "立即检查job状态",
                "confidence": 0.95
            })
        
        if avg_duration and avg_duration > 300:  # 超过5分钟
            predictions.append({
                "type": "cron_slow",
                "severity": "medium",
                "description": f"Job {job_id} 执行时间过长 ({avg_duration:.1f}s)",
                "recommendation": "优化job执行效率",
                "confidence": 0.7
            })
    
    conn.close()
    return predictions

def analyze_memory_health():
    """分析记忆系统健康"""
    if not os.path.exists(MEMORY_DB):
        return []
    
    conn = sqlite3.connect(MEMORY_DB)
    cursor = conn.cursor()
    
    predictions = []
    
    # 分析低信任fact
    cursor.execute("SELECT COUNT(*) FROM facts WHERE trust_score < 0.3")
    low_trust = cursor.fetchone()[0]
    if low_trust > 10:
        predictions.append({
            "type": "memory_low_trust",
            "severity": "medium",
            "description": f"低信任fact过多 ({low_trust} 条)",
            "recommendation": "清理低信任fact",
            "confidence": 0.8
        })
    
    # 分析从未检索的fact
    cursor.execute("SELECT COUNT(*) FROM facts WHERE retrieval_count = 0")
    never_retrieved = cursor.fetchone()[0]
    if never_retrieved > 50:
        predictions.append({
            "type": "memory_unused",
            "severity": "low",
            "description": f"从未检索的fact过多 ({never_retrieved} 条)",
            "recommendation": "评估是否需要清理",
            "confidence": 0.6
        })
    
    conn.close()
    return predictions

def run_prediction():
    """运行预测"""
    print("=== 运行预测 ===")
    
    all_predictions = []
    
    # 分析Cron健康
    cron_predictions = analyze_cron_health()
    all_predictions.extend(cron_predictions)
    
    # 分析记忆系统
    memory_predictions = analyze_memory_health()
    all_predictions.extend(memory_predictions)
    
    # 保存预测结果
    conn = get_predict_connection()
    cursor = conn.cursor()
    
    for pred in all_predictions:
        cursor.execute("""
            INSERT INTO predictions (prediction_type, severity, description, recommendation, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (pred["type"], pred["severity"], pred["description"], pred["recommendation"], pred["confidence"]))
    
    conn.commit()
    conn.close()
    
    # 输出预测结果
    if all_predictions:
        print(f"\n发现 {len(all_predictions)} 个潜在问题:")
        for i, pred in enumerate(all_predictions, 1):
            severity_icon = "🔴" if pred["severity"] == "high" else "🟡" if pred["severity"] == "medium" else "🟢"
            print(f"\n{severity_icon} 问题 {i}: {pred['description']}")
            print(f"   类型: {pred['type']}")
            print(f"   建议: {pred['recommendation']}")
            print(f"   置信度: {pred['confidence']:.0%}")
    else:
        print("\n✅ 未发现潜在问题")
    
    return all_predictions

def show_schedule():
    """显示定时任务"""
    print("=== 定时任务 ===")
    print("建议的定时任务:")
    print("  1. 每日预测: 每天早上8:00运行")
    print("  2. 每周报告: 每周日晚上20:00运行")
    print("  3. 月度清理: 每月1日运行")

def generate_report():
    """生成预测报告"""
    print("=== 预测报告 ===")
    
    conn = get_predict_connection()
    cursor = conn.cursor()
    
    # 获取最近的预测
    cursor.execute("""
        SELECT prediction_type, severity, description, recommendation, confidence, created_at 
        FROM predictions 
        WHERE created_at >= datetime('now', '-7 days')
        ORDER BY created_at DESC
    """)
    
    predictions = cursor.fetchall()
    conn.close()
    
    if not predictions:
        print("最近7天没有预测记录")
        return
    
    print(f"\n最近7天的预测 ({len(predictions)} 条):")
    
    # 按严重程度统计
    severity_stats = {"high": 0, "medium": 0, "low": 0}
    for pred in predictions:
        severity_stats[pred[1]] = severity_stats.get(pred[1], 0) + 1
    
    print(f"\n严重程度统计:")
    print(f"  🔴 高: {severity_stats.get('high', 0)}")
    print(f"  🟡 中: {severity_stats.get('medium', 0)}")
    print(f"  🟢 低: {severity_stats.get('low', 0)}")
    
    # 显示最近的预测
    print(f"\n最近的预测:")
    for pred in predictions[:5]:
        severity_icon = "🔴" if pred[1] == "high" else "🟡" if pred[1] == "medium" else "🟢"
        print(f"  {severity_icon} {pred[2][:50]}... ({pred[5]})")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "run":
        run_prediction()
    elif command == "schedule":
        show_schedule()
    elif command == "report":
        generate_report()
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
