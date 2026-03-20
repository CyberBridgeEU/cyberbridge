import React, {useEffect, useState} from 'react';
import {Select, notification, Table, type TableProps} from "antd";
import {QuestionCircleOutlined} from "@ant-design/icons";
import Sidebar from "../components/Sidebar.tsx";
import useQuestionsStore, {FrameworksQuestions} from "../store/useQuestionsStore.ts";
import useFrameworksStore from "../store/useFrameworksStore.ts";
import useAssessmentTypesStore from "../store/useAssessmentTypesStore.ts";
import {FrameworksQuestionsGridColumns} from "../constants/FrameworksQuestionsGridColumns.tsx";
import InfoTitle from "../components/InfoTitle.tsx";
import {
    AddQuestionsInfo,
    EditQuestionsInfo
} from "../constants/infoContent.tsx";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import useCRAFilteredFrameworks from "../hooks/useCRAFilteredFrameworks.ts";

const FrameworkQuestionsPage: React.FC = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Global State
    const {questions, frameworks_questions, addQuestion, removeQuestion, clearQuestions, toggleMandatory, uploadQuestionsFromCSV, saveQuestions, fetchFrameworksQuestions, deleteQuestion} = useQuestionsStore();
    const {assessmentTypes, fetchAssessmentTypes} = useAssessmentTypesStore();
    const {frameworks, fetchFrameworks} = useFrameworksStore();
    const { filteredFrameworks, craFrameworkId, isCRAModeActive } = useCRAFilteredFrameworks();

    // Local State
    const [newQuestionText, setNewQuestionText] = useState<string>('');
    const [frameworkSelectedIds, setFrameworkSelectedIds] = useState<string[]>([]);
    const [api, contextHolder] = notification.useNotification();
    const [selectedTableRow, setSelectedTableRow] = useState<FrameworksQuestions | null>(null);
    const [selectedAssessmentType, setSelectedAssessmentType] = useState<string>('');

    // On Component Mount
    useEffect(() => {
        fetchFrameworks();
        fetchAssessmentTypes();
    }, []);

    // Auto-select CRA framework when CRA mode is active
    useEffect(() => {
        if (isCRAModeActive && craFrameworkId && frameworkSelectedIds.length === 0) {
            handleFrameworkChange([craFrameworkId]);
        }
    }, [isCRAModeActive, craFrameworkId]);

    // Framework options
    const options = filteredFrameworks.map(framework => ({
        value: framework.id,
        label: framework.organisation_domain ? `${framework.name} (${framework.organisation_domain})` : framework.name,
    }));

    // Assessment type options
    const assessmentTypeOptions = assessmentTypes.map(assessmentType => ({
        value: assessmentType.id,
        label: assessmentType.type_name.charAt(0).toUpperCase() + assessmentType.type_name.slice(1),
    }));

    // Handle framework change
    const handleFrameworkChange = async (value: string[]) => {
        const selectedIds = value.filter(Boolean);
        setFrameworkSelectedIds(selectedIds);
        await fetchFrameworksQuestions(selectedIds);
    };

    // Handle adding new question
    const handleAddingNewQuestion = () => {
        if (!newQuestionText || newQuestionText.trim() === '') {
            api.error({
                message: 'Invalid Question',
                description: 'Question text cannot be empty!',
                duration: 4,
            });
            return;
        }

        if (!selectedAssessmentType || selectedAssessmentType.trim() === '') {
            api.error({
                message: 'Assessment Type Required',
                description: 'Please select an assessment type for the question!',
                duration: 4,
            });
            return;
        }

        addQuestion(newQuestionText, selectedAssessmentType);
        setNewQuestionText('');
    };

    // Save questions for selected frameworks
    const saveQuestionsForSelectedFrameworks = async () => {
        if (frameworkSelectedIds.length <= 0) {
            api.error({
                message: 'No Framework Selected',
                description: 'Please select at least one framework to save questions for!',
                duration: 4,
            });
            return;
        }

        if (questions && questions.length > 0) {
            const invalidQuestions = questions.filter(q => !q.text || q.text.trim() === '');

            if (invalidQuestions.length > 0) {
                api.error({
                    message: 'Invalid Question(s) Found',
                    description: 'Question text cannot be empty!',
                    duration: 4,
                });
                return;
            }

            const success = await saveQuestions(frameworkSelectedIds);
            if (success) {
                api.success({
                    message: 'Questions Creation Success',
                    description: 'Questions created.',
                    duration: 4,
                });
                clearQuestions();
                setNewQuestionText('');
                await fetchFrameworksQuestions(frameworkSelectedIds);
            } else {
                api.error({
                    message: 'Questions Creation Failed',
                    description: 'Api not responding...',
                    duration: 4,
                });
            }
        } else {
            api.error({
                message: 'No Questions Found',
                description: 'Please add at least one question.',
                duration: 4,
            });
        }
    };

    // Handle delete question
    const handleDeleteQuestion = async () => {
        if (!selectedTableRow) {
            api.error({
                message: 'Question Deletion Failed',
                description: 'Please select a question to delete first!',
                duration: 4,
            });
            return;
        }

        const success = await deleteQuestion(selectedTableRow.question_id);

        if (success) {
            api.success({
                message: 'Question Deletion Success',
                description: 'Question deleted successfully.',
                duration: 4,
            });
            setSelectedTableRow(null);

            if (frameworkSelectedIds.length > 0) {
                await fetchFrameworksQuestions(frameworkSelectedIds);
            }
        } else {
            api.error({
                message: 'Question Deletion Failed',
                description: 'Failed to delete question. Please try again.',
                duration: 4,
            });
        }
    };

    // Handle file upload
    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            await uploadQuestionsFromCSV(file);
            e.target.value = '';
        }
    };

    // Handle row click
    const handleRowClick = (record: FrameworksQuestions) => {
        setSelectedTableRow(record);
    };

    const onFrameworksQuestionsChange: TableProps<FrameworksQuestions>['onChange'] = (pagination, filters, sorter, extra) => {
        console.log('params', pagination, filters, sorter, extra);
    };

    return (
        <div>
            {contextHolder}
            <div className={'page-parent'}>
                <Sidebar selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange} />
                <div className="page-content">

                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <QuestionCircleOutlined style={{ fontSize: 22, color: '#1a365d' }} />
                            <h1 className="page-title" style={{ margin: 0 }}>Framework Questions</h1>
                        </div>
                    </div>

                    {/* Framework Selection */}
                    <div className="page-section">
                        <div className="form-row">
                            <div className="form-group" style={{ flex: 1 }}>
                                <label className="form-label">Select Frameworks</label>
                                <Select
                                    mode="multiple"
                                    className="framework-dropdown"
                                    placeholder="Select frameworks to manage questions"
                                    onChange={handleFrameworkChange}
                                    options={options}
                                    value={frameworkSelectedIds}
                                    style={{ width: '100%' }}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Question Management Section */}
                    <div className="page-section">
                        <InfoTitle
                            title="Add Questions"
                            infoContent={AddQuestionsInfo}
                            className="section-title"
                        />
                        <p className="section-subtitle">
                            Add new questions to selected frameworks or upload from CSV file
                        </p>

                        <div className="form-row" style={{ alignItems: 'flex-end' }}>
                            <div className="form-group" style={{ minWidth: '150px', flex: '0 0 180px' }}>
                                <label className="form-label">Question Type</label>
                                <Select
                                    placeholder="Select type"
                                    className="question-input"
                                    options={assessmentTypeOptions}
                                    value={selectedAssessmentType || undefined}
                                    onChange={setSelectedAssessmentType}
                                    style={{ width: '100%', height: '40px' }}
                                />
                            </div>
                            <div className="form-group" style={{ flex: '2', marginLeft: '16px', marginRight: '16px' }}>
                                <label className="form-label required">Question Text</label>
                                <input
                                    type="text"
                                    className="question-input"
                                    placeholder="Enter your question or request"
                                    value={newQuestionText}
                                    onChange={(e) => setNewQuestionText(e.target.value)}
                                />
                            </div>
                            <div className="control-group" style={{
                                alignItems: 'center',
                                marginBottom: '0',
                                gap: '8px',
                                flexWrap: 'nowrap'
                            }}>
                                <button
                                    className="add-button"
                                    onClick={handleAddingNewQuestion}
                                    style={{ height: '40px', minWidth: '100px' }}
                                >
                                    Add Question
                                </button>
                                <button
                                    className="add-button"
                                    onClick={saveQuestionsForSelectedFrameworks}
                                    style={{ height: '40px', minWidth: '80px' }}
                                >
                                    Save All
                                </button>
                                <label className="upload-button" style={{ height: '40px', minWidth: '100px' }}>
                                    Upload CSV
                                    <input type="file" accept=".csv" className="hidden-input" onChange={handleFileUpload}/>
                                </label>
                            </div>
                        </div>

                        {/* Questions List */}
                        {questions.length > 0 && (
                            <div style={{ marginTop: '20px' }}>
                                <h4 className="section-title" style={{ fontSize: '16px', marginBottom: '12px' }}>Pending Questions</h4>
                                <div className="questions-list">
                                    {questions.map((question) => (
                                        <div key={question.id} className="question-item">
                                            <p className="question-text">{question.text}</p>
                                            <div className="question-options">
                                                <span className="mandatory-label">mandatory</span>
                                                <input
                                                    type="checkbox"
                                                    checked={question.mandatory}
                                                    onChange={() => toggleMandatory(question.id)}
                                                    className="mandatory-checkbox"
                                                />
                                                <button className="delete-button" onClick={() => removeQuestion(question.id)}>
                                                    Remove
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Edit Questions Section */}
                    <div className="page-section">
                        <InfoTitle
                            title="Edit Questions"
                            infoContent={EditQuestionsInfo}
                            className="section-title"
                        />
                        <p className="section-subtitle">
                            Manage existing questions within selected frameworks
                        </p>

                        {selectedTableRow && (
                            <div className="form-row" style={{ marginBottom: '20px', alignItems: 'flex-end' }}>
                                <div className="form-group" style={{ flex: '1', minWidth: '200px' }}>
                                    <label className="form-label">Selected Framework</label>
                                    <input
                                        type="text"
                                        className="framework-input"
                                        value={selectedTableRow.framework_name}
                                        readOnly
                                        style={{ backgroundColor: '#f5f5f5' }}
                                    />
                                </div>
                                <div className="form-group" style={{ flex: '2', marginLeft: '16px', marginRight: '16px' }}>
                                    <label className="form-label">Selected Question</label>
                                    <input
                                        type="text"
                                        className="framework-input"
                                        value={selectedTableRow.question_text}
                                        readOnly
                                        style={{ backgroundColor: '#f5f5f5' }}
                                    />
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0', gap: '8px' }}>
                                    <button
                                        className="delete-button"
                                        onClick={handleDeleteQuestion}
                                        style={{ height: '40px' }}
                                    >
                                        Delete Question
                                    </button>
                                    <button
                                        className="add-button"
                                        onClick={() => setSelectedTableRow(null)}
                                        style={{ height: '40px', background: '#f5f5f5', color: '#666', border: '1px solid #d9d9d9' }}
                                    >
                                        Clear Selection
                                    </button>
                                </div>
                            </div>
                        )}

                        <Table<FrameworksQuestions>
                            columns={FrameworksQuestionsGridColumns()}
                            dataSource={frameworks_questions}
                            onChange={onFrameworksQuestionsChange}
                            showSorterTooltip={{ target: 'sorter-icon' }}
                            pagination={{
                                pageSize: 10,
                                showSizeChanger: true,
                                showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} questions`
                            }}
                            scroll={{ x: 1000 }}
                            onRow={(record) => ({
                                onClick: () => handleRowClick(record),
                                style: {
                                    cursor: 'pointer',
                                    backgroundColor: selectedTableRow?.question_id === record.question_id ? '#e6f7ff' : undefined
                                }
                            })}
                        />
                    </div>

                </div>
            </div>
        </div>
    );
};

export default FrameworkQuestionsPage;
