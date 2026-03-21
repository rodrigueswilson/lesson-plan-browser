/** Unicode U+2192; escape keeps .ts source ASCII-only. */
export const VOCAB_PAIR_SEP = ' \u2192 ';

const ARROW = '\u2192';

/**
 * Split a single line body (after bullet prefix) into english / portuguese.
 * Tries Unicode arrow first, then ASCII "->", for backward compatibility.
 */
export function splitVocabularyPairContent(content: string): {
  english: string;
  portuguese: string;
} | null {
  const trimmed = content.trim();
  if (!trimmed) {
    return null;
  }

  let sepIndex = trimmed.indexOf(ARROW);
  if (sepIndex === -1) {
    const asciiMatch = /\s*->\s*/.exec(trimmed);
    if (asciiMatch && asciiMatch.index !== undefined) {
      sepIndex = asciiMatch.index;
      const afterSep = asciiMatch[0].length;
      const english = trimmed.slice(0, sepIndex).trim();
      const portuguese = trimmed.slice(sepIndex + afterSep).trim();
      if (english && portuguese) {
        return { english, portuguese };
      }
    }
    return null;
  }

  const english = trimmed.slice(0, sepIndex).trim();
  const portuguese = trimmed.slice(sepIndex + ARROW.length).trim();
  if (!english || !portuguese) {
    return null;
  }
  return { english, portuguese };
}

/** Plain bullet for offline step display_content (aligned with backend format_vocab_plain_bullet). */
export function formatVocabPlainBullet(english: string, portuguese: string): string {
  return `- ${english}${VOCAB_PAIR_SEP}${portuguese}`;
}
