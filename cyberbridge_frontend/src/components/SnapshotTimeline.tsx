import React, { useEffect, useState } from 'react';
import { Timeline, Button, Tag, notification, Typography, Popconfirm, Empty } from 'antd';
import { HistoryOutlined, RollbackOutlined } from '@ant-design/icons';
import useRegulatoryMonitorStore from '../store/useRegulatoryMonitorStore';
import InfoTitle from './InfoTitle';

const { Text } = Typography;

interface SnapshotTimelineProps {
    frameworkId: string;
}

const SnapshotTimeline: React.FC<SnapshotTimelineProps> = ({ frameworkId }) => {
    const { snapshots, fetchSnapshots, revertToSnapshot, loading } = useRegulatoryMonitorStore();
    const [reverting, setReverting] = useState<string | null>(null);

    useEffect(() => {
        if (frameworkId) {
            fetchSnapshots(frameworkId);
        }
    }, [frameworkId]);

    const handleRevert = async (snapshotId: string) => {
        setReverting(snapshotId);
        const success = await revertToSnapshot(frameworkId, snapshotId);
        setReverting(null);
        if (success) {
            notification.success({
                message: 'Framework Reverted',
                description: 'Successfully reverted to the selected snapshot. A safety snapshot was created automatically.'
            });
            fetchSnapshots(frameworkId);
        } else {
            notification.error({ message: 'Revert Failed', description: 'Failed to revert to snapshot' });
        }
    };

    const getTypeColor = (type: string) => {
        return type === 'pre_update' ? '#1a365d' : '#faad14';
    };

    const getTypeTag = (type: string) => {
        return type === 'pre_update'
            ? <Tag color="blue">Pre-Update</Tag>
            : <Tag color="orange">Pre-Revert</Tag>;
    };

    return (
        <>
            <InfoTitle
                title="Snapshots & History"
                infoContent="View the history of framework snapshots created before updates and reverts. You can revert to any previous snapshot to restore the framework state."
                className="section-title"
            />

            {snapshots.length === 0 ? (
                <Empty
                    description="No snapshots yet. Snapshots are created automatically when updates are applied."
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
            ) : (
                <Timeline
                    style={{ marginTop: 16, paddingLeft: 4 }}
                    items={snapshots.map(snapshot => ({
                        color: getTypeColor(snapshot.snapshot_type),
                        children: (
                            <div style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '4px 0'
                            }}>
                                <div>
                                    {getTypeTag(snapshot.snapshot_type)}
                                    <Text strong> Version {snapshot.update_version}</Text>
                                    <Text type="secondary" style={{ marginLeft: 8 }}>
                                        {snapshot.created_at
                                            ? new Date(snapshot.created_at).toLocaleString()
                                            : 'N/A'}
                                    </Text>
                                </div>
                                <Popconfirm
                                    title="Revert to this snapshot?"
                                    description="This will create a safety snapshot first, then restore the framework to this state."
                                    onConfirm={() => handleRevert(snapshot.id)}
                                    okText="Revert"
                                    cancelText="Cancel"
                                    okButtonProps={{ danger: true }}
                                >
                                    <Button
                                        size="small"
                                        icon={<RollbackOutlined />}
                                        loading={reverting === snapshot.id}
                                        style={{ borderColor: '#1a365d', color: '#1a365d' }}
                                    >
                                        Revert
                                    </Button>
                                </Popconfirm>
                            </div>
                        )
                    }))}
                />
            )}
        </>
    );
};

export default SnapshotTimeline;
