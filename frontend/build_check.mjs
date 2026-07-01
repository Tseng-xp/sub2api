import { execSync } from 'child_process';
import fs from 'fs';

try {
  const result = execSync('npx vite build', {
    cwd: process.cwd(),
    encoding: 'utf8',
    stdio: ['pipe', 'pipe', 'pipe'],
    maxBuffer: 10 * 1024 * 1024
  });
  console.log('SUCCESS');
  console.log(result);
} catch (e) {
  console.log('FAILED');
  console.log('---STDOUT---');
  console.log(e.stdout);
  console.log('---STDERR---');
  console.log(e.stderr);
  fs.writeFileSync('build_error.log', (e.stderr || e.message), 'utf8');
}
