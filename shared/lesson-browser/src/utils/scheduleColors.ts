/**
 * Color coding for schedule subjects and time periods.
 * Single Source of Truth (SSOT) for all lesson colors across schedule, browser, and day views.
 * 
 * Color Rules:
 * - Non-class periods (A.M. Routine, Lunch, Dismissal) use green tones
 * - Each room gets a base color, with different tones per subject within that room
 * - Room 501 specifically uses reddish tones with different tones per subject
 * 
 * IMPORTANT: All Tailwind classes used here must be in the safelist in tailwind.config.js
 * This comment block helps Tailwind detect the classes:
 * 
 * bg-green-50 bg-green-100 bg-green-200 bg-green-900/30 bg-green-900/35 bg-green-900/40 bg-green-900/50
 * border-green-200 border-green-300 border-green-400
 * text-green-800 text-green-900 text-green-100 text-green-200 text-green-300
 * 
 * bg-red-50 bg-red-100 bg-red-900/30 bg-red-900/40 border-red-300 border-red-400
 * text-red-800 text-red-900 text-red-200 text-red-300
 * bg-rose-50 bg-rose-900/30 border-rose-300 text-rose-800 text-rose-300
 * bg-pink-50 bg-pink-900/30 border-pink-300 text-pink-800 text-pink-300
 * 
 * bg-blue-50 bg-blue-100 bg-blue-200 bg-blue-300 bg-blue-900/30 bg-blue-900/40 bg-blue-900/50 bg-blue-900/60
 * border-blue-300 border-blue-400 border-blue-500 border-blue-600
 * text-blue-800 text-blue-900 text-blue-950 text-blue-300 text-blue-400 text-blue-500 text-blue-600
 * 
 * bg-purple-50 bg-purple-100 bg-purple-200 bg-purple-300 bg-purple-900/30 bg-purple-900/40 bg-purple-900/50 bg-purple-900/60
 * border-purple-300 border-purple-400 border-purple-500 border-purple-600
 * text-purple-800 text-purple-900 text-purple-950 text-purple-300 text-purple-400 text-purple-500 text-purple-600
 * 
 * bg-indigo-50 bg-indigo-100 bg-indigo-200 bg-indigo-300 bg-indigo-900/30 bg-indigo-900/40 bg-indigo-900/50 bg-indigo-900/60
 * border-indigo-200 border-indigo-300 border-indigo-400 border-indigo-500
 * text-indigo-700 text-indigo-800 text-indigo-900 text-indigo-950 text-indigo-300 text-indigo-400 text-indigo-500 text-indigo-600
 * 
 * bg-teal-50 bg-teal-100 bg-teal-200 bg-teal-300 bg-teal-900/30 bg-teal-900/40 bg-teal-900/50 bg-teal-900/60
 * border-teal-300 border-teal-400 border-teal-500 border-teal-600
 * text-teal-800 text-teal-900 text-teal-950 text-teal-300 text-teal-400 text-teal-500 text-teal-600
 * 
 * bg-cyan-50 bg-cyan-100 bg-cyan-200 bg-cyan-300 bg-cyan-900/30 bg-cyan-900/40 bg-cyan-900/50 bg-cyan-900/60
 * border-cyan-200 border-cyan-300 border-cyan-400 border-cyan-500
 * text-cyan-700 text-cyan-800 text-cyan-900 text-cyan-950 text-cyan-300 text-cyan-400 text-cyan-500 text-cyan-600
 * 
 * bg-emerald-50 bg-emerald-100 bg-emerald-200 bg-emerald-300 bg-emerald-900/30 bg-emerald-900/40 bg-emerald-900/50 bg-emerald-900/60
 * border-emerald-200 border-emerald-300 border-emerald-400 border-emerald-500
 * text-emerald-700 text-emerald-700 text-emerald-800 text-emerald-900 text-emerald-950 text-emerald-300 text-emerald-400 text-emerald-500 text-emerald-600
 * 
 * bg-sky-50 bg-sky-100 bg-sky-200 bg-sky-300 bg-sky-900/30 bg-sky-900/40 bg-sky-900/50 bg-sky-900/60
 * border-sky-300 border-sky-400 border-sky-500 border-sky-600
 * text-sky-800 text-sky-900 text-sky-950 text-sky-300 text-sky-400 text-sky-500 text-sky-600
 * 
 * bg-violet-50 bg-violet-100 bg-violet-200 bg-violet-300 bg-violet-900/30 bg-violet-900/40 bg-violet-900/50 bg-violet-900/60
 * border-violet-200 border-violet-300 border-violet-400 border-violet-500
 * text-violet-700 text-violet-800 text-violet-900 text-violet-950 text-violet-300 text-violet-400 text-violet-500 text-violet-600
 */

