/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
    '../shared/**/*.{js,ts,jsx,tsx}',
  ],
  safelist: [
    // Use patterns to ensure all variations are included
    {
      pattern: /!?bg-(green|red|rose|pink|blue|purple|indigo|teal|cyan|emerald|sky|violet)-(50|100|200|300)/,
    },
    {
      pattern: /bg-(green|red|rose|pink|blue|purple|indigo|teal|cyan|emerald|sky|violet)-900\/(30|35|40|50|60)/,
    },
    {
      pattern: /border-(green|red|rose|pink|blue|purple|indigo|teal|cyan|emerald|sky|violet)-(200|300|400|500|600)/,
    },
    {
      pattern: /text-(green|red|rose|pink|blue|purple|indigo|teal|cyan|emerald|sky|violet)-(100|200|300|400|500|600|700|800|900|950)/,
    },
    // Also include explicit classes as backup
    // Green tones for non-class periods
    'bg-green-50', 'bg-green-100', 'bg-green-200',
    'bg-green-900/30', 'bg-green-900/35', 'bg-green-900/40', 'bg-green-900/50',
    'border-green-200', 'border-green-300', 'border-green-400',
    'text-green-800', 'text-green-900', 'text-green-100', 'text-green-200', 'text-green-300',
    // Room 501 reddish tones
    'bg-red-50', 'bg-red-100', 'bg-red-900/30', 'bg-red-900/40',
    'border-red-300', 'border-red-400', 'text-red-800', 'text-red-900', 'text-red-200', 'text-red-300',
    'bg-rose-50', 'bg-rose-900/30', 'border-rose-300', 'text-rose-800', 'text-rose-300',
    'bg-pink-50', 'bg-pink-900/30', 'border-pink-300', 'text-pink-800', 'text-pink-300',
    // Room base colors with tone variations - Blue
    'bg-blue-50', 'bg-blue-100', 'bg-blue-200', 'bg-blue-300',
    'bg-blue-900/30', 'bg-blue-900/40', 'bg-blue-900/50', 'bg-blue-900/60',
    'border-blue-300', 'border-blue-400', 'border-blue-500', 'border-blue-600',
    'text-blue-800', 'text-blue-900', 'text-blue-950',
    'text-blue-300', 'text-blue-400', 'text-blue-500', 'text-blue-600',
    // Purple
    'bg-purple-50', 'bg-purple-100', 'bg-purple-200', 'bg-purple-300',
    'bg-purple-900/30', 'bg-purple-900/40', 'bg-purple-900/50', 'bg-purple-900/60',
    'border-purple-300', 'border-purple-400', 'border-purple-500', 'border-purple-600',
    'text-purple-800', 'text-purple-900', 'text-purple-950',
    'text-purple-300', 'text-purple-400', 'text-purple-500', 'text-purple-600',
    // Indigo
    'bg-indigo-50', 'bg-indigo-100', 'bg-indigo-200', 'bg-indigo-300',
    'bg-indigo-900/30', 'bg-indigo-900/40', 'bg-indigo-900/50', 'bg-indigo-900/60',
    'border-indigo-200', 'border-indigo-300', 'border-indigo-400', 'border-indigo-500',
    'text-indigo-700', 'text-indigo-800', 'text-indigo-900', 'text-indigo-950',
    'text-indigo-300', 'text-indigo-400', 'text-indigo-500', 'text-indigo-600',
    // Amber (meeting period PLC/GLM - distinct from green)
    '!bg-amber-50', 'bg-amber-50', 'border-amber-300', 'text-amber-800', 'text-amber-300', 'bg-amber-900/30',
    // Teal
    '!bg-teal-50', 'bg-teal-50', 'bg-teal-100', 'bg-teal-200', 'bg-teal-300',
    'bg-teal-900/30', 'bg-teal-900/40', 'bg-teal-900/50', 'bg-teal-900/60',
    'border-teal-300', 'border-teal-400', 'border-teal-500', 'border-teal-600',
    'text-teal-800', 'text-teal-900', 'text-teal-950',
    'text-teal-300', 'text-teal-400', 'text-teal-500', 'text-teal-600',
    // Cyan
    'bg-cyan-50', 'bg-cyan-100', 'bg-cyan-200', 'bg-cyan-300',
    'bg-cyan-900/30', 'bg-cyan-900/40', 'bg-cyan-900/50', 'bg-cyan-900/60',
    'border-cyan-200', 'border-cyan-300', 'border-cyan-400', 'border-cyan-500',
    'text-cyan-700', 'text-cyan-800', 'text-cyan-900', 'text-cyan-950',
    'text-cyan-300', 'text-cyan-400', 'text-cyan-500', 'text-cyan-600',
    // Emerald
    'bg-emerald-50', 'bg-emerald-100', 'bg-emerald-200', 'bg-emerald-300',
    'bg-emerald-900/30', 'bg-emerald-900/40', 'bg-emerald-900/50', 'bg-emerald-900/60',
    'border-emerald-200', 'border-emerald-300', 'border-emerald-400', 'border-emerald-500',
    'text-emerald-700', 'text-emerald-800', 'text-emerald-900', 'text-emerald-950',
    'text-emerald-300', 'text-emerald-400', 'text-emerald-500', 'text-emerald-600',
    // Sky
    'bg-sky-50', 'bg-sky-100', 'bg-sky-200', 'bg-sky-300',
    'bg-sky-900/30', 'bg-sky-900/40', 'bg-sky-900/50', 'bg-sky-900/60',
    'border-sky-300', 'border-sky-400', 'border-sky-500', 'border-sky-600',
    'text-sky-800', 'text-sky-900', 'text-sky-950',
    'text-sky-300', 'text-sky-400', 'text-sky-500', 'text-sky-600',
    // Violet
    'bg-violet-50', 'bg-violet-100', 'bg-violet-200', 'bg-violet-300',
    'bg-violet-900/30', 'bg-violet-900/40', 'bg-violet-900/50', 'bg-violet-900/60',
    'border-violet-200', 'border-violet-300', 'border-violet-400', 'border-violet-500',
    'text-violet-700', 'text-violet-800', 'text-violet-900', 'text-violet-950',
    'text-violet-300', 'text-violet-400', 'text-violet-500', 'text-violet-600',
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
