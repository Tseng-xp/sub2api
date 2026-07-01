const { execSync } = require('child_process');
const fs = require('fs');

try {
  const result = execSync('npx vite build', {
    cwd: __dirname,
    encoding: 'utf8',
    stdio: ['pipe', 'pipe', 'pipe'],
    maxBuffer: 10 * 1024 * 1024
  });
  console.log('SUCCESS');
  console.log(result);
} catch (e) {
  console.log('FAILED');
  console.log('STDOUT:', e.stdout);
  console.log('STDERR:', e.stderr);
  fs.writeFileSync('build_error.log', e.stderr || e.message, 'utf8');
}