export interface SubjectColor {
  bg: string;           // Background color (light) - use !important to override Card defaults
  bgDark: string;       // Background color for dark mode
  border: string;       // Border color
  text: string;         // Text color
  textDark: string;     // Text color for dark mode
}

/**
 * Green tone variations for non-class periods.
 * All non-class periods use green tones for consistency.
 */
const nonClassPeriodColors: Record<string, SubjectColor> = {
  'PREP': {
    bg: '!bg-green-100',
    bgDark: 'bg-green-900/40',
    border: 'border-green-300',
    text: 'text-green-900',
    textDark: 'text-green-200',
  },
  'A.M. ROUTINE': {
    bg: '!bg-green-50',
    bgDark: 'bg-green-900/30',
    border: 'border-green-200',
    text: 'text-green-800',
    textDark: 'text-green-300',
  },
  'LUNCH': {
    bg: '!bg-green-50',
    bgDark: 'bg-green-900/30',
    border: 'border-green-200',
    text: 'text-green-800',
    textDark: 'text-green-300',
  },
  'DISMISSAL': {
    bg: '!bg-green-50',
    bgDark: 'bg-green-900/30',
    border: 'border-green-200',
    text: 'text-green-800',
    textDark: 'text-green-300',
  },
};

/**
 * Meeting periods (PLC, GLM) - single source of truth for schedule and browser.
 * RGB values here drive both Tailwind (browser) and inline styles (Schedule Input).
 * Keep index.css .schedule-cell-meeting in sync with these values when changing.
 */
const MEETING_BG = 'rgb(255 251 235)';
const MEETING_BORDER = 'rgb(252 211 77)';
const MEETING_TEXT = 'rgb(146 64 14)';

export const meetingPeriodColors: SubjectColor = {
  bg: '!bg-amber-50',
  bgDark: 'bg-amber-900/30',
  border: 'border-amber-300',
  text: 'text-amber-800',
  textDark: 'text-amber-300',
};

/** Inline style object for meeting cells (Schedule Input). Same visual as meetingPeriodColors. */
export const meetingPeriodInlineStyle: { backgroundColor: string; borderColor: string; color: string } = {
  backgroundColor: MEETING_BG,
  borderColor: MEETING_BORDER,
  color: MEETING_TEXT,
};

/**
 * Base color palette for rooms (excluding room 501 which has special handling).
 * Each room gets assigned a base color from this palette.
 */
