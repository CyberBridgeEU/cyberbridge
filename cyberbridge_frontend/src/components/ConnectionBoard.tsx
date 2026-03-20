import React, { useState, useMemo } from 'react';
import { Card, Checkbox, Input, Button, Empty, Tag, Tooltip, Row, Col, Spin, Typography } from 'antd';
import { SearchOutlined, RightOutlined, LeftOutlined, LinkOutlined, DisconnectOutlined } from '@ant-design/icons';

const { Text } = Typography;

// Generic item interface that all linked items should conform to
interface BaseItem {
    id: string;
    [key: string]: unknown;
}

interface ConnectionBoardProps<T extends BaseItem, U extends BaseItem> {
    // Title and labels
    title: string;
    sourceLabel: string;  // e.g., "Asset"
    targetLabel: string;  // e.g., "Risk"
    relationshipLabel: string;  // e.g., "exposed to" -> "Asset exposed to Risk"
    itemLabel?: string;  // Optional label for list items (e.g., "Asset" or "Control")
    headerContent?: React.ReactNode;

    // Data
    availableItems: T[];
    linkedItems: U[];
    loading?: boolean;

    // Display configuration
    getItemDisplayName: (item: T | U) => string;
    getItemDescription?: (item: T | U) => string | null;
    getItemTags?: (item: T | U) => { label: string; color: string }[];
    getItemIcon?: (item: T | U) => React.ReactNode;

    // Actions
    onLink: (itemIds: string[]) => Promise<void>;
    onUnlink: (itemIds: string[]) => Promise<void>;

    // External selection (for AI suggestion integration)
    externalSelectedAvailable?: string[];
    onExternalSelectAvailable?: (ids: string[]) => void;

    // Optional styling
    height?: number | string;
}

