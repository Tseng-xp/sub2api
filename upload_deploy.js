const fs = require('fs');
const path = require('path');
const { Client } = require('ssh2');

const conn = new Client();

conn.on('ready', function() {
  console.log('SSH connection ready');
  
  const commands = [
    'cd /root/sub2api && git stash && git pull origin main',
    'cd /root/sub2api/frontend && npm install && npm run build',
    'cd /root/sub2api/backend && go build -tags embed -ldflags="-s -w -X main.Version=0.1.142" -trimpath -o bin/server ./cmd/server',
    'cd /root/sub2api && docker build -t tseng0753/sub2api:latest -f backend/Dockerfile .',
    'docker rm -f sub2api',
    'docker run -d --name sub2api --network deploy_sub2api-network -p 8080:8080 --restart=unless-stopped ' +
    '-v /root/sub2api_data/config.yaml:/app/config.yaml ' +
    'tseng0753/sub2api:latest',
    'sleep 15',
    'docker ps | grep sub2api',
    'docker logs sub2api --tail 40'
  ];
  
  let index = 0;
  
  function runNext() {
    if (index >= commands.length) {
      console.log('Deployment completed');
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