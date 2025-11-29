import type React from 'react';

/**
 * Highlights vocabulary words in text by wrapping them in a span with highlighting styles.
 * @param text - The text to highlight vocabulary words in
 * @param vocabularyWords - Array of vocabulary words (English) to highlight (should be lowercase)
 * @returns React node with highlighted vocabulary words
 */
export function highlightVocabularyWords(
  text: string,
  vocabularyWords: string[]
): React.ReactNode {
  if (vocabularyWords.length === 0) return text;

  // Create a regex pattern to match vocabulary words (case-insensitive, whole word)
  const wordsPattern = new RegExp(
    `\\b(${vocabularyWords.map((word: string) => word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})\\b`,
    'gi'
  );

  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match;

  while ((match = wordsPattern.exec(text)) !== null) {
    // Add text before the match
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }

    // Add highlighted word
    parts.push(
      <span
        key={match.index}
        className="bg-yellow-200 dark:bg-yellow-900/50 font-bold px-1 rounded"
        title="Vocabulary word"
      >
        {match[0]}
      </span>
    );

    lastIndex = wordsPattern.lastIndex;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? <>{parts}</> : text;
}

/**
 * Extracts vocabulary words (English) from vocabulary_cognates array
 * @param vocabularyCognates - Array of vocabulary items with english property
 * @returns Array of lowercase vocabulary words
 */
export function extractVocabularyWords(vocabularyCognates: any[] | null | undefined): string[] {
  if (!vocabularyCognates || !Array.isArray(vocabularyCognates)) {
    return [];
  }

  return vocabularyCognates
    .map((vocab: any) => vocab.english?.toLowerCase().trim())
    .filter((word: string | undefined): word is string => !!word);
}

/**
 * Gets the CSS classes for cognate/non-cognate badges
 * @param isCognate - Whether the vocabulary item is a cognate
 * @param size - Size variant: 'sm' for small (default) or 'md' for medium
 * @returns CSS class string for the badge
 */
export function getCognateBadgeClasses(isCognate: boolean, size: 'sm' | 'md' = 'sm'): string {
  const baseClasses = 'inline-flex items-center rounded-full uppercase tracking-wide';
  const colorClasses = isCognate
    ? 'text-green-600 bg-green-100'
    : 'text-red-600 bg-red-100';
  
  if (size === 'md') {
    return `${baseClasses} border-2 px-4 py-2 text-sm md:text-base ${colorClasses}`;
  }
  
  return `${baseClasses} border px-2 py-0.5 text-xs ${colorClasses}`;
}

/**
 * Gets the label text for cognate/non-cognate badges
 * @param isCognate - Whether the vocabulary item is a cognate
 * @returns Badge label text
 */
export function getCognateBadgeLabel(isCognate: boolean): string {
  return isCognate ? 'Cognate' : 'Non-Cognate';
}

