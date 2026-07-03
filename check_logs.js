const { Client } = require('ssh2');

const conn = new Client();

conn.on('ready', () => {
  console.log('✅ Connected');
  
  conn.exec('docker logs sub2api --tail 50', (err, stream) => {
    if (err) {
      console.error('Error:', err);
      conn.end();
      return;
    }
    
    let output = '';
    stream.on('data', (data) => { output += data.toString(); });
    stream.on('close', () => {
      console.log('\nContainer logs:');
      console.log(output);
      
      if (output.includes('Version')) {
        console.log('\n✅ Version found in logs');
      } else {
        console.log('\n❌ Version not found in logs');
      }
      conn.end();
    });
  });
}).on('error', (err) => {
  console.error('Connection failed:', err);
}).connect({
  host: '47.106.121.132',
  port: 22,
  username: 'root',
  password: 'Xn0753@#',
  readyTimeout: 15000
});