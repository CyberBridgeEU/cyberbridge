import jsPDF from 'jspdf';
import { Answer } from '../store/useAssessmentsStore';
import { trackPdfDownload } from './trackPdfDownload';
import useAuthStore from '../store/useAuthStore';

/**
 * Exports assessment with all questions, answers, policies, and file names to a structured PDF
 * @param answers - Array of answers with question data
 * @param assessmentName - Name of the assessment
 * @param frameworkName - Name of the framework
 * @param assessmentType - Type of assessment (conformity/audit)
 * @param filename - Name of the output PDF file (without extension)
 * @returns Promise that resolves when PDF is generated
 */
export const exportAssessmentToPdf = async (
    answers: Answer[],
    assessmentName: string,
    frameworkName: string,
    assessmentType: string,
    filename: string = 'assessment-report'
): Promise<void> => {
    try {
        // Track PDF download
        const { getAuthHeader } = useAuthStore.getState();
        await trackPdfDownload('assessment', getAuthHeader);
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

        // Add title page
        pdf.setFontSize(24);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Assessment Report', pageWidth / 2, currentY + 20, { align: 'center' });

        currentY += 40;
        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'normal');
        pdf.text(`Assessment: ${assessmentName}`, pageWidth / 2, currentY, { align: 'center' });
        currentY += 10;
        pdf.text(`Framework: ${frameworkName}`, pageWidth / 2, currentY, { align: 'center' });
        currentY += 10;
        pdf.text(`Type: ${assessmentType.charAt(0).toUpperCase() + assessmentType.slice(1)}`, pageWidth / 2, currentY, { align: 'center' });
        currentY += 10;
        pdf.setFontSize(12);
        pdf.text(`Generated on: ${new Date().toLocaleDateString()}`, pageWidth / 2, currentY, { align: 'center' });
        currentY += 8;
        pdf.text(`Total Questions: ${answers.length}`, pageWidth / 2, currentY, { align: 'center' });

        // Calculate progress statistics
        const answeredCount = answers.filter(a => a.answer_value).length;
        const mandatoryCount = answers.filter(a => a.is_question_mandatory).length;
        const mandatoryAnsweredCount = answers.filter(a => a.is_question_mandatory && a.answer_value).length;

        currentY += 8;
        pdf.text(`Answered: ${answeredCount} of ${answers.length} (${Math.round((answeredCount/answers.length)*100)}%)`, pageWidth / 2, currentY, { align: 'center' });
        currentY += 8;
        pdf.text(`Mandatory Answered: ${mandatoryAnsweredCount} of ${mandatoryCount}`, pageWidth / 2, currentY, { align: 'center' });

        currentY += 20;

        // Process each question and answer
        for (let i = 0; i < answers.length; i++) {
            const answer = answers[i];

            // Check if we need a new page (rough estimate)
            checkPageBreak(50);

            // Question number and mandatory status
            pdf.setFontSize(12);
            pdf.setFont('helvetica', 'bold');
            pdf.setTextColor(91, 155, 213);
            const questionHeader = `Question ${i + 1}${answer.is_question_mandatory ? ' (Mandatory)' : ''}`;
            currentY = addWrappedText(questionHeader, margin, currentY, contentWidth, 12);
            currentY += 2;

            // Add separator line
            pdf.setDrawColor(91, 155, 213);
            pdf.line(margin, currentY, pageWidth - margin, currentY);
            currentY += 8;

            // Reset text color
            pdf.setTextColor(0, 0, 0);

            // Question text
            pdf.setFontSize(10);
            pdf.setFont('helvetica', 'normal');
            currentY = addWrappedText(answer.question_text, margin, currentY, contentWidth);
            currentY += 5;

            // Answer value
            pdf.setFont('helvetica', 'bold');
            pdf.text('Answer:', margin, currentY);
            pdf.setFont('helvetica', 'normal');
            const answerValue = answer.answer_value || 'Not answered';
            const answerColor = answer.answer_value ? (
                answer.answer_value === 'yes' ? [82, 196, 26] :
                answer.answer_value === 'no' ? [255, 77, 79] :
                answer.answer_value === 'partially' ? [250, 173, 20] :
                [140, 140, 140]
            ) : [140, 140, 140];
            pdf.setTextColor(answerColor[0], answerColor[1], answerColor[2]);
            currentY = addWrappedText(answerValue.toUpperCase(), margin + 25, currentY, contentWidth - 25);
            currentY += 5;
            pdf.setTextColor(0, 0, 0);

            // Policy assignment (for conformity assessments)
            if (assessmentType.toLowerCase() === 'conformity' && answer.policy_title) {
                pdf.setFont('helvetica', 'bold');
                pdf.text('Assigned Policy:', margin, currentY);
                pdf.setFont('helvetica', 'normal');
                currentY = addWrappedText(answer.policy_title, margin + 35, currentY, contentWidth - 35);
                currentY += 5;
            }

            // Attached files
            if (answer.files && answer.files.length > 0) {
                pdf.setFont('helvetica', 'bold');
                pdf.text(`Attached Files (${answer.files.length}):`, margin, currentY);
                currentY += 5;
                pdf.setFont('helvetica', 'normal');
                pdf.setFontSize(9);

                answer.files.forEach((file, fileIndex) => {
                    checkPageBreak(6);
                    pdf.text(`  ${fileIndex + 1}. ${file.name}`, margin + 5, currentY);
                    currentY += 4;
                });

                pdf.setFontSize(10);
                currentY += 3;
            }

            // Additional metadata
            if (answer.framework_names) {
                pdf.setFontSize(8);
                pdf.setTextColor(140, 140, 140);
                pdf.text(`Common in: ${answer.framework_names}`, margin, currentY);
                currentY += 5;
                pdf.setTextColor(0, 0, 0);
                pdf.setFontSize(10);
            }

            currentY += 10; // Space between questions
        }

        // Add charts page
        pdf.addPage();
        currentY = margin;

        // Charts page title
        pdf.setFontSize(20);
        pdf.setFont('helvetica', 'bold');
        pdf.setTextColor(91, 155, 213);
        pdf.text('Assessment Statistics', pageWidth / 2, currentY, { align: 'center' });
        currentY += 15;
        pdf.setTextColor(0, 0, 0);

        // Calculate statistics
        const answerCounts: Record<string, number> = {
            'yes': 0,
            'no': 0,
            'partially': 0,
            'n/a': 0,
            'Not answered': 0
        };

        answers.forEach(answer => {
            const value = answer.answer_value || 'Not answered';
            answerCounts[value] = (answerCounts[value] || 0) + 1;
        });

        // Draw pie chart for answer distribution
        const chartCenterX = pageWidth / 2;
        const chartCenterY = currentY + 40;
        const chartRadius = 35;

        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Answer Distribution', pageWidth / 2, currentY, { align: 'center' });
        currentY += 10;

        // Define colors for each answer type
        const answerColors: Record<string, [number, number, number]> = {
            'yes': [82, 196, 26],
            'no': [255, 77, 79],
            'partially': [250, 173, 20],
            'n/a': [217, 217, 217],
            'Not answered': [140, 140, 140],
        };

        // Draw pie chart
        let startAngle = 0;
        const answerEntries = Object.entries(answerCounts).filter(([, count]) => count > 0);
        const total = answers.length;

        answerEntries.forEach(([answer, count]) => {
            const sliceAngle = (count / total) * 2 * Math.PI;
            const color = answerColors[answer] || [140, 140, 140];

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

        answerEntries.forEach(([answer, count]) => {
            const color = answerColors[answer] || [140, 140, 140];
            const percentage = ((count / total) * 100).toFixed(1);

            pdf.setFillColor(color[0], color[1], color[2]);
            pdf.rect(margin, currentY - 3, 5, 5, 'F');

            pdf.setTextColor(0, 0, 0);
            pdf.text(`${answer.toUpperCase()}: ${count} (${percentage}%)`, margin + 8, currentY);
            currentY += 7;
        });

        // Add progress bar
        currentY += 15;
        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Completion Progress', pageWidth / 2, currentY, { align: 'center' });
        currentY += 10;

        const answeredCountChart = answers.filter(a => a.answer_value).length;
        const completionRate = (answeredCountChart / total) * 100;
        const barWidth = contentWidth - 40;
        const barHeight = 15;

        // Draw progress bar background
        pdf.setFillColor(230, 230, 230);
        pdf.rect(margin + 20, currentY - 5, barWidth, barHeight, 'F');

        // Draw progress bar fill
        const fillWidth = (completionRate / 100) * barWidth;
        pdf.setFillColor(82, 196, 26);
        pdf.rect(margin + 20, currentY - 5, fillWidth, barHeight, 'F');

        // Draw progress text
        pdf.setFontSize(12);
        pdf.setTextColor(0, 0, 0);
        pdf.text(`${completionRate.toFixed(1)}% Complete (${answeredCountChart}/${total})`, pageWidth / 2, currentY + 2, { align: 'center' });
        currentY += 20;

        // Add summary statistics
        currentY += 10;
        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Summary Statistics', margin, currentY);
        currentY += 10;

        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');
        pdf.text(`Total Questions: ${answers.length}`, margin + 5, currentY);
        currentY += 6;

        const mandatoryCountChart = answers.filter(a => a.is_question_mandatory).length;
        const mandatoryAnsweredChart = answers.filter(a => a.is_question_mandatory && a.answer_value).length;
        pdf.text(`Mandatory Questions: ${mandatoryAnsweredChart}/${mandatoryCountChart} answered`, margin + 5, currentY);
        currentY += 6;

        const questionsWithFiles = answers.filter(a => a.files && a.files.length > 0).length;
        pdf.text(`Questions with Attachments: ${questionsWithFiles}`, margin + 5, currentY);
        currentY += 6;

        if (assessmentType.toLowerCase() === 'conformity') {
            const questionsWithPolicies = answers.filter(a => a.policy_title).length;
            pdf.text(`Questions with Policies: ${questionsWithPolicies}`, margin + 5, currentY);
        }

        // Add footer to all pages
        const totalPages = pdf.getNumberOfPages();
        for (let i = 1; i <= totalPages; i++) {
            pdf.setPage(i);
            pdf.setFontSize(8);
            pdf.setTextColor(128, 128, 128);
            pdf.text(`Page ${i} of ${totalPages}`, pageWidth - margin, pageHeight - 10, { align: 'right' });
            pdf.text('CyberBridge Assessment Report', margin, pageHeight - 10);
        }

        pdf.save(`${filename}.pdf`);
    } catch (error) {
        console.error('Error generating assessment PDF:', error);
        throw error;
    }
};