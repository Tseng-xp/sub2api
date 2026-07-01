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

def rollback():
    print("=== 回退到上一个版本 ===")
    ssh = ssh_connect()
    
    print("\n1. 检查备份文件...")
    run_command(ssh, "ls -la /tmp/sub2api_backup")
    
    print("\n2. 将备份文件复制回容器...")
    run_command(ssh, "docker cp /tmp/sub2api_backup sub2api:/app/sub2api_old")
    run_command(ssh, "docker exec sub2api chmod +x /app/sub2api_old")
    run_command(ssh, "docker exec sub2api mv /app/sub2api_old /app/sub2api")
    
    print("\n3. 重启服务...")
    run_command(ssh, "cd /opt/sub2api/deploy && docker compose restart sub2api")
    
    print("\n4. 等待启动...")
    import time
    time.sleep(15)
    
    print("\n5. 检查容器状态...")
    run_command(ssh, "docker ps --filter name=sub2api")
    
    print("\n6. 查看日志...")
    run_command(ssh, "docker logs sub2api --tail=20")
    
    print("\n=== 回退完成 ===")
    ssh.close()

if __name__ == "__main__":
    rollback()