const roomBaseColors: SubjectColor[] = [
  {
    bg: '!bg-blue-50',
    bgDark: 'bg-blue-900/30',
    border: 'border-blue-300',
    text: 'text-blue-800',
    textDark: 'text-blue-300',
  },
  {
    bg: '!bg-purple-50',
    bgDark: 'bg-purple-900/30',
    border: 'border-purple-300',
    text: 'text-purple-800',
    textDark: 'text-purple-300',
  },
  {
    bg: '!bg-indigo-50',
    bgDark: 'bg-indigo-900/30',
    border: 'border-indigo-300',
    text: 'text-indigo-800',
    textDark: 'text-indigo-300',
  },
  {
    bg: '!bg-teal-50',
    bgDark: 'bg-teal-900/30',
    border: 'border-teal-300',
    text: 'text-teal-800',
    textDark: 'text-teal-300',
  },
  {
    bg: '!bg-cyan-50',
    bgDark: 'bg-cyan-900/30',
    border: 'border-cyan-300',
    text: 'text-cyan-800',
    textDark: 'text-cyan-300',
  },
  {
    bg: '!bg-emerald-50',
    bgDark: 'bg-emerald-900/30',
    border: 'border-emerald-300',
    text: 'text-emerald-800',
    textDark: 'text-emerald-300',
  },
  {
    bg: '!bg-sky-50',
    bgDark: 'bg-sky-900/30',
    border: 'border-sky-300',
    text: 'text-sky-800',
    textDark: 'text-sky-300',
  },
  {
    bg: '!bg-violet-50',
    bgDark: 'bg-violet-900/30',
    border: 'border-violet-300',
    text: 'text-violet-800',
    textDark: 'text-violet-300',
  },
];

/**
 * Reddish tone variations for room 501 subjects.
 * Room 501 uses reddish tones with different shades per subject.
 */
const room501SubjectTones: Record<string, SubjectColor> = {
  'ELA': {
    bg: '!bg-red-50',
    bgDark: 'bg-red-900/30',
    border: 'border-red-300',
    text: 'text-red-800',
    textDark: 'text-red-300',
  },
  'MATH': {
    bg: '!bg-rose-50',
    bgDark: 'bg-rose-900/30',
    border: 'border-rose-300',
    text: 'text-rose-800',
    textDark: 'text-rose-300',
  },
  'SCIENCE': {
    bg: '!bg-pink-50',
    bgDark: 'bg-pink-900/30',
    border: 'border-pink-300',
    text: 'text-pink-800',
    textDark: 'text-pink-300',
  },
  'SOCIAL STUDIES': {
    bg: '!bg-red-100',
    bgDark: 'bg-red-900/40',
    border: 'border-red-400',
    text: 'text-red-900',
    textDark: 'text-red-200',
  },
  'SOCIAL S.': {
    bg: '!bg-red-100',
    bgDark: 'bg-red-900/40',
    border: 'border-red-400',
    text: 'text-red-900',
    textDark: 'text-red-200',
  },
  'SOCIAL SCIENCE': {
    bg: '!bg-red-100',
    bgDark: 'bg-red-900/40',
    border: 'border-red-400',
    text: 'text-red-900',
    textDark: 'text-red-200',
  },
};

/**
 * Subject tone variations for other rooms.
 * Maps subjects to tone intensity levels (0-3) within a room's base color.
 * Tone 0 = lightest (ELA), Tone 1 = light (MATH), Tone 2 = medium (SCIENCE), Tone 3 = darker (SOCIAL STUDIES)
 */
const subjectToneMap: Record<string, number> = {
  'ELA': 0,
  'ENGLISH LANGUAGE ARTS': 0,
  'ENGLISH': 0,
  'SS': 3,  // Social Studies abbreviation
  'MATH': 1,
  'MATHEMATICS': 1,
  'SCIENCE': 2,
  'SOCIAL STUDIES': 3,
  'SOCIAL S.': 3,
  'SOCIAL SCIENCE': 3,
  'SOCIAL': 3,
};

/**
 * Explicit tone variation mappings for all color combinations.
 * This ensures Tailwind's JIT compiler detects all classes at build time.
 * Format: colorName_toneLevel -> SubjectColor
 */
