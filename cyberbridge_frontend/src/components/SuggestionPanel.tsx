import React, { useState } from 'react';
import { Radio, Button, Tag, Tooltip, Empty, Spin, Alert, Typography, Badge } from 'antd';
import {
    ThunderboltOutlined,
    RobotOutlined,
    CheckCircleOutlined,
    CloseOutlined,
    BulbOutlined,
    DownOutlined,
    UpOutlined,
} from '@ant-design/icons';
import useSuggestionStore from '../store/useSuggestionStore.ts';
import type { SuggestionItem } from '../store/useSuggestionStore.ts';

const { Text } = Typography;

type TabKey = 'asset-risk' | 'risk-control' | 'control-policy' | 'policy-objective';

interface SuggestionPanelProps {
    tab: TabKey;
    entityId: string;
    frameworkId?: string;
    availableItemIds?: string[];
    onSelectItems: (ids: string[]) => void;
    disabled?: boolean;
}

const confidenceColor = (confidence: number): string => {
    if (confidence >= 75) return '#52c41a';
    if (confidence >= 50) return '#faad14';
    if (confidence >= 25) return '#fa8c16';
    return '#f5222d';
};

const confidenceTagColor = (confidence: number): string => {
    if (confidence >= 75) return 'success';
    if (confidence >= 50) return 'warning';
    return 'error';
};

