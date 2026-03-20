import type {TableColumnsType} from "antd";
import useObjectiveStore, {Objective} from "../store/useObjectiveStore";

export const ObjectivesGridColumns = (): TableColumnsType<Objective> => {
    const { objectives } = useObjectiveStore();

    // Extract distinct values for filtering
    const distinctSubchapters = [...new Set(objectives.map(obj => obj.subchapter).filter(Boolean))];
    const distinctTitles = [...new Set(objectives.map(obj => obj.title))];
    const distinctRequirements = [...new Set(objectives.map(obj => obj.requirement_description).filter(Boolean))];
    const distinctUtilities = [...new Set(objectives.map(obj => obj.objective_utilities).filter(Boolean))];

    // Create filters array from distinct values
    const subchapterFilter = distinctSubchapters.map(subchapter => ({
        text: subchapter,
        value: subchapter,
    }));

    const titleFilter = distinctTitles.map(title => ({
        text: title,
        value: title,
    }));

    const requirementFilter = distinctRequirements.map(requirement => ({
        text: requirement,
        value: requirement,
    }));

    const utilitiesFilter = distinctUtilities.map(utility => ({
        text: utility,
        value: utility,
    }));

    return [
        {
            title: 'Subchapter',
            dataIndex: 'subchapter',
            key: 'subchapter',
            showSorterTooltip: { target: 'full-header' },
            filters: subchapterFilter,
            onFilter: (value, record) => record.subchapter?.indexOf(value as string) === 0,
            sorter: (a, b) => {
                const aSubchapter = a.subchapter || '';
                const bSubchapter = b.subchapter || '';
                return aSubchapter.localeCompare(bSubchapter);
            },
            render: (text) => text || '-',
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Title',
            dataIndex: 'title',
            key: 'title',
            showSorterTooltip: { target: 'full-header' },
            filters: titleFilter,
            onFilter: (value, record) => record.title.indexOf(value as string) === 0,
            sorter: (a, b) => a.title.localeCompare(b.title),
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Requirement Description',
            dataIndex: 'requirement_description',
            key: 'requirement_description',
            showSorterTooltip: { target: 'full-header' },
            filters: requirementFilter,
            onFilter: (value, record) => record.requirement_description?.indexOf(value as string) === 0,
            sorter: (a, b) => {
                const aDesc = a.requirement_description || '';
                const bDesc = b.requirement_description || '';
                return aDesc.localeCompare(bDesc);
            },
            render: (text) => text || '-',
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Objective Utilities',
            dataIndex: 'objective_utilities',
            key: 'objective_utilities',
            showSorterTooltip: { target: 'full-header' },
            filters: utilitiesFilter,
            onFilter: (value, record) => record.objective_utilities?.indexOf(value as string) === 0,
            sorter: (a, b) => {
                const aUtil = a.objective_utilities || '';
                const bUtil = b.objective_utilities || '';
                return aUtil.localeCompare(bUtil);
            },
            render: (text) => text || '-',
            sortDirections: ['descend', 'ascend'],
        },
    ];
};
