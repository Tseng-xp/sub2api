import paramiko
import time
import subprocess
import os

HOST = "47.106.121.132"
USER = "root"
PASSWORD = "Xn0753@#"

def ssh_connect():
    max_retries = 5
    for i in range(max_retries):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)
            print(f"✓ SSH连接成功 (尝试 {i+1}/{max_retries})")
            return ssh
        except Exception as e:
            print(f"✗ SSH连接失败 (尝试 {i+1}/{max_retries}): {e}")
            time.sleep(5)
    raise Exception("SSH连接失败，已达到最大重试次数")

def run_command(ssh, command):
    print(f"\n$ {command}")
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    if output:
        print(output[:3000])
    if error:
        print(f"STDERR: {error[:1000]}")
    return output, error

def apply_customizations():
    print("\n0. 应用自定义修改...")
    project_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(project_dir, "apply_customizations.py")
    if os.path.exists(script_path):
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            cwd=project_dir
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"STDERR: {result.stderr}")
        print("✓ 自定义修改应用完成")
    else:
        print("✗ 未找到 apply_customizations.py")

def deploy():
    print("=== 部署新版本到服务器 ===")
    
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    apply_customizations()
    
    print("\n1. 构建前端...")
    cmd = "pnpm install"
    print(f"本地执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.join(project_dir, "frontend"))
    if result.returncode != 0:
        print(f"STDERR: {result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr}")
        raise Exception(f"前端安装失败，退出码: {result.returncode}")
    
    cmd = "pnpm build"
    print(f"本地执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.join(project_dir, "frontend"))
    if result.returncode != 0:
        print(f"STDERR: {result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr}")
        raise Exception(f"前端构建失败，退出码: {result.returncode}")
    print("✓ 前端构建成功")
    
    print("\n2. 构建Linux后端二进制...")
    build_env = os.environ.copy()
    build_env['CGO_ENABLED'] = '0'
    build_env['GOOS'] = 'linux'
    build_env['GOARCH'] = 'amd64'
    cmd = "go build -tags embed -o ../sub2api_new ./cmd/server/"
    print(f"本地执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.join(project_dir, "backend"), env=build_env)
    if result.returncode != 0:
        print(f"STDERR: {result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr}")
        raise Exception(f"后端构建失败，退出码: {result.returncode}")
    print("✓ 后端构建成功")
    
    ssh = ssh_connect()
    
    print("\n3. 备份现有服务...")
    run_command(ssh, "cp /opt/sub2api/deploy/sub2api /opt/sub2api/deploy/sub2api_backup_$(date +%Y%m%d_%H%M%S)")
    
    print("\n4. 停止当前服务...")
    run_command(ssh, "docker stop sub2api")
    
    print("\n5. 上传新版本...")
    sftp = ssh.open_sftp()
    sftp.put(os.path.join(project_dir, "sub2api_new"), "/opt/sub2api/deploy/sub2api")
    
    print("\n6. 更新文档...")
    sftp.put(os.path.join(project_dir, "docs/index.html"), "/opt/sub2api/docs/index.html")
    
    sftp.close()
    print("✓ 上传成功")
    
    print("\n7. 启动服务...")
    run_command(ssh, "docker start sub2api")
    
    print("\n8. 等待服务启动...")
    time.sleep(15)
    
    print("\n9. 检查服务状态...")
    run_command(ssh, "docker ps --filter name=sub2api")
    
    print("\n10. 检查服务日志...")
    run_command(ssh, "docker logs sub2api --tail=50")
    
    ssh.close()
    
    print("\n=== 部署完成 ===")
    print("\n⚠️ 重要提示:")
    print("  - 本次部署仅替换了后端二进制文件和文档")
    print("  - Nginx配置文件 (/www/server/panel/vhost/nginx/) 未被修改")
    print("  - 数据库数据保持不变")
    print("  - 备案号等网站设置已包含在前端代码中")
    print("\n下次部署时，只会替换以下文件:")
    print("  - /opt/sub2api/deploy/sub2api (后端二进制)")
    print("  - /opt/sub2api/docs/index.html (文档)")

if __name__ == "__main__":
    deploy()