function ConnectionBoard<T extends BaseItem, U extends BaseItem>({
    title,
    sourceLabel,
    targetLabel,
    relationshipLabel,
    itemLabel,
    headerContent,
    availableItems,
    linkedItems,
    loading = false,
    getItemDisplayName,
    getItemDescription,
    getItemTags,
    getItemIcon,
    onLink,
    onUnlink,
    externalSelectedAvailable,
    onExternalSelectAvailable,
    height = 400,
}: ConnectionBoardProps<T, U>) {
    const listLabel = itemLabel ?? targetLabel;
    // State
    const [availableSearch, setAvailableSearch] = useState('');
    const [linkedSearch, setLinkedSearch] = useState('');
    const [internalSelectedAvailable, setInternalSelectedAvailable] = useState<string[]>([]);
    const [selectedLinked, setSelectedLinked] = useState<string[]>([]);
    const [actionLoading, setActionLoading] = useState(false);

    // Merge internal + external selection for available items
    const selectedAvailable = useMemo(() => {
        if (!externalSelectedAvailable || externalSelectedAvailable.length === 0) return internalSelectedAvailable;
        const merged = new Set([...internalSelectedAvailable, ...externalSelectedAvailable]);
        return Array.from(merged);
    }, [internalSelectedAvailable, externalSelectedAvailable]);

    const setSelectedAvailable = (updater: string[] | ((prev: string[]) => string[])) => {
        if (typeof updater === 'function') {
            setInternalSelectedAvailable(updater);
        } else {
            setInternalSelectedAvailable(updater);
        }
        // Also notify external handler if present
        if (onExternalSelectAvailable) {
            onExternalSelectAvailable([]);
        }
    };

    // Get linked item IDs
    const linkedIds = useMemo(() => new Set(linkedItems.map(item => item.id)), [linkedItems]);

    // Filter available items (exclude already linked)
    const filteredAvailable = useMemo(() => {
        return availableItems
            .filter(item => !linkedIds.has(item.id))
            .filter(item => {
                if (!availableSearch) return true;
                const name = getItemDisplayName(item).toLowerCase();
                const desc = getItemDescription?.(item)?.toLowerCase() || '';
                const searchLower = availableSearch.toLowerCase();
                return name.includes(searchLower) || desc.includes(searchLower);
            });
    }, [availableItems, linkedIds, availableSearch, getItemDisplayName, getItemDescription]);

    // Filter linked items
    const filteredLinked = useMemo(() => {
        return linkedItems.filter(item => {
            if (!linkedSearch) return true;
            const name = getItemDisplayName(item).toLowerCase();
            const desc = getItemDescription?.(item)?.toLowerCase() || '';
            const searchLower = linkedSearch.toLowerCase();
            return name.includes(searchLower) || desc.includes(searchLower);
        });
    }, [linkedItems, linkedSearch, getItemDisplayName, getItemDescription]);

    // Handle link action
    const handleLink = async () => {
        if (selectedAvailable.length === 0) return;
        setActionLoading(true);
        try {
            await onLink(selectedAvailable);
            setSelectedAvailable([]);
        } finally {
            setActionLoading(false);
        }
    };

    // Handle unlink action
    const handleUnlink = async () => {
        if (selectedLinked.length === 0) return;
        setActionLoading(true);
        try {
            await onUnlink(selectedLinked);
            setSelectedLinked([]);
        } finally {
            setActionLoading(false);
        }
    };

    // Toggle selection for available items
    const toggleAvailableSelection = (id: string) => {
        setSelectedAvailable(prev =>
            prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
        );
    };

    // Toggle selection for linked items
    const toggleLinkedSelection = (id: string) => {
        setSelectedLinked(prev =>
            prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
        );
    };

    // Select all available
    const selectAllAvailable = () => {
        if (selectedAvailable.length === filteredAvailable.length) {
            setSelectedAvailable([]);
        } else {
            setSelectedAvailable(filteredAvailable.map(item => item.id));
        }
    };

    // Select all linked
    const selectAllLinked = () => {
        if (selectedLinked.length === filteredLinked.length) {
            setSelectedLinked([]);
        } else {
            setSelectedLinked(filteredLinked.map(item => item.id));
        }
    };

    // Render item card
    const renderItem = (item: T | U, isSelected: boolean, onToggle: () => void) => {
        const tags = getItemTags?.(item) || [];
        const icon = getItemIcon?.(item);
        const description = getItemDescription?.(item);

        return (
            <div
                key={item.id}
                onClick={onToggle}
                style={{
                    padding: '10px 12px',
                    marginBottom: 8,
                    border: `1.5px solid ${isSelected ? '#0f386a' : '#e8e8e8'}`,
                    borderRadius: 6,
                    backgroundColor: isSelected ? 'rgba(15, 56, 106, 0.05)' : '#fff',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                }}
                onMouseEnter={(e) => {
                    if (!isSelected) {
                        e.currentTarget.style.borderColor = '#bfbfbf';
                    }
                }}
                onMouseLeave={(e) => {
                    if (!isSelected) {
                        e.currentTarget.style.borderColor = '#e8e8e8';
                    }
                }}
            >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                    <Checkbox checked={isSelected} style={{ marginTop: 2 }} />
                    {icon && <span style={{ fontSize: 18, marginTop: 2 }}>{icon}</span>}
                    <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontWeight: 500, fontSize: 13, marginBottom: 4 }}>
                            {getItemDisplayName(item)}
                        </div>
                        {description && (
                            <Tooltip title={description}>
                                <Text
                                    ellipsis
                                    style={{ fontSize: 12, color: '#666', display: 'block' }}
                                >
                                    {description}
                                </Text>
                            </Tooltip>
                        )}
                        {tags.length > 0 && (
                            <div style={{ marginTop: 6, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                                {tags.map((tag, index) => (
                                    <Tag key={index} color={tag.color} style={{ fontSize: 11, margin: 0, padding: '0 6px' }}>
                                        {tag.label}
                                    </Tag>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <Card
            title={
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <LinkOutlined style={{ color: '#0f386a' }} />
                    <span>{title}</span>
                </div>
            }
            size="small"
            style={{ height: '100%' }}
            styles={{ body: { padding: 16 } }}
        >
            {/* Relationship label */}
            <div
                style={{
                    textAlign: 'center',
                    marginBottom: 16,
                    padding: '8px 16px',
                    background: 'linear-gradient(135deg, rgba(26, 54, 93, 0.05), rgba(15, 56, 106, 0.1))',
                    borderRadius: 6,
                    fontSize: 13,
                    color: '#1a365d',
                }}
            >
                <strong>{sourceLabel}</strong>
                <span style={{ margin: '0 8px', color: '#0f386a' }}>{relationshipLabel}</span>
                <strong>{targetLabel}</strong>
            </div>
            {headerContent && (
                <div style={{ marginBottom: 12 }}>
                    {headerContent}
                </div>
            )}

            <Spin spinning={loading || actionLoading}>
                <Row gutter={16}>
                    {/* Available Items Panel */}
                    <Col span={11}>
                        <div style={{ marginBottom: 12 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                <Text strong style={{ fontSize: 13, color: '#1a365d' }}>
                                    Available {listLabel}s ({filteredAvailable.length})
                                </Text>
                                {filteredAvailable.length > 0 && (
                                    <Button
                                        type="link"
                                        size="small"
                                        onClick={selectAllAvailable}
                                        style={{ padding: 0, fontSize: 12 }}
                                    >
                                        {selectedAvailable.length === filteredAvailable.length ? 'Deselect All' : 'Select All'}
                                    </Button>
                                )}
                            </div>
                            <Input
                                placeholder={`Search available ${listLabel.toLowerCase()}s...`}
                                prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                                value={availableSearch}
                                onChange={(e) => setAvailableSearch(e.target.value)}
                                allowClear
                                size="small"
                            />
                        </div>
                        <div
                            style={{
                                height: typeof height === 'number' ? height : height,
                                overflowY: 'auto',
                                border: '1px solid #f0f0f0',
                                borderRadius: 6,
                                padding: 8,
                                backgroundColor: '#fafafa',
                            }}
                        >
                            {filteredAvailable.length === 0 ? (
                                <Empty
                                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                                    description={
                                        availableSearch
                                            ? `No ${listLabel.toLowerCase()}s match your search`
                                            : `No available ${listLabel.toLowerCase()}s`
                                    }
                                    style={{ marginTop: 60 }}
                                />
                            ) : (
                                filteredAvailable.map(item =>
                                    renderItem(
                                        item,
                                        selectedAvailable.includes(item.id),
                                        () => toggleAvailableSelection(item.id)
                                    )
                                )
                            )}
                        </div>
                    </Col>

                    {/* Action Buttons Column */}
                    <Col span={2} style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: 12 }}>
                        <Tooltip title={`Link selected ${listLabel.toLowerCase()}s`}>
                            <Button
                                type="primary"
                                icon={<RightOutlined />}
                                onClick={handleLink}
                                disabled={selectedAvailable.length === 0}
                                style={{
                                    background: selectedAvailable.length > 0 ? 'linear-gradient(135deg, #1a365d, #0f386a)' : undefined,
                                    border: 'none',
                                }}
                            >
                                Link
                            </Button>
                        </Tooltip>
                        <Tooltip title={`Unlink selected ${listLabel.toLowerCase()}s`}>
                            <Button
                                danger
                                icon={<LeftOutlined />}
                                onClick={handleUnlink}
                                disabled={selectedLinked.length === 0}
                            >
                                Unlink
                            </Button>
                        </Tooltip>
                    </Col>

                    {/* Linked Items Panel */}
                    <Col span={11}>
                        <div style={{ marginBottom: 12 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                <Text strong style={{ fontSize: 13, color: '#1a365d' }}>
                                    Linked {listLabel}s ({filteredLinked.length})
                                </Text>
                                {filteredLinked.length > 0 && (
                                    <Button
                                        type="link"
                                        size="small"
                                        onClick={selectAllLinked}
                                        style={{ padding: 0, fontSize: 12 }}
                                    >
                                        {selectedLinked.length === filteredLinked.length ? 'Deselect All' : 'Select All'}
                                    </Button>
                                )}
                            </div>
                            <Input
                                placeholder={`Search linked ${listLabel.toLowerCase()}s...`}
                                prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                                value={linkedSearch}
                                onChange={(e) => setLinkedSearch(e.target.value)}
                                allowClear
                                size="small"
                            />
                        </div>
                        <div
                            style={{
                                height: typeof height === 'number' ? height : height,
                                overflowY: 'auto',
                                border: '1px solid #f0f0f0',
                                borderRadius: 6,
                                padding: 8,
                                backgroundColor: '#fafafa',
                            }}
                        >
                            {filteredLinked.length === 0 ? (
                                <Empty
                                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                                    description={
                                        linkedSearch
                                            ? `No ${listLabel.toLowerCase()}s match your search`
                                            : (
                                                <span>
                                                    <DisconnectOutlined style={{ fontSize: 24, display: 'block', marginBottom: 8, color: '#bfbfbf' }} />
                                                    No {listLabel.toLowerCase()}s linked yet
                                                </span>
                                            )
                                    }
                                    style={{ marginTop: 60 }}
                                />
                            ) : (
                                filteredLinked.map(item =>
                                    renderItem(
                                        item,
                                        selectedLinked.includes(item.id),
                                        () => toggleLinkedSelection(item.id)
                                    )
                                )
                            )}
                        </div>
                    </Col>
                </Row>
            </Spin>

            {/* Selection Summary */}
            {(selectedAvailable.length > 0 || selectedLinked.length > 0) && (
                <div
                    style={{
                        marginTop: 16,
                        padding: '8px 12px',
                        background: '#f5f5f5',
                        borderRadius: 6,
                        fontSize: 12,
                        color: '#666',
                        textAlign: 'center',
                    }}
                >
                    {selectedAvailable.length > 0 && (
                        <span style={{ marginRight: 16 }}>
                            <LinkOutlined style={{ marginRight: 4 }} />
                            {selectedAvailable.length} {listLabel.toLowerCase()}(s) selected to link
                        </span>
                    )}
                    {selectedLinked.length > 0 && (
                        <span>
                            <DisconnectOutlined style={{ marginRight: 4 }} />
                            {selectedLinked.length} {listLabel.toLowerCase()}(s) selected to unlink
                        </span>
                    )}
                </div>
            )}
        </Card>
    );
}

export default ConnectionBoard;
