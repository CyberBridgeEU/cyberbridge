/**
 * Risk score utilities for the 5x5 risk matrix methodology.
 * Maps quantitative scores (1-25) to severity labels and colors.
 */

export type RiskSeverity = 'Low' | 'Medium' | 'High' | 'Critical';

export function scoreToSeverity(score: number | null | undefined): RiskSeverity | null {
    if (score == null) return null;
    if (score <= 4) return 'Low';
    if (score <= 10) return 'Medium';
    if (score <= 16) return 'High';
    return 'Critical';
}

export function severityToColor(severity: RiskSeverity | null | undefined): string {
    switch (severity) {
        case 'Low': return '#52c41a';
        case 'Medium': return '#faad14';
        case 'High': return '#fa8c16';
        case 'Critical': return '#f5222d';
        default: return '#d9d9d9';
    }
}

export function getGaugeColor(score: number | null | undefined): string {
    return severityToColor(scoreToSeverity(score));
}

export function getGaugePercent(score: number | null | undefined): number {
    if (score == null) return 0;
    return (score / 25) * 100;
}

/** 5x5 risk matrix cell colors for visual reference */
export const MATRIX_COLORS: Record<number, string> = {
    1: '#52c41a', 2: '#52c41a', 3: '#52c41a', 4: '#52c41a',
    5: '#faad14', 6: '#faad14', 8: '#faad14', 10: '#faad14',
    12: '#fa8c16', 15: '#fa8c16', 16: '#fa8c16',
    9: '#faad14',
    20: '#f5222d', 25: '#f5222d',
};

export function getMatrixCellColor(impact: number, likelihood: number): string {
    const score = impact * likelihood;
    if (score <= 4) return '#52c41a';
    if (score <= 10) return '#faad14';
    if (score <= 16) return '#fa8c16';
    return '#f5222d';
}
