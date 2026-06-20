#!/usr/bin/env python3
"""
Phoenix Protocol 修复效果评估CLI - 修复后运行测试用例，评估修复效果
用法: python3 phoenix_evaluate.py <command> [args...]

命令:
  test <test_name>        运行测试用例
  evaluate <repair_id>    评估修复效果
  list-tests              列出可用测试
"""

import sys
import os
import sqlite3
import subprocess
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
            status TEXT NOT NULL,
            duration REAL,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def run_test(test_name):
    """运行测试用例"""
    print(f"=== 运行测试: {test_name} ===")
    
    # 定义测试用例
    tests = {
        "memory-check": {
            "command": "python3 ~/.hermes/scripts/phoenix_diagnose.py check-memory",
            "description": "检查记忆系统健康"
        },
        "cron-check": {
            "command": "python3 ~/.hermes/scripts/phoenix_diagnose.py check-cron",
            "description": "检查Cron健康"
        },
        "skill-check": {
            "command": "python3 ~/.hermes/scripts/phoenix_diagnose.py check-skills",
            "description": "检查技能健康"
        },
        "fact-store-check": {
            "command": "python3 ~/.hermes/scripts/fact_store_cli.py stats",
            "description": "检查fact_store健康"
        },
        "cron-history-check": {
            "command": "python3 ~/.hermes/scripts/cron_history_cli.py stats",
            "description": "检查Cron历史健康"
        }
    }
    
    if test_name not in tests:
        print(f"错误: 未知测试 '{test_name}'")
        print("可用测试:")
        for name, test in tests.items():
            print(f"  - {name}: {test['description']}")
        return False
    
    test = tests[test_name]
    
    # 运行测试
    start_time = datetime.now()
    try:
        result = subprocess.run(test["command"], shell=True, capture_output=True, text=True, timeout=60)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if result.returncode == 0:
            print(f"✅ 测试通过 ({duration:.2f}s)")
            print(result.stdout)
            
            # 记录结果
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO eval_results (test_name, status, duration, created_at)
                VALUES (?, 'success', ?, datetime('now'))
            """, (test_name, duration))
            conn.commit()
            conn.close()
            
            return True
        else:
            print(f"❌ 测试失败 ({duration:.2f}s)")
            print(f"错误: {result.stderr}")
            
            # 记录结果
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO eval_results (test_name, status, duration, error_message, created_at)
                VALUES (?, 'failure', ?, ?, datetime('now'))
            """, (test_name, duration, result.stderr))
            conn.commit()
            conn.close()
            
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ 测试超时 (60s)")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def evaluate_repair(repair_id):
    """评估修复效果"""
    print(f"=== 评估修复效果: {repair_id} ===")
    
    # 运行所有测试
    tests = ["memory-check", "cron-check", "skill-check", "fact-store-check", "cron-history-check"]
    
    results = []
    for test_name in tests:
        success = run_test(test_name)
        results.append((test_name, success))
    
    # 统计结果
    total = len(results)
    passed = sum(1 for _, success in results if success)
    failed = total - passed
    
    print("\n=== 评估结果 ===")
    print(f"总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"通过率: {passed/total*100:.1f}%")
    
    if failed == 0:
        print("\n✅ 修复效果良好")
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败，需要进一步检查")

def list_tests():
    """列出可用测试"""
    print("=== 可用测试 ===")
    print("  - memory-check: 检查记忆系统健康")
    print("  - cron-check: 检查Cron健康")
    print("  - skill-check: 检查技能健康")
    print("  - fact-store-check: 检查fact_store健康")
    print("  - cron-history-check: 检查Cron历史健康")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "test":
        if len(sys.argv) < 3:
            print("错误: test 需要测试名称")
            sys.exit(1)
        run_test(sys.argv[2])
    elif command == "evaluate":
        if len(sys.argv) < 3:
            print("错误: evaluate 需要修复ID")
            sys.exit(1)
        evaluate_repair(sys.argv[2])
    elif command == "list-tests":
        list_tests()
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
