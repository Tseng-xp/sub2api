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

def fix_deploy():
    print("=== 修复部署 ===")
    ssh = ssh_connect()
    
    print("\n1. 停止容器...")
    run_command(ssh, "docker stop sub2api")
    
    print("\n2. 删除容器...")
    run_command(ssh, "docker rm sub2api")
    
    print("\n3. 重新上传新版本...")
    sftp = ssh.open_sftp()
    sftp.put("backend/bin/sub2api", "/opt/sub2api/deploy/sub2api")
    sftp.close()
    
    print("\n4. 设置权限...")
    run_command(ssh, "chmod +x /opt/sub2api/deploy/sub2api")
    
    print("\n5. 重新启动容器...")
    run_command(ssh, "cd /opt/sub2api/deploy && docker compose up -d")
    
    print("\n6. 等待启动...")
    import time
    time.sleep(20)
    
    print("\n7. 检查容器状态...")
    run_command(ssh, "docker ps --filter name=sub2api")
    
    print("\n8. 查看日志...")
    run_command(ssh, "docker logs sub2api --tail=30")
    
    print("\n=== 修复完成 ===")
    ssh.close()

if __name__ == "__main__":
    fix_deploy()
