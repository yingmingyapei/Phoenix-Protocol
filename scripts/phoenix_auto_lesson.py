#!/usr/bin/env python3
"""
Phoenix Protocol 自动提取教训CLI - 从错误日志和修复记录中自动提取教训
用法: python3 phoenix_auto_lesson.py <command> [args...]

命令:
  extract-logs            从错误日志提取教训
  extract-cron            从Cron失败提取教训
  extract-memory          从记忆系统提取教训
  auto-extract            自动提取所有教训
"""

import sys
import os
import sqlite3
import re
from datetime import datetime

HERMES_HOME = os.path.expanduser("~/.hermes")
ERROR_LOG = os.path.join(HERMES_HOME, "errors.log")
CRON_DB = os.path.join(HERMES_HOME, "cron_history.db")
LESSON_DB = os.path.join(HERMES_HOME, "phoenix_lessons.db")

def get_lesson_connection():
    conn = sqlite3.connect(LESSON_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            category TEXT,
            severity TEXT,
            source TEXT,
            parent_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES lessons(lesson_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_relations (
            relation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL,
            related_id INTEGER NOT NULL,
            relation_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lesson_id) REFERENCES lessons(lesson_id),
            FOREIGN KEY (related_id) REFERENCES lessons(lesson_id)
        )
    """)
    conn.commit()
    return conn

def add_lesson(content, category=None, severity=None, source=None, parent_id=None):
    """添加教训"""
    conn = get_lesson_connection()
    cursor = conn.cursor()
    
    # 检查是否已存在相同教训
    cursor.execute("SELECT lesson_id FROM lessons WHERE content = ?", (content,))
    if cursor.fetchone():
        conn.close()
        return None
    
    cursor.execute("""
        INSERT INTO lessons (content, category, severity, source, parent_id, created_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
    """, (content, category, severity, source, parent_id))
    
    lesson_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return lesson_id

def extract_from_logs():
    """从错误日志提取教训"""
    print("=== 从错误日志提取教训 ===")
    
    if not os.path.exists(ERROR_LOG):
        print("错误日志文件不存在")
        return []
    
    lessons = []
    
    # 定义错误模式和对应的教训
    error_patterns = [
        {
            "pattern": r"timeout|timed out",
            "lesson": "API调用超时：需要增加超时时间或检查网络连接",
            "category": "timeout",
            "severity": "medium"
        },
        {
            "pattern": r"connection refused|connection reset",
            "lesson": "连接被拒绝：服务可能未启动或端口被占用",
            "category": "connection",
            "severity": "high"
        },
        {
            "pattern": r"permission denied|access denied",
            "lesson": "权限被拒绝：检查文件权限或用户权限",
            "category": "permission",
            "severity": "high"
        },
        {
            "pattern": r"not found|does not exist",
            "lesson": "文件或资源不存在：检查路径是否正确",
            "category": "not_found",
            "severity": "medium"
        },
        {
            "pattern": r"out of memory|memory error",
            "lesson": "内存不足：检查内存使用情况或增加内存",
            "category": "memory",
            "severity": "high"
        }
    ]
    
    with open(ERROR_LOG, 'r') as f:
        content = f.read()
        
        for pattern_info in error_patterns:
            matches = re.findall(pattern_info["pattern"], content, re.IGNORECASE)
            if matches:
                lesson = pattern_info["lesson"]
                category = pattern_info["category"]
                severity = pattern_info["severity"]
                
                lesson_id = add_lesson(lesson, category, severity, "error_log")
                if lesson_id:
                    lessons.append({
                        "id": lesson_id,
                        "content": lesson,
                        "category": category,
                        "severity": severity,
                        "matches": len(matches)
                    })
                    print(f"✅ 提取教训: {lesson}")
                    print(f"   匹配次数: {len(matches)}")
    
    return lessons

def extract_from_cron():
    """从Cron失败提取教训"""
    print("=== 从Cron失败提取教训 ===")
    
    if not os.path.exists(CRON_DB):
        print("Cron历史数据库不存在")
        return []
    
    conn = sqlite3.connect(CRON_DB)
    cursor = conn.cursor()
    
    # 获取失败记录
    cursor.execute("""
        SELECT job_id, error_message, created_at 
        FROM cron_runs 
        WHERE status = 'failure' AND error_message IS NOT NULL
        ORDER BY created_at DESC
    """)
    
    failures = cursor.fetchall()
    conn.close()
    
    lessons = []
    
    for job_id, error_message, created_at in failures:
        # 分析错误类型
        if "timeout" in error_message.lower():
            lesson = f"Job {job_id} 超时失败：检查job执行时间或增加超时设置"
            category = "timeout"
            severity = "medium"
        elif "connection" in error_message.lower():
            lesson = f"Job {job_id} 连接失败：检查网络连接或服务状态"
            category = "connection"
            severity = "high"
        elif "permission" in error_message.lower():
            lesson = f"Job {job_id} 权限失败：检查执行权限"
            category = "permission"
            severity = "high"
        else:
            lesson = f"Job {job_id} 执行失败：{error_message[:50]}"
            category = "other"
            severity = "medium"
        
        lesson_id = add_lesson(lesson, category, severity, "cron_failure")
        if lesson_id:
            lessons.append({
                "id": lesson_id,
                "content": lesson,
                "category": category,
                "severity": severity,
                "job_id": job_id
            })
            print(f"✅ 提取教训: {lesson}")
    
    return lessons

def extract_from_memory():
    """从记忆系统提取教训"""
    print("=== 从记忆系统提取教训 ===")
    
    memory_db = os.path.join(HERMES_HOME, "memory_store.db")
    if not os.path.exists(memory_db):
        print("记忆数据库不存在")
        return []
    
    conn = sqlite3.connect(memory_db)
    cursor = conn.cursor()
    
    # 获取低信任fact
    cursor.execute("""
        SELECT fact_id, content, category, trust_score 
        FROM facts 
        WHERE trust_score < 0.3
    """)
    
    low_trust_facts = cursor.fetchall()
    conn.close()
    
    lessons = []
    
    for fact_id, content, category, trust_score in low_trust_facts:
        lesson = f"低信任fact (ID:{fact_id}): {content[:50]}... 可能需要清理或更新"
        category = "memory_cleanup"
        severity = "low"
        
        lesson_id = add_lesson(lesson, category, severity, "memory_system")
        if lesson_id:
            lessons.append({
                "id": lesson_id,
                "content": lesson,
                "category": category,
                "severity": severity,
                "fact_id": fact_id
            })
            print(f"✅ 提取教训: {lesson}")
    
    return lessons

def auto_extract():
    """自动提取所有教训"""
    print("=== 自动提取所有教训 ===")
    
    all_lessons = []
    
    # 从错误日志提取
    log_lessons = extract_from_logs()
    all_lessons.extend(log_lessons)
    
    # 从Cron失败提取
    cron_lessons = extract_from_cron()
    all_lessons.extend(cron_lessons)
    
    # 从记忆系统提取
    memory_lessons = extract_from_memory()
    all_lessons.extend(memory_lessons)
    
    print(f"\n=== 提取完成 ===")
    print(f"总共提取 {len(all_lessons)} 条教训")
    
    return all_lessons

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "extract-logs":
        extract_from_logs()
    elif command == "extract-cron":
        extract_from_cron()
    elif command == "extract-memory":
        extract_from_memory()
    elif command == "auto-extract":
        auto_extract()
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
