import React, {useEffect, useState} from 'react';
import {Select, notification, Table, type TableProps} from "antd";
import {AppstoreOutlined, BookOutlined} from "@ant-design/icons";
import Sidebar from "../components/Sidebar.tsx";
import useFrameworksStore from "../store/useFrameworksStore.ts";
import {ObjectivesGridColumns} from "../constants/ObjectivesGridColumns.tsx";
import useObjectiveStore, {Objective} from "../store/useObjectiveStore.ts";
import InfoTitle from "../components/InfoTitle.tsx";
import {
    ManageChaptersObjectivesInfo,
    EditObjectivesInfo
} from "../constants/infoContent.tsx";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import useCRAFilteredFrameworks from "../hooks/useCRAFilteredFrameworks.ts";
import useCRAModeStore from "../store/useCRAModeStore.ts";

const ChaptersObjectivesPage: React.FC = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Global State
    const {chapters, objectives, chaptersWithObjectives, createChapter, updateChapter, deleteChapter, fetchObjectives, fetchChapters, createObjective, updateObjective, deleteObjective, fetchObjectivesChecklist} = useObjectiveStore();
    const {frameworks, fetchFrameworks} = useFrameworksStore();
    const { filteredFrameworks, craFrameworkId, isCRAModeActive } = useCRAFilteredFrameworks();
    const { craOperatorRole } = useCRAModeStore();

    // Local State
    const [frameworkSelectedIds, setFrameworkSelectedIds] = useState<string[]>([]);
    const [chapterSelectedIds, setChapterSelectedIds] = useState<string>('');
    const [api, contextHolder] = notification.useNotification();
    const [newChapterName, setNewChapterName] = useState<string>('');

    // State for objective form
    const [objectiveTitle, setObjectiveTitle] = useState<string>('');
    const [subchapter, setSubchapter] = useState<string>('');
    const [requirementDescription, setRequirementDescription] = useState<string>('');
    const [objectiveUtilities, setObjectiveUtilities] = useState<string>('');

    // State for selected objective
    const [selectedObjective, setSelectedObjective] = useState<Objective | null>(null);

    // State for chapter objectives
    const [chapterObjectives, setChapterObjectives] = useState<Objective[]>([]);

    // On Component Mount
    useEffect(() => {
        fetchFrameworks();
        fetchChapters();
        fetchObjectives();
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

    // Chapter options - only show when exactly one framework is selected
    const chapterOptions = frameworkSelectedIds.length === 1 && chaptersWithObjectives.length > 0
        ? chaptersWithObjectives.map(chapter => ({
            value: chapter.id,
            label: chapter.title,
        }))
        : [];

    // Handle framework change
    const handleFrameworkChange = async (value: string[]) => {
        const selectedIds = value.filter(Boolean);
        setFrameworkSelectedIds(selectedIds);

        // Clear chapter and objective data
        setChapterSelectedIds('');
        setChapterObjectives([]);
        setSelectedObjective(null);
        setObjectiveTitle('');
        setSubchapter('');
        setRequirementDescription('');
        setObjectiveUtilities('');

        if (selectedIds.length === 1) {
            await fetchObjectivesChecklist(selectedIds[0], undefined, undefined, craOperatorRole || undefined);
        }
    };

    // Re-fetch when operator role changes
    useEffect(() => {
        if (frameworkSelectedIds.length === 1) {
            fetchObjectivesChecklist(frameworkSelectedIds[0], undefined, undefined, craOperatorRole || undefined);
        }
    }, [craOperatorRole]);

    // Handle chapter change
    const handleChapterChange = async (value: string) => {
        setChapterSelectedIds(value);

        // Clear selected objective and form fields
        setSelectedObjective(null);
        setObjectiveTitle('');
        setSubchapter('');
        setRequirementDescription('');
        setObjectiveUtilities('');

        if (frameworkSelectedIds.length === 1) {
            await fetchObjectivesChecklist(frameworkSelectedIds[0], undefined, undefined, craOperatorRole || undefined);

            const chaptersWithObjectives = useObjectiveStore.getState().chaptersWithObjectives;
            const selectedChapter = chaptersWithObjectives.find(chapter => chapter.id === value);

            if (selectedChapter) {
                setChapterObjectives(selectedChapter.objectives);
            } else {
                setChapterObjectives([]);
            }
        } else {
            setChapterObjectives([]);
        }
    };

    // Handle create chapter
    const handleCreateChapter = async () => {
        if (frameworkSelectedIds.length !== 1) {
            api.error({message: 'Chapter Creation Failed', description: 'Please select exactly one framework to create a chapter!', duration: 4});
            return;
        }

        if (!newChapterName || newChapterName.trim() === '') {
            api.error({message: 'Chapter Creation Failed', description: 'Chapter name cannot be empty!', duration: 4});
            return;
        }

        const success = await createChapter(newChapterName, frameworkSelectedIds[0]);

        if (success) {
            api.success({message: 'Chapter Creation Success', description: 'Chapter created successfully.', duration: 4});
            setNewChapterName('');
            await fetchObjectivesChecklist(frameworkSelectedIds[0]);
        } else {
            api.error({message: 'Chapter Creation Failed', description: 'Failed to create chapter. Please try again.', duration: 4});
        }
    };

    // Handle delete chapter
    const handleDeleteChapter = async () => {
        if (!chapterSelectedIds || chapterSelectedIds.trim() === '') {
            api.error({message: 'Chapter Deletion Failed', description: 'Please select a chapter to delete first!', duration: 4});
            return;
        }

        const success = await deleteChapter(chapterSelectedIds);

        if (success) {
            api.success({message: 'Chapter Deletion Success', description: 'Chapter deleted successfully.', duration: 4});
            setObjectiveTitle('');
            setSubchapter('');
            setRequirementDescription('');
            setObjectiveUtilities('');
            setSelectedObjective(null);
            setChapterSelectedIds('');
            setChapterObjectives([]);

            if (frameworkSelectedIds.length === 1) {
                await fetchObjectivesChecklist(frameworkSelectedIds[0]);
            }
        } else {
            api.error({message: 'Chapter Deletion Failed', description: 'Failed to delete chapter. Please try again.', duration: 4});
        }
    };

    // Handle objective row click
    const handleObjectiveRowClick = (objective: Objective) => {
        setSelectedObjective(objective);
        setObjectiveTitle(objective.title);
        setSubchapter(objective.subchapter || '');
        setRequirementDescription(objective.requirement_description || '');
        setObjectiveUtilities(objective.objective_utilities || '');
    };

    // Handle create objective
    const handleCreateObjective = async () => {
        if (!chapterSelectedIds || chapterSelectedIds.trim() === '') {
            api.error({message: 'Objective Creation Failed', description: 'Please select a chapter first!', duration: 4});
            return;
        }

        if (!objectiveTitle || objectiveTitle.trim() === '') {
            api.error({message: 'Objective Creation Failed', description: 'Objective title cannot be empty!', duration: 4});
            return;
        }

        if (!requirementDescription || requirementDescription.trim() === '') {
            api.error({message: 'Objective Creation Failed', description: 'Requirement description cannot be empty!', duration: 4});
            return;
        }

        if (!objectiveUtilities || objectiveUtilities.trim() === '') {
            api.error({message: 'Objective Creation Failed', description: 'Objective utilities cannot be empty!', duration: 4});
            return;
        }

        const success = await createObjective(
            objectiveTitle,
            subchapter || "",
            chapterSelectedIds,
            requirementDescription,
            objectiveUtilities
        );

        if (success) {
            api.success({message: 'Objective Creation Success', description: 'Objective created successfully.', duration: 4});
            setObjectiveTitle('');
            setSubchapter('');
            setRequirementDescription('');
            setObjectiveUtilities('');

            if (frameworkSelectedIds.length === 1) {
                await fetchObjectivesChecklist(frameworkSelectedIds[0]);
                const chaptersWithObjectives = useObjectiveStore.getState().chaptersWithObjectives;
                const selectedChapter = chaptersWithObjectives.find(chapter => chapter.id === chapterSelectedIds);
                if (selectedChapter) {
                    setChapterObjectives(selectedChapter.objectives);
                }
            }
        } else {
            api.error({message: 'Objective Creation Failed', description: 'Failed to create objective. Please try again.', duration: 4});
        }
    };

    // Handle update objective
    const handleUpdateObjective = async () => {
        if (!selectedObjective) {
            api.error({message: 'Objective Update Failed', description: 'No objective selected for update!', duration: 4});
            return;
        }

        if (!objectiveTitle || objectiveTitle.trim() === '') {
            api.error({message: 'Objective Update Failed', description: 'Objective title cannot be empty!', duration: 4});
            return;
        }

        if (!requirementDescription || requirementDescription.trim() === '') {
            api.error({message: 'Objective Update Failed', description: 'Requirement description cannot be empty!', duration: 4});
            return;
        }

        if (!objectiveUtilities || objectiveUtilities.trim() === '') {
            api.error({message: 'Objective Update Failed', description: 'Objective utilities cannot be empty!', duration: 4});
            return;
        }

        const success = await updateObjective(
            objectiveTitle,
            subchapter || "",
            selectedObjective.chapter_id,
            requirementDescription,
            objectiveUtilities,
            selectedObjective.id
        );

        if (success) {
            api.success({message: 'Objective Update Success', description: 'Objective updated successfully!', duration: 4});
            setObjectiveTitle('');
            setSubchapter('');
            setRequirementDescription('');
            setObjectiveUtilities('');
            setSelectedObjective(null);

            if (frameworkSelectedIds.length === 1 && chapterSelectedIds) {
                await fetchObjectivesChecklist(frameworkSelectedIds[0]);
                const chaptersWithObjectives = useObjectiveStore.getState().chaptersWithObjectives;
                const selectedChapter = chaptersWithObjectives.find(chapter => chapter.id === chapterSelectedIds);
                if (selectedChapter) {
                    setChapterObjectives(selectedChapter.objectives);
                }
            }
        } else {
            api.error({message: 'Objective Update Failed', description: 'Failed to update objective. Please try again.', duration: 4});
        }
    };

    // Handle delete objective
    const handleDeleteObjective = async () => {
        if (!selectedObjective) {
            api.error({message: 'Objective Deletion Failed', description: 'Please select an objective to delete first!', duration: 4});
            return;
        }

        const success = await deleteObjective(selectedObjective.id);

        if (success) {
            api.success({message: 'Objective Deletion Success', description: 'Objective deleted successfully.', duration: 4});
            setObjectiveTitle('');
            setSubchapter('');
            setRequirementDescription('');
            setObjectiveUtilities('');
            setSelectedObjective(null);

            await fetchObjectives();
            const latestObjectives = useObjectiveStore.getState().objectives;
            const filteredObjectives = latestObjectives.filter(obj => obj.chapter_id === chapterSelectedIds);
            setChapterObjectives(filteredObjectives);
        } else {
            api.error({message: 'Objective Deletion Failed', description: 'Failed to delete objective. Please try again.', duration: 4});
        }
    };

    const onObjectivesChange: TableProps<Objective>['onChange'] = (pagination, filters, sorter, extra) => {
        console.log('objectives params', pagination, filters, sorter, extra);
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
                            <BookOutlined style={{ fontSize: 22, color: '#1a365d' }} />
                            <h1 className="page-title" style={{ margin: 0 }}>Chapters & Objectives</h1>
                        </div>
                    </div>

                    {/* Framework Selection */}
                    <div className="page-section">
                        <div className="form-row">
                            <div className="form-group" style={{ flex: 1 }}>
                                <label className="form-label">Select Framework</label>
                                <Select
                                    mode="multiple"
                                    className="framework-dropdown"
                                    placeholder="Select a framework to manage its chapters and objectives"
                                    onChange={handleFrameworkChange}
                                    options={options}
                                    value={frameworkSelectedIds}
                                    style={{ width: '100%' }}
                                />
                            </div>
                        </div>
                        {frameworkSelectedIds.length > 1 && (
                            <p style={{ color: '#fa8c16', fontSize: '13px', marginTop: '8px' }}>
                                Please select only one framework to manage chapters and objectives.
                            </p>
                        )}
                    </div>

                    {/* Chapters and Objectives Management Section */}
                    <div className="page-section">
                        <InfoTitle
                            title="Manage Chapters"
                            infoContent={ManageChaptersObjectivesInfo}
                            className="section-title"
                        />
                        <p className="section-subtitle">
                            Organize framework content into chapters and define specific objectives
                        </p>

                        {/* Create New Chapter */}
                        <div className="form-row">
                            <div className="form-group" style={{ flex: '1' }}>
                                <label className="form-label required">Chapter Name</label>
                                <input
                                    type="text"
                                    className="framework-input"
                                    placeholder="Enter chapter name"
                                    value={newChapterName}
                                    onChange={(e) => setNewChapterName(e.target.value)}
                                />
                            </div>
                            <div style={{ display: 'flex', alignItems: 'flex-end', marginLeft: '12px' }}>
                                <button
                                    className="add-button"
                                    onClick={handleCreateChapter}
                                    disabled={frameworkSelectedIds.length !== 1}
                                    style={{ marginBottom: '0', height: '40px' }}
                                >
                                    Create Chapter
                                </button>
                            </div>
                        </div>

                        {/* Chapter Selection and Management */}
                        <div className="form-row" style={{ alignItems: 'flex-end' }}>
                            <div className="form-group" style={{ flex: '1', minWidth: '300px' }}>
                                <label className="form-label">Select Chapter</label>
                                <Select
                                    className="framework-dropdown"
                                    placeholder="Choose a chapter to manage"
                                    onChange={handleChapterChange}
                                    options={chapterOptions}
                                    value={chapterSelectedIds || undefined}
                                    disabled={frameworkSelectedIds.length !== 1}
                                    style={{ width: '100%', height: '40px' }}
                                />
                            </div>
                            <div className="control-group" style={{
                                alignItems: 'center',
                                marginBottom: '0',
                                marginLeft: '12px',
                                gap: '8px'
                            }}>
                                <button
                                    className="delete-button"
                                    onClick={handleDeleteChapter}
                                    disabled={!chapterSelectedIds}
                                    style={{ height: '40px' }}
                                >
                                    Delete Chapter
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Objectives Management Section */}
                    <div className="page-section">
                        <InfoTitle
                            title="Manage Objectives"
                            infoContent={EditObjectivesInfo}
                            className="section-title"
                        />
                        <p className="section-subtitle">
                            Create, edit, and delete objectives within the selected chapter
                        </p>

                        {/* Objective Form */}
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">Subchapter</label>
                                <input
                                    type="text"
                                    className="framework-input"
                                    placeholder="Enter subchapter (optional)"
                                    value={subchapter}
                                    onChange={(e) => setSubchapter(e.target.value)}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label required">Objective Title</label>
                                <input
                                    type="text"
                                    className="framework-input"
                                    placeholder="Enter objective title"
                                    value={objectiveTitle}
                                    onChange={(e) => setObjectiveTitle(e.target.value)}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label required">Requirement Description</label>
                                <input
                                    type="text"
                                    className="framework-input"
                                    placeholder="Enter requirement description"
                                    value={requirementDescription}
                                    onChange={(e) => setRequirementDescription(e.target.value)}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label required">Objective Utilities</label>
                                <input
                                    type="text"
                                    className="framework-input"
                                    placeholder="Enter objective utilities"
                                    value={objectiveUtilities}
                                    onChange={(e) => setObjectiveUtilities(e.target.value)}
                                />
                            </div>
                        </div>

                        {/* Objective Action Buttons */}
                        <div className="form-row">
                            <div className="control-group" style={{ gap: '8px' }}>
                                <button
                                    className="add-button"
                                    onClick={selectedObjective ? handleUpdateObjective : handleCreateObjective}
                                    disabled={!chapterSelectedIds && !selectedObjective}
                                    style={{ height: '40px' }}
                                >
                                    {selectedObjective ? 'Update Objective' : 'Save Objective'}
                                </button>
                                <button
                                    className="delete-button"
                                    onClick={handleDeleteObjective}
                                    disabled={!selectedObjective}
                                    style={{ height: '40px' }}
                                >
                                    Delete Objective
                                </button>
                                {selectedObjective && (
                                    <button
                                        className="add-button"
                                        onClick={() => {
                                            setSelectedObjective(null);
                                            setObjectiveTitle('');
                                            setSubchapter('');
                                            setRequirementDescription('');
                                            setObjectiveUtilities('');
                                        }}
                                        style={{ height: '40px', background: '#f5f5f5', color: '#666', border: '1px solid #d9d9d9' }}
                                    >
                                        Clear Selection
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Objectives Table */}
                    <div className="page-section">
                        <InfoTitle
                            title="Objectives List"
                            infoContent="Click on an objective row to edit it. The form above will be populated with the objective's data."
                            className="section-title"
                        />
                        <p className="section-subtitle">
                            View and select objectives for the selected chapter
                        </p>
                        <Table<Objective>
                            columns={ObjectivesGridColumns()}
                            dataSource={chapterObjectives.map(obj => ({ ...obj, key: obj.id }))}
                            onChange={onObjectivesChange}
                            showSorterTooltip={{ target: 'sorter-icon' }}
                            rowKey="id"
                            pagination={{
                                pageSize: 10,
                                showSizeChanger: true,
                                showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} objectives`
                            }}
                            scroll={{ x: 800 }}
                            onRow={(record) => ({
                                onClick: () => handleObjectiveRowClick(record),
                                style: {
                                    cursor: 'pointer',
                                    backgroundColor: selectedObjective?.id === record.id ? '#e6f7ff' : undefined
                                }
                            })}
                        />
                    </div>

                </div>
            </div>
        </div>
    );
};

export default ChaptersObjectivesPage;
