// src/utils/docExportUtils.ts
import html2pdf from 'html2pdf.js';

/** Trigger a file download from a Blob */
function saveBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Download markdown content as a plain .txt file (strips markdown formatting)
 */
export const downloadAsText = (content: string, filename: string): void => {
    const plainText = content
        .replace(/^#{1,6}\s+/gm, '')
        .replace(/\*\*(.+?)\*\*/g, '$1')
        .replace(/\*(.+?)\*/g, '$1')
        .replace(/`{1,3}([^`]+)`{1,3}/g, '$1')
        .replace(/^\s*[-*+]\s+/gm, '  - ')
        .replace(/^\s*\d+\.\s+/gm, '  ')
        .replace(/\[(.+?)\]\((.+?)\)/g, '$1 ($2)')
        .replace(/^>\s*/gm, '  ')
        .replace(/^-{3,}$/gm, '---')
        .replace(/\n{3,}/g, '\n\n');

    const blob = new Blob([plainText], { type: 'text/plain;charset=utf-8' });
    saveBlob(blob, `${filename}.txt`);
};

/**
 * Download markdown content as a .md file
 */
export const downloadAsMarkdown = (content: string, filename: string): void => {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    saveBlob(blob, `${filename}.md`);
};

/**
 * Download rendered documentation as a PDF file
 */
export const downloadAsPdf = async (
    contentElement: HTMLElement | null,
    filename: string
): Promise<void> => {
    if (!contentElement) return;

    const opt = {
        margin: [10, 10, 10, 10],
        filename: `${filename}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: {
            scale: 2,
            useCORS: true,
            scrollY: 0,
            foreignObjectRendering: false,
            removeContainer: true,
            onclone: (clonedDoc: Document) => {
                const styles = clonedDoc.querySelectorAll('style, link[rel="stylesheet"]');
                styles.forEach((el) => {
                    if (el instanceof HTMLLinkElement && el.href.includes('fonts.googleapis.com')) {
                        el.remove();
                    }
                    if (el instanceof HTMLStyleElement && el.textContent?.includes('fonts.googleapis.com')) {
                        el.textContent = el.textContent.replace(/@import\s+url\([^)]*fonts\.googleapis\.com[^)]*\)\s*;?/g, '');
                    }
                });
            }
        },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' as const },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
    };

    await html2pdf().set(opt).from(contentElement).save();
};
