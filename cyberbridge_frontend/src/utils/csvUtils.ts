import { Answer } from '../store/useAssessmentsStore';

/**
 * Exports assessment answers to CSV format (answer values only)
 * @param answers - Array of answers to export
 * @param assessmentName - Name of the assessment
 * @param frameworkId - Framework ID for validation
 * @param assessmentTypeId - Assessment type ID for validation
 * @returns CSV string
 */
export const exportAnswersToCSV = (
    answers: Answer[],
    assessmentName: string,
    frameworkId: string,
    assessmentTypeId: string
): void => {
    // Define CSV headers (simple - only what's needed)
    const headers = [
        'Framework ID',
        'Assessment Type ID',
        'Question ID',
        'Question Text',
        'Answer Value'
    ];

    // Create CSV rows (only answer values, no policies or files)
    const rows = answers.map(answer => [
        frameworkId,
        assessmentTypeId,
        answer.question_id || '',
        `"${(answer.question_text || '').replace(/"/g, '""')}"`, // Escape quotes
        answer.answer_value || ''
    ]);

    // Combine headers and rows
    const csvContent = [
        headers.join(','),
        ...rows.map(row => row.join(','))
    ].join('\n');

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', `${assessmentName}_answers_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};

/**
 * Parses CSV file and extracts answer data (answer values only)
 * @param file - CSV file to parse
 * @returns Promise with array of parsed answer objects
 */
export const parseAnswersFromCSV = (file: File): Promise<Array<{
    framework_id: string;
    assessment_type_id: string;
    question_id: string;
    question_text: string;
    answer_value: string;
}>> => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();

        reader.onload = (e) => {
            try {
                const text = e.target?.result as string;
                const lines = text.split('\n').filter(line => line.trim().length > 0);

                if (lines.length < 2) {
                    reject(new Error('CSV file is empty or invalid'));
                    return;
                }

                // Skip header line
                const dataLines = lines.slice(1);

                const parsedAnswers = dataLines.map(line => {
                    // Handle quoted fields properly
                    const fields: string[] = [];
                    let currentField = '';
                    let inQuotes = false;

                    for (let i = 0; i < line.length; i++) {
                        const char = line[i];

                        if (char === '"') {
                            if (inQuotes && line[i + 1] === '"') {
                                // Escaped quote
                                currentField += '"';
                                i++;
                            } else {
                                // Toggle quote state
                                inQuotes = !inQuotes;
                            }
                        } else if (char === ',' && !inQuotes) {
                            // Field separator
                            fields.push(currentField);
                            currentField = '';
                        } else {
                            currentField += char;
                        }
                    }
                    // Add last field
                    fields.push(currentField);

                    // Extract relevant fields (Framework ID, Assessment Type ID, Question ID, Question Text, Answer Value)
                    return {
                        framework_id: fields[0]?.trim() || '',
                        assessment_type_id: fields[1]?.trim() || '',
                        question_id: fields[2]?.trim() || '',
                        question_text: fields[3]?.trim() || '',
                        answer_value: fields[4]?.trim() || ''
                    };
                }).filter(answer =>
                    // Filter out invalid entries
                    answer.framework_id && answer.assessment_type_id && answer.question_id
                );

                resolve(parsedAnswers);
            } catch (error) {
                reject(new Error('Failed to parse CSV file: ' + (error instanceof Error ? error.message : 'Unknown error')));
            }
        };

        reader.onerror = () => {
            reject(new Error('Failed to read CSV file'));
        };

        reader.readAsText(file);
    });
};

/**
 * Validates imported answers against existing answers
 * @param importedAnswers - Parsed answers from CSV
 * @param existingAnswers - Current answers in the system
 * @param currentFrameworkId - Current framework ID for validation
 * @param currentAssessmentTypeId - Current assessment type ID for validation
 * @returns Validation result with valid answers and errors
 */
export const validateImportedAnswers = (
    importedAnswers: Array<{framework_id: string; assessment_type_id: string; question_id: string; question_text: string; answer_value: string}>,
    existingAnswers: Answer[],
    currentFrameworkId: string,
    currentAssessmentTypeId: string
): {
    validAnswers: Array<{answer_id: string; question_id: string; answer_value: string}>;
    errors: string[];
} => {
    const validAnswers: Array<{answer_id: string; question_id: string; answer_value: string}> = [];
    const errors: string[] = [];

    // Get the current assessment type name from existing answers
    const currentAssessmentTypeName = existingAnswers.length > 0 ? existingAnswers[0].assessment_type : 'Current Assessment';

    // Check if at least one row exists to validate assessment type
    if (importedAnswers.length > 0) {
        const firstRow = importedAnswers[0];

        // Validate assessment type ID matches (this is critical - conformity vs audit)
        if (firstRow.assessment_type_id !== currentAssessmentTypeId) {
            errors.push(`Assessment type mismatch: You cannot import answers from a different assessment type into "${currentAssessmentTypeName}". Please select the correct assessment type.`);
            return { validAnswers, errors };
        }

        // Note: We don't strictly check framework_id anymore
        // This allows importing between different instances of the same framework
        // (e.g., CRA in different organizations with the same questions)
        // The validation will happen at the question level below
    }

    const existingQuestionIds = new Set(existingAnswers.map(a => a.question_id));
    // Create a map of question_id to answer for quick lookup
    const questionToAnswerMap = new Map(existingAnswers.map(a => [a.question_id, a]));

    importedAnswers.forEach((imported, index) => {
        const lineNumber = index + 2; // +2 because of header and 0-index

        // Validate question exists in current assessment
        if (!existingQuestionIds.has(imported.question_id)) {
            const truncatedQuestion = imported.question_text.length > 100
                ? imported.question_text.substring(0, 100) + '...'
                : imported.question_text;
            errors.push(`Line ${lineNumber}: Question "${truncatedQuestion}" not found in current assessment`);
            return;
        }

        // Get the actual answer for this question in the current assessment
        const currentAnswer = questionToAnswerMap.get(imported.question_id);
        if (!currentAnswer) {
            const truncatedQuestion = imported.question_text.length > 100
                ? imported.question_text.substring(0, 100) + '...'
                : imported.question_text;
            errors.push(`Line ${lineNumber}: Could not find answer for question "${truncatedQuestion}" in current assessment`);
            return;
        }

        // Validate answer value
        const validValues = ['yes', 'no', 'partially', 'n/a', ''];
        if (imported.answer_value && !validValues.includes(imported.answer_value.toLowerCase())) {
            errors.push(`Line ${lineNumber}: Invalid answer value "${imported.answer_value}". Must be: yes, no, partially, n/a, or empty`);
            return;
        }

        // Use the answer_id from the current assessment (not from the imported CSV)
        // This allows importing answers from one assessment to another
        // Only import the answer value - policies and files are NOT affected
        validAnswers.push({
            answer_id: currentAnswer.answer_id, // Use current assessment's answer_id
            question_id: imported.question_id,
            answer_value: imported.answer_value.toLowerCase()
        });
    });

    return { validAnswers, errors };
};