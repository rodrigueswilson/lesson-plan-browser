import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');
const envLocalPath = path.join(projectRoot, '.env.local');
const envDir = path.join(projectRoot, 'env');

const envSources = {
  android: [
    path.join(projectRoot, '.env.android'),
    path.join(envDir, 'android.env'),
  ],
  desktop: [
    path.join(projectRoot, '.env.desktop'),
    path.join(envDir, 'desktop.env'),
  ],
  default: [
    path.join(projectRoot, '.env'),
    path.join(envDir, 'desktop.env'),
  ],
};

const exists = (p) => {
  try {
    fs.accessSync(p, fs.constants.R_OK);
    return true;
  } catch {
    return false;
  }
};

const pickSource = (candidates) => candidates.find((candidate) => exists(candidate));

export function selectEnv() {
  const platform = (process.env.TAURI_ENV_PLATFORM || '').toLowerCase();
  const target = (process.env.TAURI_ENV_TARGET_TRIPLE || '').toLowerCase();
  const isAndroid = platform === 'android' || target.includes('android');

  const label = isAndroid ? 'android' : 'desktop';
  let sourcePath = pickSource(envSources[label]);

  if (!sourcePath) {
    sourcePath = pickSource(envSources.default);
  }

  if (!sourcePath) {
    console.warn('[env] No environment template found; skipping .env.local sync.');
    if (exists(envLocalPath)) {
      fs.rmSync(envLocalPath);
    }
    return;
  }

  fs.copyFileSync(sourcePath, envLocalPath);
  const relativeSource = path.relative(projectRoot, sourcePath);
  console.log(`[env] Synced ${relativeSource} -> .env.local`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  selectEnv();
}