const toneVariationMap: Record<string, Record<number, SubjectColor>> = {
  blue: {
    0: { bg: '!bg-blue-50', bgDark: 'bg-blue-900/30', border: 'border-blue-300', text: 'text-blue-800', textDark: 'text-blue-300' },
    1: { bg: '!bg-blue-100', bgDark: 'bg-blue-900/40', border: 'border-blue-400', text: 'text-blue-900', textDark: 'text-blue-400' },
    2: { bg: '!bg-blue-200', bgDark: 'bg-blue-900/50', border: 'border-blue-500', text: 'text-blue-950', textDark: 'text-blue-500' },
    3: { bg: '!bg-blue-300', bgDark: 'bg-blue-900/60', border: 'border-blue-600', text: 'text-blue-950', textDark: 'text-blue-600' },
  },
  purple: {
    0: { bg: '!bg-purple-50', bgDark: 'bg-purple-900/30', border: 'border-purple-300', text: 'text-purple-800', textDark: 'text-purple-300' },
    1: { bg: '!bg-purple-100', bgDark: 'bg-purple-900/40', border: 'border-purple-400', text: 'text-purple-900', textDark: 'text-purple-400' },
    2: { bg: '!bg-purple-200', bgDark: 'bg-purple-900/50', border: 'border-purple-500', text: 'text-purple-950', textDark: 'text-purple-500' },
    3: { bg: '!bg-purple-300', bgDark: 'bg-purple-900/60', border: 'border-purple-600', text: 'text-purple-950', textDark: 'text-purple-600' },
  },
  indigo: {
    0: { bg: '!bg-indigo-50', bgDark: 'bg-indigo-900/30', border: 'border-indigo-200', text: 'text-indigo-700', textDark: 'text-indigo-300' },
    1: { bg: '!bg-indigo-100', bgDark: 'bg-indigo-900/40', border: 'border-indigo-300', text: 'text-indigo-800', textDark: 'text-indigo-400' },
    2: { bg: '!bg-indigo-200', bgDark: 'bg-indigo-900/50', border: 'border-indigo-400', text: 'text-indigo-900', textDark: 'text-indigo-500' },
    3: { bg: '!bg-indigo-300', bgDark: 'bg-indigo-900/60', border: 'border-indigo-500', text: 'text-indigo-950', textDark: 'text-indigo-600' },
  },
  teal: {
    0: { bg: '!bg-teal-50', bgDark: 'bg-teal-900/30', border: 'border-teal-300', text: 'text-teal-800', textDark: 'text-teal-300' },
    1: { bg: '!bg-teal-100', bgDark: 'bg-teal-900/40', border: 'border-teal-400', text: 'text-teal-900', textDark: 'text-teal-400' },
    2: { bg: '!bg-teal-200', bgDark: 'bg-teal-900/50', border: 'border-teal-500', text: 'text-teal-950', textDark: 'text-teal-500' },
    3: { bg: '!bg-teal-300', bgDark: 'bg-teal-900/60', border: 'border-teal-600', text: 'text-teal-950', textDark: 'text-teal-600' },
  },
  cyan: {
    0: { bg: '!bg-cyan-50', bgDark: 'bg-cyan-900/30', border: 'border-cyan-200', text: 'text-cyan-700', textDark: 'text-cyan-300' },
    1: { bg: '!bg-cyan-100', bgDark: 'bg-cyan-900/40', border: 'border-cyan-300', text: 'text-cyan-800', textDark: 'text-cyan-400' },
    2: { bg: '!bg-cyan-200', bgDark: 'bg-cyan-900/50', border: 'border-cyan-400', text: 'text-cyan-900', textDark: 'text-cyan-500' },
    3: { bg: '!bg-cyan-300', bgDark: 'bg-cyan-900/60', border: 'border-cyan-500', text: 'text-cyan-950', textDark: 'text-cyan-600' },
  },
  emerald: {
    0: { bg: '!bg-emerald-50', bgDark: 'bg-emerald-900/30', border: 'border-emerald-200', text: 'text-emerald-700', textDark: 'text-emerald-300' },
    1: { bg: '!bg-emerald-100', bgDark: 'bg-emerald-900/40', border: 'border-emerald-300', text: 'text-emerald-800', textDark: 'text-emerald-400' },
    2: { bg: '!bg-emerald-200', bgDark: 'bg-emerald-900/50', border: 'border-emerald-400', text: 'text-emerald-900', textDark: 'text-emerald-500' },
    3: { bg: '!bg-emerald-300', bgDark: 'bg-emerald-900/60', border: 'border-emerald-500', text: 'text-emerald-950', textDark: 'text-emerald-600' },
  },
  sky: {
    0: { bg: '!bg-sky-50', bgDark: 'bg-sky-900/30', border: 'border-sky-300', text: 'text-sky-800', textDark: 'text-sky-300' },
    1: { bg: '!bg-sky-100', bgDark: 'bg-sky-900/40', border: 'border-sky-400', text: 'text-sky-900', textDark: 'text-sky-400' },
    2: { bg: '!bg-sky-200', bgDark: 'bg-sky-900/50', border: 'border-sky-500', text: 'text-sky-950', textDark: 'text-sky-500' },
    3: { bg: '!bg-sky-300', bgDark: 'bg-sky-900/60', border: 'border-sky-600', text: 'text-sky-950', textDark: 'text-sky-600' },
  },
  violet: {
    0: { bg: '!bg-violet-50', bgDark: 'bg-violet-900/30', border: 'border-violet-200', text: 'text-violet-700', textDark: 'text-violet-300' },
    1: { bg: '!bg-violet-100', bgDark: 'bg-violet-900/40', border: 'border-violet-300', text: 'text-violet-800', textDark: 'text-violet-400' },
    2: { bg: '!bg-violet-200', bgDark: 'bg-violet-900/50', border: 'border-violet-400', text: 'text-violet-900', textDark: 'text-violet-500' },
    3: { bg: '!bg-violet-300', bgDark: 'bg-violet-900/60', border: 'border-violet-500', text: 'text-violet-950', textDark: 'text-violet-600' },
  },
};

