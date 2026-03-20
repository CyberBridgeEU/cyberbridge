import React, { useEffect, useState } from 'react';
import { Table, Select, Space, Typography, Tag, Spin, Alert, MenuProps, Button, Tooltip, notification, DatePicker } from 'antd';
import { HistoryOutlined, UserOutlined, ClockCircleOutlined, ReloadOutlined, FileTextOutlined, DeleteOutlined, ExclamationCircleOutlined, BarChartOutlined, LineChartOutlined, TeamOutlined } from '@ant-design/icons';
import { useHistoryStore, HistoryEntry } from '../store/historyStore';
import useAuthStore from '../store/useAuthStore';
import useUserStore from '../store/useUserStore';
import type { ColumnsType } from 'antd/es/table';
import Sidebar from '../components/Sidebar';
import InfoTitle from '../components/InfoTitle';
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import { Chart } from 'react-google-charts';

const { Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

const HistoryAreaPage: React.FC = () => {
  const [location] = useLocation();
  const menuHighlighting = useMenuHighlighting(location);
  const {
    historyEntries,
    loading,
    error,
    fetchHistory,
    clearError
  } = useHistoryStore();

  const { user, getAuthHeader } = useAuthStore();
  const { current_user, fetchCurrentUser } = useUserStore();

  // Active tab state
  const [activeTab, setActiveTab] = useState<'audit' | 'sessions'>('audit');

  // Filter states
  const [tableFilter, setTableFilter] = useState<string>('all');
  const [actionFilter, setActionFilter] = useState<string>('all');

  // Organization selector for Clear All functionality
  const [selectedOrgIdForClearAll, setSelectedOrgIdForClearAll] = useState<string>('');
  const [allOrganisationsForClearAll, setAllOrganisationsForClearAll] = useState<any[]>([]);
  const [clearingHistory, setClearingHistory] = useState<boolean>(false);

  // User sessions state (super_admin only)
  const [userSessions, setUserSessions] = useState<any[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [visitsPerEmail, setVisitsPerEmail] = useState<any[]>([]);
  const [totalVisits, setTotalVisits] = useState(0);
  const [totalPdfDownloads, setTotalPdfDownloads] = useState(0);
  const [downloadsPerType, setDownloadsPerType] = useState<any[]>([]);
  const [dateRange, setDateRange] = useState<[any, any] | null>(null);

  // Online users state
  const [onlineUsers, setOnlineUsers] = useState<any[]>([]);
  const [loadingOnlineUsers, setLoadingOnlineUsers] = useState(false);

  // Initialize notification API
  const [api, contextHolder] = notification.useNotification();

  // Determine if user is super_admin
  const isSuperAdmin = current_user?.role_name === 'super_admin';

  useEffect(() => {
    // Fetch current user data if not already loaded
    if (!current_user || !current_user.role_name) {
      fetchCurrentUser();
    }
    // Fetch history on component mount
    fetchHistory();
  }, [fetchCurrentUser, fetchHistory]);

  useEffect(() => {
    if (error) {
      clearError();
    }
  }, [error, clearError]);

  // Initialize organization selector based on user role
  useEffect(() => {
    if (current_user) {
      if (current_user.role_name === 'super_admin') {
        // Fetch all organizations for super_admin
        fetchAllOrganisationsForClearAll();
      } else if (current_user.role_name === 'org_admin') {
        // For org_admin, set their own organization
        setSelectedOrgIdForClearAll(current_user.organisation_id || '');
      }
    }
  }, [current_user]);

  // Fetch online users
  const fetchOnlineUsers = async () => {
    setLoadingOnlineUsers(true);
    try {
      const authHeader = getAuthHeader();
      const response = await fetch(`${cyberbridge_back_end_rest_api}/admin/online-users`, {
        headers: {
          'Content-Type': 'application/json',
          ...authHeader
        }
      });

      if (response.ok) {
        const data = await response.json();
        setOnlineUsers(data);
      }
    } catch (error) {
      console.error('Error fetching online users:', error);
    } finally {
      setLoadingOnlineUsers(false);
    }
  };

  // Poll for online users every 20 seconds when on sessions tab
  useEffect(() => {
    if (activeTab === 'sessions') {
      fetchOnlineUsers();
      const interval = setInterval(() => {
        fetchOnlineUsers();
      }, 20000);
      return () => clearInterval(interval);
    }
  }, [activeTab]);

  // Fetch user sessions (super_admin only)
  const fetchUserSessions = async () => {
    if (!isSuperAdmin) return;

    setLoadingSessions(true);
    try {
      const authHeader = getAuthHeader();

      let queryParams = '';
      if (dateRange && dateRange[0] && dateRange[1]) {
        const fromDate = dateRange[0].toISOString();
        const toDate = dateRange[1].toISOString();
        queryParams = `?from_date=${encodeURIComponent(fromDate)}&to_date=${encodeURIComponent(toDate)}`;
      }

      const [sessionsRes, visitsRes, totalRes, pdfDownloadsRes, downloadsPerTypeRes] = await Promise.all([
        fetch(`${cyberbridge_back_end_rest_api}/admin/user-sessions${queryParams}`, {
          headers: { 'Content-Type': 'application/json', ...authHeader }
        }),
        fetch(`${cyberbridge_back_end_rest_api}/admin/visits-per-email${queryParams}`, {
          headers: { 'Content-Type': 'application/json', ...authHeader }
        }),
        fetch(`${cyberbridge_back_end_rest_api}/admin/total-visits${queryParams}`, {
          headers: { 'Content-Type': 'application/json', ...authHeader }
        }),
        fetch(`${cyberbridge_back_end_rest_api}/admin/total-pdf-downloads${queryParams}`, {
          headers: { 'Content-Type': 'application/json', ...authHeader }
        }),
        fetch(`${cyberbridge_back_end_rest_api}/admin/pdf-downloads-per-type${queryParams}`, {
          headers: { 'Content-Type': 'application/json', ...authHeader }
        })
      ]);

      if (sessionsRes.ok) {
        const sessionsData = await sessionsRes.json();
        setUserSessions(sessionsData);
      }

      if (visitsRes.ok) {
        const visitsData = await visitsRes.json();
        setVisitsPerEmail(visitsData);
      }

      if (totalRes.ok) {
        const totalData = await totalRes.json();
        setTotalVisits(totalData.total_visits || 0);
      }

      if (pdfDownloadsRes.ok) {
        const pdfData = await pdfDownloadsRes.json();
        setTotalPdfDownloads(pdfData.total_pdf_downloads || 0);
      }

      if (downloadsPerTypeRes.ok) {
        const downloadsData = await downloadsPerTypeRes.json();
        setDownloadsPerType(downloadsData);
      }
    } catch (error) {
      console.error('Error fetching user sessions:', error);
    } finally {
      setLoadingSessions(false);
    }
  };

  // Fetch sessions on mount and when date range changes (super_admin only)
  useEffect(() => {
    if (isSuperAdmin && activeTab === 'sessions') {
      fetchUserSessions();
    }
  }, [dateRange, isSuperAdmin, activeTab]);

  // Clear all user sessions
  const handleClearAllSessions = async () => {
    try {
      const authHeader = getAuthHeader();
      const response = await fetch(`${cyberbridge_back_end_rest_api}/admin/user-sessions`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          ...authHeader
        }
      });

      if (response.ok) {
        const data = await response.json();
        api.success({
          message: 'Sessions Cleared',
          description: `Successfully deleted ${data.deleted_count} session records`,
          duration: 4,
        });
        fetchUserSessions();
      } else {
        api.error({
          message: 'Failed to Clear Sessions',
          description: 'An error occurred while clearing sessions',
          duration: 4,
        });
      }
    } catch (error) {
      console.error('Error deleting sessions:', error);
      api.error({
        message: 'Failed to Clear Sessions',
        description: 'An error occurred while clearing sessions',
        duration: 4,
      });
    }
  };

  // Calculate time ago
  const getTimeAgo = (lastActivity: string | null) => {
    if (!lastActivity) return 'Never';
    const now = new Date();
    const lastActivityDate = new Date(lastActivity);
    const diffMs = now.getTime() - lastActivityDate.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins === 1) return '1 minute ago';
    if (diffMins < 60) return `${diffMins} minutes ago`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours === 1) return '1 hour ago';
    return `${diffHours} hours ago`;
  };

  const fetchAllOrganisationsForClearAll = async () => {
    try {
      const authHeader = getAuthHeader();
      if (!authHeader) {
        api.error({
          message: 'Authentication Error',
          description: 'Please log in again.'
        });
        return;
      }

      const response = await fetch(`${cyberbridge_back_end_rest_api}/users/get_all_organisations`, {
        headers: {
          'Content-Type': 'application/json',
          ...authHeader
        }
      });
      if (response.ok) {
        const data = await response.json();
        setAllOrganisationsForClearAll(data);
        // Set first organization as default if available
        if (data.length > 0) {
          setSelectedOrgIdForClearAll(data[0].id);
        }
      } else {
        api.error({
          message: 'Failed to Fetch Organizations',
          description: 'Could not load organizations list.'
        });
      }
    } catch (error) {
      console.error('Error fetching organizations:', error);
      api.error({
        message: 'Error',
        description: 'An error occurred while fetching organizations.'
      });
    }
  };

  const handleClearAllHistory = async () => {
    if (!selectedOrgIdForClearAll) {
      api.warning({
        message: 'No Organization Selected',
        description: 'Please select an organization to clear history.'
      });
      return;
    }

    // Get organization name for confirmation message
    const orgName = allOrganisationsForClearAll.find(org => org.id === selectedOrgIdForClearAll)?.name
      || (current_user?.role_name === 'org_admin' && current_user.organisation_name)
      || 'this organization';

    // Use browser confirm dialog
    const confirmed = window.confirm(
      `Are you sure you want to delete ALL history records for ${orgName}?\n\nThis action cannot be undone.`
    );

    if (!confirmed) {
      return;
    }

    setClearingHistory(true);
    try {
      const authHeader = getAuthHeader();
      if (!authHeader) {
        api.error({
          message: 'Authentication Error',
          description: 'Please log in again.'
        });
        setClearingHistory(false);
        return;
      }

      const response = await fetch(
        `${cyberbridge_back_end_rest_api}/history/organization/${selectedOrgIdForClearAll}/clear-all`,
        {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            ...authHeader
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        api.success({
          message: 'History Cleared',
          description: `Successfully cleared ${data.deleted_count} history records for ${orgName}.`
        });
        // Refresh the history list
        fetchHistory(tableFilter, actionFilter);
      } else {
        const errorData = await response.json();
        api.error({
          message: 'Failed to Clear History',
          description: errorData.detail || 'Could not clear history records.'
        });
      }
    } catch (error) {
      console.error('Error clearing history:', error);
      api.error({
        message: 'Error',
        description: 'An error occurred while clearing history.'
      });
    } finally {
      setClearingHistory(false);
    }
  };

  const handleFilterChange = () => {
    fetchHistory(tableFilter, actionFilter);
  };

  const handleRefresh = () => {
    fetchHistory(tableFilter, actionFilter);
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'insert':
        return 'success';
      case 'update':
        return 'processing';
      case 'delete':
        return 'error';
      default:
        return 'default';
    }
  };

  const getTableDisplayName = (tableName: string) => {
    const tableMap: { [key: string]: string } = {
      'products': 'Products',
      'policies': 'Policies',
      'risks': 'Risks',
      'objectives': 'Objectives'
    };
    return tableMap[tableName] || tableName;
  };

  const extractMeaningfulValue = (data: any): string => {
    if (!data) return 'null';

    // If it's a simple value wrapped in an object with 'value' property (UPDATE operations)
    if (data.value !== undefined) {
      return String(data.value);
    }

    // For complex objects (INSERT/DELETE operations), extract key identifying fields
    if (typeof data === 'object') {
      // Try to find meaningful identifying fields in order of priority
      const meaningfulFields = ['name', 'title', 'description', 'status', 'type', 'label', 'email', 'product_name', 'policy_name', 'risk_name'];

      for (const field of meaningfulFields) {
        if (data[field] !== undefined && data[field] !== null) {
          return String(data[field]);
        }
      }

      // If no meaningful field found, show a brief summary of available fields
      const keys = Object.keys(data).filter(key => !['id', 'created_at', 'updated_at', 'organisation_id'].includes(key));
      if (keys.length > 0) {
        const firstKey = keys[0];
        const value = data[firstKey];
        if (typeof value === 'string' || typeof value === 'number') {
          return `${firstKey}: ${String(value)}`;
        }
      }

      // Last resort: show object type info
      return `[Object with ${Object.keys(data).length} fields]`;
    }

    return String(data);
  };

  const formatDataChange = (oldData: any, newData: any, action: string) => {
    if (action === 'insert') {
      const meaningfulValue = extractMeaningfulValue(newData);
      return (
        <div>
          <div>
            <Text type="success">New record created</Text>
          </div>
          <div style={{ marginTop: 4 }}>
            <Text strong style={{ fontSize: 12 }}>
              {meaningfulValue}
            </Text>
          </div>
        </div>
      );
    } else if (action === 'delete') {
      const meaningfulValue = extractMeaningfulValue(oldData);
      return (
        <div>
          <div>
            <Text type="danger">Record deleted</Text>
          </div>
          <div style={{ marginTop: 4 }}>
            <Text strong style={{ fontSize: 12 }}>
              {meaningfulValue}
            </Text>
          </div>
        </div>
      );
    } else if (action === 'update' && oldData && newData) {
      const oldValue = extractMeaningfulValue(oldData);
      const newValue = extractMeaningfulValue(newData);

      return (
        <div>
          <div>
            <Text type="secondary">From: </Text>
            <Text code style={{ fontSize: 12 }}>
              {oldValue}
            </Text>
          </div>
          <div style={{ marginTop: 2 }}>
            <Text type="secondary">To: </Text>
            <Text code style={{ fontSize: 12 }}>
              {newValue}
            </Text>
          </div>
        </div>
      );
    }
    return <Text type="secondary">No data</Text>;
  };

  const columns: ColumnsType<HistoryEntry> = [
    {
      title: 'Timestamp',
      dataIndex: 'last_timestamp',
      key: 'last_timestamp',
      width: 180,
      sorter: (a, b) => new Date(a.last_timestamp).getTime() - new Date(b.last_timestamp).getTime(),
      defaultSortOrder: 'descend',
      render: (timestamp: string) => {
        const date = new Date(timestamp);
        return (
          <Space direction="vertical" size={0}>
            <Text style={{ fontSize: 12 }}>
              {date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
              })}
            </Text>
            <Text type="secondary" style={{ fontSize: 11 }}>
              {date.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
              })}
            </Text>
          </Space>
        );
      },
    },
    {
      title: 'Table',
      dataIndex: 'table_name_changed',
      key: 'table_name_changed',
      width: 120,
      filters: [
        { text: 'Products', value: 'products' },
        { text: 'Policies', value: 'policies' },
        { text: 'Risks', value: 'risks' },
        { text: 'Objectives', value: 'objectives' },
      ],
      onFilter: (value, record) => record.table_name_changed === value,
      render: (table: string) => (
        <Tag icon={<FileTextOutlined />} color="blue">
          {getTableDisplayName(table)}
        </Tag>
      ),
    },
    {
      title: 'Action',
      dataIndex: 'action',
      key: 'action',
      width: 100,
      filters: [
        { text: 'Insert', value: 'insert' },
        { text: 'Update', value: 'update' },
        { text: 'Delete', value: 'delete' },
      ],
      onFilter: (value, record) => record.action === value,
      render: (action: string) => (
        <Tag color={getActionColor(action)}>
          {action.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Record ID',
      dataIndex: 'record_id',
      key: 'record_id',
      width: 120,
      render: (id: string) => (
        <Tooltip title={id}>
          <Text code style={{ fontSize: 11 }}>
            {id.substring(0, 8)}...
          </Text>
        </Tooltip>
      ),
    },
    {
      title: 'Column Changed',
      dataIndex: 'column_name',
      key: 'column_name',
      width: 150,
      render: (column: string | null, record: HistoryEntry) => {
        if (record.action === 'insert') {
          return <Tag color="green">New Record</Tag>;
        } else if (record.action === 'delete') {
          return <Tag color="red">Deleted Record</Tag>;
        }
        return column ? <Text code>{column}</Text> : <Text type="secondary">-</Text>;
      },
    },
    {
      title: 'Data Changes',
      key: 'data_changes',
      width: 300,
      render: (_, record: HistoryEntry) =>
        formatDataChange(record.old_data, record.new_data, record.action),
    },
    {
      title: 'Initial User',
      dataIndex: 'initial_user_email',
      key: 'initial_user_email',
      width: 200,
      render: (email: string | null) => (
        email ? (
          <Space>
            <UserOutlined />
            <Text>{email}</Text>
          </Space>
        ) : (
          <Text type="secondary">-</Text>
        )
      ),
    },
    {
      title: 'Last Modified By',
      dataIndex: 'last_user_email',
      key: 'last_user_email',
      width: 200,
      render: (email: string) => (
        <Space>
          <UserOutlined />
          <Text strong>{email}</Text>
        </Space>
      ),
    },
  ];

  // Sessions table columns
  const sessionsColumns = [
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      sorter: (a: any, b: any) => a.email.localeCompare(b.email),
      render: (email: string) => (
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <UserOutlined />
          {email}
        </span>
      ),
    },
    {
      title: 'Login Timestamp',
      dataIndex: 'login_timestamp',
      key: 'login_timestamp',
      sorter: (a: any, b: any) => new Date(a.login_timestamp).getTime() - new Date(b.login_timestamp).getTime(),
      render: (timestamp: string) => {
        return new Date(timestamp).toLocaleString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        });
      },
    },
    {
      title: 'Logout Timestamp',
      dataIndex: 'logout_timestamp',
      key: 'logout_timestamp',
      render: (timestamp: string | null) => {
        if (!timestamp) {
          return <Tag color="green">Active</Tag>;
        }
        return new Date(timestamp).toLocaleString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        });
      },
    },
  ];

  const onClick: MenuProps['onClick'] = (e) => {
    console.log('click ', e);
  };

  // Check if user has permission to access this page
  if (!current_user || !current_user.role_name || (current_user.role_name !== 'super_admin' && current_user.role_name !== 'org_admin')) {
    return (
      <div>
        {contextHolder}
        <div className={'page-parent'}>
          <Sidebar onClick={onClick} selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange} />
          <div className={'page-content'}>
            <Alert
              message="Access Denied"
              description="You do not have permission to access the Activity Log. Only Super Administrators and Organization Administrators can view this page."
              type="error"
              showIcon
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      {contextHolder}
      <div className={'page-parent'}>
        <Sidebar onClick={onClick} selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange} />
        <div className={'page-content'}>
          {/* Page Header */}
          <div className="page-header">
            <div className="page-header-left">
              <HistoryOutlined style={{ fontSize: 22, color: '#0f386a' }} />
              <InfoTitle
                title="Activity Log"
                infoContent="View audit history, user sessions, and system activity"
                className="page-title"
              />
            </div>
          </div>

          {/* Tabs */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', position: 'relative' }}>
              <button
                onClick={() => setActiveTab('audit')}
                style={{
                  padding: '14px 28px',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '15px',
                  fontWeight: 500,
                  color: activeTab === 'audit' ? '#1890ff' : '#666',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  position: 'relative'
                }}
              >
                <FileTextOutlined /> Audit History
                {activeTab === 'audit' && (
                  <span style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    height: '3px',
                    backgroundColor: '#1890ff',
                    borderRadius: '3px 3px 0 0'
                  }} />
                )}
              </button>
              <button
                onClick={() => setActiveTab('sessions')}
                style={{
                  padding: '14px 28px',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '15px',
                  fontWeight: 500,
                  color: activeTab === 'sessions' ? '#1890ff' : '#666',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  position: 'relative'
                }}
              >
                <LineChartOutlined /> User Sessions
                {activeTab === 'sessions' && (
                  <span style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    height: '3px',
                    backgroundColor: '#1890ff',
                    borderRadius: '3px 3px 0 0'
                  }} />
                )}
              </button>
            </div>
            <div style={{ height: '1px', backgroundColor: '#e8e8e8' }} />
          </div>

          {/* Audit History Tab Content */}
          {activeTab === 'audit' && (
            <div className="page-section">
              <h3 className="section-title">Audit History</h3>
              <p className="section-subtitle">
                {current_user.role_name === 'super_admin'
                  ? 'View all audit history across the system.'
                  : 'View audit history for your organization.'}
              </p>

              {/* Legend */}
              <div style={{ marginBottom: '16px', padding: '16px', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #e8e8e8' }}>
                <h4 style={{ margin: '0 0 12px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>Action Types:</h4>
                <div style={{ color: '#8c8c8c', fontSize: '14px', lineHeight: '1.6' }}>
                  <Tag color="success">INSERT</Tag> - New record created |{' '}
                  <Tag color="processing">UPDATE</Tag> - Record modified |{' '}
                  <Tag color="error">DELETE</Tag> - Record removed
                </div>
              </div>

              {/* Quick Filters Section */}
              <div className="form-row" style={{ marginBottom: '16px', padding: '16px', backgroundColor: '#f0f8ff', borderRadius: '6px', border: '1px solid #0f386a' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
                  <Text strong style={{ marginRight: '16px', color: '#0f386a' }}>
                    <HistoryOutlined /> Quick Filters:
                  </Text>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Table Filter</label>
                    <Select
                      placeholder="All Tables"
                      value={tableFilter}
                      onChange={(value) => {
                        setTableFilter(value);
                        fetchHistory(value, actionFilter);
                      }}
                      style={{ width: '100%' }}
                    >
                      <Option value="all">All Tables</Option>
                      <Option value="products">Products</Option>
                      <Option value="policies">Policies</Option>
                      <Option value="risks">Risks</Option>
                      <Option value="objectives">Objectives</Option>
                    </Select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Action Filter</label>
                    <Select
                      placeholder="All Actions"
                      value={actionFilter}
                      onChange={(value) => {
                        setActionFilter(value);
                        fetchHistory(tableFilter, value);
                      }}
                      style={{ width: '100%' }}
                    >
                      <Option value="all">All Actions</Option>
                      <Option value="insert">Insert</Option>
                      <Option value="update">Update</Option>
                      <Option value="delete">Delete</Option>
                    </Select>
                  </div>
                  <div className="control-group">
                    <button className="add-button" onClick={handleRefresh}>
                      <ReloadOutlined /> Refresh
                    </button>
                  </div>
                </div>
              </div>

              {/* Clear All History Section */}
              <div style={{ marginBottom: '16px', padding: '20px', backgroundColor: '#fff2e8', borderRadius: '6px', border: '1px solid #ff7a45' }}>
                <div style={{ marginBottom: '20px' }}>
                  <Text strong style={{ fontSize: '15px', color: '#d4380d' }}>
                    <DeleteOutlined /> Clear All History
                  </Text>
                </div>

                {/* Organization Selector (only for super_admin) */}
                {current_user?.role_name === 'super_admin' && allOrganisationsForClearAll.length > 0 && (
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', color: '#d4380d', fontWeight: '600', fontSize: '14px' }}>
                      Select Organization
                    </label>
                    <Select
                      placeholder="Select organization"
                      value={selectedOrgIdForClearAll || undefined}
                      onChange={(value) => setSelectedOrgIdForClearAll(value)}
                      style={{ width: '100%', maxWidth: '400px' }}
                    >
                      {allOrganisationsForClearAll.map((org) => (
                        <Option key={org.id} value={org.id}>
                          {org.name}
                        </Option>
                      ))}
                    </Select>
                  </div>
                )}

                {/* Warning message */}
                <div style={{ marginBottom: '16px', padding: '12px', backgroundColor: '#fff1f0', borderRadius: '4px', border: '1px solid #ffccc7' }}>
                  <Text type="danger" style={{ fontSize: '13px' }}>
                    <ExclamationCircleOutlined style={{ marginRight: '8px' }} />
                    Warning: This will permanently delete ALL history records for{' '}
                    {current_user?.role_name === 'super_admin'
                      ? allOrganisationsForClearAll.find(org => org.id === selectedOrgIdForClearAll)?.name || 'the selected organization'
                      : 'your organization'}. This action cannot be undone.
                  </Text>
                </div>

                {/* Clear All Button */}
                <div>
                  <Button
                    type="primary"
                    danger
                    size="large"
                    icon={<DeleteOutlined />}
                    onClick={handleClearAllHistory}
                    loading={clearingHistory}
                    disabled={!selectedOrgIdForClearAll}
                  >
                    Clear All History
                  </Button>
                </div>
              </div>

              {/* Results Summary */}
              <div style={{ marginBottom: '16px', padding: '12px', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #e8e8e8' }}>
                <Text type="secondary">
                  <ClockCircleOutlined /> Showing {historyEntries.length} audit entries
                  {(tableFilter !== 'all' || actionFilter !== 'all') && ' (filtered)'}
                </Text>
              </div>

              {loading && historyEntries.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '48px 0' }}>
                  <Spin size="large" />
                  <div style={{ marginTop: '16px' }}>
                    <Text>Loading audit history...</Text>
                  </div>
                </div>
              ) : (
                <Table<HistoryEntry>
                  columns={columns}
                  dataSource={historyEntries}
                  rowKey="id"
                  loading={loading}
                  locale={{
                    emptyText: 'No audit history found.'
                  }}
                  pagination={{
                    pageSize: 20,
                    showSizeChanger: true,
                    pageSizeOptions: ['10', '20', '50', '100'],
                    showTotal: (total, range) =>
                      `${range[0]}-${range[1]} of ${total} entries`,
                  }}
                  scroll={{ x: 1500 }}
                  size="small"
                />
              )}
            </div>
          )}

          {/* User Sessions Tab Content */}
          {activeTab === 'sessions' && (
            <>
              {/* Online Users Section */}
              <div className="page-section" style={{ marginBottom: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h3 className="section-title">Online Users</h3>
                    <p className="section-subtitle">
                      Users currently active in the application (active within the last 3 minutes)
                    </p>
                  </div>
                  <Tooltip title="Refresh online users">
                    <Button
                      icon={<ReloadOutlined spin={loadingOnlineUsers} />}
                      onClick={fetchOnlineUsers}
                      loading={false}
                      size="small"
                      style={{ marginTop: '4px' }}
                    >
                      Refresh
                    </Button>
                  </Tooltip>
                </div>

                <div style={{ padding: '16px', backgroundColor: '#f0f8ff', borderRadius: '6px', border: '1px solid #0f386a' }}>
                  {loadingOnlineUsers && onlineUsers.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '24px' }}>
                      <Spin size="small" />
                      <Text style={{ marginLeft: '12px', color: '#8c8c8c' }}>Loading online users...</Text>
                    </div>
                  ) : onlineUsers.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '24px' }}>
                      <Text type="secondary">No users are currently online</Text>
                    </div>
                  ) : (
                    <div>
                      <div style={{ marginBottom: '12px' }}>
                        <Text strong style={{ color: '#0f386a' }}>
                          {onlineUsers.length} {onlineUsers.length === 1 ? 'user' : 'users'} online
                        </Text>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '12px' }}>
                        {onlineUsers.map((user: any) => (
                          <div
                            key={user.id}
                            style={{
                              padding: '12px',
                              backgroundColor: 'white',
                              borderRadius: '6px',
                              border: '1px solid #e8e8e8',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '12px'
                            }}
                          >
                            <div style={{
                              width: '8px',
                              height: '8px',
                              borderRadius: '50%',
                              backgroundColor: '#52c41a',
                              flexShrink: 0
                            }}></div>
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <div style={{ fontWeight: 500, color: '#262626', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {user.email}
                              </div>
                              <div style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '4px' }}>
                                <Tag color="blue" style={{ marginRight: '4px', fontSize: '11px' }}>
                                  {user.role_name === 'super_admin' ? 'Super Admin' :
                                   user.role_name === 'org_admin' ? 'Org Admin' :
                                   user.role_name === 'org_user' ? 'Org User' : user.role_name}
                                </Tag>
                                {user.organisation_name}
                              </div>
                              <div style={{ fontSize: '11px', color: '#8c8c8c', marginTop: '4px' }}>
                                Active {getTimeAgo(user.last_activity)}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* User Sessions Analytics - Super Admin Only */}
              {isSuperAdmin && (
                <div className="page-section" style={{ marginBottom: '24px' }}>
                  <h3 className="section-title">User Sessions Analytics</h3>
                  <p className="section-subtitle">
                    Track user login and logout activity with detailed session history and analytics
                  </p>

                  {/* Date Range Filter */}
                  <div style={{ marginBottom: '16px', padding: '16px', backgroundColor: '#f0f8ff', borderRadius: '6px', border: '1px solid #0f386a' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                      <Text strong style={{ color: '#0f386a' }}>Filter by Date Range:</Text>
                      <RangePicker
                        value={dateRange}
                        onChange={(dates) => setDateRange(dates)}
                        style={{ flex: 1, maxWidth: '400px' }}
                        showTime
                      />
                      {dateRange && (
                        <Button onClick={() => setDateRange(null)} type="link">
                          Clear Filter
                        </Button>
                      )}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <Button
                        danger
                        onClick={handleClearAllSessions}
                        style={{ fontWeight: 500 }}
                      >
                        Clear All Sessions
                      </Button>
                    </div>
                  </div>

                  {/* Sessions Table */}
                  <div style={{ marginBottom: '24px' }}>
                    <h4 style={{ marginBottom: '12px', color: '#595959' }}>Session History</h4>
                    <Table
                      columns={sessionsColumns}
                      dataSource={userSessions}
                      rowKey="id"
                      loading={loadingSessions}
                      pagination={{
                        pageSize: 10,
                        showSizeChanger: true,
                        pageSizeOptions: ['5', '10', '20', '50'],
                        showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} sessions`,
                      }}
                      locale={{
                        emptyText: 'No session data available'
                      }}
                    />
                  </div>

                  {/* Charts Section */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px' }}>
                    {/* Visits Per Email Chart */}
                    <div style={{ padding: '16px', backgroundColor: 'white', borderRadius: '6px', border: '1px solid #e8e8e8', height: '350px', display: 'flex', flexDirection: 'column' }}>
                      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
                        <BarChartOutlined style={{ fontSize: '20px', marginRight: '8px', color: '#0f386a' }} />
                        <Text strong style={{ fontSize: '16px' }}>Visits Per Email</Text>
                      </div>
                      {loadingSessions ? (
                        <div style={{ textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1 }}>
                          <Spin size="small" />
                        </div>
                      ) : visitsPerEmail.length === 0 ? (
                        <div style={{ textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1 }}>
                          <Text type="secondary">No data available</Text>
                        </div>
                      ) : (
                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                          <Chart
                            chartType="PieChart"
                            data={[
                              ['Email', 'Visits'],
                              ...visitsPerEmail.map(item => [item.email, item.visit_count])
                            ]}
                            options={{
                              legend: { position: 'bottom' },
                              pieSliceText: 'value',
                              chartArea: { width: '90%', height: '70%' },
                            }}
                            width="100%"
                            height="280px"
                          />
                        </div>
                      )}
                    </div>

                    {/* Total Visits Card */}
                    <div style={{ padding: '16px', backgroundColor: 'white', borderRadius: '6px', border: '1px solid #e8e8e8', height: '350px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                        <BarChartOutlined style={{ fontSize: '20px', marginRight: '8px', color: '#0f386a' }} />
                        <Text strong style={{ fontSize: '16px' }}>Total Visits</Text>
                      </div>
                      {loadingSessions ? (
                        <div style={{ textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1 }}>
                          <Spin size="small" />
                        </div>
                      ) : (
                        <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1 }}>
                          <div style={{ fontSize: '48px', fontWeight: 'bold', color: '#0f386a', marginBottom: '8px' }}>
                            {totalVisits}
                          </div>
                          <Text type="secondary" style={{ fontSize: '16px' }}>
                            Total User Visits
                            {dateRange && ' (Filtered)'}
                          </Text>
                        </div>
                      )}
                    </div>

                    {/* Total PDF Downloads Card */}
                    <div style={{ padding: '16px', backgroundColor: 'white', borderRadius: '6px', border: '1px solid #e8e8e8', height: '350px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                        <BarChartOutlined style={{ fontSize: '20px', marginRight: '8px', color: '#52c41a' }} />
                        <Text strong style={{ fontSize: '16px' }}>Total PDF Downloads</Text>
                      </div>
                      {loadingSessions ? (
                        <div style={{ textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1 }}>
                          <Spin size="small" />
                        </div>
                      ) : (
                        <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1 }}>
                          <div style={{ fontSize: '48px', fontWeight: 'bold', color: '#52c41a', marginBottom: '8px' }}>
                            {totalPdfDownloads}
                          </div>
                          <Text type="secondary" style={{ fontSize: '16px' }}>
                            Total PDF Downloads
                            {dateRange && ' (Filtered)'}
                          </Text>
                        </div>
                      )}
                    </div>

                    {/* PDF Downloads Per Type Chart */}
                    <div style={{ padding: '16px', backgroundColor: 'white', borderRadius: '6px', border: '1px solid #e8e8e8', height: '350px', display: 'flex', flexDirection: 'column' }}>
                      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
                        <BarChartOutlined style={{ fontSize: '20px', marginRight: '8px', color: '#52c41a' }} />
                        <Text strong style={{ fontSize: '16px' }}>PDF Downloads per Type</Text>
                      </div>
                      {loadingSessions ? (
                        <div style={{ textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1 }}>
                          <Spin size="small" />
                        </div>
                      ) : downloadsPerType.length === 0 ? (
                        <div style={{ textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1 }}>
                          <Text type="secondary">No data available</Text>
                        </div>
                      ) : (
                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                          <Chart
                            chartType="PieChart"
                            data={[
                              ['PDF Type', 'Downloads'],
                              ...downloadsPerType.map(item => [item.pdf_type, item.download_count])
                            ]}
                            options={{
                              legend: { position: 'bottom' },
                              pieSliceText: 'value',
                              chartArea: { width: '90%', height: '70%' },
                              colors: ['#52c41a', '#1890ff', '#faad14', '#f5222d', '#722ed1', '#eb2f96', '#13c2c2', '#fa8c16', '#a0d911']
                            }}
                            width="100%"
                            height="280px"
                          />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Non-super admin message */}
              {!isSuperAdmin && (
                <div className="page-section">
                  <Alert
                    message="Limited Access"
                    description="Session analytics and detailed session history are only available to Super Administrators."
                    type="info"
                    showIcon
                  />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default HistoryAreaPage;
