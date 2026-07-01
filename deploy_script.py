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

def deploy():
    print("=== 部署新版本 ===")
    ssh = ssh_connect()
    
    print("\n1. 检查容器状态...")
    run_command(ssh, "docker ps --filter name=sub2api")
    
    print("\n2. 备份旧版本...")
    run_command(ssh, "docker exec sub2api cp /app/sub2api /tmp/sub2api_backup")
    
    print("\n3. 上传新版本...")
    sftp = ssh.open_sftp()
    sftp.put("backend/bin/sub2api", "/tmp/sub2api_new")
    sftp.close()
    
    print("\n4. 复制到容器...")
    run_command(ssh, "docker cp /tmp/sub2api_new sub2api:/app/sub2api")
    run_command(ssh, "docker exec sub2api chmod +x /app/sub2api")
    
    print("\n5. 重启服务...")
    run_command(ssh, "cd /opt/sub2api/deploy && docker compose restart sub2api")
    
    print("\n6. 等待启动...")
    import time
    time.sleep(15)
    
    print("\n7. 检查容器状态...")
    run_command(ssh, "docker ps --filter name=sub2api")
    
    print("\n8. 查看日志...")
    run_command(ssh, "docker logs sub2api --tail=20")
    
    print("\n=== 部署完成 ===")
    ssh.close()

if __name__ == "__main__":
    deploy()
