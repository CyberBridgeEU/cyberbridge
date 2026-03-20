import jsPDF from 'jspdf';
import { ZapAlert } from '../store/useZapStore';
import { trackPdfDownload } from './trackPdfDownload';
import useAuthStore from '../store/useAuthStore';

/**
 * Exports ZAP scan results to a structured PDF with modern styling
 * @param alerts - Array of ZAP alerts to export
 * @param targetUrl - The target URL that was scanned
 * @param filename - Name of the output PDF file (without extension)
 * @returns Promise that resolves when PDF is generated
 */
export const exportZapResultsToPdf = async (alerts: ZapAlert[], targetUrl: string = '', filename: string = 'webapp-scan-report'): Promise<void> => {
    try {
        // Track PDF download
        const { getAuthHeader } = useAuthStore.getState();
        await trackPdfDownload('zap', getAuthHeader);
        const pdf = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        });

        const pageWidth = pdf.internal.pageSize.getWidth();
        const pageHeight = pdf.internal.pageSize.getHeight();
        const margin = 20;
        const contentWidth = pageWidth - (margin * 2);
        let currentY = margin;

        // Helper function to add a new page if needed
        const checkPageBreak = (requiredHeight: number) => {
            if (currentY + requiredHeight > pageHeight - margin) {
                pdf.addPage();
                currentY = margin;
                return true;
            }
            return false;
        };

        // Helper function to add text with word wrapping
        const addWrappedText = (text: string, x: number, y: number, maxWidth: number, fontSize: number = 10): number => {
            pdf.setFontSize(fontSize);
            const lines = pdf.splitTextToSize(text, maxWidth);
            pdf.text(lines, x, y);
            return y + (lines.length * (fontSize * 0.35)); // Approximate line height
        };

        // Helper function to get risk color
        const getRiskColor = (risk: string): [number, number, number] => {
            switch (risk.toLowerCase()) {
                case 'high': return [220, 20, 60]; // Crimson
                case 'medium': return [255, 140, 0]; // Dark orange
                case 'low': return [255, 215, 0]; // Gold
                case 'informational': return [70, 130, 180]; // Steel blue
                default: return [128, 128, 128]; // Gray
            }
        };

        // Count alerts by risk level
        const riskCounts = {
            high: alerts.filter(a => a.risk.toLowerCase() === 'high').length,
            medium: alerts.filter(a => a.risk.toLowerCase() === 'medium').length,
            low: alerts.filter(a => a.risk.toLowerCase() === 'low').length,
            informational: alerts.filter(a => a.risk.toLowerCase() === 'informational').length
        };

        // Add title page
        pdf.setFontSize(24);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Web App Security Scan Report', pageWidth / 2, currentY + 20, { align: 'center' });
        
        currentY += 40;
        pdf.setFontSize(12);
        pdf.setFont('helvetica', 'normal');
        pdf.text(`Generated on: ${new Date().toLocaleDateString()}`, pageWidth / 2, currentY, { align: 'center' });
        
        if (targetUrl) {
            currentY += 10;
            pdf.text(`Target: ${targetUrl}`, pageWidth / 2, currentY, { align: 'center' });
        }
        
        currentY += 10;
        pdf.text(`Total Vulnerabilities: ${alerts.length}`, pageWidth / 2, currentY, { align: 'center' });

        // Add summary section
        currentY += 20;
        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Risk Summary', margin, currentY);
        currentY += 10;

        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');
        pdf.setTextColor(220, 20, 60);
        pdf.text(`High Risk: ${riskCounts.high}`, margin, currentY);
        pdf.setTextColor(255, 140, 0);
        pdf.text(`Medium Risk: ${riskCounts.medium}`, margin + 50, currentY);
        currentY += 7;
        pdf.setTextColor(255, 215, 0);
        pdf.text(`Low Risk: ${riskCounts.low}`, margin, currentY);
        pdf.setTextColor(70, 130, 180);
        pdf.text(`Informational: ${riskCounts.informational}`, margin + 50, currentY);

        // Reset text color
        pdf.setTextColor(0, 0, 0);
        currentY += 20;

        // Process each alert
        for (let i = 0; i < alerts.length; i++) {
            const alert = alerts[i];
            
            // Check if we need a new page for this alert (estimate ~150mm per alert)
            checkPageBreak(150);

            // Alert header with risk-based color
            pdf.setFontSize(14);
            pdf.setFont('helvetica', 'bold');
            const riskColor = getRiskColor(alert.risk);
            pdf.setTextColor(riskColor[0], riskColor[1], riskColor[2]);
            currentY = addWrappedText(`${alert.name} [${alert.risk}]`, margin, currentY, contentWidth, 14);
            currentY += 5;

            // Add separator line
            pdf.setDrawColor(riskColor[0], riskColor[1], riskColor[2]);
            pdf.line(margin, currentY, pageWidth - margin, currentY);
            currentY += 10;

            // Reset text color
            pdf.setTextColor(0, 0, 0);

            // Alert details in two columns
            const leftColumnX = margin;
            const rightColumnX = pageWidth / 2 + 10;
            const columnWidth = (contentWidth - 20) / 2;
            let leftY = currentY;
            let rightY = currentY;

            // Left column
            pdf.setFontSize(9);
            pdf.setFont('helvetica', 'bold');
            pdf.text('URL:', leftColumnX, leftY);
            pdf.setFont('helvetica', 'normal');
            leftY = addWrappedText(alert.url || 'N/A', leftColumnX + 15, leftY, columnWidth - 15, 9);
            leftY += 3;

            pdf.setFont('helvetica', 'bold');
            pdf.text('Method:', leftColumnX, leftY);
            pdf.setFont('helvetica', 'normal');
            leftY = addWrappedText(alert.method || 'N/A', leftColumnX + 20, leftY, columnWidth - 20, 9);
            leftY += 3;

            pdf.setFont('helvetica', 'bold');
            pdf.text('Parameter:', leftColumnX, leftY);
            pdf.setFont('helvetica', 'normal');
            leftY = addWrappedText(alert.param || 'N/A', leftColumnX + 25, leftY, columnWidth - 25, 9);
            leftY += 3;

            // Right column
            pdf.setFont('helvetica', 'bold');
            pdf.text('Confidence:', rightColumnX, rightY);
            pdf.setFont('helvetica', 'normal');
            rightY = addWrappedText(alert.confidence || 'N/A', rightColumnX + 25, rightY, columnWidth - 25, 9);
            rightY += 3;

            if (alert.cweid) {
                pdf.setFont('helvetica', 'bold');
                pdf.text('CWE ID:', rightColumnX, rightY);
                pdf.setFont('helvetica', 'normal');
                rightY = addWrappedText(alert.cweid, rightColumnX + 20, rightY, columnWidth - 20, 9);
                rightY += 3;
            }

            if (alert.wascid) {
                pdf.setFont('helvetica', 'bold');
                pdf.text('WASC ID:', rightColumnX, rightY);
                pdf.setFont('helvetica', 'normal');
                rightY = addWrappedText(alert.wascid, rightColumnX + 22, rightY, columnWidth - 22, 9);
                rightY += 3;
            }

            currentY = Math.max(leftY, rightY) + 5;

            // Description
            if (alert.description) {
                checkPageBreak(25);
                
                pdf.setFontSize(10);
                pdf.setFont('helvetica', 'bold');
                pdf.text('Description:', margin, currentY);
                pdf.setFont('helvetica', 'normal');
                pdf.setFontSize(9);
                currentY = addWrappedText(alert.description, margin, currentY + 5, contentWidth, 9);
                currentY += 5;
            }

            // Solution
            if (alert.solution) {
                checkPageBreak(25);
                
                pdf.setFontSize(10);
                pdf.setFont('helvetica', 'bold');
                pdf.text('Solution:', margin, currentY);
                pdf.setFont('helvetica', 'normal');
                pdf.setFontSize(9);
                currentY = addWrappedText(alert.solution, margin, currentY + 5, contentWidth, 9);
                currentY += 5;
            }

            // Evidence
            if (alert.evidence) {
                checkPageBreak(20);
                
                pdf.setFontSize(10);
                pdf.setFont('helvetica', 'bold');
                pdf.text('Evidence:', margin, currentY);
                pdf.setFont('helvetica', 'normal');
                pdf.setFontSize(8);
                currentY = addWrappedText(alert.evidence, margin, currentY + 5, contentWidth, 8);
                currentY += 5;
            }

            // Attack
            if (alert.attack) {
                checkPageBreak(15);
                
                pdf.setFontSize(10);
                pdf.setFont('helvetica', 'bold');
                pdf.text('Attack:', margin, currentY);
                pdf.setFont('helvetica', 'normal');
                pdf.setFontSize(8);
                currentY = addWrappedText(alert.attack, margin, currentY + 5, contentWidth, 8);
                currentY += 5;
            }

            // References
            if (alert.reference) {
                checkPageBreak(15);
                
                pdf.setFontSize(10);
                pdf.setFont('helvetica', 'bold');
                pdf.text('References:', margin, currentY);
                pdf.setFont('helvetica', 'normal');
                pdf.setFontSize(8);
                currentY = addWrappedText(alert.reference, margin, currentY + 5, contentWidth, 8);
                currentY += 5;
            }

            // Add separator between alerts (except for the last one)
            if (i < alerts.length - 1) {
                currentY += 5;
                pdf.setDrawColor(200, 200, 200);
                pdf.line(margin, currentY, pageWidth - margin, currentY);
                currentY += 15;
            }
        }

        // Add footer to all pages
        const totalPages = pdf.getNumberOfPages();
        for (let i = 1; i <= totalPages; i++) {
            pdf.setPage(i);
            pdf.setFontSize(8);
            pdf.setTextColor(128, 128, 128);
            pdf.text(`Page ${i} of ${totalPages}`, pageWidth - margin, pageHeight - 10, { align: 'right' });
            pdf.text('CyberBridge Web App Security Scan Report', margin, pageHeight - 10);
        }

        pdf.save(`${filename}.pdf`);
    } catch (error) {
        console.error('Error generating ZAP scan PDF:', error);
        throw error;
    }
};