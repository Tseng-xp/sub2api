import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('47.106.121.132', username='root', password='Xn0753@#', timeout=30)

print("=" * 60)
print("修复配置冲突")
print("=" * 60)

# 1. 检查主站配置中的 docs 路径
print("\n--- 检查主站配置 ---")
cmd = "cat /www/server/panel/vhost/nginx/tongyuan-ai.cn.conf | grep -A10 'location.*docs'"
stdin, stdout, stderr = ssh.exec_command(cmd)
output = stdout.read().decode()
print("主站 docs 配置:", output)

# 2. 更新主站配置，移除 /docs/ 路径（因为已迁移到独立子域名）
nginx_config = """server
{
    listen 80;
    listen 443 ssl;
    http2 on;
    server_name tongyuan-ai.cn;
    index index.php index.html index.htm default.php default.htm default.html;
    root /www/wwwroot/tongyuan-ai.cn;
    #CERT-APPLY-CHECK--START
    include /www/server/panel/vhost/nginx/well-known/tongyuan-ai.cn.conf;
    #CERT-APPLY-CHECK--END
    include /www/server/panel/vhost/nginx/extension/tongyuan-ai.cn/*.conf;

    ssl_certificate    /www/server/panel/vhost/cert/tongyuan-ai.cn/fullchain.pem;
    ssl_certificate_key    /www/server/panel/vhost/cert/tongyuan-ai.cn/privkey.pem;
    ssl_protocols TLSv1.1 TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_tickets on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000";
    error_page 497  https://$host$request_uri;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    #PHP-INFO-START
    include enable-php-00.conf;
    #PHP-INFO-END

    #REWRITE-START
    include /www/server/panel/vhost/rewrite/tongyuan-ai.cn.conf;
    #REWRITE-END

    # 禁止访问的敏感文件
    location ~* \\.user\\.ini|\\.htaccess|\\.htpasswd|\\.env.*|\\.project|\\.bashrc|\\.bash_profile|\\.bash_logout|\\.DS_Store|\\.gitignore|\\.gitattributes|LICENSE|README\\.md|CLAUDE\\.md|CHANGELOG\\.md|CHANGELOG|CONTRIBUTING\\.md|TODO\\.md|FAQ\\.md|composer\\.json|composer\\.lock|package(-lock)?\\.json|yarn\\.lock|pnpm-lock\\.yaml|\\.\\w+|\\.swp|\\.swo|\\.bak(up)?|\\.old|\\.tmp|\\.temp|\\.log|\\.sql(\\.gz)?|docker-compose\\.yml|docker\\.env|Dockerfile|\\.csproj|\\.sln|Cargo\\.toml|Cargo\\.lock|go\\.mod|go\\.sum|phpunit\\.xml|phpunit\\.xml|pom\\.xml|build\\.gradl|pyproject\\.toml|requirements\\.txt|application(-\\w+)?\\.(ya?ml|properties)$
    {
        return 404;
    }

    # 禁止访问的敏感目录
    location ~* /(\\.git|\\.svn|\\.bzr|\\.vscode|\\.claude|\\.idea|\\.ssh|\\.github|\\.npm|\\.yarn|\\.pnpm|\\.cache|\\.husky|\\.turbo|\\.next|\\.nuxt|node_modules|runtime)/ {
        return 404;
    }

    #一键申请SSL证书验证目录相关设置
    location ~ \\.well-known{
        allow all;
    }

    #禁止在证书验证目录放入敏感文件
    if ( $uri ~ "^/\\.well-known/.*\\.(php|jsp|py|js|css|lua|ts|go|zip|tar\\.gz|rar|7z|sql|bak)$" ) {
        return 403;
    }

    access_log  /www/wwwlogs/tongyuan-ai.cn.log;
    error_log  /www/wwwlogs/tongyuan-ai.cn.error.log;
}
"""

sftp = ssh.open_sftp()
remote_file = "/www/server/panel/vhost/nginx/tongyuan-ai.cn.conf"

with sftp.file(remote_file, 'w') as f:
    f.write(nginx_config)

print("✓ 主站配置已更新，移除 /docs/ 路径")

sftp.close()

# 3. 测试 Nginx 配置
print("\n--- 测试 Nginx 配置 ---")
cmd = "nginx -t"
stdin, stdout, stderr = ssh.exec_command(cmd)
output = stderr.read().decode()
print(output)

if "successful" in output:
    # 重启 Nginx
    print("\n--- 重启 Nginx ---")
    cmd = "/etc/init.d/nginx restart"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    print("✓ Nginx 重启完成")

    # 4. 验证两个站点
    print("\n--- 验证主站 ---")
    cmd = "curl -s https://tongyuan-ai.cn/ 2>&1 | head -5"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode()
    if "TYM" in output or "sub2api" in output:
        print("✓ 主站正常:", output[:100])
    else:
        print("主站响应:", output[:100])

    print("\n--- 验证文档站 ---")
    cmd = "curl -s https://docs.tongyuan-ai.cn/ 2>&1 | head -10"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode()
    if "通元聚合" in output:
        print("✓ 文档站正常: https://docs.tongyuan-ai.cn/")
        print(output[:200])
    else:
        print("文档站响应:", output[:200])
else:
    print("✗ Nginx 配置测试失败")

ssh.close()
print("\n配置完成！")