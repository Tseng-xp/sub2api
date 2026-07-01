import paramiko
import sys
import os

HOST = "47.106.121.132"
USER = "root"
PASSWORD = "Xn0753@#"

def ssh_connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    return ssh

def run_command(ssh, command):
    print(f"$ {command}")
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    if output:
        print(output)
    if error:
        print(f"STDERR: {error}", file=sys.stderr)
    return output, error, stdout.channel.recv_exit_status()

def check_deployment():
    print("=== 检查服务器部署状态 ===")
    ssh = ssh_connect()
    
    print("\n--- Docker 容器状态 ---")
    run_command(ssh, "docker ps -a")
    
    print("\n--- Docker 镜像 ---")
    run_command(ssh, "docker images | grep sub2api")
    
    print("\n--- 查找 docker-compose 文件 ---")
    run_command(ssh, "find /root -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' 2>/dev/null | head -20")
    run_command(ssh, "find /opt -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' 2>/dev/null | head -20")
    run_command(ssh, "find / -maxdepth 3 -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' 2>/dev/null | head -20")
    
    print("\n--- 当前目录 ---")
    run_command(ssh, "pwd && ls -la")
    
    ssh.close()

if __name__ == "__main__":
    check_deployment()
