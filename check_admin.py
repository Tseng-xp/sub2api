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

def check_admin():
    ssh = ssh_connect()
    
    print("\n=== 检查所有用户角色 ===")
    run_command(ssh, "docker exec sub2api-postgres psql -U sub2api -d sub2api -c \"SELECT id, email, role, status FROM users ORDER BY id;\"")
    
    print("\n=== 检查管理员用户数量 ===")
    run_command(ssh, "docker exec sub2api-postgres psql -U sub2api -d sub2api -c \"SELECT COUNT(*) as admin_count FROM users WHERE role='admin';\"")
    
    ssh.close()

if __name__ == "__main__":
    check_admin()