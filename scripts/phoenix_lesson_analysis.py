#!/usr/bin/env python3
"""
Phoenix Protocol 教训关联分析CLI - 分析教训之间的关联关系
用法: python3 phoenix_lesson_analysis.py <command> [args...]

命令:
  analyze                 分析教训关联
  cluster                 聚类分析
  root-cause              根因分析
  recommend               生成推荐
"""

import sys
import os
import sqlite3
from collections import defaultdict

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

def analyze_relations():
    """分析教训关联"""
    print("=== 分析教训关联 ===")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 获取所有教训
    cursor.execute("SELECT lesson_id, content, category, severity FROM lessons")
    lessons = cursor.fetchall()
    
    # 获取所有关联
    cursor.execute("SELECT lesson_id, related_id, relation_type FROM lesson_relations")
    relations = cursor.fetchall()
    
    conn.close()
    
    # 构建关联图
    graph = defaultdict(list)
    for lesson_id, related_id, relation_type in relations:
        graph[lesson_id].append((related_id, relation_type))
        graph[related_id].append((lesson_id, relation_type))
    
    # 分析关联度
    print(f"\n教训总数: {len(lessons)}")
    print(f"关联总数: {len(relations)}")
    
    # 找出关联度最高的教训
    if graph:
        most_connected = max(graph.items(), key=lambda x: len(x[1]))
        print(f"\n关联度最高的教训:")
        print(f"  ID: {most_connected[0]}")
        print(f"  关联数: {len(most_connected[1])}")
        
        # 显示关联的教训
        lesson_dict = {l[0]: l for l in lessons}
        if most_connected[0] in lesson_dict:
            lesson = lesson_dict[most_connected[0]]
            print(f"  内容: {lesson[1][:50]}...")
    
    # 按类别统计
    category_stats = defaultdict(int)
    for lesson in lessons:
        if lesson[2]:
            category_stats[lesson[2]] += 1
    
    if category_stats:
        print(f"\n类别分布:")
        for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")

def cluster_analysis():
    """聚类分析"""
    print("=== 聚类分析 ===")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 获取所有教训
    cursor.execute("SELECT lesson_id, content, category, severity FROM lessons")
    lessons = cursor.fetchall()
    
    conn.close()
    
    # 按类别聚类
    clusters = defaultdict(list)
    for lesson in lessons:
        category = lesson[2] or "未分类"
        clusters[category].append(lesson)
    
    print(f"\n聚类数量: {len(clusters)}")
    
    for category, cluster_lessons in clusters.items():
        print(f"\n类别: {category} ({len(cluster_lessons)} 条)")
        for lesson in cluster_lessons[:3]:  # 只显示前3条
            print(f"  - {lesson[1][:50]}...")

def root_cause_analysis():
    """根因分析"""
    print("=== 根因分析 ===")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 获取所有教训
    cursor.execute("SELECT lesson_id, content, category, severity FROM lessons")
    lessons = cursor.fetchall()
    
    # 获取所有关联
    cursor.execute("SELECT lesson_id, related_id, relation_type FROM lesson_relations")
    relations = cursor.fetchall()
    
    conn.close()
    
    # 分析根因
    print(f"\n教训总数: {len(lessons)}")
    
    # 按严重程度统计
    severity_stats = defaultdict(int)
    for lesson in lessons:
        severity = lesson[3] or "未指定"
        severity_stats[severity] += 1
    
    print(f"\n严重程度分布:")
    for severity, count in sorted(severity_stats.items()):
        print(f"  {severity}: {count}")
    
    # 找出高频问题
    category_counts = defaultdict(int)
    for lesson in lessons:
        if lesson[2]:
            category_counts[lesson[2]] += 1
    
    if category_counts:
        most_common = max(category_counts.items(), key=lambda x: x[1])
        print(f"\n高频问题类别: {most_common[0]} ({most_common[1]} 条)")

def generate_recommendations():
    """生成推荐"""
    print("=== 生成推荐 ===")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 获取所有教训
    cursor.execute("SELECT lesson_id, content, category, severity FROM lessons")
    lessons = cursor.fetchall()
    
    conn.close()
    
    recommendations = []
    
    # 分析教训
    for lesson in lessons:
        lesson_id, content, category, severity = lesson
        
        # 根据严重程度生成推荐
        if severity == "high":
            recommendations.append({
                "priority": "high",
                "lesson_id": lesson_id,
                "content": content,
                "recommendation": f"立即处理高优先级问题: {content[:50]}..."
            })
        elif severity == "medium":
            recommendations.append({
                "priority": "medium",
                "lesson_id": lesson_id,
                "content": content,
                "recommendation": f"计划处理中优先级问题: {content[:50]}..."
            })
    
    # 输出推荐
    if recommendations:
        print(f"\n生成 {len(recommendations)} 条推荐:")
        for i, rec in enumerate(recommendations, 1):
            priority_icon = "🔴" if rec["priority"] == "high" else "🟡"
            print(f"\n{priority_icon} 推荐 {i}:")
            print(f"   教训ID: {rec['lesson_id']}")
            print(f"   内容: {rec['content'][:50]}...")
            print(f"   建议: {rec['recommendation']}")
    else:
        print("\n✅ 无推荐")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "analyze":
        analyze_relations()
    elif command == "cluster":
        cluster_analysis()
    elif command == "root-cause":
        root_cause_analysis()
    elif command == "recommend":
        generate_recommendations()
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
