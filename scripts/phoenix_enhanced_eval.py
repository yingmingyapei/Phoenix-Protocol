#!/usr/bin/env python3
"""
Phoenix Protocol 增强评估CLI - 添加更多测试用例
用法: python3 phoenix_enhanced_eval.py <command> [args...]

命令:
  test-all               运行所有测试
  test-category <cat>    运行指定类别测试
  list-categories        列出测试类别
  report                 生成测试报告
"""

import sys
import os
import sqlite3
import subprocess
import json
from datetime import datetime

HERMES_HOME = os.path.expanduser("~/.hermes")
EVAL_DB = os.path.join(HERMES_HOME, "phoenix_eval.db")

def get_connection():
    conn = sqlite3.connect(EVAL_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eval_results (
            eval_id INTEGER PRIMARY KEY AUTOINCREMENT,
            repair_id TEXT,
            test_name TEXT NOT NULL,
            test_category TEXT,
            status TEXT NOT NULL,
            duration REAL,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

# 测试用例定义
TEST_CASES = {
    "memory": [
        {"name": "memory-md-exists", "command": "test -f ~/.hermes/memories/MEMORY.md", "description": "检查MEMORY.md是否存在"},
        {"name": "memory-md-lines", "command": "python3 -c \"with open('/home/yingming/.hermes/memories/MEMORY.md') as f: lines=[l for l in f.read().split('\\n') if l.strip() and l.strip()!='§']; print(len(lines))\"", "description": "检查MEMORY.md规则数量"},
        {"name": "user-md-exists", "command": "test -f ~/.hermes/memories/USER.md", "description": "检查USER.md是否存在"},
        {"name": "fact-store-exists", "command": "test -f ~/.hermes/memory_store.db", "description": "检查fact_store数据库是否存在"},
        {"name": "no-orphan-files", "command": "test $(ls ~/.hermes/memories/memory/*.md 2>/dev/null | wc -l) -eq 0", "description": "检查无孤儿文件"},
    ],
    "cron": [
        {"name": "cron-history-exists", "command": "test -f ~/.hermes/cron_history.db", "description": "检查Cron历史数据库是否存在"},
        {"name": "cron-scripts-exist", "command": "test -f ~/.hermes/scripts/cron_history_cli.py", "description": "检查Cron历史CLI是否存在"},
    ],
    "skills": [
        {"name": "skills-dir-exists", "command": "test -d ~/.hermes/skills", "description": "检查技能目录是否存在"},
        {"name": "evolution-engine-exists", "command": "test -f ~/.hermes/skills/hermes/evolution-engine/SKILL.md", "description": "检查evolution-engine技能是否存在"},
        {"name": "agent-self-evolution-exists", "command": "test -f ~/.hermes/skills/self-improvement/agent-self-evolution/SKILL.md", "description": "检查agent-self-evolution技能是否存在"},
    ],
    "scripts": [
        {"name": "fact-store-cli", "command": "test -f ~/.hermes/scripts/fact_store_cli.py", "description": "检查fact_store CLI是否存在"},
        {"name": "cron-history-cli", "command": "test -f ~/.hermes/scripts/cron_history_cli.py", "description": "检查Cron历史CLI是否存在"},
        {"name": "phoenix-diagnose", "command": "test -f ~/.hermes/scripts/phoenix_diagnose.py", "description": "检查诊断CLI是否存在"},
        {"name": "phoenix-rollback", "command": "test -f ~/.hermes/scripts/phoenix_rollback.py", "description": "检查回滚CLI是否存在"},
        {"name": "phoenix-evaluate", "command": "test -f ~/.hermes/scripts/phoenix_evaluate.py", "description": "检查评估CLI是否存在"},
        {"name": "phoenix-lesson-graph", "command": "test -f ~/.hermes/scripts/phoenix_lesson_graph.py", "description": "检查教训图谱CLI是否存在"},
        {"name": "phoenix-preventive", "command": "test -f ~/.hermes/scripts/phoenix_preventive.py", "description": "检查预防性维护CLI是否存在"},
        {"name": "phoenix-collab", "command": "test -f ~/.hermes/scripts/phoenix_collab.py", "description": "检查协同CLI是否存在"},
    ],
    "functionality": [
        {"name": "fact-store-stats", "command": "python3 ~/.hermes/scripts/fact_store_cli.py stats", "description": "测试fact_store统计功能"},
        {"name": "cron-history-stats", "command": "python3 ~/.hermes/scripts/cron_history_cli.py stats", "description": "测试Cron历史统计功能"},
        {"name": "phoenix-diagnose-health", "command": "python3 ~/.hermes/scripts/phoenix_diagnose.py health", "description": "测试诊断健康检查功能"},
    ]
}

def run_test(test_case):
    """运行单个测试"""
    try:
        result = subprocess.run(test_case["command"], shell=True, capture_output=True, text=True, timeout=30)
        return {
            "name": test_case["name"],
            "category": test_case.get("category", "unknown"),
            "status": "success" if result.returncode == 0 else "failure",
            "duration": 0,
            "error": result.stderr if result.returncode != 0 else None
        }
    except subprocess.TimeoutExpired:
        return {
            "name": test_case["name"],
            "category": test_case.get("category", "unknown"),
            "status": "timeout",
            "duration": 30,
            "error": "测试超时"
        }
    except Exception as e:
        return {
            "name": test_case["name"],
            "category": test_case.get("category", "unknown"),
            "status": "error",
            "duration": 0,
            "error": str(e)
        }

def run_all_tests():
    """运行所有测试"""
    print("=== 运行所有测试 ===")
    
    results = []
    for category, tests in TEST_CASES.items():
        print(f"\n--- {category} ---")
        for test in tests:
            test["category"] = category
            result = run_test(test)
            results.append(result)
            
            status_icon = "✅" if result["status"] == "success" else "❌"
            print(f"{status_icon} {result['name']}: {result['status']}")
            if result["error"]:
                print(f"   错误: {result['error'][:100]}")
    
    # 保存结果
    conn = get_connection()
    cursor = conn.cursor()
    for result in results:
        cursor.execute("""
            INSERT INTO eval_results (test_name, test_category, status, duration, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (result["name"], result["category"], result["status"], result["duration"], result["error"]))
    conn.commit()
    conn.close()
    
    # 统计结果
    total = len(results)
    success = sum(1 for r in results if r["status"] == "success")
    failure = total - success
    
    print(f"\n=== 测试结果 ===")
    print(f"总测试数: {total}")
    print(f"通过: {success}")
    print(f"失败: {failure}")
    print(f"通过率: {success/total*100:.1f}%")
    
    return results

def run_category_tests(category):
    """运行指定类别测试"""
    if category not in TEST_CASES:
        print(f"错误: 未知类别 '{category}'")
        print(f"可用类别: {', '.join(TEST_CASES.keys())}")
        return []
    
    print(f"=== 运行 {category} 测试 ===")
    
    results = []
    for test in TEST_CASES[category]:
        test["category"] = category
        result = run_test(test)
        results.append(result)
        
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"{status_icon} {result['name']}: {result['status']}")
        if result["error"]:
            print(f"   错误: {result['error'][:100]}")
    
    # 保存结果
    conn = get_connection()
    cursor = conn.cursor()
    for result in results:
        cursor.execute("""
            INSERT INTO eval_results (test_name, test_category, status, duration, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (result["name"], result["category"], result["status"], result["duration"], result["error"]))
    conn.commit()
    conn.close()
    
    return results

def list_categories():
    """列出测试类别"""
    print("=== 测试类别 ===")
    for category, tests in TEST_CASES.items():
        print(f"{category}: {len(tests)} 个测试")

def generate_report():
    """生成测试报告"""
    print("=== 测试报告 ===")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 获取最近的测试结果
    cursor.execute("""
        SELECT test_category, status, COUNT(*) 
        FROM eval_results 
        WHERE created_at >= datetime('now', '-1 day')
        GROUP BY test_category, status
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        print("最近没有测试结果")
        return
    
    # 按类别统计
    category_stats = {}
    for category, status, count in results:
        if category not in category_stats:
            category_stats[category] = {"success": 0, "failure": 0, "timeout": 0, "error": 0}
        category_stats[category][status] = count
    
    # 输出报告
    for category, stats in category_stats.items():
        total = sum(stats.values())
        success = stats.get("success", 0)
        print(f"\n{category}:")
        print(f"  总测试: {total}")
        print(f"  通过: {success}")
        print(f"  失败: {total - success}")
        print(f"  通过率: {success/total*100:.1f}%" if total > 0 else "  通过率: N/A")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "test-all":
        run_all_tests()
    elif command == "test-category":
        if len(sys.argv) < 3:
            print("错误: test-category 需要类别名称")
            sys.exit(1)
        run_category_tests(sys.argv[2])
    elif command == "list-categories":
        list_categories()
    elif command == "report":
        generate_report()
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
