/**
 * Color coding for schedule subjects and time periods.
 * Provides consistent visual distinction between different subjects and non-class periods.
 */

export interface SubjectColor {
  bg: string;           // Background color (light)
  bgDark: string;       // Background color for dark mode
  border: string;       // Border color
  text: string;         // Text color
  textDark: string;     // Text color for dark mode
}

const colorMap: Record<string, SubjectColor> = {
  // Non-class periods
  'PREP': {
    bg: 'bg-slate-200',
    bgDark: 'bg-slate-700',
    border: 'border-slate-400',
    text: 'text-slate-900',
    textDark: 'text-slate-100',
  },
  'Prep Time': {
    bg: 'bg-slate-200',
    bgDark: 'bg-slate-700',
    border: 'border-slate-400',
    text: 'text-slate-900',
    textDark: 'text-slate-100',
  },
  'A.M. Routine': {
    bg: 'bg-blue-50',
    bgDark: 'bg-blue-900/30',
    border: 'border-blue-200',
    text: 'text-blue-800',
    textDark: 'text-blue-300',
  },
  'AM Routine': {
    bg: 'bg-blue-50',
    bgDark: 'bg-blue-900/30',
    border: 'border-blue-200',
    text: 'text-blue-800',
    textDark: 'text-blue-300',
  },
  'Lunch': {
    bg: 'bg-orange-100',
    bgDark: 'bg-orange-900/40',
    border: 'border-orange-400',
    text: 'text-orange-900',
    textDark: 'text-orange-200',
  },
  'LUNCH': {
    bg: 'bg-orange-100',
    bgDark: 'bg-orange-900/40',
    border: 'border-orange-400',
    text: 'text-orange-900',
    textDark: 'text-orange-200',
  },
  'Dismissal': {
    bg: 'bg-purple-50',
    bgDark: 'bg-purple-900/30',
    border: 'border-purple-200',
    text: 'text-purple-800',
    textDark: 'text-purple-300',
  },
  'DISMISSAL': {
    bg: 'bg-purple-50',
    bgDark: 'bg-purple-900/30',
    border: 'border-purple-200',
    text: 'text-purple-800',
    textDark: 'text-purple-300',
  },
  
  // Core subjects
  'ELA': {
    bg: 'bg-green-50',
    bgDark: 'bg-green-900/30',
    border: 'border-green-300',
    text: 'text-green-800',
    textDark: 'text-green-300',
  },
  'MATH': {
    bg: 'bg-blue-50',
    bgDark: 'bg-blue-900/30',
    border: 'border-blue-300',
    text: 'text-blue-800',
    textDark: 'text-blue-300',
  },
  'Science': {
    bg: 'bg-yellow-50',
    bgDark: 'bg-yellow-900/30',
    border: 'border-yellow-300',
    text: 'text-yellow-800',
    textDark: 'text-yellow-300',
  },
  'SCIENCE': {
    bg: 'bg-yellow-50',
    bgDark: 'bg-yellow-900/30',
    border: 'border-yellow-300',
    text: 'text-yellow-800',
    textDark: 'text-yellow-300',
  },
  'Social Studies': {
    bg: 'bg-red-50',
    bgDark: 'bg-red-900/30',
    border: 'border-red-300',
    text: 'text-red-800',
    textDark: 'text-red-300',
  },
  'SOCIAL S.': {
    bg: 'bg-red-50',
    bgDark: 'bg-red-900/30',
    border: 'border-red-300',
    text: 'text-red-800',
    textDark: 'text-red-300',
  },
  'Social Science': {
    bg: 'bg-red-50',
    bgDark: 'bg-red-900/30',
    border: 'border-red-300',
    text: 'text-red-800',
    textDark: 'text-red-300',
  },
};

/**
 * Get color scheme based on homeroom or non-class period.
 * - Each homeroom gets a unique color (all subjects in same homeroom share color)
 * - Non-class periods (PREP, Lunch, A.M. Routine, Dismissal) get specific colors
 */