/**
 * Generate tone variations for a base color.
 * Creates lighter/darker variations of a base color for different subjects.
 */
function generateToneVariation(baseColor: SubjectColor, toneLevel: number): SubjectColor {
  // Extract color name from base color (e.g., 'blue' from 'bg-blue-50')
  const bgMatch = baseColor.bg.match(/bg-(\w+)-(\d+)/);
  if (!bgMatch) return baseColor;
  
  const colorName = bgMatch[1];
  const safeToneLevel = Math.min(Math.max(toneLevel, 0), 3);
  
  // Use explicit mapping to ensure Tailwind detects all classes
  const colorMap = toneVariationMap[colorName];
  if (colorMap && colorMap[safeToneLevel]) {
    return colorMap[safeToneLevel];
  }
  
  // Fallback to base color if mapping not found
  return baseColor;
}

/**
 * Get base color for a room based on hash.
 * Room 501 is handled specially and returns null to trigger special handling.
 */
function getRoomBaseColor(homeroom: string): SubjectColor | null {
  const normalizedHomeroom = homeroom.trim().toUpperCase();
  
  // Special handling for room 501 - return null to trigger reddish color logic
  if (normalizedHomeroom === '501' || normalizedHomeroom === 'ROOM 501') {
    return null;
  }
  
  // Hash function for consistent color assignment
  let hash = 0;
  for (let i = 0; i < normalizedHomeroom.length; i++) {
    hash = normalizedHomeroom.charCodeAt(i) + ((hash << 5) - hash);
  }
  
  const index = Math.abs(hash) % roomBaseColors.length;
  return roomBaseColors[index];
}

