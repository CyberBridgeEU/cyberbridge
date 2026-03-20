import jsPDF from 'jspdf';
import { Risk, RiskSeverity } from '../store/useRiskStore';
import { trackPdfDownload } from './trackPdfDownload';
import useAuthStore from '../store/useAuthStore';

/**
 * Exports all risks to a structured PDF with modern styling
 * @param risks - Array of risks to export
 * @param riskSeverities - Array of risk severities for GUID resolution
 * @param filename - Name of the output PDF file (without extension)
 * @returns Promise that resolves when PDF is generated
 */
export const exportRisksToPdf = async (risks: Risk[], riskSeverities: RiskSeverity[], filename: string = 'risks-report'): Promise<void> => {
    try {
        // Track PDF download
        const { getAuthHeader } = useAuthStore.getState();
        await trackPdfDownload('risk', getAuthHeader);
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

        // Helper function to resolve GUID to severity name
        const getSeverityName = (severityId: string): string => {
            const severity = riskSeverities.find(s => s.id === severityId);
            return severity ? severity.risk_severity_name : 'N/A';
        };

        // Helper function to add a new page if needed
        const checkPageBreak = (requiredHeight: number) => {
            if (currentY + requiredHeight > pageHeight - margin) {
                pdf.addPage();
                currentY = margin;
                return true;
            }
            return false;
        };

        // Helper function to add text with word wrapping and automatic page breaks
        const addWrappedText = (text: string, x: number, y: number, maxWidth: number, fontSize: number = 10): number => {
            pdf.setFontSize(fontSize);
            const lines = pdf.splitTextToSize(text, maxWidth);
            const lineHeight = fontSize * 0.4; // Better line height calculation
            let currentLineY = y;
            
            for (let i = 0; i < lines.length; i++) {
                // Check if we need a new page for this line
                if (currentLineY + lineHeight > pageHeight - margin) {
                    pdf.addPage();
                    currentLineY = margin;
                    // Update the global currentY to track the position after page break
                    currentY = currentLineY;
                }
                
                pdf.text(lines[i], x, currentLineY);
                currentLineY += lineHeight;
            }
            
            // Update the global currentY variable
            currentY = currentLineY;
            return currentLineY;
        };

        // Helper function to add simple text with page break checking
        const addText = (text: string, x: number, y: number, fontSize: number = 10): number => {
            const lineHeight = fontSize * 0.4;
            if (y + lineHeight > pageHeight - margin) {
                pdf.addPage();
                y = margin;
                currentY = y;
            }
            pdf.setFontSize(fontSize);
            pdf.text(text, x, y);
            currentY = y + lineHeight;
            return currentY;
        };

        // Add title page
        pdf.setFontSize(24);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Risk Assessment Report', pageWidth / 2, currentY + 20, { align: 'center' });
        
        currentY += 40;
        pdf.setFontSize(12);
        pdf.setFont('helvetica', 'normal');
        pdf.text(`Generated on: ${new Date().toLocaleDateString()}`, pageWidth / 2, currentY, { align: 'center' });
        pdf.text(`Total Risks: ${risks.length}`, pageWidth / 2, currentY + 10, { align: 'center' });

        currentY += 30;

        // Process each risk
        for (let i = 0; i < risks.length; i++) {
            const risk = risks[i];
            
            // Start each risk on a new page
            pdf.addPage();
            currentY = margin;

            // Risk header
            pdf.setFontSize(16);
            pdf.setFont('helvetica', 'bold');
            pdf.setTextColor(204, 0, 0); // Red color for risks
            currentY = addWrappedText(risk.risk_category_name, margin, currentY, contentWidth, 16);
            currentY += 5;

            // Add separator line
            pdf.setDrawColor(204, 0, 0);
            pdf.line(margin, currentY, pageWidth - margin, currentY);
            currentY += 10;

            // Reset text color
            pdf.setTextColor(0, 0, 0);

            // Risk details in two columns
            const leftColumnX = margin;
            const rightColumnX = pageWidth / 2 + 10;
            const columnWidth = (contentWidth - 20) / 2;
            let leftY = currentY;
            let rightY = currentY;

            // Left column
            pdf.setFontSize(10);
            pdf.setFont('helvetica', 'bold');
            pdf.text('Asset Category:', leftColumnX, leftY);
            pdf.setFont('helvetica', 'normal');
            leftY = addWrappedText(risk.asset_category || 'N/A', leftColumnX + 30, leftY, columnWidth - 30);
            leftY += 5;

            pdf.setFont('helvetica', 'bold');
            pdf.text('Severity:', leftColumnX, leftY);
            pdf.setFont('helvetica', 'normal');
            leftY = addWrappedText(risk.risk_severity || 'N/A', leftColumnX + 30, leftY, columnWidth - 30);
            leftY += 5;

            pdf.setFont('helvetica', 'bold');
            pdf.text('Status:', leftColumnX, leftY);
            pdf.setFont('helvetica', 'normal');
            leftY = addWrappedText(risk.risk_status || 'N/A', leftColumnX + 30, leftY, columnWidth - 30);
            leftY += 5;

            pdf.setFont('helvetica', 'bold');
            pdf.text('Likelihood:', leftColumnX, leftY);
            pdf.setFont('helvetica', 'normal');
            leftY = addWrappedText(getSeverityName(risk.likelihood), leftColumnX + 30, leftY, columnWidth - 30);
            leftY += 5;

            // Right column
            pdf.setFont('helvetica', 'bold');
            pdf.text('Residual Risk:', rightColumnX, rightY);
            pdf.setFont('helvetica', 'normal');
            rightY = addWrappedText(getSeverityName(risk.residual_risk), rightColumnX + 30, rightY, columnWidth - 30);
            rightY += 5;

            pdf.setFont('helvetica', 'bold');
            pdf.text('Created:', rightColumnX, rightY);
            pdf.setFont('helvetica', 'normal');
            const createdDate = new Date(risk.created_at).toLocaleDateString();
            rightY = addWrappedText(createdDate, rightColumnX + 30, rightY, columnWidth - 30);
            rightY += 5;

            pdf.setFont('helvetica', 'bold');
            pdf.text('Updated:', rightColumnX, rightY);
            pdf.setFont('helvetica', 'normal');
            const updatedDate = new Date(risk.updated_at).toLocaleDateString();
            rightY = addWrappedText(updatedDate, rightColumnX + 30, rightY, columnWidth - 30);
            rightY += 5;

            currentY = Math.max(leftY, rightY) + 5;

            // Risk Description
            if (risk.risk_category_description) {
                pdf.setFont('helvetica', 'bold');
                pdf.text('Description:', margin, currentY);
                pdf.setFont('helvetica', 'normal');
                currentY = addWrappedText(risk.risk_category_description, margin, currentY + 5, contentWidth);
                currentY += 5;
            }

            // Potential Impact
            if (risk.risk_potential_impact) {
                pdf.setFont('helvetica', 'bold');
                pdf.text('Potential Impact:', margin, currentY);
                pdf.setFont('helvetica', 'normal');
                currentY = addWrappedText(risk.risk_potential_impact, margin, currentY + 5, contentWidth);
                currentY += 5;
            }

            // Risk Controls
            if (risk.risk_control) {
                pdf.setFont('helvetica', 'bold');
                pdf.text('Risk Controls:', margin, currentY);
                pdf.setFont('helvetica', 'normal');
                currentY = addWrappedText(risk.risk_control, margin, currentY + 5, contentWidth);
                currentY += 5;
            }
        }

        // Add charts page
        pdf.addPage();
        currentY = margin;

        // Charts page title
        pdf.setFontSize(20);
        pdf.setFont('helvetica', 'bold');
        pdf.setTextColor(204, 0, 0);
        pdf.text('Risk Statistics', pageWidth / 2, currentY, { align: 'center' });
        currentY += 15;
        pdf.setTextColor(0, 0, 0);

        // Calculate statistics
        const severityCounts: Record<string, number> = {};
        const statusCounts: Record<string, number> = {};
        risks.forEach(risk => {
            const severity = risk.risk_severity || 'Unknown';
            const status = risk.risk_status || 'Unknown';
            severityCounts[severity] = (severityCounts[severity] || 0) + 1;
            statusCounts[status] = (statusCounts[status] || 0) + 1;
        });

        // Draw pie chart for risk severity distribution
        const chartCenterX = pageWidth / 2;
        const chartCenterY = currentY + 40;
        const chartRadius = 35;

        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Risk Severity Distribution', pageWidth / 2, currentY, { align: 'center' });
        currentY += 10;

        // Define colors for each severity
        const severityColors: Record<string, [number, number, number]> = {
            'Low': [82, 196, 26],
            'Medium': [250, 173, 20],
            'High': [255, 77, 79],
            'Critical': [204, 0, 0],
        };

        // Draw pie chart
        let startAngle = 0;
        const severities = Object.entries(severityCounts);
        const total = risks.length;

        severities.forEach(([severity, count]) => {
            const sliceAngle = (count / total) * 2 * Math.PI;
            const color = severityColors[severity] || [140, 140, 140];

            pdf.setFillColor(color[0], color[1], color[2]);

            // Draw pie slice using triangles
            for (let i = 0; i < 50; i++) {
                const angle1 = startAngle + (sliceAngle * i / 50);
                const angle2 = startAngle + (sliceAngle * (i + 1) / 50);

                pdf.triangle(
                    chartCenterX, chartCenterY,
                    chartCenterX + chartRadius * Math.cos(angle1),
                    chartCenterY + chartRadius * Math.sin(angle1),
                    chartCenterX + chartRadius * Math.cos(angle2),
                    chartCenterY + chartRadius * Math.sin(angle2),
                    'F'
                );
            }

            startAngle += sliceAngle;
        });

        // Draw legend for severity
        currentY = chartCenterY + chartRadius + 15;
        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');

        severities.forEach(([severity, count]) => {
            const color = severityColors[severity] || [140, 140, 140];
            const percentage = ((count / total) * 100).toFixed(1);

            pdf.setFillColor(color[0], color[1], color[2]);
            pdf.rect(margin, currentY - 3, 5, 5, 'F');

            pdf.setTextColor(0, 0, 0);
            pdf.text(`${severity}: ${count} (${percentage}%)`, margin + 8, currentY);
            currentY += 7;
        });

        // Add bar chart for risk status
        currentY += 15;
        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Risk Status Distribution', pageWidth / 2, currentY, { align: 'center' });
        currentY += 10;

        const statuses = Object.entries(statusCounts);
        const maxCount = Math.max(...statuses.map(([, count]) => count));
        const barHeight = 10;
        const maxBarWidth = contentWidth - 60;

        pdf.setFontSize(9);
        pdf.setFont('helvetica', 'normal');

        statuses.forEach(([status, count]) => {
            const barWidth = (count / maxCount) * maxBarWidth;

            // Draw bar
            pdf.setFillColor(99, 102, 241);
            pdf.rect(margin + 50, currentY - 7, barWidth, barHeight, 'F');

            // Draw status label
            pdf.setTextColor(0, 0, 0);
            pdf.text(status, margin, currentY);

            // Draw count
            pdf.text(count.toString(), margin + 52 + barWidth, currentY);

            currentY += barHeight + 5;
        });

        // Add summary statistics
        currentY += 10;
        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Summary Statistics', margin, currentY);
        currentY += 10;

        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');
        pdf.text(`Total Risks: ${risks.length}`, margin + 5, currentY);
        currentY += 6;

        const criticalRisks = risks.filter(r => r.risk_severity === 'Critical').length;
        pdf.text(`Critical Risks: ${criticalRisks}`, margin + 5, currentY);
        currentY += 6;

        const highRisks = risks.filter(r => r.risk_severity === 'High').length;
        pdf.text(`High Risks: ${highRisks}`, margin + 5, currentY);

        // Add footer to all pages
        const totalPages = pdf.getNumberOfPages();
        for (let i = 1; i <= totalPages; i++) {
            pdf.setPage(i);
            pdf.setFontSize(8);
            pdf.setTextColor(128, 128, 128);
            pdf.text(`Page ${i} of ${totalPages}`, pageWidth - margin, pageHeight - 10, { align: 'right' });
            pdf.text('CyberBridge Risk Assessment Report', margin, pageHeight - 10);
        }

        pdf.save(`${filename}.pdf`);
    } catch (error) {
        console.error('Error generating risks PDF:', error);
        throw error;
    }
};