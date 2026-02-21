import React from 'react';
import { highlightVocabularyWords } from './vocabularyHighlight';

/**
 * Parses a string containing Markdown-like syntax and returns a React node.
 * Supported syntax:
 * - Links: [label](url)
 * - Underline: <u>text</u>
 * - Italics: *text* or _text_
 * - Line breaks: <br />
 * - Arrows: →
 * 
 * Note: Bold syntax (**text**) is intentionally passed through to highlightVocabularyWords,
 * which already handles it by stripping the markers and highlighting the content.
 * 
 * @param text - The raw text to parse
 * @param vocabularyWords - List of vocabulary words to highlight (passed to highlightVocabularyWords)
 * @returns React.ReactNode
 */
export function parseMarkdown(text: string, vocabularyWords: string[] = []): React.ReactNode {
    if (!text) return null;

    // Helper to open links natively in Tauri if available
    const handleLinkClick = async (e: React.MouseEvent<HTMLAnchorElement>, url: string) => {
        e.preventDefault();
        e.stopPropagation();

        // Check for Tauri
        const isTauri = typeof window !== 'undefined' && (
            (window as any).__TAURI_INTERNALS__ !== undefined ||
            (window as any).__TAURI__ !== undefined
        );

        if (isTauri) {
            try {
                // Use the custom open_file command implemented in Rust
                // This provides better performance and reliability, especially on Android
                const { invoke } = await import('@tauri-apps/api/core');
                await invoke('open_file', { path: url });
            } catch (err) {
                console.error('[markdownUtils] Failed to open link via Tauri:', err);
                window.open(url, '_blank');
            }
        } else {
            window.open(url, '_blank');
        }
    };

    // Pattern for different markdown elements
    // We process them one by one based on their appearance in the text
    const tokens = [
        { type: 'link', regex: /\[([^\]]+)\]\(([^)]+)\)/ },
        { type: 'underline', regex: /<u>(.*?)<\/u>/i },
        { type: 'italic_star', regex: /(?<!\*)\*([^*]+)\*(?!\*)/ }, // Matches *text* but not **text**
        { type: 'italic_underscore', regex: /(?<!_)_([^_]+)_(?!_)/ }, // Matches _text_ but not __text__
        { type: 'br', regex: /<br\s*\/?>/i },
        { type: 'arrow', regex: /→/ }
    ];

    function processSegments(input: string): React.ReactNode[] {
        if (!input) return [];

        let earliestMatch: RegExpExecArray | null = null;
        let earliestToken: any = null;

        // Find the first occurring token in the input string
        for (const token of tokens) {
            const match = token.regex.exec(input);
            if (match && (earliestMatch === null || match.index < earliestMatch.index)) {
                earliestMatch = match;
                earliestToken = token;
            }
        }

        // Base case: No more tokens found
        if (!earliestMatch || !earliestToken) {
            // Pass the remaining text through the original vocabulary highlight logic
            return [highlightVocabularyWords(input, vocabularyWords)];
        }

        const result: React.ReactNode[] = [];
        const beforeText = input.substring(0, earliestMatch.index);
        const matchText = earliestMatch[0];
        const keyPrefix = `md-${input.length}-${earliestMatch.index}`;

        // 1. Process anything before the token
        if (beforeText) {
            result.push(highlightVocabularyWords(beforeText, vocabularyWords));
        }

        // 2. Process the token itself
        try {
            if (earliestToken.type === 'link') {
                const label = earliestMatch[1];
                const url = earliestMatch[2];
                result.push(
                    <a
                        key={`${keyPrefix}-link`}
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 underline hover:text-blue-800 transition-colors"
                        onClick={(e) => handleLinkClick(e, url)}
                    >
                        {label}
                    </a>
                );
            } else if (earliestToken.type === 'underline') {
                result.push(
                    <u key={`${keyPrefix}-u`}>
                        {highlightVocabularyWords(earliestMatch[1], vocabularyWords)}
                    </u>
                );
            } else if (earliestToken.type === 'italic_star' || earliestToken.type === 'italic_underscore') {
                result.push(
                    <em key={`${keyPrefix}-em`} className="italic">
                        {highlightVocabularyWords(earliestMatch[1], vocabularyWords)}
                    </em>
                );
            } else if (earliestToken.type === 'br') {
                result.push(<br key={`${keyPrefix}-br`} />);
            } else if (earliestToken.type === 'arrow') {
                result.push(<span key={`${keyPrefix}-arrow`}>→</span>);
            }
        } catch (err) {
            // Fallback in case of rendering errors
            result.push(matchText);
        }

        // 3. Recurse on the remaining text after the token
        const afterText = input.substring(earliestMatch.index + matchText.length);
        if (afterText) {
            result.push(...processSegments(afterText));
        }

        return result;
    }

    const nodes = processSegments(text);
    return nodes.length === 1 ? nodes[0] : <>{nodes}</>;
}
