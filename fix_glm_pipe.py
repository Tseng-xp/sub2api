import paramiko
import time

def ssh_connect():
    max_retries = 5
    for i in range(max_retries):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect('47.106.121.132', username='root', password='Xn0753@#', timeout=30)
            print(f"✓ SSH连接成功 (尝试 {i+1}/{max_retries})")
            return ssh
        except Exception as e:
            print(f"✗ SSH连接失败 (尝试 {i+1}/{max_retries}): {e}")
            time.sleep(5)
    raise Exception("SSH连接失败，已达到最大重试次数")

ssh = ssh_connect()

print("\n=== 修复GLM账号路由配置 ===")

print("\n1. 通过管道执行SQL命令...")

sql_content = '''UPDATE accounts SET extra = '{"openai_responses_mode": "force_chat_completions", "openai_responses_supported": false, "openai_apikey_responses_websockets_v2_mode": "off", "openai_apikey_responses_websockets_v2_enabled": false}'::jsonb WHERE id = 1;
UPDATE accounts SET extra = '{"openai_responses_mode": "force_chat_completions", "openai_responses_supported": false, "openai_apikey_responses_websockets_v2_mode": "off", "openai_apikey_responses_websockets_v2_enabled": false}'::jsonb WHERE id = 2;
SELECT id, name, extra FROM accounts;'''

cmd = "docker exec -i sub2api-postgres psql -U sub2api -d sub2api"

stdin, stdout, stderr = ssh.exec_command(cmd)
stdin.write(sql_content)
stdin.flush()
stdin.channel.shutdown_write()

output = stdout.read().decode()
print("OUTPUT:", output)
err = stderr.read().decode()
if err:
    print("STDERR:", err)

ssh.close()

if "force_chat_completions" in output:
    print("\n✓ 修改已生效！")
    print("\n现在可以重新测试GLM账号，应该能正常连接了。")
else:
    print("\n✗ 修改未生效，请检查")