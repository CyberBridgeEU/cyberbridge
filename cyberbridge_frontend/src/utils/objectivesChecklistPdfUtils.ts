import jsPDF from 'jspdf';
import { ChapterWithObjectives } from '../store/useObjectiveStore';
import { trackPdfDownload } from './trackPdfDownload';
import useAuthStore from '../store/useAuthStore';

/**
 * Exports objectives checklist with chapters, objectives, and compliance status to a structured PDF
 * @param chaptersWithObjectives - Array of chapters with their objectives
 * @param frameworkName - Name of the framework
 * @param filename - Name of the output PDF file (without extension)
 * @returns Promise that resolves when PDF is generated
 */
export const exportObjectivesChecklistToPdf = async (
    chaptersWithObjectives: ChapterWithObjectives[],
    frameworkName: string,
    filename: string = 'objectives-checklist-report'
): Promise<void> => {
    try {
        // Track PDF download
        const { getAuthHeader } = useAuthStore.getState();
        await trackPdfDownload('objectives', getAuthHeader);
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
            const lineHeight = fontSize * 0.4;
            let currentLineY = y;

            for (let i = 0; i < lines.length; i++) {
                if (currentLineY + lineHeight > pageHeight - margin) {
                    pdf.addPage();
                    currentLineY = margin;
                    currentY = currentLineY;
                }

                pdf.text(lines[i], x, currentLineY);
                currentLineY += lineHeight;
            }

            currentY = currentLineY;
            return currentLineY;
        };

        // Helper function to get status color
        const getStatusColor = (status: string | null): [number, number, number] => {
            switch (status) {
                case 'compliant':
                    return [82, 196, 26];
                case 'partially compliant':
                    return [250, 173, 20];
                case 'not compliant':
                    return [99, 102, 241];
                case 'in review':
                    return [24, 144, 255];
                case 'not applicable':
                    return [217, 217, 217];
                case 'not assessed':
                default:
                    return [140, 140, 140];
            }
        };

        // Add title page
        pdf.setFontSize(24);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Objectives Checklist Report', pageWidth / 2, currentY + 20, { align: 'center' });

        currentY += 40;
        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'normal');
        pdf.text(`Framework: ${frameworkName}`, pageWidth / 2, currentY, { align: 'center' });
        currentY += 10;
        pdf.setFontSize(12);
        pdf.text(`Generated on: ${new Date().toLocaleDateString()}`, pageWidth / 2, currentY, { align: 'center' });
        currentY += 8;

        // Calculate statistics
        const totalObjectives = chaptersWithObjectives.reduce((sum, chapter) => sum + chapter.objectives.length, 0);
        const statusCounts = chaptersWithObjectives.reduce((counts, chapter) => {
            chapter.objectives.forEach(obj => {
                const status = obj.compliance_status || 'not assessed';
                counts[status] = (counts[status] || 0) + 1;
            });
            return counts;
        }, {} as Record<string, number>);

        pdf.text(`Total Chapters: ${chaptersWithObjectives.length}`, pageWidth / 2, currentY, { align: 'center' });
        currentY += 8;
        pdf.text(`Total Objectives: ${totalObjectives}`, pageWidth / 2, currentY, { align: 'center' });

        currentY += 15;

        // Status summary
        if (Object.keys(statusCounts).length > 0) {
            pdf.setFontSize(10);
            pdf.setFont('helvetica', 'bold');
            pdf.text('Compliance Status Summary:', pageWidth / 2, currentY, { align: 'center' });
            currentY += 7;
            pdf.setFont('helvetica', 'normal');

            Object.entries(statusCounts).forEach(([status, count]) => {
                const color = getStatusColor(status);
                pdf.setTextColor(color[0], color[1], color[2]);
                pdf.text(`${status}: ${count}`, pageWidth / 2, currentY, { align: 'center' });
                currentY += 6;
            });
            pdf.setTextColor(0, 0, 0);
        }

        currentY += 20;

        // Process each chapter
        for (let chapterIndex = 0; chapterIndex < chaptersWithObjectives.length; chapterIndex++) {
            const chapter = chaptersWithObjectives[chapterIndex];

            // Start each chapter on a new page (except the first one if space allows)
            if (chapterIndex > 0 || currentY > pageHeight / 2) {
                pdf.addPage();
                currentY = margin;
            } else {
                checkPageBreak(40);
            }

            // Chapter header
            pdf.setFontSize(16);
            pdf.setFont('helvetica', 'bold');
            pdf.setTextColor(91, 155, 213);
            currentY = addWrappedText(`Chapter ${chapterIndex + 1}: ${chapter.title}`, margin, currentY, contentWidth, 16);
            currentY += 3;

            // Add separator line
            pdf.setDrawColor(91, 155, 213);
            pdf.line(margin, currentY, pageWidth - margin, currentY);
            currentY += 10;

            // Reset text color
            pdf.setTextColor(0, 0, 0);

            // Chapter metadata
            pdf.setFontSize(9);
            pdf.setTextColor(140, 140, 140);
            pdf.text(`${chapter.objectives.length} objective${chapter.objectives.length !== 1 ? 's' : ''}`, margin, currentY);
            currentY += 8;
            pdf.setTextColor(0, 0, 0);
            pdf.setFontSize(10);

            // Process each objective in the chapter
            for (let objIndex = 0; objIndex < chapter.objectives.length; objIndex++) {
                const objective = chapter.objectives[objIndex];

                // Check if we need a new page
                checkPageBreak(40);

                // Objective number and title
                pdf.setFont('helvetica', 'bold');
                currentY = addWrappedText(`${objIndex + 1}. ${objective.title}`, margin + 5, currentY, contentWidth - 5, 11);
                currentY += 5;

                // Requirement description
                if (objective.requirement_description) {
                    pdf.setFont('helvetica', 'bold');
                    pdf.text('Requirement:', margin + 10, currentY);
                    pdf.setFont('helvetica', 'normal');
                    pdf.setFontSize(9);
                    currentY = addWrappedText(objective.requirement_description, margin + 10, currentY + 5, contentWidth - 10, 9);
                    currentY += 5;
                    pdf.setFontSize(10);
                }

                // Objective utilities
                if (objective.objective_utilities) {
                    pdf.setFont('helvetica', 'bold');
                    pdf.text('Utilities:', margin + 10, currentY);
                    pdf.setFont('helvetica', 'normal');
                    pdf.setFontSize(9);
                    currentY = addWrappedText(objective.objective_utilities, margin + 10, currentY + 5, contentWidth - 10, 9);
                    currentY += 5;
                    pdf.setFontSize(10);
                }

                // Compliance status with color
                pdf.setFont('helvetica', 'bold');
                pdf.text('Status:', margin + 10, currentY);
                const status = objective.compliance_status || 'not assessed';
                const statusColor = getStatusColor(status);
                pdf.setTextColor(statusColor[0], statusColor[1], statusColor[2]);
                pdf.setFont('helvetica', 'normal');
                currentY = addWrappedText(status.toUpperCase(), margin + 30, currentY, contentWidth - 30);
                currentY += 8;
                pdf.setTextColor(0, 0, 0);

                // Add a light separator between objectives
                if (objIndex < chapter.objectives.length - 1) {
                    pdf.setDrawColor(230, 230, 230);
                    pdf.line(margin + 10, currentY, pageWidth - margin, currentY);
                    currentY += 8;
                }
            }

            currentY += 10; // Space between chapters
        }

        // Add charts page
        pdf.addPage();
        currentY = margin;

        // Charts page title
        pdf.setFontSize(20);
        pdf.setFont('helvetica', 'bold');
        pdf.setTextColor(91, 155, 213);
        pdf.text('Objectives Statistics', pageWidth / 2, currentY, { align: 'center' });
        currentY += 15;
        pdf.setTextColor(0, 0, 0);

        // Use already calculated statistics from the title page
        // statusCounts and totalObjectives are already calculated above

        // Draw pie chart for compliance status distribution
        const chartCenterX = pageWidth / 2;
        const chartCenterY = currentY + 45;
        const chartRadius = 35;

        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Compliance Status Distribution', pageWidth / 2, currentY, { align: 'center' });
        currentY += 10;

        // Define colors for each status (matching the UI)
        const statusColors: Record<string, [number, number, number]> = {
            'compliant': [82, 196, 26],
            'partially compliant': [250, 173, 20],
            'not compliant': [99, 102, 241],
            'in review': [24, 144, 255],
            'not applicable': [217, 217, 217],
            'not assessed': [140, 140, 140],
        };

        // Draw pie chart
        let startAngle = 0;
        const statuses = Object.entries(statusCounts);
        const total = totalObjectives;

        statuses.forEach(([status, count]) => {
            const sliceAngle = (count / total) * 2 * Math.PI;
            const color = statusColors[status] || [140, 140, 140];

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

        // Draw legend
        currentY = chartCenterY + chartRadius + 15;
        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');

        statuses.forEach(([status, count]) => {
            const color = statusColors[status] || [140, 140, 140];
            const percentage = ((count / total) * 100).toFixed(1);

            pdf.setFillColor(color[0], color[1], color[2]);
            pdf.rect(margin, currentY - 3, 5, 5, 'F');

            pdf.setTextColor(0, 0, 0);
            pdf.text(`${status}: ${count} (${percentage}%)`, margin + 8, currentY);
            currentY += 7;
        });

        // Add bar chart for chapters
        currentY += 15;
        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Objectives per Chapter', pageWidth / 2, currentY, { align: 'center' });
        currentY += 10;

        const maxChapterCount = Math.max(...chaptersWithObjectives.map(ch => ch.objectives.length));
        const barHeight = 8;
        const maxBarWidth = contentWidth - 60;

        pdf.setFontSize(8);
        pdf.setFont('helvetica', 'normal');

        chaptersWithObjectives.forEach(chapter => {
            const count = chapter.objectives.length;
            const barWidth = (count / maxChapterCount) * maxBarWidth;

            // Draw bar
            pdf.setFillColor(91, 155, 213);
            pdf.rect(margin + 50, currentY - 6, barWidth, barHeight, 'F');

            // Draw chapter title (truncated if too long)
            pdf.setTextColor(0, 0, 0);
            const truncatedTitle = chapter.title.length > 20 ? chapter.title.substring(0, 17) + '...' : chapter.title;
            pdf.text(truncatedTitle, margin, currentY);

            // Draw count
            pdf.text(count.toString(), margin + 52 + barWidth, currentY);

            currentY += barHeight + 4;
        });

        // Add summary statistics
        currentY += 10;
        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Summary Statistics', margin, currentY);
        currentY += 10;

        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');
        pdf.text(`Total Chapters: ${chaptersWithObjectives.length}`, margin + 5, currentY);
        currentY += 6;
        pdf.text(`Total Objectives: ${totalObjectives}`, margin + 5, currentY);
        currentY += 6;

        const compliantCount = statusCounts['compliant'] || 0;
        const complianceRate = totalObjectives > 0 ? ((compliantCount / totalObjectives) * 100).toFixed(1) : '0.0';
        pdf.text(`Fully Compliant: ${compliantCount} (${complianceRate}%)`, margin + 5, currentY);
        currentY += 6;

        const assessedCount = totalObjectives - (statusCounts['not assessed'] || 0);
        const assessmentRate = totalObjectives > 0 ? ((assessedCount / totalObjectives) * 100).toFixed(1) : '0.0';
        pdf.text(`Assessed Objectives: ${assessedCount} (${assessmentRate}%)`, margin + 5, currentY);

        // Add footer to all pages
        const totalPages = pdf.getNumberOfPages();
        for (let i = 1; i <= totalPages; i++) {
            pdf.setPage(i);
            pdf.setFontSize(8);
            pdf.setTextColor(128, 128, 128);
            pdf.text(`Page ${i} of ${totalPages}`, pageWidth - margin, pageHeight - 10, { align: 'right' });
            pdf.text('CyberBridge Objectives Checklist', margin, pageHeight - 10);
        }

        pdf.save(`${filename}.pdf`);
    } catch (error) {
        console.error('Error generating objectives checklist PDF:', error);
        throw error;
    }
};