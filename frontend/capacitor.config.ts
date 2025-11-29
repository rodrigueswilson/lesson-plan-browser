import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.lessonplanner.app',
  appName: 'Bilingual Lesson Planner',
  webDir: 'dist',
  server: {
    // For development on same machine: use localhost
    // For testing on Android device: use your PC's IP address
    // Run find-pc-ip.ps1 or find-pc-ip.bat to find your IP
    // Then update this URL to: http://YOUR_IP:8000
    // Example: url: 'http://192.168.1.100:8000'
    url: 'http://localhost:8000',
    cleartext: true
  },
  android: {
    allowMixedContent: true,
    buildOptions: {
      keystorePath: undefined,
      keystorePassword: undefined,
      keystoreAlias: undefined,
      keystoreAliasPassword: undefined
    }
  }
};

export default config;
