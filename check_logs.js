const { Client } = require('ssh2');

const conn = new Client();

conn.on('ready', function() {
  console.log('SSH connection ready');
  
  conn.exec('docker logs --tail 100 sub2api', function(err, stream) {
    if (err) {
      console.error('Error:', err);
      conn.end();
      return;
    }
    
    stream.on('data', function(data) {
      console.log(data.toString());
    });
    
    stream.on('stderr', function(data) {
      console.log('STDERR:', data.toString());
    });
    
    stream.on('close', function(code, signal) {
      console.log('Exit code:', code);
      conn.end();
    });
  });
}).on('error', function(err) {
  console.error('Connection error:', err);
}).connect({
  host: '47.106.121.132',
  port: 22,
  username: 'root',
  password: 'Xn0753@#',
  readyTimeout: 10000
});