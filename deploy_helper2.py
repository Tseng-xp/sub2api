import paramiko
import sys

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

def check_deployment_detail():
    print("=== 详细检查部署状态 ===")
    ssh = ssh_connect()
    
    print("\n--- /opt/sub2api 目录结构 ---")
    run_command(ssh, "ls -la /opt/sub2api/")
    
    print("\n--- 查找 docker-compose 实际使用目录 ---")
    run_command(ssh, "find /opt/sub2api -name '.env' -o -name 'docker-compose.yml' | head -20")
    
    print("\n--- 检查 sub2api 容器详情 ---")
    run_command(ssh, "docker inspect sub2api --format='{{.Config.Image}}' && docker inspect sub2api --format='{{json .Mounts}}' | python3 -m json.tool 2>/dev/null || docker inspect sub2api --format='{{json .Mounts}}'")
    
    print("\n--- 检查 sub2api 容器内的二进制 ---")
    run_command(ssh, "docker exec sub2api ls -la /app/ && docker exec sub2api /app/sub2api --version 2>/dev/null || docker exec sub2api /app/sub2api -v 2>/dev/null || echo 'no version flag'")
    
    print("\n--- 检查网络 ---")
    run_command(ssh, "docker network ls | grep sub2api")
    
    print("\n--- 检查 volume ---")
    run_command(ssh, "docker volume ls | grep sub2api")
    
    ssh.close()

if __name__ == "__main__":
    check_deployment_detail()
