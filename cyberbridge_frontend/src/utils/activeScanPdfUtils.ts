import jsPDF from 'jspdf';
import { ActiveScanState } from '../store/useZapStore';

/**
 * Exports ZAP Active Scan Details to a structured PDF with modern styling
 * @param activeScanState - Active scan state data to export
 * @param targetUrl - The target URL that was scanned
 * @param filename - Name of the output PDF file (without extension)
 * @returns Promise that resolves when PDF is generated
 */
export const exportActiveScanDetailsToPdf = async (
    activeScanState: ActiveScanState | null,
    targetUrl: string = '',
    filename: string = 'webapp-active-scan-details'
): Promise<void> => {
    try {
        if (!activeScanState) {
            throw new Error('No active scan state data available');
        }

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

        // Helper function to get status color
        const getStatusColor = (status: string): [number, number, number] => {
            if (status === 'Pending') return [128, 128, 128]; // Gray
            if (status.includes('%')) {
                const percent = parseInt(status, 10);
                if (percent < 30) return [255, 140, 0]; // Orange
                if (percent < 70) return [70, 130, 180]; // Blue
                return [34, 139, 34]; // Green
            }
            return [0, 0, 0]; // Black
        };

        // Add title page
        pdf.setFontSize(24);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Web App Active Scan Details', pageWidth / 2, currentY + 20, { align: 'center' });

        currentY += 40;
        pdf.setFontSize(12);
        pdf.setFont('helvetica', 'normal');
        pdf.text(`Generated on: ${new Date().toLocaleDateString()}`, pageWidth / 2, currentY, { align: 'center' });

        if (targetUrl) {
            currentY += 10;
            pdf.text(`Target: ${targetUrl}`, pageWidth / 2, currentY, { align: 'center' });
        }

        // Add Active Scans Overview section
        currentY += 20;
        pdf.setFontSize(16);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Active Scans Overview', margin, currentY);
        currentY += 10;

        if (activeScanState.active_scans && activeScanState.active_scans.scans) {
            pdf.setFontSize(10);
            pdf.setFont('helvetica', 'normal');
            pdf.text(`Total Active Scans: ${activeScanState.active_scans.scans.length}`, margin, currentY);
            currentY += 10;

            // Display each active scan
            activeScanState.active_scans.scans.forEach((scan, index) => {
                checkPageBreak(40);

                pdf.setFontSize(12);
                pdf.setFont('helvetica', 'bold');
                pdf.text(`Scan ID: ${scan.id}`, margin, currentY);
                currentY += 7;

                pdf.setFontSize(10);
                pdf.setFont('helvetica', 'normal');
                pdf.text(`State: ${scan.state}`, margin + 5, currentY);
                currentY += 6;
                pdf.text(`Progress: ${scan.progress}%`, margin + 5, currentY);
                currentY += 6;
                pdf.text(`Requests: ${scan.reqCount}`, margin + 5, currentY);
                currentY += 6;
                pdf.text(`Alerts: ${scan.alertCount} (New: ${scan.newAlertCount})`, margin + 5, currentY);
                currentY += 10;

                if (index < activeScanState.active_scans.scans.length - 1) {
                    pdf.setDrawColor(200, 200, 200);
                    pdf.line(margin, currentY, pageWidth - margin, currentY);
                    currentY += 10;
                }
            });
        } else {
            pdf.setFontSize(10);
            pdf.setFont('helvetica', 'italic');
            pdf.text('No active scans data available', margin, currentY);
            currentY += 10;
        }

        // Add Scanner Progress Details section
        currentY += 10;
        checkPageBreak(30);
        pdf.setFontSize(16);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Scanner Progress Details', margin, currentY);
        currentY += 10;

        if (activeScanState.scanner_progress.scanProgress &&
            activeScanState.scanner_progress.scanProgress.length > 1) {

            const targetHost = activeScanState.scanner_progress.scanProgress[0];
            pdf.setFontSize(12);
            pdf.setFont('helvetica', 'normal');
            pdf.text(`Target: ${targetHost}`, margin, currentY);
            currentY += 10;

            const hostProcesses = activeScanState.scanner_progress.scanProgress[1].HostProcess;

            if (hostProcesses && hostProcesses.length > 0) {
                // Process each plugin
                hostProcesses.forEach((hostProcess, index) => {
                    if (!hostProcess.Plugin || hostProcess.Plugin.length < 7) return;

                    const pluginName = hostProcess.Plugin[0];
                    const pluginId = hostProcess.Plugin[1];
                    const pluginQuality = hostProcess.Plugin[2];
                    const pluginStatus = hostProcess.Plugin[3];
                    const pluginTimeInMs = hostProcess.Plugin[4];
                    const pluginReqCount = hostProcess.Plugin[5];
                    const pluginAlertCount = hostProcess.Plugin[6];

                    checkPageBreak(35);

                    // Plugin header with status color
                    const statusColor = getStatusColor(pluginStatus);
                    pdf.setFontSize(11);
                    pdf.setFont('helvetica', 'bold');
                    pdf.setTextColor(statusColor[0], statusColor[1], statusColor[2]);
                    currentY = addWrappedText(`${pluginName}`, margin, currentY, contentWidth, 11);
                    currentY += 2;

                    // Reset text color
                    pdf.setTextColor(0, 0, 0);

                    // Plugin details
                    pdf.setFontSize(9);
                    pdf.setFont('helvetica', 'normal');
                    pdf.text(`ID: ${pluginId} | Quality: ${pluginQuality} | Status: ${pluginStatus}`, margin + 5, currentY);
                    currentY += 5;

                    if (pluginStatus !== 'Pending') {
                        pdf.text(`Time: ${pluginTimeInMs}ms | Requests: ${pluginReqCount} | Alerts: ${pluginAlertCount}`, margin + 5, currentY);
                        currentY += 5;
                    }

                    currentY += 3;

                    // Add separator between plugins
                    if (index < hostProcesses.length - 1) {
                        pdf.setDrawColor(230, 230, 230);
                        pdf.line(margin, currentY, pageWidth - margin, currentY);
                        currentY += 5;
                    }
                });
            } else {
                pdf.setFontSize(10);
                pdf.setFont('helvetica', 'italic');
                pdf.text('No scanner progress data available', margin, currentY);
                currentY += 10;
            }
        } else {
            pdf.setFontSize(10);
            pdf.setFont('helvetica', 'italic');
            pdf.text('Scanner progress details will be available once the active scan starts processing', margin, currentY);
            currentY += 10;
        }

        // Add footer to all pages
        const totalPages = pdf.getNumberOfPages();
        for (let i = 1; i <= totalPages; i++) {
            pdf.setPage(i);
            pdf.setFontSize(8);
            pdf.setTextColor(128, 128, 128);
            pdf.text(`Page ${i} of ${totalPages}`, pageWidth - margin, pageHeight - 10, { align: 'right' });
            pdf.text('CyberBridge Web App Security Active Scan Details', margin, pageHeight - 10);
        }

        pdf.save(`${filename}.pdf`);
    } catch (error) {
        console.error('Error generating Active Scan Details PDF:', error);
        throw error;
    }
};
