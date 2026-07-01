const { Client } = require('ssh2');

const conn = new Client();

conn.on('ready', function() {
  console.log('SSH connection ready');
  
  const commands = [
    'docker exec sub2api-postgres psql -U sub2api -d sub2api -c "SELECT count(*) FROM settings;"',
    'docker rm -f sub2api',
    'docker run -d --name sub2api --network deploy_sub2api-network -p 8080:8080 --restart=unless-stopped ' +
    '-v /root/sub2api_data/config.yaml:/app/config.yaml ' +
    '-v /root/sub2api:/app/sub2api ' +
    'golang:1.26.4-alpine',
    'docker exec sub2api ls -la /app/',
    'docker exec sub2api chmod +x /app/sub2api',
    'docker exec sub2api ./sub2api'
  ];
  
  let index = 0;
  
  function runNext() {
    if (index >= commands.length) {
      console.log('Rebuild completed');
      conn.end();
      return;
    }
    
    const cmd = commands[index];
    console.log(`\n--- Executing: ${cmd}`);
    index++;
    
    conn.exec(cmd, function(err, stream) {
      if (err) {
        console.error('Error:', err);
        runNext();
        return;
      }
      
      stream.on('data', function(data) {
        console.log(data.toString().trim());
      });
      
      stream.on('stderr', function(data) {
        console.log('STDERR:', data.toString().trim());
      });
      
      stream.on('close', function(code, signal) {
        console.log('Exit code:', code);
        runNext();
      });
    });
  }
  
  runNext();
}).on('error', function(err) {
  console.error('Connection error:', err);
}).connect({
  host: '47.106.121.132',
  port: 22,
  username: 'root',
  password: 'Xn0753@#',
  readyTimeout: 10000
});