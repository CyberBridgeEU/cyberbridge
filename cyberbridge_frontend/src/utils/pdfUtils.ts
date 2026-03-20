// src/utils/pdfUtils.ts
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

/**
 * Exports a DOM element to PDF
 * @param elementRef - Reference to the DOM element to export
 * @param filename - Name of the output PDF file (without extension)
 * @returns Promise that resolves when PDF is generated
 */
export const exportToPdf = async (elementRef: HTMLDivElement | null, filename: string = 'report'): Promise<void> => {
    try {
            if (!elementRef) {
                console.error('No element reference provided for PDF export');
                return;
            }
            const element = elementRef;
            const pdf = new jsPDF({orientation: 'portrait', unit: 'mm', format: 'a4',});
            const leftMargin = 10;
            const topMargin = 10;
            const rightMargin = 10;
            const bottomMargin = 10;
            const pageWidth = pdf.internal.pageSize.getWidth();
            const pageHeight = pdf.internal.pageSize.getHeight();
            const contentWidth = pageWidth - leftMargin - rightMargin;
            const contentHeight = pageHeight - topMargin - bottomMargin;
            // Render the full element once
            const fullCanvas = await html2canvas(element, {scale: 2, scrollY: -window.scrollY,});
            const imgData = fullCanvas.toDataURL('image/png');
            const imgProps = pdf.getImageProperties(imgData);
            const imgHeight = (imgProps.height * contentWidth) / imgProps.width;
            let remainingHeight = imgHeight;
            let position = 0;

            while (remainingHeight > 0) {
                if (position > 0) {
                    pdf.addPage();
                }
                pdf.addImage(imgData, 'PNG', leftMargin, topMargin - position, contentWidth, imgHeight);
                position += contentHeight;
                remainingHeight -= contentHeight;
            }

            pdf.save(`${filename}.pdf`);
    } catch (error) {
        console.error('Error generating PDF:', error);
    }
};