/**
 * Get color scheme based on subject, homeroom, and grade.
 * 
 * Rules:
 * - Non-class periods always use green tones
 * - Room 501 uses reddish tones with different shades per subject
 * - Other rooms use a base color with tone variations per subject
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
  
  // Normalize: trim, collapse spaces, uppercase; remove BOM/zero-width so comparisons are reliable
  const normalized = (subject ?? '')
    .replace(/\uFEFF/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .toUpperCase();
  const normalizedHomeroom = homeroom ? homeroom.trim().toUpperCase() : null;

  // CRITICAL: Green non-class periods first so Lunch, Dismissal, PREP, A.M. Routine always get green (never teal)
  if (normalized === 'PREP' || normalized === 'PREP TIME') {
    return nonClassPeriodColors['PREP'];
  }
  if (normalized === 'LUNCH') {
    return nonClassPeriodColors['LUNCH'];
  }
  if (normalized === 'A.M. ROUTINE' || normalized === 'AM ROUTINE' || normalized === 'MORNING ROUTINE' ||
      (normalized.includes('A.M.') && normalized.includes('ROUTINE')) ||
      normalized.startsWith('A.M. ROUTINE') || normalized.startsWith('AM ROUTINE')) {
    return nonClassPeriodColors['A.M. ROUTINE'];
  }
  if (normalized === 'DISMISSAL') {
    return nonClassPeriodColors['DISMISSAL'];
  }

  // Meeting periods (PLC, GLM) use teal (green periods already returned above)
  const isMeeting =
    normalized === 'PLC' ||
    normalized === 'PLC MEETING' ||
    normalized === 'PROFESSIONAL LEARNING COMMUNITY' ||
    normalized === 'GLM' ||
    normalized === 'GLM MEETING' ||
    normalized === 'GRADE LEVEL MEETING' ||
    normalized === 'GRADE LEVEL MEETINGS' ||
    /\bGLM\b/.test(normalized) ||
    /\bPLC\b/.test(normalized) ||
    (normalized.includes('GRADE') && normalized.includes('LEVEL') && normalized.includes('MEETING'));
  if (isMeeting) {
    return meetingPeriodColors;
  }

  // For all other subjects (NOT A.M. Routine, Lunch, Dismissal, or meetings),
  // use room-based color system if homeroom is present
  // Rooms should NEVER get green - they use room-based colors
  if (normalizedHomeroom) {
    // Special handling for room 501 - use reddish tones
    // Handle variations like "501", "Room 501", "ROOM 501", etc.
    if (normalizedHomeroom === '501' || 
        normalizedHomeroom === 'ROOM 501' ||
        normalizedHomeroom.includes('501')) {
      const room501Color = room501SubjectTones[normalized];
      if (room501Color) {
        return room501Color;
      }
      // Fallback for room 501 if subject not in map
      return room501SubjectTones['ELA'];
    }
    
    // For other rooms, get base color and apply subject tone variation
    const baseColor = getRoomBaseColor(homeroom);
    if (baseColor) {
      // Handle compound subjects like "ELA/SS" - check if it contains known subjects
      let toneLevel = subjectToneMap[normalized] ?? 0;
      
      // If not found, try to extract subject from compound names
      if (toneLevel === 0 && normalized.includes('/')) {
        const parts = normalized.split('/').map(p => p.trim());
        for (const part of parts) {
          if (subjectToneMap[part] !== undefined) {
            toneLevel = subjectToneMap[part];
            break;
          }
        }
      }
      
      // If still not found, try partial matches
      if (toneLevel === 0) {
        for (const [key, value] of Object.entries(subjectToneMap)) {
          if (normalized.includes(key) || key.includes(normalized)) {
            toneLevel = value;
            break;
          }
        }
      }
      
      // Use hash of subject name to create consistent but different tones for multiple subjects in same room
      // This ensures different subjects in the same room get different soft tones
      if (toneLevel === 0) {
        // Generate a consistent tone based on subject name hash
        let subjectHash = 0;
        for (let i = 0; i < normalized.length; i++) {
          subjectHash = normalized.charCodeAt(i) + ((subjectHash << 5) - subjectHash);
        }
        toneLevel = Math.abs(subjectHash) % 4; // 0-3 for soft tones
      }
      
      return generateToneVariation(baseColor, toneLevel);
    }
  }
  
  // Fallback: if no homeroom and not a non-class period, use a default color (not green)
  // Use a soft blue as default to avoid green
  return {
    bg: '!bg-blue-50',
    bgDark: 'bg-blue-900/30',
    border: 'border-blue-300',
    text: 'text-blue-800',
    textDark: 'text-blue-300',
  };
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

