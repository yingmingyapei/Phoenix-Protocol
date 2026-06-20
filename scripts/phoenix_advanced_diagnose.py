#!/usr/bin/env python3
"""
Phoenix Protocol 增强诊断CLI - 添加更多诊断模式
用法: python3 phoenix_advanced_diagnose.py <command> [args...]

命令:
  network                 网络诊断
  performance             性能诊断
  security                安全诊断
  dependency              依赖诊断
  full                    全面诊断
"""

import sys
import os
import subprocess
import socket
from datetime import datetime

HERMES_HOME = os.path.expanduser("~/.hermes")

def run_command(cmd, timeout=30):
    """执行命令"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "命令超时", 1
    except Exception as e:
        return "", str(e), 1

def network_diagnosis():
    """网络诊断"""
    print("=== 网络诊断 ===")
    
    # 检查网络连接
    print("\n1. 检查网络连接:")
    stdout, stderr, returncode = run_command("ping -c 3 8.8.8.8")
    if returncode == 0:
        print("  ✓ 外网连接正常")
    else:
        print(f"  ✗ 外网连接失败: {stderr}")
    
    # 检查DNS解析
    print("\n2. 检查DNS解析:")
    stdout, stderr, returncode = run_command("nslookup google.com")
    if returncode == 0:
        print("  ✓ DNS解析正常")
    else:
        print(f"  ✗ DNS解析失败: {stderr}")
    
    # 检查代理配置
    print("\n3. 检查代理配置:")
    proxy_vars = ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"  ✓ {var} = {value}")
        else:
            print(f"  - {var} 未设置")
    
    # 检查端口占用
    print("\n4. 检查常用端口:")
    ports = [80, 443, 8080, 3000, 5000]
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result == 0:
                print(f"  ✓ 端口 {port} 已占用")
            else:
                print(f"  - 端口 {port} 空闲")
        except:
            print(f"  - 端口 {port} 检查失败")

def performance_diagnosis():
    """性能诊断"""
    print("=== 性能诊断 ===")
    
    # 检查CPU使用率
    print("\n1. 检查CPU使用率:")
    stdout, stderr, returncode = run_command("top -bn1 | head -5")
    if returncode == 0:
        print(f"  {stdout}")
    
    # 检查内存使用
    print("\n2. 检查内存使用:")
    stdout, stderr, returncode = run_command("free -h")
    if returncode == 0:
        print(f"  {stdout}")
    
    # 检查磁盘使用
    print("\n3. 检查磁盘使用:")
    stdout, stderr, returncode = run_command("df -h | head -5")
    if returncode == 0:
        print(f"  {stdout}")
    
    # 检查Hermes进程
    print("\n4. 检查Hermes进程:")
    stdout, stderr, returncode = run_command("ps aux | grep hermes | grep -v grep")
    if returncode == 0 and stdout:
        print(f"  ✓ Hermes进程运行中")
        print(f"  {stdout}")
    else:
        print("  - Hermes进程未运行")

def security_diagnosis():
    """安全诊断"""
    print("=== 安全诊断 ===")
    
    # 检查文件权限
    print("\n1. 检查敏感文件权限:")
    sensitive_files = [
        ("config.yaml", "~/.hermes/config.yaml"),
        (".env", "~/.hermes/.env"),
        ("MEMORY.md", "~/.hermes/memories/MEMORY.md"),
    ]
    
    for name, path in sensitive_files:
        full_path = os.path.expanduser(path)
        if os.path.exists(full_path):
            stat = os.stat(full_path)
            mode = oct(stat.st_mode)[-3:]
            if mode in ["600", "644"]:
                print(f"  ✓ {name}: {mode}")
            else:
                print(f"  ⚠️ {name}: {mode} (建议 600 或 644)")
        else:
            print(f"  - {name}: 不存在")
    
    # 检查SSH配置
    print("\n2. 检查SSH配置:")
    ssh_config = os.path.expanduser("~/.ssh/config")
    if os.path.exists(ssh_config):
        print("  ✓ SSH配置文件存在")
    else:
        print("  - SSH配置文件不存在")
    
    # 检查防火墙
    print("\n3. 检查防火墙:")
    stdout, stderr, returncode = run_command("sudo ufw status 2>/dev/null || echo '防火墙状态未知'")
    if returncode == 0:
        print(f"  {stdout}")

def dependency_diagnosis():
    """依赖诊断"""
    print("=== 依赖诊断 ===")
    
    # 检查Python版本
    print("\n1. 检查Python版本:")
    stdout, stderr, returncode = run_command("python3 --version")
    if returncode == 0:
        print(f"  ✓ {stdout}")
    else:
        print(f"  ✗ Python未安装")
    
    # 检查pip包
    print("\n2. 检查关键pip包:")
    packages = ["sqlite3", "requests", "psutil"]
    for package in packages:
        stdout, stderr, returncode = run_command(f"python3 -c 'import {package}; print({package}.__version__)'")
        if returncode == 0:
            print(f"  ✓ {package}: {stdout}")
        else:
            print(f"  ✗ {package}: 未安装")
    
    # 检查系统工具
    print("\n3. 检查系统工具:")
    tools = ["git", "curl", "wget", "ssh", "scp"]
    for tool in tools:
        stdout, stderr, returncode = run_command(f"which {tool}")
        if returncode == 0:
            print(f"  ✓ {tool}: {stdout}")
        else:
            print(f"  ✗ {tool}: 未安装")

def full_diagnosis():
    """全面诊断"""
    print("=== 全面诊断 ===")
    
    network_diagnosis()
    print("\n" + "="*50)
    performance_diagnosis()
    print("\n" + "="*50)
    security_diagnosis()
    print("\n" + "="*50)
    dependency_diagnosis()

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "network":
        network_diagnosis()
    elif command == "performance":
        performance_diagnosis()
    elif command == "security":
        security_diagnosis()
    elif command == "dependency":
        dependency_diagnosis()
    elif command == "full":
        full_diagnosis()
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