export function getSubjectColors(subject: string | null | undefined, _grade: string | null | undefined = null, homeroom: string | null | undefined = null): SubjectColor {
  if (!subject) {
    return {
      bg: 'bg-background',
      bgDark: 'bg-background',
      border: 'border-border',
      text: 'text-foreground',
      textDark: 'text-foreground',
    };
  }
  
  const normalized = subject.trim().toUpperCase();
  
  // First, check for non-class periods (they get specific colors regardless of homeroom)
  if (normalized === 'PREP' || normalized === 'PREP TIME') {
    return colorMap['PREP'] || colorMap['Prep Time'];
  }
  
  if (normalized === 'LUNCH') {
    return colorMap['Lunch'] || colorMap['LUNCH'];
  }
  
  if (normalized === 'A.M. ROUTINE' || normalized === 'AM ROUTINE' || normalized === 'MORNING ROUTINE') {
    return colorMap['A.M. Routine'] || colorMap['AM Routine'];
  }
  
  if (normalized === 'DISMISSAL') {
    return colorMap['Dismissal'] || colorMap['DISMISSAL'];
  }
  
  // For class subjects, use homeroom to determine color
  // All subjects in the same homeroom share the same color
  if (homeroom) {
    return generateColorFromHomeroom(homeroom);
  }
  
  // Fallback: if no homeroom, use subject-based color
  const upperKey = Object.keys(colorMap).find(
    key => key.toUpperCase() === normalized && !key.includes('|')
  );
  
  if (upperKey) {
    return colorMap[upperKey];
  }
  
  // Default fallback
  return {
    bg: 'bg-gray-50',
    bgDark: 'bg-gray-800',
    border: 'border-gray-200',
    text: 'text-gray-700',
    textDark: 'text-gray-300',
  };
}

/**
 * Generate a consistent color for a homeroom based on hash.
 * All subjects in the same homeroom will share the same color.
 */
function generateColorFromHomeroom(homeroom: string): SubjectColor {
  // Simple hash function
  let hash = 0;
  const normalizedHomeroom = homeroom.trim().toUpperCase();
  for (let i = 0; i < normalizedHomeroom.length; i++) {
    hash = normalizedHomeroom.charCodeAt(i) + ((hash << 5) - hash);
  }
  
  // Color palette for homerooms - distinct colors for different rooms
  const colors: SubjectColor[] = [
    {
      bg: 'bg-green-50',
      bgDark: 'bg-green-900/30',
      border: 'border-green-300',
      text: 'text-green-800',
      textDark: 'text-green-300',
    },
    {
      bg: 'bg-blue-50',
      bgDark: 'bg-blue-900/30',
      border: 'border-blue-300',
      text: 'text-blue-800',
      textDark: 'text-blue-300',
    },
    {
      bg: 'bg-purple-50',
      bgDark: 'bg-purple-900/30',
      border: 'border-purple-300',
      text: 'text-purple-800',
      textDark: 'text-purple-300',
    },
    {
      bg: 'bg-yellow-50',
      bgDark: 'bg-yellow-900/30',
      border: 'border-yellow-300',
      text: 'text-yellow-800',
      textDark: 'text-yellow-300',
    },
    {
      bg: 'bg-pink-50',
      bgDark: 'bg-pink-900/30',
      border: 'border-pink-300',
      text: 'text-pink-800',
      textDark: 'text-pink-300',
    },
    {
      bg: 'bg-indigo-50',
      bgDark: 'bg-indigo-900/30',
      border: 'border-indigo-300',
      text: 'text-indigo-800',
      textDark: 'text-indigo-300',
    },
    {
      bg: 'bg-teal-50',
      bgDark: 'bg-teal-900/30',
      border: 'border-teal-300',
      text: 'text-teal-800',
      textDark: 'text-teal-300',
    },
    {
      bg: 'bg-orange-50',
      bgDark: 'bg-orange-900/30',
      border: 'border-orange-300',
      text: 'text-orange-800',
      textDark: 'text-orange-300',
    },
    {
      bg: 'bg-cyan-50',
      bgDark: 'bg-cyan-900/30',
      border: 'border-cyan-300',
      text: 'text-cyan-800',
      textDark: 'text-cyan-300',
    },
    {
      bg: 'bg-emerald-50',
      bgDark: 'bg-emerald-900/30',
      border: 'border-emerald-300',
      text: 'text-emerald-800',
      textDark: 'text-emerald-300',
    },
  ];
  
  const index = Math.abs(hash) % colors.length;
  return colors[index];
}

/**
 * Get CSS classes for a schedule cell based on subject, grade, and homeroom.
 */
export function getScheduleCellClasses(subject: string | null | undefined, grade: string | null | undefined = null, homeroom: string | null | undefined = null, isDark: boolean = false): string {
  const colors = getSubjectColors(subject, grade, homeroom);
  
  if (isDark) {
    return `${colors.bgDark} ${colors.border} ${colors.textDark} border`;
  }
  
  return `${colors.bg} ${colors.border} ${colors.text} border`;
}

