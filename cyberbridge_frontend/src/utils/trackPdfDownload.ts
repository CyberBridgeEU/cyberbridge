// Utility function to track PDF downloads
import { cyberbridge_back_end_rest_api } from '../constants/urls';

export const trackPdfDownload = async (pdfType: string, getAuthHeader: () => Record<string, string>) => {
  try {
    const authHeader = getAuthHeader();

    await fetch(`${cyberbridge_back_end_rest_api}/admin/track-pdf-download`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeader
      },
      body: JSON.stringify({ pdf_type: pdfType })
    });

    // Silent tracking - don't show errors to user
  } catch (error) {
    console.error('Failed to track PDF download:', error);
    // Silently fail - don't interrupt user's PDF download experience
  }
};
