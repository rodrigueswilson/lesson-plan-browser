/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  safelist: [
    { pattern: /^(bg|border|text)-teal-/ },
    '!bg-teal-50',
    'border-teal-300',
    'text-teal-800',
    { pattern: /^(bg|border|text)-amber-/ },
    '!bg-amber-50',
    'border-amber-300',
    'text-amber-800',
  ],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
    '../../shared/lesson-browser/src/**/*.{js,ts,jsx,tsx}',
    '../../shared/lesson-mode/src/**/*.{js,ts,jsx,tsx}',
    '../../shared/lesson-api/src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [],
};