const SuggestionPanel: React.FC<SuggestionPanelProps> = ({
    tab,
    entityId,
    frameworkId,
    availableItemIds,
    onSelectItems,
    disabled = false,
}) => {
    const { tabs, engine, setEngine, fetchSuggestions, cancelRequest } = useSuggestionStore();
    const tabState = tabs[tab];
    const [expanded, setExpanded] = useState(false);

    const hasSuggestions = tabState.suggestions.length > 0;
    const isActive = hasSuggestions || tabState.loading || tabState.error;

    const handleGetSuggestions = () => {
        setExpanded(true);
        fetchSuggestions(tab, entityId, frameworkId, availableItemIds);
    };

    const handleCancel = () => {
        cancelRequest(tab);
    };

    const handleSelectAll = () => {
        const ids = tabState.suggestions.map((s: SuggestionItem) => s.item_id);
        onSelectItems(ids);
    };

    const handleSelectOne = (itemId: string) => {
        onSelectItems([itemId]);
    };

    return (
        <div
            style={{
                borderRadius: 8,
                overflow: 'hidden',
                background: isActive
                    ? 'linear-gradient(135deg, rgba(26, 54, 93, 0.06) 0%, rgba(15, 56, 106, 0.10) 50%, rgba(114, 46, 209, 0.06) 100%)'
                    : 'linear-gradient(135deg, rgba(26, 54, 93, 0.03) 0%, rgba(15, 56, 106, 0.06) 50%, rgba(250, 173, 20, 0.04) 100%)',
                border: isActive ? '1.5px solid rgba(15, 56, 106, 0.35)' : '1.5px dashed rgba(15, 56, 106, 0.25)',
                transition: 'all 0.3s ease',
            }}
        >
            {/* Header banner — always visible */}
            <div
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    gap: 10,
                    flexWrap: 'wrap',
                }}
            >
                {/* Left: icon + title */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div
                        style={{
                            width: 30,
                            height: 30,
                            borderRadius: 8,
                            background: 'linear-gradient(135deg, #1a365d, #0f386a)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                        }}
                    >
                        <BulbOutlined style={{ color: '#fff', fontSize: 15 }} />
                    </div>
                    <div>
                        <Text strong style={{ fontSize: 13, color: '#1a365d', lineHeight: 1.2 }}>
                            AI Suggestions
                        </Text>
                        <div style={{ fontSize: 11, color: '#8c8c8c', lineHeight: 1.2, marginTop: 1 }}>
                            {hasSuggestions
                                ? `${tabState.suggestions.length} match${tabState.suggestions.length !== 1 ? 'es' : ''} found`
                                : 'Find relevant items automatically'}
                        </div>
                    </div>
                    {hasSuggestions && (
                        <Badge
                            count={tabState.suggestions.length}
                            style={{ backgroundColor: '#0f386a', boxShadow: 'none', marginLeft: 2 }}
                        />
                    )}
                </div>

                {/* Center: engine toggle */}
                <Radio.Group
                    value={engine}
                    onChange={(e) => setEngine(e.target.value)}
                    size="small"
                    disabled={tabState.loading}
                    style={{ flexShrink: 0 }}
                >
                    <Radio.Button value="rule" style={{ fontSize: 12 }}>
                        <ThunderboltOutlined style={{ marginRight: 3 }} />Fast
                    </Radio.Button>
                    <Radio.Button value="llm" style={{ fontSize: 12 }}>
                        <RobotOutlined style={{ marginRight: 3 }} />AI
                    </Radio.Button>
                </Radio.Group>

                {/* Right: action buttons */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    {tabState.loading ? (
                        <Button
                            size="small"
                            danger
                            icon={<CloseOutlined />}
                            onClick={handleCancel}
                        >
                            Cancel
                        </Button>
                    ) : (
                        <Button
                            size="small"
                            type="primary"
                            icon={<BulbOutlined />}
                            onClick={handleGetSuggestions}
                            disabled={disabled || !entityId}
                            style={{
                                background: disabled || !entityId
                                    ? undefined
                                    : 'linear-gradient(135deg, #1a365d 0%, #0f386a 100%)',
                                border: 'none',
                                fontWeight: 600,
                                boxShadow: disabled || !entityId
                                    ? undefined
                                    : '0 2px 8px rgba(15, 56, 106, 0.35)',
                            }}
                        >
                            {hasSuggestions ? 'Refresh' : 'Get Suggestions'}
                        </Button>
                    )}

                    {hasSuggestions && !tabState.loading && (
                        <>
                            <Button
                                size="small"
                                icon={<CheckCircleOutlined />}
                                onClick={handleSelectAll}
                                style={{ borderColor: '#52c41a', color: '#52c41a' }}
                            >
                                Select All
                            </Button>
                            <Button
                                type="text"
                                size="small"
                                icon={expanded ? <UpOutlined /> : <DownOutlined />}
                                onClick={() => setExpanded(!expanded)}
                                style={{ color: '#8c8c8c', fontSize: 11 }}
                            >
                                {expanded ? 'Hide' : 'Show'}
                            </Button>
                        </>
                    )}
                </div>
            </div>

            {/* Loading indicator inline */}
            {tabState.loading && (
                <div
                    style={{
                        padding: '14px 16px',
                        textAlign: 'center',
                        borderTop: '1px solid rgba(15, 56, 106, 0.12)',
                    }}
                >
                    <Spin size="small" />
                    <Text style={{ marginLeft: 10, fontSize: 12, color: '#0f386a' }}>
                        {engine === 'llm' ? 'Analyzing with AI — this may take a moment...' : 'Applying matching rules...'}
                    </Text>
                </div>
            )}

            {/* Error state */}
            {tabState.error && (
                <div style={{ padding: '0 14px 10px' }}>
                    <Alert
                        message={tabState.error}
                        type="error"
                        showIcon
                        closable
                        style={{ fontSize: 12 }}
                        description={engine === 'llm' ? 'Try switching to the Fast engine for instant results.' : undefined}
                    />
                </div>
            )}

            {/* Expandable suggestions list */}
            {hasSuggestions && !tabState.loading && expanded && (
                <div
                    style={{
                        borderTop: '1px solid rgba(15, 56, 106, 0.12)',
                        maxHeight: 250,
                        overflowY: 'auto',
                        padding: '8px 10px',
                    }}
                >
                    {tabState.suggestions.map((suggestion: SuggestionItem) => (
                        <div
                            key={suggestion.item_id}
                            onClick={() => handleSelectOne(suggestion.item_id)}
                            style={{
                                padding: '7px 10px',
                                marginBottom: 4,
                                borderRadius: 6,
                                cursor: 'pointer',
                                transition: 'all 0.15s ease',
                                display: 'flex',
                                alignItems: 'center',
                                gap: 8,
                                background: '#fff',
                                border: '1px solid #f0f0f0',
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.borderColor = '#0f386a';
                                e.currentTarget.style.background = 'rgba(15, 56, 106, 0.06)';
                                e.currentTarget.style.transform = 'translateX(2px)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.borderColor = '#f0f0f0';
                                e.currentTarget.style.background = '#fff';
                                e.currentTarget.style.transform = 'translateX(0)';
                            }}
                        >
                            <Tag
                                color={confidenceTagColor(suggestion.confidence)}
                                style={{ minWidth: 42, textAlign: 'center', margin: 0, fontSize: 11, fontWeight: 600 }}
                            >
                                {suggestion.confidence}%
                            </Tag>
                            <div
                                style={{
                                    width: 3,
                                    height: 18,
                                    borderRadius: 2,
                                    backgroundColor: confidenceColor(suggestion.confidence),
                                    flexShrink: 0,
                                }}
                            />
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <Text ellipsis style={{ fontSize: 12, fontWeight: 500 }}>
                                    {suggestion.display_name}
                                </Text>
                            </div>
                            <Tooltip title={suggestion.reasoning} placement="left">
                                <Text
                                    style={{
                                        fontSize: 11,
                                        color: '#8c8c8c',
                                        whiteSpace: 'nowrap',
                                        maxWidth: 180,
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                    }}
                                >
                                    {suggestion.reasoning}
                                </Text>
                            </Tooltip>
                        </div>
                    ))}
                </div>
            )}

            {/* Collapsed summary when results exist but panel is collapsed */}
            {hasSuggestions && !tabState.loading && !expanded && (
                <div
                    style={{
                        borderTop: '1px solid rgba(15, 56, 106, 0.12)',
                        padding: '6px 14px',
                        display: 'flex',
                        gap: 6,
                        alignItems: 'center',
                        flexWrap: 'wrap',
                        cursor: 'pointer',
                    }}
                    onClick={() => setExpanded(true)}
                >
                    {tabState.suggestions.slice(0, 5).map((s: SuggestionItem) => (
                        <Tag
                            key={s.item_id}
                            color={confidenceTagColor(s.confidence)}
                            style={{ fontSize: 11, margin: 0, cursor: 'pointer' }}
                        >
                            {s.confidence}% {s.display_name.length > 20 ? s.display_name.substring(0, 20) + '...' : s.display_name}
                        </Tag>
                    ))}
                    {tabState.suggestions.length > 5 && (
                        <Text style={{ fontSize: 11, color: '#8c8c8c' }}>
                            +{tabState.suggestions.length - 5} more
                        </Text>
                    )}
                </div>
            )}

            {/* Empty initial state — nothing shown, the CTA button is enough */}
            {!hasSuggestions && !tabState.loading && !tabState.error && (
                <div style={{ display: 'none' }} />
            )}
        </div>
    );
};

export default SuggestionPanel;
