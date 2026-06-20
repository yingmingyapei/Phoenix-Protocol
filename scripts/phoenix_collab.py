#!/usr/bin/env python3
"""
Phoenix Protocol 多Agent协同修复CLI - WA和IA协同诊断和修复
用法: python3 phoenix_collab.py <command> [args...]

命令:
  sync-scripts            同步脚本到IA
  sync-skills             同步技能到IA
  remote-diagnose <host>  远程诊断
  remote-repair <host>    远程修复
"""

import sys
import os
import subprocess
from datetime import datetime

IA_HOST = "192.168.3.88"
IA_USER = "root"

def run_ssh_command(host, user, command):
    """执行SSH命令"""
    try:
        ssh_cmd = f"ssh {user}@{host} '{command}'"
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=60)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "SSH命令超时", 1
    except Exception as e:
        return "", str(e), 1

def sync_scripts():
    """同步脚本到IA"""
    print("=== 同步脚本到IA ===")
    
    scripts_dir = os.path.expanduser("~/.hermes/scripts")
    remote_scripts_dir = "/root/.hermes/scripts"
    
    # 要同步的脚本
    scripts = [
        "fact_store_cli.py",
        "cron_history_cli.py",
        "phoenix_diagnose.py",
        "phoenix_rollback.py",
        "phoenix_evaluate.py",
        "phoenix_lesson_graph.py",
        "phoenix_preventive.py"
    ]
    
    for script in scripts:
        local_path = os.path.join(scripts_dir, script)
        if os.path.exists(local_path):
            print(f"同步 {script}...")
            scp_cmd = f"scp {local_path} {IA_USER}@{IA_HOST}:{remote_scripts_dir}/"
            result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"  ✅ 成功")
            else:
                print(f"  ❌ 失败: {result.stderr}")
        else:
            print(f"⚠️ 脚本不存在: {script}")

def sync_skills():
    """同步技能到IA"""
    print("=== 同步技能到IA ===")
    
    skills_dir = os.path.expanduser("~/.hermes/skills")
    remote_skills_dir = "/root/.hermes/skills"
    
    # 要同步的技能目录
    skill_dirs = [
        "hermes/evolution-engine",
        "self-improvement/agent-self-evolution"
    ]
    
    for skill_dir in skill_dirs:
        local_path = os.path.join(skills_dir, skill_dir)
        if os.path.exists(local_path):
            print(f"同步 {skill_dir}...")
            scp_cmd = f"scp -r {local_path} {IA_USER}@{IA_HOST}:{remote_skills_dir}/{os.path.dirname(skill_dir)}/"
            result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"  ✅ 成功")
            else:
                print(f"  ❌ 失败: {result.stderr}")
        else:
            print(f"⚠️ 技能目录不存在: {skill_dir}")

def remote_diagnose(host):
    """远程诊断"""
    print(f"=== 远程诊断 ({host}) ===")
    
    # 执行远程诊断命令
    commands = [
        ("检查Python", "python3 --version"),
        ("检查脚本目录", "ls -la ~/.hermes/scripts/ 2>/dev/null | head -5"),
        ("检查fact_store", "python3 ~/.hermes/scripts/fact_store_cli.py stats 2>/dev/null || echo 'fact_store CLI未安装'"),
        ("检查Cron历史", "python3 ~/.hermes/scripts/cron_history_cli.py stats 2>/dev/null || echo 'Cron历史CLI未安装'"),
        ("检查MEMORY.md", "cat ~/.hermes/memories/MEMORY.md 2>/dev/null | wc -l || echo 'MEMORY.md不存在'"),
    ]
    
    for desc, cmd in commands:
        print(f"\n{desc}:")
        stdout, stderr, returncode = run_ssh_command(host, IA_USER, cmd)
        if returncode == 0:
            print(f"  {stdout}")
        else:
            print(f"  ❌ 错误: {stderr}")

def remote_repair(host):
    """远程修复"""
    print(f"=== 远程修复 ({host}) ===")
    
    # 同步脚本
    sync_scripts()
    
    # 远程测试
    print("\n远程测试:")
    stdout, stderr, returncode = run_ssh_command(host, IA_USER, "python3 ~/.hermes/scripts/fact_store_cli.py stats")
    if returncode == 0:
        print(f"  ✅ fact_store CLI正常")
        print(f"  {stdout}")
    else:
        print(f"  ❌ fact_store CLI异常: {stderr}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "sync-scripts":
        sync_scripts()
    elif command == "sync-skills":
        sync_skills()
    elif command == "remote-diagnose":
        host = sys.argv[2] if len(sys.argv) > 2 else IA_HOST
        remote_diagnose(host)
    elif command == "remote-repair":
        host = sys.argv[2] if len(sys.argv) > 2 else IA_HOST
        remote_repair(host)
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
