import paramiko

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
        print(f"STDERR: {error}")
    return output, error

def check_deploy():
    ssh = ssh_connect()
    
    print("\n=== 检查 Docker Compose 配置 ===")
    run_command(ssh, "cat /opt/sub2api/deploy/docker-compose.yml")
    
    print("\n=== 检查容器内二进制文件 ===")
    run_command(ssh, "docker exec sub2api ls -la /app/sub2api")
    run_command(ssh, "docker exec sub2api file /app/sub2api")
    
    print("\n=== 测试 API 接口 ===")
    run_command(ssh, "curl -s http://localhost:8080/api/v1/settings/public | head -50")
    
    print("\n=== 检查服务端路由 ===")
    run_command(ssh, "docker exec sub2api ./sub2api --help 2>&1 || echo 'No help available'")
    
    ssh.close()

if __name__ == "__main__":
    check_deploy()
