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

def cleanup_old_versions():
    print("=== 清理旧版本 ===")
    ssh = ssh_connect()
    
    print("\n--- 当前所有容器 ---")
    run_command(ssh, "docker ps -a")
    
    print("\n--- 删除已退出的容器 ---")
    run_command(ssh, "docker container prune -f")
    
    print("\n--- 当前所有镜像 ---")
    run_command(ssh, "docker images")
    
    print("\n--- 删除 weishaw/sub2api 旧镜像 ---")
    run_command(ssh, "docker rmi weishaw/sub2api:latest 2>/dev/null || echo '镜像不存在或正在使用'")
    
    print("\n--- 清理临时文件 ---")
    run_command(ssh, "rm -f /tmp/sub2api_new /tmp/sub2api_backup")
    
    print("\n--- 清理后状态 ---")
    run_command(ssh, "docker ps -a")
    run_command(ssh, "docker images")
    run_command(ssh, "docker volume ls")
    
    print("\n=== 清理完成 ===")
    ssh.close()

if __name__ == "__main__":
    cleanup_old_versions()
