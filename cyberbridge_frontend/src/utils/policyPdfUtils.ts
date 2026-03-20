import jsPDF from 'jspdf';
import { Policy } from '../store/usePolicyStore';
import { trackPdfDownload } from './trackPdfDownload';
import useAuthStore from '../store/useAuthStore';

/**
 * Exports all policies to a structured PDF with modern styling
 * @param policies - Array of policies to export
 * @param filename - Name of the output PDF file (without extension)
 * @returns Promise that resolves when PDF is generated
 */
export const exportPoliciesToPdf = async (policies: Policy[], filename: string = 'policies-report'): Promise<void> => {
    try {
        // Track PDF download
        const { getAuthHeader } = useAuthStore.getState();
        await trackPdfDownload('policy', getAuthHeader);
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
        pdf.text('Policies Report', pageWidth / 2, currentY + 20, { align: 'center' });
        
        currentY += 40;
        pdf.setFontSize(12);
        pdf.setFont('helvetica', 'normal');
        pdf.text(`Generated on: ${new Date().toLocaleDateString()}`, pageWidth / 2, currentY, { align: 'center' });
        pdf.text(`Total Policies: ${policies.length}`, pageWidth / 2, currentY + 10, { align: 'center' });

        currentY += 30;

        // Process each policy
        for (let i = 0; i < policies.length; i++) {
            const policy = policies[i];
            
            // Start each policy on a new page
            pdf.addPage();
            currentY = margin;

            // Policy header
            pdf.setFontSize(16);
            pdf.setFont('helvetica', 'bold');
            pdf.setTextColor(91, 155, 213); // Blue color
            currentY = addWrappedText(policy.title, margin, currentY, contentWidth, 16);
            currentY += 5;

            // Add separator line
            pdf.setDrawColor(91, 155, 213);
            pdf.line(margin, currentY, pageWidth - margin, currentY);
            currentY += 10;

            // Reset text color
            pdf.setTextColor(0, 0, 0);

            // Policy details in two columns
            const leftColumnX = margin;
            const rightColumnX = pageWidth / 2 + 10;
            const columnWidth = (contentWidth - 20) / 2;
            let leftY = currentY;
            let rightY = currentY;

            // Left column
            pdf.setFontSize(10);
            pdf.setFont('helvetica', 'bold');
            pdf.text('Status:', leftColumnX, leftY);
            pdf.setFont('helvetica', 'normal');
            leftY = addWrappedText(policy.status || 'N/A', leftColumnX + 25, leftY, columnWidth - 25);
            leftY += 5;

            pdf.setFont('helvetica', 'bold');
            pdf.text('Owner:', leftColumnX, leftY);
            pdf.setFont('helvetica', 'normal');
            leftY = addWrappedText(policy.owner || 'N/A', leftColumnX + 25, leftY, columnWidth - 25);
            leftY += 5;

            pdf.setFont('helvetica', 'bold');
            pdf.text('Company:', leftColumnX, leftY);
            pdf.setFont('helvetica', 'normal');
            leftY = addWrappedText(policy.company_name || 'N/A', leftColumnX + 25, leftY, columnWidth - 25);
            leftY += 5;

            // Right column
            pdf.setFont('helvetica', 'bold');
            pdf.text('Created:', rightColumnX, rightY);
            pdf.setFont('helvetica', 'normal');
            const createdDate = new Date(policy.created_at).toLocaleDateString();
            rightY = addWrappedText(createdDate, rightColumnX + 25, rightY, columnWidth - 25);
            rightY += 5;

            // Frameworks (if any)
            if (policy.frameworks && policy.frameworks.length > 0) {
                pdf.setFont('helvetica', 'bold');
                pdf.text('Frameworks:', rightColumnX, rightY);
                pdf.setFont('helvetica', 'normal');
                const frameworksText = policy.frameworks.join(', ');
                rightY = addWrappedText(frameworksText, rightColumnX + 30, rightY, columnWidth - 30);
                rightY += 5;
            }

            // Objectives (if any)
            if (policy.objectives && policy.objectives.length > 0) {
                pdf.setFont('helvetica', 'bold');
                pdf.text('Objectives:', rightColumnX, rightY);
                pdf.setFont('helvetica', 'normal');
                const objectivesText = policy.objectives.join(', ');
                rightY = addWrappedText(objectivesText, rightColumnX + 30, rightY, columnWidth - 30);
                rightY += 5;
            }

            currentY = Math.max(leftY, rightY) + 5;

            // Policy Body
            if (policy.body) {
                pdf.setFont('helvetica', 'bold');
                pdf.text('Policy Body:', margin, currentY);
                currentY += 7;

                pdf.setFont('helvetica', 'normal');
                pdf.setFontSize(9);
                currentY = addWrappedText(policy.body, margin + 5, currentY, contentWidth - 5, 9);
                
                pdf.setFontSize(10); // Reset font size
                currentY += 5;
            }
        }

        // Add charts page
        pdf.addPage();
        currentY = margin;

        // Charts page title
        pdf.setFontSize(20);
        pdf.setFont('helvetica', 'bold');
        pdf.setTextColor(91, 155, 213);
        pdf.text('Policy Statistics', pageWidth / 2, currentY, { align: 'center' });
        currentY += 15;
        pdf.setTextColor(0, 0, 0);

        // Calculate statistics
        const statusCounts: Record<string, number> = {};
        policies.forEach(policy => {
            const status = policy.status || 'Unknown';
            statusCounts[status] = (statusCounts[status] || 0) + 1;
        });

        // Draw pie chart for policy status distribution
        const chartCenterX = pageWidth / 2;
        const chartCenterY = currentY + 50;
        const chartRadius = 40;

        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Policy Status Distribution', pageWidth / 2, currentY, { align: 'center' });
        currentY += 10;

        // Define colors for each status
        const statusColors: Record<string, [number, number, number]> = {
            'Draft': [140, 140, 140],
            'Review': [24, 144, 255],
            'Ready for Approval': [250, 173, 20],
            'Approved': [82, 196, 26],
        };

        // Draw pie chart
        let startAngle = 0;
        const statuses = Object.entries(statusCounts);
        const total = policies.length;

        statuses.forEach(([status, count]) => {
            const sliceAngle = (count / total) * 2 * Math.PI;
            const color = statusColors[status] || [140, 140, 140];

            pdf.setFillColor(color[0], color[1], color[2]);

            // Draw pie slice
            const points: [number, number][] = [[chartCenterX, chartCenterY]];
            for (let a = 0; a <= sliceAngle; a += 0.1) {
                const angle = startAngle + a;
                points.push([
                    chartCenterX + chartRadius * Math.cos(angle),
                    chartCenterY + chartRadius * Math.sin(angle)
                ]);
            }
            points.push([chartCenterX, chartCenterY]);

            pdf.triangle(
                points[0][0], points[0][1],
                points[1][0], points[1][1],
                points[Math.floor(points.length/2)][0], points[Math.floor(points.length/2)][1],
                'F'
            );

            // Draw multiple triangles to create the arc
            for (let i = 0; i < points.length - 2; i++) {
                pdf.triangle(
                    chartCenterX, chartCenterY,
                    points[i][0], points[i][1],
                    points[i+1][0], points[i+1][1],
                    'F'
                );
            }

            startAngle += sliceAngle;
        });

        // Draw legend
        currentY = chartCenterY + chartRadius + 20;
        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');

        statuses.forEach(([status, count]) => {
            const color = statusColors[status] || [140, 140, 140];
            const percentage = ((count / total) * 100).toFixed(1);

            // Draw color box
            pdf.setFillColor(color[0], color[1], color[2]);
            pdf.rect(margin, currentY - 3, 5, 5, 'F');

            // Draw text
            pdf.setTextColor(0, 0, 0);
            pdf.text(`${status}: ${count} (${percentage}%)`, margin + 8, currentY);
            currentY += 7;
        });

        // Add summary statistics
        currentY += 15;
        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Summary Statistics', margin, currentY);
        currentY += 10;

        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');
        pdf.text(`Total Policies: ${policies.length}`, margin + 5, currentY);
        currentY += 6;

        const policiesWithFrameworks = policies.filter(p => p.frameworks && p.frameworks.length > 0).length;
        pdf.text(`Policies with Frameworks: ${policiesWithFrameworks}`, margin + 5, currentY);
        currentY += 6;

        const policiesWithObjectives = policies.filter(p => p.objectives && p.objectives.length > 0).length;
        pdf.text(`Policies with Objectives: ${policiesWithObjectives}`, margin + 5, currentY);
        currentY += 6;

        const policiesWithBody = policies.filter(p => p.body && p.body.trim().length > 0).length;
        pdf.text(`Policies with Content: ${policiesWithBody}`, margin + 5, currentY);

        // Add footer to all pages
        const totalPages = pdf.getNumberOfPages();
        for (let i = 1; i <= totalPages; i++) {
            pdf.setPage(i);
            pdf.setFontSize(8);
            pdf.setTextColor(128, 128, 128);
            pdf.text(`Page ${i} of ${totalPages}`, pageWidth - margin, pageHeight - 10, { align: 'right' });
            pdf.text('CyberBridge Policies Report', margin, pageHeight - 10);
        }

        pdf.save(`${filename}.pdf`);
    } catch (error) {
        console.error('Error generating policies PDF:', error);
        throw error;
    }
};