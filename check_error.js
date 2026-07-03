const { Client } = require('ssh2');

const conn = new Client();
const HOST = process.env.SERVER_HOST || '';
const PASSWORD = process.env.SERVER_PASSWORD || '';

conn.on('ready', function() {
  console.log('SSH connection ready');
  
  const commands = [
    'docker logs --tail 20 sub2api 2>&1 | head -20',
    'docker inspect sub2api --format "{{.State.ExitCode}} {{.State.Error}}"'
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
        console.log(data.toString());
      });
      
      stream.on('stderr', function(data) {
        console.log('STDERR:', data.toString());
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
  host: HOST,
  port: 22,
  username: 'root',
  password: PASSWORD,
  readyTimeout: 10000
});