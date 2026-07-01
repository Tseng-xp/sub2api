const fs = require('fs');
const { Client } = require('ssh2');

const conn = new Client();

conn.on('ready', function() {
  console.log('SSH connection ready');
  
  const localFile = './backend/bin/server';
  const remoteFile = '/root/sub2api_new';
  
  console.log(`Uploading ${localFile} to ${remoteFile}...`);
  
  conn.sftp(function(err, sftp) {
    if (err) {
      console.error('SFTP error:', err);
      conn.end();
      return;
    }
    
    const readStream = fs.createReadStream(localFile);
    const writeStream = sftp.createWriteStream(remoteFile);
    
    writeStream.on('close', function() {
      console.log('File uploaded successfully');
      
      sftp.end();
      
      const commands = [
        'chmod +x /root/sub2api_new',
        'docker cp /root/sub2api_new sub2api:/app/sub2api',
        'docker exec sub2api chmod +x /app/sub2api',
        'docker restart sub2api',
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
    });
    
    writeStream.on('error', function(err) {
      console.error('Write error:', err);
      sftp.end();
      conn.end();
    });
    
    readStream.pipe(writeStream);
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