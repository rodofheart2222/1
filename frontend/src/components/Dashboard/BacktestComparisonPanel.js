import React, { useState, useEffect, useCallback } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Upload, 
  Button, 
  Table, 
  Alert, 
  Progress, 
  Tag, 
  Space, 
  Tooltip,
  Modal,
  Statistic,
  Divider,
  Select,
  Input,
  notification
} from 'antd';
import apiService from '../../services/api';
import { 
  UploadOutlined, 
  FileTextOutlined, 
  WarningOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LineChartOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';
import { useDashboard } from '../../context/DashboardContext';
import './BacktestComparisonPanel.css';

const { Dragger } = Upload;
const { Option } = Select;
const { Search } = Input;

const BacktestComparisonPanel = () => {
  const { state, actions } = useDashboard();
  const { eaData } = state;
  
  const [backtestData, setBacktestData] = useState([]);
  const [deviationReports, setDeviationReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [selectedEA, setSelectedEA] = useState(null);
  const [chartModalVisible, setChartModalVisible] = useState(false);
  const [selectedEAForChart, setSelectedEAForChart] = useState(null);
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchText, setSearchText] = useState('');

  // Load backtest data and deviation reports on component mount
  useEffect(() => {
    loadBacktestData();
    loadDeviationReports();
  }, []);

  const loadBacktestData = async () => {
    try {
      setLoading(true);
      console.log('🔄 Loading backtest data...');
      
      // Add cache-busting parameter to ensure fresh data
      const timestamp = Date.now();
      const data = await apiService.get('/api/backtest/benchmarks', { _t: timestamp });
      console.log('✅ Backtest data received:', data);
      
      // Handle the actual API response structure
      if (data.success && data.benchmarks) {
        setBacktestData(data.benchmarks);
        console.log(`📊 Loaded ${data.benchmarks.length} backtest benchmarks from ${data.source}`);
      } else if (Array.isArray(data)) {
        setBacktestData(data);
        console.log(`📊 Loaded ${data.length} backtest benchmarks`);
      } else {
        setBacktestData([]);
        console.log('📊 No backtest benchmarks found');
      }
    } catch (error) {
      console.error('❌ Error loading backtest data:', error);
      setBacktestData([]);
      notification.error({
        message: 'Error',
        description: `Failed to load backtest data: ${error.message}`
      });
    } finally {
      setLoading(false);
    }
  };

  const loadDeviationReports = async () => {
    try {
      // Mock API call - replace with actual API
      const response = await fetch('/api/backtest/deviations');
      const data = await response.json();
      // Ensure data is always an array
      setDeviationReports(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error loading deviation reports:', error);
      // Set to empty array on error
      setDeviationReports([]);
    }
  };

  const handleFileUpload = async (file, eaId) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('ea_id', eaId);

    try {
      setLoading(true);
      console.log(`🔄 Uploading backtest for EA ${eaId}...`);
      
      // Use API service instead of direct fetch
      const response = await apiService.uploadBacktest(formData);
      
      console.log('✅ Upload response:', response);
      
      if (response.success) {
        notification.success({
          message: 'Success',
          description: 'Backtest report uploaded successfully'
        });
        loadBacktestData();
        loadDeviationReports();
        setUploadModalVisible(false);
      } else {
        throw new Error(response.message || 'Upload failed');
      }
    } catch (error) {
      console.error('❌ Upload error:', error);
      notification.error({
        message: 'Error',
        description: 'Failed to upload backtest report'
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'good': return 'success';
      case 'warning': return 'warning';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'good': return '🟢';
      case 'warning': return '🟡';
      case 'critical': return '';
      default: return '';
    }
  };

  const getDeviationColor = (deviation) => {
    if (Math.abs(deviation) >= 30) return '#ff4d4f';
    if (Math.abs(deviation) >= 15) return '#faad14';
    return '#52c41a';
  };

  // Filter deviation reports based on status and search
  const filteredReports = (Array.isArray(deviationReports) ? deviationReports : []).filter(report => {
    if (!report) return false;
    if (filterStatus !== 'all' && report.overall_status !== filterStatus) return false;
    if (searchText) {
      const ea = (eaData || []).find(ea => ea?.magic_number === report.ea_id);
      if (!ea) return false;
      const searchLower = searchText.toLowerCase();
      return (ea.symbol || '').toLowerCase().includes(searchLower) || 
             (ea.strategy_tag || '').toLowerCase().includes(searchLower);
    }
    return true;
  });

  // Table columns for deviation reports
  const columns = [
    {
      title: 'EA',
      key: 'ea',
      render: (_, record) => {
        const ea = (eaData || []).find(ea => ea?.magic_number === record?.ea_id);
        return ea ? (
          <Space direction="vertical" size="small">
            <strong>{ea.symbol || 'Unknown'}</strong>
            <span style={{ fontSize: '12px', color: '#a6a6a6' }}>{ea.strategy_tag || 'Unknown'}</span>
          </Space>
        ) : `EA ${record?.ea_id || 'Unknown'}`;
      }
    },
    {
      title: 'Status',
      dataIndex: 'overall_status',
      key: 'status',
      render: (status) => (
        <Space>
          <span>{getStatusIcon(status)}</span>
          <Tag color={getStatusColor(status)}>
            {status.toUpperCase()}
          </Tag>
        </Space>
      )
    },
    {
      title: 'Profit Factor',
      key: 'profit_factor',
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <span style={{ color: getDeviationColor(record.profit_factor_deviation) }}>
            {record.profit_factor_deviation > 0 ? '+' : ''}{record.profit_factor_deviation.toFixed(1)}%
          </span>
          <Progress 
            percent={Math.min(Math.abs(record.profit_factor_deviation), 100)} 
            size="small"
            status={Math.abs(record.profit_factor_deviation) >= 30 ? 'exception' : 
                   Math.abs(record.profit_factor_deviation) >= 15 ? 'active' : 'success'}
            showInfo={false}
          />
        </Space>
      )
    },
    {
      title: 'Expected Payoff',
      key: 'expected_payoff',
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <span style={{ color: getDeviationColor(record.expected_payoff_deviation) }}>
            {record.expected_payoff_deviation > 0 ? '+' : ''}{record.expected_payoff_deviation.toFixed(1)}%
          </span>
          <Progress 
            percent={Math.min(Math.abs(record.expected_payoff_deviation), 100)} 
            size="small"
            status={Math.abs(record.expected_payoff_deviation) >= 40 ? 'exception' : 
                   Math.abs(record.expected_payoff_deviation) >= 20 ? 'active' : 'success'}
            showInfo={false}
          />
        </Space>
      )
    },
    {
      title: 'Drawdown',
      key: 'drawdown',
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <span style={{ color: record.drawdown_deviation > 0 ? '#ff4d4f' : '#52c41a' }}>
            {record.drawdown_deviation > 0 ? '+' : ''}{record.drawdown_deviation.toFixed(1)}%
          </span>
          <Progress 
            percent={Math.min(Math.abs(record.drawdown_deviation), 100)} 
            size="small"
            status={record.drawdown_deviation >= 50 ? 'exception' : 
                   record.drawdown_deviation >= 25 ? 'active' : 'success'}
            showInfo={false}
          />
        </Space>
      )
    },
    {
      title: 'Alerts',
      key: 'alerts',
      render: (_, record) => (
        <Space direction="vertical" size="small">
          {(record.alerts || []).slice(0, 2).map((alert, index) => (
            <Tooltip key={index} title={alert.message}>
              <Tag 
                color={alert.alert_level === 'critical' ? 'red' : 'orange'}
                size="small"
              >
                {alert.metric_name}
              </Tag>
            </Tooltip>
          ))}
          {(record.alerts || []).length > 2 && (
            <Tag size="small">+{(record.alerts || []).length - 2} more</Tag>
          )}
        </Space>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button 
            size="small" 
            icon={<LineChartOutlined />}
            onClick={() => {
              setSelectedEAForChart(record);
              setChartModalVisible(true);
            }}
          >
            Chart
          </Button>
          <Button 
            size="small" 
            type="primary"
            danger={record.overall_status === 'critical'}
            onClick={() => handleEAAction(record)}
          >
            {record.overall_status === 'critical' ? 'Flag' : 'Monitor'}
          </Button>
        </Space>
      )
    }
  ];

  const handleEAAction = (record) => {
    if (record.overall_status === 'critical') {
      Modal.confirm({
        title: 'Flag EA for Demotion',
        content: `Are you sure you want to flag EA ${record.ea_id} for demotion due to critical performance deviation?`,
        onOk: () => {
          // Add command to flag EA
          actions.addCommand({
            type: 'flag_demotion',
            ea_id: record.ea_id,
            reason: 'Critical performance deviation from backtest'
          });
          notification.warning({
            message: 'EA Flagged',
            description: `EA ${record.ea_id} has been flagged for demotion`
          });
        }
      });
    }
  };

  // Generate mock trend data for charts
  const generateTrendData = (report) => {
    const days = 30;
    const data = [];
    for (let i = days; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      data.push({
        date: date.toISOString().split('T')[0],
        live_pf: 1.2 + Math.random() * 0.5 - 0.25,
        backtest_pf: 1.5,
        live_ep: 15 + Math.random() * 10 - 5,
        backtest_ep: 20,
        live_dd: 8 + Math.random() * 4 - 2,
        backtest_dd: 6
      });
    }
    return data;
  };

  return (
    <div className="backtest-comparison-panel">
      {/* Header */}
      <Card size="small" className="panel-header">
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <FileTextOutlined style={{ fontSize: '18px', color: '#1890ff' }} />
              <span style={{ fontSize: '16px', fontWeight: 'bold' }}>
                Backtest Comparison
              </span>
              <Divider type="vertical" />
              <span style={{ color: '#a6a6a6' }}>
                {filteredReports.length} EAs monitored
              </span>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button 
                icon={<UploadOutlined />}
                onClick={() => setUploadModalVisible(true)}
              >
                Upload Report
              </Button>
              <Button 
                icon={<ReloadOutlined />}
                onClick={() => {
                  loadBacktestData();
                  loadDeviationReports();
                }}
              >
                Refresh
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Summary Statistics */}
      <Card title="Performance Summary" size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic
              title="Total EAs with Benchmarks"
              value={deviationReports.length}
              prefix={<FileTextOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Critical Deviations"
              value={(Array.isArray(deviationReports) ? deviationReports : []).filter(r => r.overall_status === 'critical').length}
              valueStyle={{ color: '#cf1322' }}
              prefix={<ExclamationCircleOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Warning Deviations"
              value={(Array.isArray(deviationReports) ? deviationReports : []).filter(r => r.overall_status === 'warning').length}
              valueStyle={{ color: '#d48806' }}
              prefix={<WarningOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Performing Well"
              value={(Array.isArray(deviationReports) ? deviationReports : []).filter(r => r.overall_status === 'good').length}
              valueStyle={{ color: '#389e0d' }}
              prefix={<CheckCircleOutlined />}
            />
          </Col>
        </Row>
      </Card>

      {/* Filters */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col span={8}>
            <Search
              placeholder="Search by symbol or strategy"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear
            />
          </Col>
          <Col span={8}>
            <Select
              value={filterStatus}
              onChange={setFilterStatus}
              style={{ width: '100%' }}
              placeholder="Filter by status"
            >
              <Option value="all">All Status</Option>
              <Option value="good">Good</Option>
              <Option value="warning">Warning</Option>
              <Option value="critical">Critical</Option>
            </Select>
          </Col>
        </Row>
      </Card>

      {/* Critical Alerts */}
      {deviationReports.some(r => r.overall_status === 'critical') && (
        <Alert
          message="Critical Performance Deviations Detected"
          description={`${(Array.isArray(deviationReports) ? deviationReports : []).filter(r => r.overall_status === 'critical').length} EAs are showing critical performance deviations from their backtest benchmarks. Immediate attention required.`}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
          action={
            <Button size="small" danger>
              Review All
            </Button>
          }
        />
      )}

      {/* Deviation Reports Table */}
      <Card title="Live vs Backtest Comparison" size="small">
        <Table
          columns={columns}
          dataSource={filteredReports}
          rowKey="ea_id"
          loading={loading}
          size="small"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} EAs`
          }}
          expandable={{
            expandedRowRender: (record) => (
              <div style={{ padding: '16px', backgroundColor: '#262626' }}>
                <Row gutter={16}>
                  <Col span={12}>
                    <h4>Recommendation</h4>
                    <p>{record.recommendation}</p>
                    <h4>Alerts</h4>
                    {(record?.alerts || []).map((alert, index) => (
                      <Alert
                        key={index}
                        message={alert?.message || 'No message'}
                        type={(alert?.alert_level === 'critical') ? 'error' : 'warning'}
                        size="small"
                        style={{ marginBottom: 8 }}
                      />
                    ))}
                  </Col>
                  <Col span={12}>
                    <h4>Performance Metrics</h4>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div>Profit Factor Deviation: <strong style={{ color: getDeviationColor(record?.profit_factor_deviation || 0) }}>{(record?.profit_factor_deviation || 0).toFixed(1)}%</strong></div>
                      <div>Expected Payoff Deviation: <strong style={{ color: getDeviationColor(record?.expected_payoff_deviation || 0) }}>{(record?.expected_payoff_deviation || 0).toFixed(1)}%</strong></div>
                      <div>Drawdown Deviation: <strong style={{ color: (record?.drawdown_deviation || 0) > 0 ? '#ff4d4f' : '#52c41a' }}>{(record?.drawdown_deviation || 0).toFixed(1)}%</strong></div>
                    </Space>
                  </Col>
                </Row>
              </div>
            )
          }}
        />
      </Card>

      {/* Upload Modal */}
      <Modal
        title="Upload Backtest Report"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
        width={600}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <label>Select EA:</label>
            <Select
              value={selectedEA}
              onChange={setSelectedEA}
              style={{ width: '100%', marginTop: 8 }}
              placeholder="Choose EA to upload backtest for"
            >
              {(eaData || []).map(ea => (
                <Option key={ea?.magic_number || Math.random()} value={ea?.magic_number}>
                  {ea?.symbol || 'Unknown'} - {ea?.strategy_tag || 'Unknown'} (#{ea?.magic_number || 'N/A'})
                </Option>
              ))}
            </Select>
          </div>
          
          <Dragger
            name="file"
            multiple={false}
            accept=".html,.htm"
            beforeUpload={(file) => {
              if (!selectedEA) {
                notification.error({
                  message: 'Error',
                  description: 'Please select an EA first'
                });
                return false;
              }
              handleFileUpload(file, selectedEA);
              return false;
            }}
            disabled={!selectedEA}
          >
            <p className="ant-upload-drag-icon">
              <UploadOutlined />
            </p>
            <p className="ant-upload-text">Click or drag MT5 backtest HTML report to this area to upload</p>
            <p className="ant-upload-hint">
              Support for single HTML file upload. The system will automatically parse profit factor, expected payoff, drawdown, and other metrics.
            </p>
          </Dragger>
        </Space>
      </Modal>

      {/* Performance Trend Chart Modal */}
      <Modal
        title={`Performance Trend - EA ${selectedEAForChart?.ea_id}`}
        open={chartModalVisible}
        onCancel={() => setChartModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedEAForChart && (
          <div style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={generateTrendData(selectedEAForChart)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <RechartsTooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="live_pf" 
                  stroke="#1890ff" 
                  name="Live Profit Factor"
                  strokeWidth={2}
                />
                <Line 
                  type="monotone" 
                  dataKey="backtest_pf" 
                  stroke="#52c41a" 
                  name="Backtest Profit Factor"
                  strokeDasharray="5 5"
                />
                <Line 
                  type="monotone" 
                  dataKey="live_ep" 
                  stroke="#fa8c16" 
                  name="Live Expected Payoff"
                  strokeWidth={2}
                />
                <Line 
                  type="monotone" 
                  dataKey="backtest_ep" 
                  stroke="#13c2c2" 
                  name="Backtest Expected Payoff"
                  strokeDasharray="5 5"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default BacktestComparisonPanel;