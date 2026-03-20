import type {TableColumnsType} from "antd";
import useQuestionsStore, {FrameworksQuestions} from "../store/useQuestionsStore";

export const FrameworksQuestionsGridColumns = (): TableColumnsType<FrameworksQuestions> => {
    const { frameworks_questions } = useQuestionsStore();

    // Extract distinct values
    const distinctFrameworkNames = [...new Set(frameworks_questions.map(q => q.framework_name))];
    const distinctQuestions = [...new Set(frameworks_questions.map(q => q.question_text))];
    const distinctMandatoryValues = [...new Set(frameworks_questions.map(q => q.is_question_mandatory.toString()))];
    const distinctAssessmentTypes = [...new Set(frameworks_questions.map(q => q.assessment_type))];

    // Create filters array from distinct values
    const frameworkNameFilter = distinctFrameworkNames.map(framework_name => ({
        text: framework_name,
        value: framework_name,
    }));

    const mandatoryFilter = distinctMandatoryValues.map(mandatory => ({
        text: mandatory,
        value: mandatory,
    }));

    const questionFilter = distinctQuestions.map(question => ({
        text: question,
        value: question,
    }))

    const assessmentTypeFilter = distinctAssessmentTypes.map(assessmentType => ({
        text: assessmentType,
        value: assessmentType,
    }))

    return [
        {
            title: 'Framework Name',
            dataIndex: 'framework_name',
            showSorterTooltip: { target: 'full-header' },
            filters: frameworkNameFilter,
            onFilter: (value, record) => record.framework_name.indexOf(value as string) === 0,
            sorter: (a, b) => a.framework_name.length - b.framework_name.length,
            sortDirections: ['descend'],
        },
        {
            title: 'Framework Description',
            dataIndex: 'framework_description',
            defaultSortOrder: 'descend',
            sorter: (a, b) => a.framework_description.length - b.framework_description.length,
        },
        {
            title: 'Question Text',
            dataIndex: 'question_text',
            showSorterTooltip: { target: 'full-header' },
            filters: questionFilter,
            onFilter: (value, record) => record.question_text.indexOf(value as string) === 0,
            sorter: (a, b) => a.question_text.length - b.question_text.length,
            sortDirections: ['descend'],
        },
        {
            title: 'Assessment Type',
            dataIndex: 'assessment_type',
            showSorterTooltip: { target: 'full-header' },
            filters: assessmentTypeFilter,
            onFilter: (value, record) => record.assessment_type.indexOf(value as string) === 0,
            sorter: (a, b) => a.assessment_type.length - b.assessment_type.length,
            sortDirections: ['descend'],
        },
        {
            title: 'is Question Mandatory',
            dataIndex: 'is_question_mandatory',
            showSorterTooltip: { target: 'full-header' },
            filters: mandatoryFilter,
            onFilter: (value, record) => record.is_question_mandatory.toString().indexOf(value as string) === 0,
            sorter: (a, b) => a.is_question_mandatory.toString().length - b.is_question_mandatory.toString().length,
            sortDirections: ['descend'],
        },
    ];
};
