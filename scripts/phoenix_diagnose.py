#!/usr/bin/env python3
"""
Phoenix Protocol 诊断CLI - 系统健康检查和故障诊断
用法: python3 phoenix_diagnose.py <command> [args...]

命令:
  health                  系统健康检查
  diagnose <symptom>      故障诊断
  check-cron              检查Cron健康
  check-memory            检查记忆系统健康
  check-skills            检查技能健康
"""

import sys
import os
import sqlite3
import subprocess
from datetime import datetime, timedelta

HERMES_HOME = os.path.expanduser("~/.hermes")
MEMORY_DB = os.path.join(HERMES_HOME, "memory_store.db")
CRON_DB = os.path.join(HERMES_HOME, "cron_history.db")

def run_command(cmd):
    """执行命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "命令超时", 1
    except Exception as e:
        return "", str(e), 1

def check_memory_health():
    """检查记忆系统健康"""
    print("=== 记忆系统健康检查 ===")
    
    # 检查MEMORY.md
    memory_path = os.path.join(HERMES_HOME, "memories", "MEMORY.md")
    if os.path.exists(memory_path):
        with open(memory_path, 'r') as f:
            content = f.read()
            lines = [l for l in content.split('\n') if l.strip() and l.strip() != '§']
            print(f"✓ MEMORY.md 存在 ({len(lines)} 条规则)")
            if len(lines) > 3:
                print(f"  ⚠️ 警告: 规则数量超过3条 ({len(lines)} 条)")
    else:
        print("✗ MEMORY.md 不存在")
    
    # 检查USER.md
    user_path = os.path.join(HERMES_HOME, "memories", "USER.md")
    if os.path.exists(user_path):
        with open(user_path, 'r') as f:
            content = f.read()
            lines = [l for l in content.split('\n') if l.strip() and l.strip() != '§']
            print(f"✓ USER.md 存在 ({len(lines)} 条)")
    else:
        print("✗ USER.md 不存在")
    
    # 检查fact_store
    if os.path.exists(MEMORY_DB):
        try:
            conn = sqlite3.connect(MEMORY_DB)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM facts")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM facts WHERE trust_score < 0.3")
            low_trust = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM facts WHERE retrieval_count = 0")
            never_retrieved = cursor.fetchone()[0]
            conn.close()
            print(f"✓ fact_store 正常 ({total} 条fact)")
            if low_trust > 0:
                print(f"  ⚠️ 低信任fact: {low_trust} 条")
            if never_retrieved > 0:
                print(f"  ⚠️ 从未检索: {never_retrieved} 条")
        except Exception as e:
            print(f"✗ fact_store 错误: {e}")
    else:
        print("✗ fact_store 数据库不存在")
    
    # 检查孤儿文件
    memory_dir = os.path.join(HERMES_HOME, "memories", "memory")
    user_dir = os.path.join(HERMES_HOME, "memories", "user")
    memory_count = len([f for f in os.listdir(memory_dir) if f.endswith('.md')]) if os.path.exists(memory_dir) else 0
    user_count = len([f for f in os.listdir(user_dir) if f.endswith('.md')]) if os.path.exists(user_dir) else 0
    if memory_count > 0 or user_count > 0:
        print(f"⚠️ 孤儿文件: memory/{memory_count} 个, user/{user_count} 个")
    else:
        print("✓ 无孤儿文件")

def check_cron_health():
    """检查Cron健康"""
    print("\n=== Cron健康检查 ===")
    
    # 检查Cron历史数据库
    if os.path.exists(CRON_DB):
        try:
            conn = sqlite3.connect(CRON_DB)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cron_runs")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM cron_runs WHERE status = 'success'")
            success = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM cron_runs WHERE status = 'failure'")
            failure = cursor.fetchone()[0]
            
            # 检查连续失败
            cursor.execute("SELECT job_id, status FROM cron_runs ORDER BY created_at DESC LIMIT 20")
            recent_runs = cursor.fetchall()
            
            job_failures = {}
            for job_id, status in recent_runs:
                if job_id not in job_failures:
                    job_failures[job_id] = 0
                if status == 'failure':
                    job_failures[job_id] += 1
                else:
                    break
            
            conn.close()
            
            print(f"✓ Cron历史数据库正常 ({total} 条记录)")
            print(f"  成功: {success}, 失败: {failure}")
            print(f"  成功率: {success/total*100:.1f}%" if total > 0 else "  成功率: N/A")
            
            for job_id, failures in job_failures.items():
                if failures >= 3:
                    print(f"  ❌ 严重: job {job_id} 连续失败 {failures} 次")
                elif failures >= 1:
                    print(f"  ⚠️ 警告: job {job_id} 连续失败 {failures} 次")
        except Exception as e:
            print(f"✗ Cron历史数据库错误: {e}")
    else:
        print("⚠️ Cron历史数据库不存在（首次运行将自动创建）")

def check_skills_health():
    """检查技能健康"""
    print("\n=== 技能健康检查 ===")
    
    skills_dir = os.path.join(HERMES_HOME, "skills")
    if not os.path.exists(skills_dir):
        print("✗ 技能目录不存在")
        return
    
    total_skills = 0
    outdated_skills = []
    
    for root, dirs, files in os.walk(skills_dir):
        for file in files:
            if file == "SKILL.md":
                total_skills += 1
                skill_path = os.path.join(root, file)
                try:
                    with open(skill_path, 'r') as f:
                        content = f.read()
                        # 检查是否有updated字段
                        if 'updated:' in content:
                            for line in content.split('\n'):
                                if line.strip().startswith('updated:'):
                                    date_str = line.split(':')[1].strip()
                                    try:
                                        updated_date = datetime.strptime(date_str, '%Y-%m-%d')
                                        days_old = (datetime.now() - updated_date).days
                                        if days_old > 30:
                                            skill_name = os.path.basename(os.path.dirname(skill_path))
                                            outdated_skills.append((skill_name, days_old))
                                    except:
                                        pass
                except:
                    pass
    
    print(f"✓ 技能总数: {total_skills}")
    if outdated_skills:
        print(f"⚠️ 过时技能 (>30天未更新): {len(outdated_skills)} 个")
        for name, days in outdated_skills[:5]:
            print(f"  - {name}: {days} 天前更新")
    else:
        print("✓ 所有技能都在30天内更新")

def system_health():
    """系统健康检查"""
    print("==========================================")
    print("  Phoenix Protocol 系统健康检查")
    print("==========================================")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    check_memory_health()
    check_cron_health()
    check_skills_health()
    
    print("\n==========================================")
    print("  健康检查完成")
    print("==========================================")

def diagnose_symptom(symptom):
    """故障诊断"""
    print(f"=== 故障诊断: {symptom} ===")
    
    # 简单的关键词匹配诊断
    diagnoses = {
        "memory": ["检查MEMORY.md是否超过3条规则", "检查fact_store是否正常", "检查孤儿文件"],
        "cron": ["检查Cron历史数据库", "检查连续失败次数", "检查Gateway是否运行"],
        "skill": ["检查技能目录", "检查技能是否过时", "检查技能Pitfalls"],
        "gateway": ["检查Gateway进程", "检查配置文件", "检查日志"],
        "timeout": ["检查网络连接", "检查API密钥", "检查模型提供商"],
    }
    
    found = False
    for keyword, suggestions in diagnoses.items():
        if keyword in symptom.lower():
            print(f"可能的原因和解决方案:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
            found = True
    
    if not found:
        print("未找到匹配的诊断，请提供更详细的症状描述")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "health":
        system_health()
    elif command == "diagnose":
        if len(sys.argv) < 3:
            print("错误: diagnose 需要症状描述")
            sys.exit(1)
        diagnose_symptom(' '.join(sys.argv[2:]))
    elif command == "check-cron":
        check_cron_health()
    elif command == "check-memory":
        check_memory_health()
    elif command == "check-skills":
        check_skills_health()
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
