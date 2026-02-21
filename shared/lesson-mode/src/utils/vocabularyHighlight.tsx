import type React from 'react';

/**
 * Strips markdown bold syntax (**word**) from text and returns the cleaned text
 * along with information about which words were marked as bold.
 */
function stripMarkdownBold(text: string): { cleanedText: string; boldWords: string[] } {
  const boldWords: string[] = [];
  // Match **word** pattern (non-greedy to handle multiple words)
  const markdownPattern = /\*\*([^*]+?)\*\*/g;
  let match;

  // Collect all bold words
  while ((match = markdownPattern.exec(text)) !== null) {
    boldWords.push(match[1].toLowerCase().trim());
  }

  // Remove markdown syntax
  const cleanedText = text.replace(/\*\*([^*]+?)\*\*/g, '$1');

  return { cleanedText, boldWords };
}

/**
 * Highlights vocabulary words in text by wrapping them in a span with highlighting styles.
 * Handles markdown bold syntax (**word**) by stripping it first, then highlighting vocabulary words.
 * @param text - The text to highlight vocabulary words in (may contain markdown **word** syntax)
 * @param vocabularyWords - Array of vocabulary words (English) to highlight (should be lowercase)
 * @returns React node with highlighted vocabulary words
 */
export function highlightVocabularyWords(
  text: string,
  vocabularyWords: string[]
): React.ReactNode {
  // First, strip markdown bold syntax and get cleaned text
  const { cleanedText, boldWords: markdownBoldWords } = stripMarkdownBold(text);

  // Combine vocabulary words with words that were marked as bold in markdown
  // This ensures we highlight both explicitly marked words and vocabulary words
  const allWordsToHighlight = new Set([
    ...vocabularyWords.map(w => w.toLowerCase().trim()),
    ...markdownBoldWords
  ]);

  if (allWordsToHighlight.size === 0) return cleanedText;

  // Sort keywords by length (longest first) to ensure phrases are matched before individual words
  const sortedKeywords = Array.from(allWordsToHighlight).sort((a, b) => b.length - a.length);

  // Create a regex pattern to match vocabulary words (case-insensitive, whole word)
  const wordsPattern = new RegExp(
    `\\b(${sortedKeywords.map((word: string) => word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})\\b`,
    'gi'
  );

  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match;

  while ((match = wordsPattern.exec(cleanedText)) !== null) {
    // Add text before the match
    if (match.index > lastIndex) {
      parts.push(cleanedText.substring(lastIndex, match.index));
    }

    // Add highlighted word with yellow background and bold
    parts.push(
      <span
        key={match.index}
        className="!bg-yellow-300 dark:!bg-yellow-800/70 font-bold px-1 rounded"
        style={{
          backgroundColor: 'rgb(253 224 71)', // yellow-300 for better visibility
          color: 'inherit' // Ensure text color is inherited
        }}
        title="Vocabulary word"
      >
        {match[0]}
      </span>
    );

    lastIndex = wordsPattern.lastIndex;
  }

  // Add remaining text
  if (lastIndex < cleanedText.length) {
    parts.push(cleanedText.substring(lastIndex));
  }

  return parts.length > 0 ? <>{parts}</> : cleanedText;
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
  if (size === 'md') {
    return isCognate
      ? 'inline-flex items-center rounded-full uppercase tracking-wider font-bold border-2 px-4 py-2 text-sm md:text-base text-green-700 bg-green-100 border-green-300 dark:text-green-300 dark:bg-green-900/50 dark:border-green-700'
      : 'inline-flex items-center rounded-full uppercase tracking-wider font-bold border-2 px-4 py-2 text-sm md:text-base text-red-700 bg-red-100 border-red-300 dark:text-red-300 dark:bg-red-900/50 dark:border-red-700';
  }

  // Small size badges
  return isCognate
    ? 'inline-flex items-center rounded-full uppercase tracking-wider font-bold border px-1.5 py-0.5 text-[10px] text-green-700 bg-green-100 border-green-300 dark:text-green-300 dark:bg-green-900/50 dark:border-green-700'
    : 'inline-flex items-center rounded-full uppercase tracking-wider font-bold border px-1.5 py-0.5 text-[10px] text-red-700 bg-red-100 border-red-300 dark:text-red-300 dark:bg-red-900/50 dark:border-red-700';
}

/**
 * Gets the label text for cognate/non-cognate badges
 * @param isCognate - Whether the vocabulary item is a cognate
 * @returns Badge label text
 */
export function getCognateBadgeLabel(isCognate: boolean): string {
  return isCognate ? 'Cognate' : 'Non-Cognate';
}
