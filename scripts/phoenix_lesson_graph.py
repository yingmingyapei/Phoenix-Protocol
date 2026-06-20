#!/usr/bin/env python3
"""
Phoenix Protocol 教训知识图谱CLI - 建立教训之间的关联关系
用法: python3 phoenix_lesson_graph.py <command> [args...]

命令:
  add <lesson> [--parent PARENT] [--related RELATED]  添加教训
  list                    列出所有教训
  show <lesson_id>        显示教训详情
  relate <lesson_id> <related_id>  建立关联
  search <query>          搜索教训
"""

import sys
import os
import sqlite3
from datetime import datetime

HERMES_HOME = os.path.expanduser("~/.hermes")
LESSON_DB = os.path.join(HERMES_HOME, "phoenix_lessons.db")

def get_connection():
    conn = sqlite3.connect(LESSON_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            category TEXT,
            severity TEXT,
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

def add_lesson(content, category=None, severity=None, parent_id=None):
    """添加教训"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO lessons (content, category, severity, parent_id, created_at)
        VALUES (?, ?, ?, ?, datetime('now'))
    """, (content, category, severity, parent_id))
    
    lesson_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"✅ 已添加教训 ID {lesson_id}: {content[:50]}...")
    return lesson_id

def list_lessons():
    """列出所有教训"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT lesson_id, content, category, severity, parent_id, created_at FROM lessons ORDER BY lesson_id DESC")
    lessons = cursor.fetchall()
    conn.close()
    
    print(f"=== 教训列表 ({len(lessons)} 条) ===")
    for lesson in lessons:
        parent_str = f" (父教训: {lesson[4]})" if lesson[4] else ""
        severity_str = f" [{lesson[3]}]" if lesson[3] else ""
        category_str = f" ({lesson[2]})" if lesson[2] else ""
        print(f"ID {lesson[0]}: {lesson[1][:60]}...{category_str}{severity_str}{parent_str} ({lesson[5]})")

def show_lesson(lesson_id):
    """显示教训详情"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 获取教训详情
    cursor.execute("SELECT lesson_id, content, category, severity, parent_id, created_at FROM lessons WHERE lesson_id = ?", (lesson_id,))
    lesson = cursor.fetchone()
    
    if not lesson:
        print(f"错误: 教训 ID {lesson_id} 不存在")
        conn.close()
        return
    
    # 获取关联教训
    cursor.execute("""
        SELECT l.lesson_id, l.content, lr.relation_type 
        FROM lesson_relations lr
        JOIN lessons l ON lr.related_id = l.lesson_id
        WHERE lr.lesson_id = ?
    """, (lesson_id,))
    related = cursor.fetchall()
    
    # 获取子教训
    cursor.execute("SELECT lesson_id, content FROM lessons WHERE parent_id = ?", (lesson_id,))
    children = cursor.fetchall()
    
    conn.close()
    
    print(f"=== 教训详情 (ID: {lesson[0]}) ===")
    print(f"内容: {lesson[1]}")
    print(f"类别: {lesson[2] or '未分类'}")
    print(f"严重程度: {lesson[3] or '未指定'}")
    print(f"父教训: {lesson[4] or '无'}")
    print(f"创建时间: {lesson[5]}")
    
    if related:
        print(f"\n关联教训 ({len(related)} 条):")
        for rel in related:
            print(f"  - ID {rel[0]}: {rel[1][:50]}... (关系: {rel[2]})")
    
    if children:
        print(f"\n子教训 ({len(children)} 条):")
        for child in children:
            print(f"  - ID {child[0]}: {child[1][:50]}...")

def relate_lessons(lesson_id, related_id, relation_type="related"):
    """建立教训关联"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 检查教训是否存在
    cursor.execute("SELECT lesson_id FROM lessons WHERE lesson_id IN (?, ?)", (lesson_id, related_id))
    if len(cursor.fetchall()) != 2:
        print(f"错误: 教训 ID {lesson_id} 或 {related_id} 不存在")
        conn.close()
        return
    
    # 检查是否已存在关联
    cursor.execute("""
        SELECT relation_id FROM lesson_relations 
        WHERE (lesson_id = ? AND related_id = ?) OR (lesson_id = ? AND related_id = ?)
    """, (lesson_id, related_id, related_id, lesson_id))
    if cursor.fetchone():
        print(f"警告: 教训 {lesson_id} 和 {related_id} 已存在关联")
        conn.close()
        return
    
    # 建立关联
    cursor.execute("""
        INSERT INTO lesson_relations (lesson_id, related_id, relation_type, created_at)
        VALUES (?, ?, ?, datetime('now'))
    """, (lesson_id, related_id, relation_type))
    
    conn.commit()
    conn.close()
    
    print(f"✅ 已建立关联: 教训 {lesson_id} <-> 教训 {related_id} (关系: {relation_type})")

def search_lessons(query):
    """搜索教训"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT lesson_id, content, category, severity 
        FROM lessons 
        WHERE content LIKE ? OR category LIKE ?
        ORDER BY lesson_id DESC
        LIMIT 10
    """, (f"%{query}%", f"%{query}%"))
    
    lessons = cursor.fetchall()
    conn.close()
    
    print(f"=== 搜索 '{query}' 结果: {len(lessons)} 条 ===")
    for lesson in lessons:
        category_str = f" ({lesson[2]})" if lesson[2] else ""
        severity_str = f" [{lesson[3]}]" if lesson[3] else ""
        print(f"ID {lesson[0]}: {lesson[1][:60]}...{category_str}{severity_str}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "add":
        if len(sys.argv) < 3:
            print("错误: add 需要教训内容")
            sys.exit(1)
        content = sys.argv[2]
        category = None
        severity = None
        parent_id = None
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--category" and i + 1 < len(sys.argv):
                category = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--severity" and i + 1 < len(sys.argv):
                severity = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--parent" and i + 1 < len(sys.argv):
                parent_id = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1
        add_lesson(content, category, severity, parent_id)
    elif command == "list":
        list_lessons()
    elif command == "show":
        if len(sys.argv) < 3:
            print("错误: show 需要教训ID")
            sys.exit(1)
        show_lesson(int(sys.argv[2]))
    elif command == "relate":
        if len(sys.argv) < 4:
            print("错误: relate 需要两个教训ID")
            sys.exit(1)
        relate_lessons(int(sys.argv[2]), int(sys.argv[3]))
    elif command == "search":
        if len(sys.argv) < 3:
            print("错误: search 需要查询参数")
            sys.exit(1)
        search_lessons(sys.argv[2])
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
