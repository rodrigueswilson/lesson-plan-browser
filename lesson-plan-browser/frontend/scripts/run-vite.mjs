import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import { selectEnv } from './select-env.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

const command = process.argv[2] ?? 'dev';
if (!['dev', 'build'].includes(command)) {
  console.error(`[vite] Unsupported command "${command}". Use "dev" or "build".`);
  process.exit(1);
}

selectEnv();

const rawPlatform = process.env.TAURI_ENV_PLATFORM ?? '';
const rawTarget = process.env.TAURI_ENV_TARGET_TRIPLE ?? '';
const platform = rawPlatform.toLowerCase();
const target = rawTarget.toLowerCase();
const isAndroid = platform === 'android' || target.includes('android');

const mode = isAndroid ? 'android' : command === 'dev' ? 'development' : 'production';
const useShell = process.platform === 'win32';
const bin = 'npx';
const args = ['vite'];
if (command === 'build') {
  args.push('build');
}
args.push('--mode', mode);

if (rawPlatform || rawTarget) {
  console.log(`[vite] TAURI env: platform=${rawPlatform || '(unset)'} target=${rawTarget || '(unset)'}`);
}
console.log(`[vite] Running "${command}" with mode "${mode}" (${isAndroid ? 'android' : 'default'} env)`);

const child = spawn(bin, args, {
  cwd: projectRoot,
  stdio: 'inherit',
  env: process.env,
  shell: useShell,
});

child.on('close', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
  } else {
    process.exit(code ?? 0);
  }
});

