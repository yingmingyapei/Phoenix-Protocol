#!/usr/bin/env python3
"""
Phoenix Protocol 预防性维护CLI - 基于历史数据预测潜在故障
用法: python3 phoenix_preventive.py <command> [args...]

命令:
  predict                 预测潜在故障
  analyze                 分析历史数据
  recommend               生成维护建议
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta

HERMES_HOME = os.path.expanduser("~/.hermes")
MEMORY_DB = os.path.join(HERMES_HOME, "memory_store.db")
CRON_DB = os.path.join(HERMES_HOME, "cron_history.db")

def analyze_cron_patterns():
    """分析Cron运行模式"""
    if not os.path.exists(CRON_DB):
        return {}
    
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
    
    patterns = {}
    for row in cursor.fetchall():
        job_id = row[0]
        patterns[job_id] = {
            "total_runs": row[1],
            "success_runs": row[2],
            "failure_runs": row[3],
            "avg_duration": row[4],
            "success_rate": row[2] / row[1] * 100 if row[1] > 0 else 0
        }
    
    conn.close()
    return patterns

def analyze_memory_health():
    """分析记忆系统健康"""
    if not os.path.exists(MEMORY_DB):
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
    
    conn.close()
    
    return {
        "total_facts": total_facts,
        "low_trust": low_trust,
        "never_retrieved": never_retrieved,
        "avg_trust": avg_trust
    }

def predict_failures():
    """预测潜在故障"""
    print("=== 预测潜在故障 ===")
    
    predictions = []
    
    # 分析Cron模式
    cron_patterns = analyze_cron_patterns()
    for job_id, pattern in cron_patterns.items():
        if pattern["success_rate"] < 80:
            predictions.append({
                "type": "cron_failure",
                "severity": "high",
                "description": f"Job {job_id} 成功率低 ({pattern['success_rate']:.1f}%)",
                "recommendation": "检查job配置和依赖服务"
            })
        
        if pattern["failure_runs"] >= 3:
            predictions.append({
                "type": "cron_consecutive_failure",
                "severity": "high",
                "description": f"Job {job_id} 连续失败 {pattern['failure_runs']} 次",
                "recommendation": "立即检查job状态"
            })
    
    # 分析记忆系统
    memory_health = analyze_memory_health()
    if memory_health.get("low_trust", 0) > 10:
        predictions.append({
            "type": "memory_low_trust",
            "severity": "medium",
            "description": f"低信任fact过多 ({memory_health['low_trust']} 条)",
            "recommendation": "清理低信任fact"
        })
    
    if memory_health.get("never_retrieved", 0) > 50:
        predictions.append({
            "type": "memory_unused",
            "severity": "low",
            "description": f"从未检索的fact过多 ({memory_health['never_retrieved']} 条)",
            "recommendation": "评估是否需要清理"
        })
    
    # 输出预测结果
    if predictions:
        print(f"\n发现 {len(predictions)} 个潜在问题:")
        for i, pred in enumerate(predictions, 1):
            severity_icon = "🔴" if pred["severity"] == "high" else "🟡" if pred["severity"] == "medium" else "🟢"
            print(f"\n{severity_icon} 问题 {i}: {pred['description']}")
            print(f"   类型: {pred['type']}")
            print(f"   建议: {pred['recommendation']}")
    else:
        print("\n✅ 未发现潜在问题")

def analyze_history():
    """分析历史数据"""
    print("=== 分析历史数据 ===")
    
    # 分析Cron历史
    cron_patterns = analyze_cron_patterns()
    if cron_patterns:
        print("\nCron运行统计:")
        for job_id, pattern in cron_patterns.items():
            print(f"  {job_id}:")
            print(f"    总运行: {pattern['total_runs']}")
            print(f"    成功: {pattern['success_runs']}")
            print(f"    失败: {pattern['failure_runs']}")
            print(f"    成功率: {pattern['success_rate']:.1f}%")
            print(f"    平均耗时: {pattern['avg_duration']:.1f}s" if pattern['avg_duration'] else "    平均耗时: N/A")
    
    # 分析记忆系统
    memory_health = analyze_memory_health()
    if memory_health:
        print("\n记忆系统统计:")
        print(f"  总fact数: {memory_health.get('total_facts', 0)}")
        print(f"  低信任: {memory_health.get('low_trust', 0)}")
        print(f"  从未检索: {memory_health.get('never_retrieved', 0)}")
        print(f"  平均信任分: {memory_health.get('avg_trust', 0):.2f}")

def generate_recommendations():
    """生成维护建议"""
    print("=== 维护建议 ===")
    
    recommendations = []
    
    # 分析Cron模式
    cron_patterns = analyze_cron_patterns()
    for job_id, pattern in cron_patterns.items():
        if pattern["success_rate"] < 90:
            recommendations.append({
                "priority": "high",
                "category": "cron",
                "description": f"优化Job {job_id} 的成功率 (当前: {pattern['success_rate']:.1f}%)",
                "action": "检查job配置，修复失败原因"
            })
    
    # 分析记忆系统
    memory_health = analyze_memory_health()
    if memory_health.get("low_trust", 0) > 5:
        recommendations.append({
            "priority": "medium",
            "category": "memory",
            "description": f"清理低信任fact ({memory_health['low_trust']} 条)",
            "action": "使用fact_store_cli.py remove删除低信任fact"
        })
    
    if memory_health.get("never_retrieved", 0) > 30:
        recommendations.append({
            "priority": "low",
            "category": "memory",
            "description": f"评估从未检索的fact ({memory_health['never_retrieved']} 条)",
            "action": "检查是否需要保留这些fact"
        })
    
    # 输出建议
    if recommendations:
        print(f"\n生成 {len(recommendations)} 条维护建议:")
        for i, rec in enumerate(recommendations, 1):
            priority_icon = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
            print(f"\n{priority_icon} 建议 {i}: {rec['description']}")
            print(f"   类别: {rec['category']}")
            print(f"   操作: {rec['action']}")
    else:
        print("\n✅ 无需维护")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "predict":
        predict_failures()
    elif command == "analyze":
        analyze_history()
    elif command == "recommend":
        generate_recommendations()
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
