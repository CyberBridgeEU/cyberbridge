import React, { useEffect, useState, useMemo } from 'react';
import { Table, Radio, message, Space, Card, Typography, Tag, Spin, Alert, MenuProps, Input, Select, Button, DatePicker } from 'antd';
import { UserOutlined, TeamOutlined, SearchOutlined, ReloadOutlined, SafetyOutlined, BarChartOutlined } from '@ant-design/icons';
import { Chart } from 'react-google-charts';
import { useAdminAreaStore, User } from '../store/adminAreaStore';
import useAuthStore from '../store/useAuthStore';
import useUserStore from '../store/useUserStore';
import type { ColumnsType } from 'antd/es/table';
import type { FilterDropdownProps } from 'antd/es/table/interface';
import Sidebar from '../components/Sidebar';
import InfoTitle from '../components/InfoTitle';
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

const AdminAreaPage: React.FC = () => {
  const [location] = useLocation();
  const menuHighlighting = useMenuHighlighting(location);
  const {
    users,
    loading,
    error,
    fetchAllUsers,
    updateUserStatus,
    clearError
  } = useAdminAreaStore();

  const { user } = useAuthStore();
  const { current_user, fetchCurrentUser } = useUserStore();

  // Filter states
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [orgFilter, setOrgFilter] = useState<string>('all');
  const [searchText, setSearchText] = useState('');

  // Online users state
  const [onlineUsers, setOnlineUsers] = useState<any[]>([]);
  const [loadingOnlineUsers, setLoadingOnlineUsers] = useState(false);

  // User sessions state
  const [userSessions, setUserSessions] = useState<any[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [visitsPerEmail, setVisitsPerEmail] = useState<any[]>([]);
  const [totalVisits, setTotalVisits] = useState(0);
  const [totalPdfDownloads, setTotalPdfDownloads] = useState(0);
  const [downloadsPerType, setDownloadsPerType] = useState<any[]>([]);
  const [dateRange, setDateRange] = useState<[any, any] | null>(null);

  useEffect(() => {
    // Fetch current user data if not already loaded
    if (!current_user || !current_user.role_name) {
      fetchCurrentUser();
    }
    // Fetch all users instead of just pending
    fetchAllUsers();
  }, [fetchAllUsers, fetchCurrentUser]);

  useEffect(() => {
    if (error) {
      message.error(error);
      clearError();
    }
  }, [error, clearError]);

  // Fetch online users
  const fetchOnlineUsers = async () => {
    setLoadingOnlineUsers(true);
    try {
      const { getAuthHeader } = useAuthStore.getState();
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
      } else {
        console.error('Failed to fetch online users');
      }
    } catch (error) {
      console.error('Error fetching online users:', error);
    } finally {
      setLoadingOnlineUsers(false);
    }
  };

  // Poll for online users every 20 seconds
  useEffect(() => {
    // Initial fetch
    fetchOnlineUsers();

    // Set up polling
    const interval = setInterval(() => {
      fetchOnlineUsers();
    }, 20000); // 20 seconds

    // Cleanup
    return () => clearInterval(interval);
  }, []);

  // Fetch user sessions
  const fetchUserSessions = async () => {
    setLoadingSessions(true);
    try {
      const { getAuthHeader } = useAuthStore.getState();
      const authHeader = getAuthHeader();

      // Build query params for date filter
      let queryParams = '';
      if (dateRange && dateRange[0] && dateRange[1]) {
        const fromDate = dateRange[0].toISOString();
        const toDate = dateRange[1].toISOString();
        queryParams = `?from_date=${encodeURIComponent(fromDate)}&to_date=${encodeURIComponent(toDate)}`;
      }

      // Fetch sessions, visits per email, total visits, total PDF downloads, and downloads per type in parallel
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
        console.log('Visits data received:', visitsData);
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
        console.log('Downloads per type data received:', downloadsData);
        setDownloadsPerType(downloadsData);
      }
    } catch (error) {
      console.error('Error fetching user sessions:', error);
      message.error('Failed to load user sessions data');
    } finally {
      setLoadingSessions(false);
    }
  };

  // Fetch sessions on mount and when date range changes
  useEffect(() => {
    fetchUserSessions();
  }, [dateRange]);

  // Clear all user sessions
  const handleClearAllSessions = async () => {
    try {
      const { getAuthHeader } = useAuthStore.getState();
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
        message.success(`Successfully deleted ${data.deleted_count} session records`);
        // Refresh the sessions data
        fetchUserSessions();
      } else {
        message.error('Failed to delete sessions');
      }
    } catch (error) {
      console.error('Error deleting sessions:', error);
      message.error('Failed to delete sessions');
    }
  };

  // Calculate time ago from last activity
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

  const handleStatusChange = async (userId: string, newStatus: string) => {
    try {
      await updateUserStatus(userId, newStatus);
      message.success(`User status updated to ${newStatus}`);
    } catch (err) {
      message.error('Failed to update user status');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'pending_approval':
        return 'warning';
      case 'inactive':
        return 'default';
      default:
        return 'default';
    }
  };

  // Get unique organizations for filter
  const organizations = useMemo(() => {
    const orgs = [...new Set(users.map(u => u.organisation_name))];
    return orgs.sort();
  }, [users]);

  // Get unique roles for filter
  const roles = useMemo(() => {
    const roleSet = [...new Set(users.map(u => u.role_name))];
    return roleSet.sort();
  }, [users]);

  // Filter users based on selected filters
  const filteredUsers = useMemo(() => {
    let filtered = [...users];

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(u => u.status === statusFilter);
    }

    // Role filter
    if (roleFilter !== 'all') {
      filtered = filtered.filter(u => u.role_name === roleFilter);
    }

    // Organization filter
    if (orgFilter !== 'all') {
      filtered = filtered.filter(u => u.organisation_name === orgFilter);
    }

    // Search filter (email)
    if (searchText) {
      filtered = filtered.filter(u =>
        u.email.toLowerCase().includes(searchText.toLowerCase())
      );
    }

    return filtered;
  }, [users, statusFilter, roleFilter, orgFilter, searchText]);

  const handleReset = () => {
    setStatusFilter('all');
    setRoleFilter('all');
    setOrgFilter('all');
    setSearchText('');
  };

  const handleRefresh = () => {
    fetchAllUsers();
    message.info('Refreshing user list...');
  };

  const columns: ColumnsType<User> = [
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      sorter: (a, b) => a.email.localeCompare(b.email),
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }: FilterDropdownProps) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="Search email"
            value={selectedKeys[0]}
            onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              icon={<SearchOutlined />}
              size="small"
              style={{ width: 90 }}
            >
              Search
            </Button>
            <Button onClick={() => clearFilters && clearFilters()} size="small" style={{ width: 90 }}>
              Reset
            </Button>
          </Space>
        </div>
      ),
      filterIcon: (filtered) => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
      onFilter: (value, record) => record.email.toLowerCase().includes(value.toString().toLowerCase()),
      render: (email: string) => (
        <Space>
          <UserOutlined />
          <Text strong>{email}</Text>
        </Space>
      ),
    },
    {
      title: 'Role',
      dataIndex: 'role_name',
      key: 'role_name',
      filters: [
        { text: 'Super Admin', value: 'super_admin' },
        { text: 'Organization Admin', value: 'org_admin' },
        { text: 'Organization User', value: 'org_user' },
      ],
      onFilter: (value, record) => record.role_name === value,
      render: (role: string) => {
        let color = 'blue';
        let displayText = role;

        switch(role) {
          case 'super_admin':
            color = 'red';
            displayText = 'Super Admin';
            break;
          case 'org_admin':
            color = 'orange';
            displayText = 'Organization Admin';
            break;
          case 'org_user':
            color = 'blue';
            displayText = 'Organization User';
            break;
        }

        return <Tag color={color}>{displayText}</Tag>;
      },
    },
    {
      title: 'Organization',
      dataIndex: 'organisation_name',
      key: 'organisation_name',
      filters: organizations.map(org => ({ text: org, value: org })),
      onFilter: (value, record) => record.organisation_name === value,
      sorter: (a, b) => a.organisation_name.localeCompare(b.organisation_name),
      render: (org: string) => (
        <Space>
          <TeamOutlined />
          <Text>{org}</Text>
        </Space>
      ),
    },
    {
      title: 'Current Status',
      dataIndex: 'status',
      key: 'current_status',
      filters: [
        { text: 'Pending Approval', value: 'pending_approval' },
        { text: 'Active', value: 'active' },
        { text: 'Inactive', value: 'inactive' },
      ],
      onFilter: (value, record) => record.status === value,
      render: (status: string) => {
        let displayText = status;
        switch(status) {
          case 'pending_approval':
            displayText = 'Pending Approval';
            break;
          case 'active':
            displayText = 'Active';
            break;
          case 'inactive':
            displayText = 'Inactive';
            break;
        }
        return <Tag color={getStatusColor(status)}>{displayText}</Tag>;
      },
    },
    {
      title: 'Status Control',
      key: 'status_control',
      render: (_, record: User) => {
        // Don't allow changing status for super_admin
        if (record.role_name === 'super_admin') {
          return <Text type="secondary">Protected</Text>;
        }

        // Don't allow org_admin to change status of users from other organizations
        if (current_user?.role_name === 'org_admin' &&
            record.organisation_name !== current_user?.organisation_name) {
          return <Text type="secondary">No Permission</Text>;
        }

        return (
          <Radio.Group
            value={record.status}
            onChange={(e) => handleStatusChange(record.id, e.target.value)}
            disabled={loading}
          >
            <Radio.Button value="pending_approval">Pending</Radio.Button>
            <Radio.Button value="active">Active</Radio.Button>
            <Radio.Button value="inactive">Inactive</Radio.Button>
          </Radio.Group>
        );
      },
    },
    {
      title: 'Registration Date',
      dataIndex: 'created_at',
      key: 'created_at',
      sorter: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      render: (date: string) => {
        const formattedDate = new Date(date).toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });
        return <Text type="secondary">{formattedDate}</Text>;
      },
    },
  ];

  // User sessions table columns
  const sessionsColumns: ColumnsType<any> = [
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      sorter: (a, b) => a.email.localeCompare(b.email),
      render: (email: string) => (
        <Space>
          <UserOutlined />
          <Text>{email}</Text>
        </Space>
      ),
    },
    {
      title: 'Login Timestamp',
      dataIndex: 'login_timestamp',
      key: 'login_timestamp',
      sorter: (a, b) => new Date(a.login_timestamp).getTime() - new Date(b.login_timestamp).getTime(),
      render: (timestamp: string) => {
        return new Date(timestamp).toLocaleString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        });
      },
    },
    {
      title: 'Logout Timestamp',
      dataIndex: 'logout_timestamp',
      key: 'logout_timestamp',
      sorter: (a, b) => {
        if (!a.logout_timestamp) return 1;
        if (!b.logout_timestamp) return -1;
        return new Date(a.logout_timestamp).getTime() - new Date(b.logout_timestamp).getTime();
      },
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
          second: '2-digit'
        });
      },
    },
  ];

  const onClick: MenuProps['onClick'] = (e) => {
    console.log('click ', e);
  };

  // Check if user has permission to access this page using current_user from useUserStore
  if (!current_user || !current_user.role_name || (current_user.role_name !== 'super_admin' && current_user.role_name !== 'org_admin')) {
    return (
      <div>
        <div className={'page-parent'}>
          <Sidebar onClick={onClick} selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange} />
          <div className={'page-content'}>
            <Alert
              message="Access Denied"
              description="You do not have permission to access the Admin Area. Only Super Administrators and Organization Administrators can view this page."
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
      <div className={'page-parent'}>
        <Sidebar onClick={onClick} selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange} />
        <div className={'page-content'}>
          {/* Page Header */}
          <div className="page-header">
            <div className="page-header-left">
              <SafetyOutlined style={{ fontSize: 22, color: '#0f386a' }} />
              <InfoTitle
                title="Admin Area"
                infoContent="Manage user account approvals and organizational settings"
                className="page-title"
              />
            </div>
          </div>

          {/* Online Users Section */}
          <div className="page-section" style={{ marginBottom: '24px' }}>
            <h3 className="section-title">Online Users</h3>
            <p className="section-subtitle">
              Users currently active in the application (active within the last 3 minutes)
            </p>

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

          {/* User Sessions Section - Only visible to super_admin */}
          {current_user.role_name === 'super_admin' && (
          <div className="page-section" style={{ marginBottom: '24px' }}>
            <h3 className="section-title">User Sessions Analytics</h3>
            <p className="section-subtitle">
              Track user login and logout activity with detailed session history and analytics
            </p>

            {/* Date Range Filter and Actions */}
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

          {/* User Management Section */}
          <div className="page-section">
            <h3 className="section-title">User Account Management</h3>
            <p className="section-subtitle">
              {current_user.role_name === 'super_admin'
                ? 'As a Super Admin, you can manage users from all organizations.'
                : 'As an Organization Admin, you can manage users from your organization.'}
            </p>

            <div style={{ marginBottom: '16px', padding: '16px', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #e8e8e8' }}>
              <h4 style={{ margin: '0 0 12px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>Status Guide:</h4>
              <div style={{ color: '#8c8c8c', fontSize: '14px', lineHeight: '1.6' }}>
                <Tag color="warning">Pending Approval</Tag> - New registrations awaiting approval |{' '}
                <Tag color="success">Active</Tag> - Approved users with access |{' '}
                <Tag color="default">Inactive</Tag> - Rejected or deactivated users
              </div>
            </div>

            {/* Quick Filters Section */}
            <div className="form-row" style={{ marginBottom: '16px', padding: '16px', backgroundColor: '#f0f8ff', borderRadius: '6px', border: '1px solid #0f386a' }}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
                <Text strong style={{ marginRight: '16px', color: '#0f386a' }}>Quick Filters:</Text>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Status Filter</label>
                  <Select
                    placeholder="All Status"
                    value={statusFilter}
                    onChange={setStatusFilter}
                    style={{ width: '100%' }}
                  >
                    <Option value="all">All Status</Option>
                    <Option value="pending_approval">Pending</Option>
                    <Option value="active">Active</Option>
                    <Option value="inactive">Inactive</Option>
                  </Select>
                </div>
                <div className="form-group">
                  <label className="form-label">Role Filter</label>
                  <Select
                    placeholder="All Roles"
                    value={roleFilter}
                    onChange={setRoleFilter}
                    style={{ width: '100%' }}
                  >
                    <Option value="all">All Roles</Option>
                    <Option value="super_admin">Super Admin</Option>
                    <Option value="org_admin">Organization Admin</Option>
                    <Option value="org_user">Organization User</Option>
                  </Select>
                </div>
                {organizations.length > 0 && (
                  <div className="form-group">
                    <label className="form-label">Organization</label>
                    <Select
                      placeholder="All Organizations"
                      value={orgFilter}
                      onChange={setOrgFilter}
                      style={{ width: '100%' }}
                    >
                      <Option value="all">All Organizations</Option>
                      {organizations.map(org => (
                        <Option key={org} value={org}>{org}</Option>
                      ))}
                    </Select>
                  </div>
                )}
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Search by Email</label>
                  <Input
                    placeholder="Search by email"
                    value={searchText}
                    onChange={(e) => setSearchText(e.target.value)}
                    prefix={<SearchOutlined />}
                    className="form-input"
                    allowClear
                  />
                </div>
                <div className="control-group">
                  <button className="secondary-button" onClick={handleReset}>Clear Filters</button>
                  <button className="add-button" onClick={handleRefresh}>
                    <ReloadOutlined /> Refresh
                  </button>
                </div>
              </div>
            </div>

            {/* Results Summary */}
            <div style={{ marginBottom: '16px', padding: '12px', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #e8e8e8' }}>
              <Text type="secondary">
                Showing {filteredUsers.length} of {users.length} users
                {(statusFilter !== 'all' || roleFilter !== 'all' || orgFilter !== 'all' || searchText) &&
                  ' (filtered)'}
              </Text>
            </div>

            {loading && users.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '48px 0' }}>
                <Spin size="large" />
                <div style={{ marginTop: '16px' }}>
                  <Text>Loading users...</Text>
                </div>
              </div>
            ) : (
              <Table<User>
                columns={columns}
                dataSource={filteredUsers}
                rowKey="id"
                loading={loading}
                locale={{
                  emptyText: searchText || statusFilter !== 'all' || roleFilter !== 'all' || orgFilter !== 'all'
                    ? 'No users match the selected filters.'
                    : 'No users found.'
                }}
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  pageSizeOptions: ['5', '10', '20', '50'],
                  showTotal: (total, range) =>
                    `${range[0]}-${range[1]} of ${total} users`,
                }}
                scroll={{ x: 1200 }}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminAreaPage;