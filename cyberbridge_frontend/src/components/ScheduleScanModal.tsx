// ScheduleScanModal.tsx
import { useState, useEffect } from 'react';
import { Modal, InputNumber, Select, Space, Radio, TimePicker, Checkbox, notification } from 'antd';
import { ScheduleOutlined } from '@ant-design/icons';
import useScanScheduleStore from '../store/useScanScheduleStore';
import type { ScanScheduleCreateData, ScanScheduleUpdateData, ScanSchedule } from '../store/useScanScheduleStore';
import dayjs from 'dayjs';

interface ScheduleScanModalProps {
    open: boolean;
    onClose: () => void;
    scannerType: string;
    scanTarget: string;
    scanType?: string;
    scanConfig?: Record<string, any>;
    editingSchedule?: ScanSchedule | null;
}

const DAYS_OF_WEEK = [
    { label: 'Mon', value: 'mon' },
    { label: 'Tue', value: 'tue' },
    { label: 'Wed', value: 'wed' },
    { label: 'Thu', value: 'thu' },
    { label: 'Fri', value: 'fri' },
    { label: 'Sat', value: 'sat' },
    { label: 'Sun', value: 'sun' },
];

const ScheduleScanModal = ({
    open,
    onClose,
    scannerType,
    scanTarget,
    scanType,
    scanConfig,
    editingSchedule
}: ScheduleScanModalProps) => {
    const { createSchedule, updateSchedule, fetchSchedules } = useScanScheduleStore();
    const [api, contextHolder] = notification.useNotification();
    const [saving, setSaving] = useState(false);

    // Schedule type
    const [scheduleType, setScheduleType] = useState<'interval' | 'cron'>('interval');

    // Interval fields
    const [months, setMonths] = useState(0);
    const [days, setDays] = useState(0);
    const [hours, setHours] = useState(1);
    const [minutes, setMinutes] = useState(0);
    const [seconds, setSeconds] = useState(0);

    // Cron fields
    const [cronDays, setCronDays] = useState<string[]>([]);
    const [cronHour, setCronHour] = useState(0);
    const [cronMinute, setCronMinute] = useState(0);

    // Populate fields from editingSchedule
    useEffect(() => {
        if (editingSchedule) {
            setScheduleType(editingSchedule.schedule_type as 'interval' | 'cron');
            setMonths(editingSchedule.interval_months);
            setDays(editingSchedule.interval_days);
            setHours(editingSchedule.interval_hours);
            setMinutes(editingSchedule.interval_minutes);
            setSeconds(editingSchedule.interval_seconds);
            if (editingSchedule.cron_day_of_week) {
                setCronDays(editingSchedule.cron_day_of_week === '*' ? [] : editingSchedule.cron_day_of_week.split(','));
            } else {
                setCronDays([]);
            }
            setCronHour(editingSchedule.cron_hour ?? 0);
            setCronMinute(editingSchedule.cron_minute ?? 0);
        } else {
            // Reset to defaults
            setScheduleType('interval');
            setMonths(0);
            setDays(0);
            setHours(1);
            setMinutes(0);
            setSeconds(0);
            setCronDays([]);
            setCronHour(0);
            setCronMinute(0);
        }
    }, [editingSchedule, open]);

    const handleSave = async () => {
        // Validate
        if (scheduleType === 'interval') {
            const total = months * 30 * 86400 + days * 86400 + hours * 3600 + minutes * 60 + seconds;
            if (total <= 0) {
                api.error({ message: 'Invalid Schedule', description: 'Interval must be greater than 0.' });
                return;
            }
        }

        setSaving(true);

        if (editingSchedule) {
            // Update existing
            const updateData: ScanScheduleUpdateData = {
                schedule_type: scheduleType,
                interval_months: months,
                interval_days: days,
                interval_hours: hours,
                interval_minutes: minutes,
                interval_seconds: seconds,
                cron_day_of_week: scheduleType === 'cron' ? (cronDays.length > 0 ? cronDays.join(',') : '*') : undefined,
                cron_hour: scheduleType === 'cron' ? cronHour : undefined,
                cron_minute: scheduleType === 'cron' ? cronMinute : undefined,
            };

            const result = await updateSchedule(editingSchedule.id, updateData);
            if (result) {
                api.success({ message: 'Schedule Updated', description: 'Scan schedule has been updated.' });
                await fetchSchedules();
                onClose();
            } else {
                api.error({ message: 'Update Failed', description: 'Failed to update schedule.' });
            }
        } else {
            // Create new
            const createData: ScanScheduleCreateData = {
                scanner_type: scannerType,
                scan_target: scanTarget,
                scan_type: scanType,
                scan_config: scanConfig ? JSON.stringify(scanConfig) : undefined,
                schedule_type: scheduleType,
                interval_months: months,
                interval_days: days,
                interval_hours: hours,
                interval_minutes: minutes,
                interval_seconds: seconds,
                cron_day_of_week: scheduleType === 'cron' ? (cronDays.length > 0 ? cronDays.join(',') : '*') : undefined,
                cron_hour: scheduleType === 'cron' ? cronHour : undefined,
                cron_minute: scheduleType === 'cron' ? cronMinute : undefined,
                is_enabled: true,
            };

            const result = await createSchedule(createData);
            if (result) {
                api.success({ message: 'Schedule Created', description: 'Scan schedule has been created and enabled.' });
                await fetchSchedules();
                onClose();
            } else {
                api.error({ message: 'Creation Failed', description: 'Failed to create schedule.' });
            }
        }

        setSaving(false);
    };

    const formatSummary = () => {
        if (scheduleType === 'interval') {
            const parts: string[] = [];
            if (months > 0) parts.push(`${months} month${months > 1 ? 's' : ''}`);
            if (days > 0) parts.push(`${days} day${days > 1 ? 's' : ''}`);
            if (hours > 0) parts.push(`${hours} hour${hours > 1 ? 's' : ''}`);
            if (minutes > 0) parts.push(`${minutes} minute${minutes > 1 ? 's' : ''}`);
            if (seconds > 0) parts.push(`${seconds} second${seconds > 1 ? 's' : ''}`);
            return parts.length > 0 ? `Repeat every ${parts.join(', ')}` : 'No interval set';
        } else {
            const dayLabels = cronDays.length > 0
                ? cronDays.map(d => d.charAt(0).toUpperCase() + d.slice(1)).join(', ')
                : 'Every day';
            return `${dayLabels} at ${String(cronHour).padStart(2, '0')}:${String(cronMinute).padStart(2, '0')}`;
        }
    };

    return (
        <>
            {contextHolder}
            <Modal
                title={
                    <Space>
                        <ScheduleOutlined />
                        <span>{editingSchedule ? 'Edit Scan Schedule' : 'Schedule Recurring Scan'}</span>
                    </Space>
                }
                open={open}
                onOk={handleSave}
                onCancel={onClose}
                confirmLoading={saving}
                okText={editingSchedule ? 'Update Schedule' : 'Create Schedule'}
                width={520}
            >
                <div style={{ marginBottom: 16 }}>
                    <div style={{ marginBottom: 8, color: '#666', fontSize: 12 }}>Scanner</div>
                    <div style={{ fontWeight: 500 }}>{scannerType.toUpperCase()} {scanType ? `(${scanType})` : ''}</div>
                    <div style={{ color: '#888', fontSize: 12, marginTop: 4 }}>Target: {scanTarget}</div>
                </div>

                <div style={{ marginBottom: 16 }}>
                    <div style={{ marginBottom: 8, fontWeight: 500 }}>Schedule Type</div>
                    <Radio.Group
                        value={scheduleType}
                        onChange={e => setScheduleType(e.target.value)}
                        optionType="button"
                        buttonStyle="solid"
                    >
                        <Radio.Button value="interval">Repeat Interval</Radio.Button>
                        <Radio.Button value="cron">Day & Time</Radio.Button>
                    </Radio.Group>
                </div>

                {scheduleType === 'interval' ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        <div style={{ marginBottom: 4, fontWeight: 500 }}>Repeat Every</div>
                        <Space wrap>
                            <div>
                                <div style={{ fontSize: 11, color: '#888', marginBottom: 2 }}>Months</div>
                                <InputNumber min={0} max={12} value={months} onChange={v => setMonths(v ?? 0)} style={{ width: 80 }} />
                            </div>
                            <div>
                                <div style={{ fontSize: 11, color: '#888', marginBottom: 2 }}>Days</div>
                                <InputNumber min={0} max={365} value={days} onChange={v => setDays(v ?? 0)} style={{ width: 80 }} />
                            </div>
                            <div>
                                <div style={{ fontSize: 11, color: '#888', marginBottom: 2 }}>Hours</div>
                                <InputNumber min={0} max={23} value={hours} onChange={v => setHours(v ?? 0)} style={{ width: 80 }} />
                            </div>
                            <div>
                                <div style={{ fontSize: 11, color: '#888', marginBottom: 2 }}>Minutes</div>
                                <InputNumber min={0} max={59} value={minutes} onChange={v => setMinutes(v ?? 0)} style={{ width: 80 }} />
                            </div>
                            <div>
                                <div style={{ fontSize: 11, color: '#888', marginBottom: 2 }}>Seconds</div>
                                <InputNumber min={0} max={59} value={seconds} onChange={v => setSeconds(v ?? 0)} style={{ width: 80 }} />
                            </div>
                        </Space>
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        <div>
                            <div style={{ marginBottom: 8, fontWeight: 500 }}>Day(s) of Week</div>
                            <Checkbox.Group
                                options={DAYS_OF_WEEK}
                                value={cronDays}
                                onChange={(vals) => setCronDays(vals as string[])}
                            />
                            <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>
                                Leave empty for every day
                            </div>
                        </div>
                        <div>
                            <div style={{ marginBottom: 8, fontWeight: 500 }}>At Time</div>
                            <TimePicker
                                format="HH:mm"
                                value={dayjs().hour(cronHour).minute(cronMinute)}
                                onChange={(time) => {
                                    if (time) {
                                        setCronHour(time.hour());
                                        setCronMinute(time.minute());
                                    }
                                }}
                            />
                        </div>
                    </div>
                )}

                <div style={{
                    marginTop: 20,
                    padding: '10px 14px',
                    background: '#f6f8fa',
                    borderRadius: 6,
                    border: '1px solid #e8e8e8',
                    fontSize: 13
                }}>
                    <strong>Summary:</strong> {formatSummary()}
                </div>
            </Modal>
        </>
    );
};

export default ScheduleScanModal;
