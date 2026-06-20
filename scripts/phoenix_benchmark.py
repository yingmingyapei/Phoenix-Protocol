#!/usr/bin/env python3
"""
Phoenix Protocol 性能基准测试CLI - 添加性能基准测试
用法: python3 phoenix_benchmark.py <command> [args...]

命令:
  run                     运行所有基准测试
  test <test_name>        运行指定测试
  list                    列出可用测试
  compare                 比较历史结果
"""

import sys
import os
import time
import sqlite3
import subprocess
from datetime import datetime

HERMES_HOME = os.path.expanduser("~/.hermes")
BENCHMARK_DB = os.path.join(HERMES_HOME, "phoenix_benchmark.db")

def get_connection():
    conn = sqlite3.connect(BENCHMARK_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_results (
            benchmark_id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT NOT NULL,
            duration REAL NOT NULL,
            status TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

# 基准测试定义
BENCHMARK_TESTS = {
    "fact_store_read": {
        "command": "python3 ~/.hermes/scripts/fact_store_cli.py stats",
        "description": "fact_store读取性能",
        "threshold": 1.0  # 1秒
    },
    "fact_store_search": {
        "command": "python3 ~/.hermes/scripts/fact_store_cli.py search 'MEMORY.md'",
        "description": "fact_store搜索性能",
        "threshold": 1.0
    },
    "cron_history_read": {
        "command": "python3 ~/.hermes/scripts/cron_history_cli.py stats",
        "description": "Cron历史读取性能",
        "threshold": 1.0
    },
    "memory_file_read": {
        "command": "cat ~/.hermes/memories/MEMORY.md",
        "description": "MEMORY.md读取性能",
        "threshold": 0.1
    },
    "user_file_read": {
        "command": "cat ~/.hermes/memories/USER.md",
        "description": "USER.md读取性能",
        "threshold": 0.1
    },
    "diagnose_health": {
        "command": "python3 ~/.hermes/scripts/phoenix_diagnose.py health",
        "description": "健康检查性能",
        "threshold": 5.0
    }
}

def run_benchmark(test_name, test_info):
    """运行单个基准测试"""
    try:
        start_time = time.time()
        result = subprocess.run(test_info["command"], shell=True, capture_output=True, text=True, timeout=30)
        end_time = time.time()
        
        duration = end_time - start_time
        status = "success" if result.returncode == 0 else "failure"
        
        return {
            "test_name": test_name,
            "duration": duration,
            "status": status,
            "details": result.stdout if result.returncode == 0 else result.stderr,
            "threshold": test_info["threshold"],
            "passed": duration <= test_info["threshold"]
        }
    except subprocess.TimeoutExpired:
        return {
            "test_name": test_name,
            "duration": 30,
            "status": "timeout",
            "details": "测试超时",
            "threshold": test_info["threshold"],
            "passed": False
        }
    except Exception as e:
        return {
            "test_name": test_name,
            "duration": 0,
            "status": "error",
            "details": str(e),
            "threshold": test_info["threshold"],
            "passed": False
        }

def run_all_benchmarks():
    """运行所有基准测试"""
    print("=== 运行所有基准测试 ===")
    
    results = []
    for test_name, test_info in BENCHMARK_TESTS.items():
        print(f"\n运行 {test_info['description']}...")
        result = run_benchmark(test_name, test_info)
        results.append(result)
        
        status_icon = "✅" if result["passed"] else "❌"
        print(f"{status_icon} {test_name}: {result['duration']:.3f}s (阈值: {result['threshold']}s)")
    
    # 保存结果
    conn = get_connection()
    cursor = conn.cursor()
    for result in results:
        cursor.execute("""
            INSERT INTO benchmark_results (test_name, duration, status, details, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (result["test_name"], result["duration"], result["status"], result["details"]))
    conn.commit()
    conn.close()
    
    # 统计结果
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    
    print(f"\n=== 基准测试结果 ===")
    print(f"总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"通过率: {passed/total*100:.1f}%")
    
    # 显示失败的测试
    if failed > 0:
        print(f"\n失败的测试:")
        for result in results:
            if not result["passed"]:
                print(f"  ❌ {result['test_name']}: {result['duration']:.3f}s (阈值: {result['threshold']}s)")
    
    return results

def run_single_test(test_name):
    """运行单个测试"""
    if test_name not in BENCHMARK_TESTS:
        print(f"错误: 未知测试 '{test_name}'")
        print(f"可用测试: {', '.join(BENCHMARK_TESTS.keys())}")
        return
    
    test_info = BENCHMARK_TESTS[test_name]
    print(f"=== 运行 {test_info['description']} ===")
    
    result = run_benchmark(test_name, test_info)
    
    status_icon = "✅" if result["passed"] else "❌"
    print(f"{status_icon} {test_name}: {result['duration']:.3f}s (阈值: {result['threshold']}s)")
    
    if result["details"]:
        print(f"\n详细信息:")
        print(result["details"][:500])
    
    # 保存结果
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO benchmark_results (test_name, duration, status, details, created_at)
        VALUES (?, ?, ?, ?, datetime('now'))
    """, (result["test_name"], result["duration"], result["status"], result["details"]))
    conn.commit()
    conn.close()

def list_tests():
    """列出可用测试"""
    print("=== 可用基准测试 ===")
    for test_name, test_info in BENCHMARK_TESTS.items():
        print(f"  - {test_name}: {test_info['description']} (阈值: {test_info['threshold']}s)")

def compare_results():
    """比较历史结果"""
    print("=== 比较历史结果 ===")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 获取每个测试的最新结果
    cursor.execute("""
        SELECT test_name, duration, created_at 
        FROM benchmark_results 
        WHERE (test_name, created_at) IN (
            SELECT test_name, MAX(created_at) 
            FROM benchmark_results 
            GROUP BY test_name
        )
        ORDER BY test_name
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        print("没有历史结果")
        return
    
    print(f"\n最新基准测试结果:")
    for test_name, duration, created_at in results:
        threshold = BENCHMARK_TESTS.get(test_name, {}).get("threshold", 0)
        status = "✅" if duration <= threshold else "❌"
        print(f"{status} {test_name}: {duration:.3f}s (阈值: {threshold}s) - {created_at}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "run":
        run_all_benchmarks()
    elif command == "test":
        if len(sys.argv) < 3:
            print("错误: test 需要测试名称")
            sys.exit(1)
        run_single_test(sys.argv[2])
    elif command == "list":
        list_tests()
    elif command == "compare":
        compare_results()
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
