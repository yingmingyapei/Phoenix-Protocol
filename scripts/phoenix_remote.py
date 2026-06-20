#!/usr/bin/env python3
"""
Phoenix Protocol 远程修复CLI - 远程诊断和修复
用法: python3 phoenix_remote.py <command> [args...]

命令:
  diagnose <host>         远程诊断
  repair <host>           远程修复
  sync-all <host>         同步所有文件
  status <host>           远程状态
"""

import sys
import os
import subprocess
from datetime import datetime

IA_HOST = "192.168.3.88"
IA_USER = "root"

def run_ssh_command(host, user, command, timeout=60):
    """执行SSH命令"""
    try:
        ssh_cmd = f"ssh {user}@{host} '{command}'"
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "SSH命令超时", 1
    except Exception as e:
        return "", str(e), 1

def remote_diagnose(host):
    """远程诊断"""
    print(f"=== 远程诊断 ({host}) ===")
    
    # 执行远程诊断命令
    commands = [
        ("检查Python", "python3 --version"),
        ("检查Hermes状态", "hermes status 2>/dev/null || echo 'Hermes未安装'"),
        ("检查脚本目录", "ls -la ~/.hermes/scripts/ 2>/dev/null | head -5"),
        ("检查MEMORY.md", "cat ~/.hermes/memories/MEMORY.md 2>/dev/null | wc -l || echo 'MEMORY.md不存在'"),
        ("检查fact_store", "python3 ~/.hermes/scripts/fact_store_cli.py stats 2>/dev/null || echo 'fact_store CLI未安装'"),
        ("检查Cron历史", "python3 ~/.hermes/scripts/cron_history_cli.py stats 2>/dev/null || echo 'Cron历史CLI未安装'"),
        ("检查Gateway状态", "pgrep -f 'hermes.*gateway' >/dev/null && echo 'Gateway运行中' || echo 'Gateway未运行'"),
    ]
    
    results = []
    for desc, cmd in commands:
        print(f"\n{desc}:")
        stdout, stderr, returncode = run_ssh_command(host, IA_USER, cmd)
        if returncode == 0:
            print(f"  ✓ {stdout}")
            results.append({"desc": desc, "status": "success", "output": stdout})
        else:
            print(f"  ✗ {stderr}")
            results.append({"desc": desc, "status": "failure", "output": stderr})
    
    return results

def remote_repair(host):
    """远程修复"""
    print(f"=== 远程修复 ({host}) ===")
    
    # 1. 同步脚本
    print("\n1. 同步脚本...")
    sync_scripts_to_host(host)
    
    # 2. 同步技能
    print("\n2. 同步技能...")
    sync_skills_to_host(host)
    
    # 3. 同步记忆文件
    print("\n3. 同步记忆文件...")
    sync_memory_to_host(host)
    
    # 4. 验证修复
    print("\n4. 验证修复...")
    stdout, stderr, returncode = run_ssh_command(host, IA_USER, "python3 ~/.hermes/scripts/fact_store_cli.py stats")
    if returncode == 0:
        print(f"  ✓ fact_store CLI正常")
    else:
        print(f"  ✗ fact_store CLI异常: {stderr}")

def sync_scripts_to_host(host):
    """同步脚本到远程主机"""
    scripts_dir = os.path.expanduser("~/.hermes/scripts")
    remote_scripts_dir = "/root/.hermes/scripts"
    
    scripts = [
        "fact_store_cli.py",
        "cron_history_cli.py",
        "phoenix_diagnose.py",
        "phoenix_rollback.py",
        "phoenix_evaluate.py",
        "phoenix_lesson_graph.py",
        "phoenix_preventive.py",
        "phoenix_collab.py",
        "phoenix_ai_diagnose.py",
        "phoenix_auto_rollback.py",
        "phoenix_enhanced_eval.py",
        "phoenix_auto_lesson.py",
        "phoenix_scheduled.py"
    ]
    
    for script in scripts:
        local_path = os.path.join(scripts_dir, script)
        if os.path.exists(local_path):
            scp_cmd = f"scp {local_path} {IA_USER}@{host}:{remote_scripts_dir}/"
            result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"  ✓ {script}")
            else:
                print(f"  ✗ {script}: {result.stderr}")

def sync_skills_to_host(host):
    """同步技能到远程主机"""
    skills_dir = os.path.expanduser("~/.hermes/skills")
    remote_skills_dir = "/root/.hermes/skills"
    
    skill_dirs = [
        "hermes/evolution-engine",
        "self-improvement/agent-self-evolution"
    ]
    
    for skill_dir in skill_dirs:
        local_path = os.path.join(skills_dir, skill_dir)
        if os.path.exists(local_path):
            scp_cmd = f"scp -r {local_path} {IA_USER}@{host}:{remote_skills_dir}/{os.path.dirname(skill_dir)}/"
            result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"  ✓ {skill_dir}")
            else:
                print(f"  ✗ {skill_dir}: {result.stderr}")

def sync_memory_to_host(host):
    """同步记忆文件到远程主机"""
    memory_files = [
        ("MEMORY.md", "~/.hermes/memories/MEMORY.md"),
        ("USER.md", "~/.hermes/memories/USER.md"),
    ]
    
    for name, local_path in memory_files:
        local_path = os.path.expanduser(local_path)
        if os.path.exists(local_path):
            scp_cmd = f"scp {local_path} {IA_USER}@{host}:/root/.hermes/memories/"
            result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"  ✓ {name}")
            else:
                print(f"  ✗ {name}: {result.stderr}")

def sync_all(host):
    """同步所有文件"""
    print(f"=== 同步所有文件到 {host} ===")
    
    sync_scripts_to_host(host)
    sync_skills_to_host(host)
    sync_memory_to_host(host)
    
    print("\n✅ 同步完成")

def remote_status(host):
    """远程状态"""
    print(f"=== 远程状态 ({host}) ===")
    
    # 检查关键服务
    services = [
        ("Gateway", "pgrep -f 'hermes.*gateway' >/dev/null && echo '运行中' || echo '未运行'"),
        ("Python", "python3 --version"),
        ("Hermes", "hermes --version 2>/dev/null || echo '未安装'"),
    ]
    
    for name, cmd in services:
        stdout, stderr, returncode = run_ssh_command(host, IA_USER, cmd)
        status = "✓" if returncode == 0 else "✗"
        output = stdout if returncode == 0 else stderr
        print(f"{status} {name}: {output}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "diagnose":
        host = sys.argv[2] if len(sys.argv) > 2 else IA_HOST
        remote_diagnose(host)
    elif command == "repair":
        host = sys.argv[2] if len(sys.argv) > 2 else IA_HOST
        remote_repair(host)
    elif command == "sync-all":
        host = sys.argv[2] if len(sys.argv) > 2 else IA_HOST
        sync_all(host)
    elif command == "status":
        host = sys.argv[2] if len(sys.argv) > 2 else IA_HOST
        remote_status(host)
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
