const { Client } = require('ssh2');

const conn = new Client();

conn.on('ready', function() {
  console.log('SSH connection ready');
  
  const commands = [
    'ls -la /root/sub2api*',
    'file /root/sub2api',
    'file /root/sub2api.bak',
    'file /root/sub2api_new'
  ];
  
  let index = 0;
  
  function runNext() {
    if (index >= commands.length) {
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