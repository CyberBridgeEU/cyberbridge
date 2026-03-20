const STOP_WORDS = new Set([
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
    'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
    'may', 'might', 'can', 'shall', 'this', 'that', 'these', 'those', 'it', 'its',
    'not', 'no', 'nor', 'as', 'if', 'then', 'than', 'so', 'all', 'each', 'every',
    'any', 'some', 'such', 'only', 'also', 'very', 'just', 'about', 'up', 'out',
    'into', 'over', 'after', 'before', 'must', 'need', 'use', 'used', 'using',
    'based', 'ensure', 'including', 'related', 'through', 'between', 'within',
]);

function tokenize(texts: (string | null | undefined)[]): Set<string> {
    const words = new Set<string>();
    texts.forEach(text => {
        if (!text) return;
        text.toLowerCase()
            .replace(/[^a-z0-9\s]/g, ' ')
            .split(/\s+/)
            .filter(w => w.length > 2 && !STOP_WORDS.has(w))
            .forEach(w => words.add(w));
    });
    return words;
}

/**
 * Compute a keyword relevance score between source entity texts and target item texts.
 * Returns a number >= 0 where higher means more relevant.
 * - Exact word match: +2 points
 * - Substring match (one word contains the other): +1 point
 */
export function getKeywordRelevanceScore(
    sourceTexts: (string | null | undefined)[],
    targetTexts: (string | null | undefined)[]
): number {
    const sourceWords = tokenize(sourceTexts);
    const targetWords = tokenize(targetTexts);

    if (sourceWords.size === 0 || targetWords.size === 0) return 0;

    let score = 0;
    sourceWords.forEach(sw => {
        targetWords.forEach(tw => {
            if (sw === tw) score += 2;
            else if (sw.length >= 4 && tw.length >= 4 && (tw.includes(sw) || sw.includes(tw))) score += 1;
        });
    });
    return score;
}

/**
 * Score and sort items by keyword relevance, returning only items with score > 0.
 * If no items match, returns all items (fallback so the tab isn't empty).
 */
export function filterByRelevance<T>(
    items: T[],
    sourceTexts: (string | null | undefined)[],
    getTargetTexts: (item: T) => (string | null | undefined)[],
): { relevant: T[]; other: T[] } {
    const scored = items.map(item => ({
        item,
        score: getKeywordRelevanceScore(sourceTexts, getTargetTexts(item)),
    }));

    const relevant = scored
        .filter(s => s.score > 0)
        .sort((a, b) => b.score - a.score)
        .map(s => s.item);

    const other = scored
        .filter(s => s.score === 0)
        .map(s => s.item);

    return { relevant, other };
}
