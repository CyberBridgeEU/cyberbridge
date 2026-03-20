import jsPDF from 'jspdf';
import { NmapVulnerability, NmapScanSummary } from '../store/useNmapStore';
import { trackPdfDownload } from './trackPdfDownload';
import useAuthStore from '../store/useAuthStore';

interface NmapScanResults {
    success: boolean;
    vulnerabilities?: NmapVulnerability[];
    summary?: NmapScanSummary;
    raw_data?: any;
    analysis?: string;
}

/**
 * Exports Nmap scan results to a structured PDF with modern styling
 * @param results - The scan results object
 * @param target - The target that was scanned
 * @param scanType - The type of scan performed
 * @param scanDuration - Duration of the scan in seconds
 * @param filename - Name of the output PDF file (without extension)
 * @returns Promise that resolves when PDF is generated
 */
export const exportNmapResultsToPdf = async (
    results: NmapScanResults,
    target: string = '',
    scanType: string = 'N/A',
    scanDuration: number | null = null,
    filename: string = 'network-scan-report'
): Promise<void> => {
    try {
        // Track PDF download
        const { getAuthHeader } = useAuthStore.getState();
        await trackPdfDownload('nmap', getAuthHeader);

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
            return y + (lines.length * (fontSize * 0.35));
        };

        // Helper function to get severity color
        const getSeverityColor = (severity: string): [number, number, number] => {
            switch (severity.toLowerCase()) {
                case 'high': return [220, 53, 69]; // Red
                case 'medium': return [255, 140, 0]; // Orange
                case 'low': return [255, 193, 7]; // Gold/Yellow
                case 'info': return [23, 162, 184]; // Blue/Cyan
                default: return [128, 128, 128]; // Gray
            }
        };

        const vulnerabilities = results.vulnerabilities || [];
        const summary = results.summary || { high: 0, medium: 0, low: 0, info: 0, total: vulnerabilities.length };

        // ===== TITLE PAGE =====
        pdf.setFontSize(24);
        pdf.setFont('helvetica', 'bold');
        pdf.setTextColor(0, 0, 0);
        pdf.text('Network Vulnerability Scan Report', pageWidth / 2, currentY + 20, { align: 'center' });

        currentY += 40;
        pdf.setFontSize(12);
        pdf.setFont('helvetica', 'normal');
        pdf.text(`Generated: ${new Date().toLocaleString()}`, pageWidth / 2, currentY, { align: 'center' });

        if (target) {
            currentY += 8;
            pdf.text(`Target: ${target}`, pageWidth / 2, currentY, { align: 'center' });
        }

        currentY += 8;
        pdf.text(`Scan Type: ${scanType}`, pageWidth / 2, currentY, { align: 'center' });

        if (scanDuration) {
            currentY += 8;
            pdf.text(`Duration: ${scanDuration.toFixed(2)}s`, pageWidth / 2, currentY, { align: 'center' });
        }

        // ===== SUMMARY SECTION =====
        currentY += 25;
        pdf.setFontSize(16);
        pdf.setFont('helvetica', 'bold');
        pdf.setTextColor(0, 0, 0);
        pdf.text('Executive Summary', margin, currentY);

        currentY += 12;
        pdf.setFontSize(11);
        pdf.setFont('helvetica', 'normal');

        // Summary box background
        pdf.setFillColor(248, 249, 250);
        pdf.roundedRect(margin, currentY - 5, contentWidth, 35, 3, 3, 'F');

        // Summary counts
        const summaryY = currentY + 5;
        const colWidth = contentWidth / 5;

        // High
        pdf.setTextColor(...getSeverityColor('high'));
        pdf.setFont('helvetica', 'bold');
        pdf.text('HIGH', margin + 10, summaryY);
        pdf.setFontSize(18);
        pdf.text(String(summary.high), margin + 10, summaryY + 12);

        // Medium
        pdf.setFontSize(11);
        pdf.setTextColor(...getSeverityColor('medium'));
        pdf.text('MEDIUM', margin + colWidth + 10, summaryY);
        pdf.setFontSize(18);
        pdf.text(String(summary.medium), margin + colWidth + 10, summaryY + 12);

        // Low
        pdf.setFontSize(11);
        pdf.setTextColor(...getSeverityColor('low'));
        pdf.text('LOW', margin + colWidth * 2 + 10, summaryY);
        pdf.setFontSize(18);
        pdf.text(String(summary.low), margin + colWidth * 2 + 10, summaryY + 12);

        // Info
        pdf.setFontSize(11);
        pdf.setTextColor(...getSeverityColor('info'));
        pdf.text('INFO', margin + colWidth * 3 + 10, summaryY);
        pdf.setFontSize(18);
        pdf.text(String(summary.info), margin + colWidth * 3 + 10, summaryY + 12);

        // Total
        pdf.setFontSize(11);
        pdf.setTextColor(0, 0, 0);
        pdf.text('TOTAL', margin + colWidth * 4 + 5, summaryY);
        pdf.setFontSize(18);
        pdf.text(String(summary.total), margin + colWidth * 4 + 5, summaryY + 12);

        currentY += 40;

        // ===== VULNERABILITIES SECTION =====
        pdf.setFontSize(16);
        pdf.setFont('helvetica', 'bold');
        pdf.setTextColor(0, 0, 0);
        pdf.text('Findings', margin, currentY);
        currentY += 10;

        // Sort vulnerabilities by severity
        const severityOrder: { [key: string]: number } = { 'High': 0, 'Medium': 1, 'Low': 2, 'Info': 3 };
        const sortedVulns = [...vulnerabilities].sort((a, b) =>
            (severityOrder[a.severity] ?? 4) - (severityOrder[b.severity] ?? 4)
        );

        // Group by severity for better organization
        const highVulns = sortedVulns.filter(v => v.severity === 'High');
        const mediumVulns = sortedVulns.filter(v => v.severity === 'Medium');
        const lowVulns = sortedVulns.filter(v => v.severity === 'Low');
        const infoVulns = sortedVulns.filter(v => v.severity === 'Info');

        const renderVulnerabilityGroup = (vulns: NmapVulnerability[], groupTitle: string, color: [number, number, number]) => {
            if (vulns.length === 0) return;

            checkPageBreak(20);

            // Group header
            pdf.setFillColor(...color);
            pdf.roundedRect(margin, currentY, contentWidth, 8, 2, 2, 'F');
            pdf.setFontSize(11);
            pdf.setFont('helvetica', 'bold');
            pdf.setTextColor(255, 255, 255);
            pdf.text(`${groupTitle} (${vulns.length})`, margin + 5, currentY + 5.5);
            currentY += 12;

            vulns.forEach((vuln, index) => {
                const cardHeight = vuln.cve_id ? 45 : 35;
                checkPageBreak(cardHeight + 5);

                // Card background
                pdf.setFillColor(255, 255, 255);
                pdf.setDrawColor(230, 230, 230);
                pdf.roundedRect(margin, currentY, contentWidth, cardHeight, 2, 2, 'FD');

                // Severity badge
                pdf.setFillColor(...color);
                pdf.roundedRect(margin + 3, currentY + 3, 18, 6, 1, 1, 'F');
                pdf.setFontSize(7);
                pdf.setTextColor(255, 255, 255);
                pdf.text(vuln.severity.toUpperCase(), margin + 5, currentY + 7);

                // Title
                pdf.setFontSize(10);
                pdf.setFont('helvetica', 'bold');
                pdf.setTextColor(0, 0, 0);
                const titleText = vuln.title.length > 80 ? vuln.title.substring(0, 77) + '...' : vuln.title;
                pdf.text(titleText, margin + 25, currentY + 8);

                // Host:Port
                pdf.setFontSize(9);
                pdf.setFont('helvetica', 'normal');
                pdf.setTextColor(100, 100, 100);
                const hostPort = vuln.port ? `${vuln.host || '-'}:${vuln.port}/${vuln.protocol || 'tcp'}` : (vuln.host || '-');
                pdf.text(`Host: ${hostPort}`, margin + 5, currentY + 16);

                // Service info
                if (vuln.service_name) {
                    const serviceInfo = vuln.service_version ? `${vuln.service_name} ${vuln.service_version}` : vuln.service_name;
                    pdf.text(`Service: ${serviceInfo}`, margin + 70, currentY + 16);
                }

                // Description (truncated)
                if (vuln.description) {
                    pdf.setFontSize(8);
                    pdf.setTextColor(80, 80, 80);
                    const descText = vuln.description.length > 150 ? vuln.description.substring(0, 147) + '...' : vuln.description;
                    const descLines = pdf.splitTextToSize(descText, contentWidth - 10);
                    pdf.text(descLines.slice(0, 2), margin + 5, currentY + 23);
                }

                // CVE and CVSS info
                if (vuln.cve_id) {
                    pdf.setFontSize(9);
                    pdf.setFont('helvetica', 'bold');
                    pdf.setTextColor(0, 102, 204);
                    pdf.text(vuln.cve_id, margin + 5, currentY + 38);

                    if (vuln.cvss_score) {
                        pdf.setFont('helvetica', 'normal');
                        pdf.setTextColor(100, 100, 100);
                        pdf.text(`CVSS: ${vuln.cvss_score.toFixed(1)}`, margin + 50, currentY + 38);
                    }

                    // CPE
                    if (vuln.cpe) {
                        pdf.setFontSize(7);
                        pdf.setTextColor(130, 130, 130);
                        const cpeText = vuln.cpe.length > 70 ? vuln.cpe.substring(0, 67) + '...' : vuln.cpe;
                        pdf.text(`CPE: ${cpeText}`, margin + 90, currentY + 38);
                    }
                }

                currentY += cardHeight + 3;
            });

            currentY += 5;
        };

        // Render each severity group
        renderVulnerabilityGroup(highVulns, 'High Severity', getSeverityColor('high'));
        renderVulnerabilityGroup(mediumVulns, 'Medium Severity', getSeverityColor('medium'));
        renderVulnerabilityGroup(lowVulns, 'Low Severity', getSeverityColor('low'));
        renderVulnerabilityGroup(infoVulns, 'Informational', getSeverityColor('info'));

        // ===== FOOTER =====
        const totalPages = pdf.getNumberOfPages();
        for (let i = 1; i <= totalPages; i++) {
            pdf.setPage(i);
            pdf.setFontSize(8);
            pdf.setTextColor(150, 150, 150);
            pdf.text(`Page ${i} of ${totalPages}`, pageWidth / 2, pageHeight - 10, { align: 'center' });
            pdf.text('Generated by CyberBridge', pageWidth - margin, pageHeight - 10, { align: 'right' });
        }

        // Save the PDF
        pdf.save(`${filename}.pdf`);
    } catch (error) {
        console.error('Error generating Nmap PDF:', error);
        throw error;
    }
};
