import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Tag,
  Badge,
  Empty,
  Tabs,
  Button,
  Select,
  Switch,
  Modal,
  Form,
  InputNumber,
  Input,
  message,
  Tooltip,
  Alert,
  Space,
  Divider
} from 'antd';
import {
  CalendarOutlined,
  ExclamationCircleOutlined,
  SettingOutlined,
  ReloadOutlined,
  StopOutlined,
  PlayCircleOutlined,
  HistoryOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import './NewsEventPanel.css';

// Removed deprecated TabPane destructuring
const { Option } = Select;

const NewsEventPanel = ({ events = [], onRefresh }) => {
  const [activeTab, setActiveTab] = useState('today');
  const [impactFilter, setImpactFilter] = useState(['high', 'medium', 'low']);
  const [configModalVisible, setConfigModalVisible] = useState(false);
  const [overrideModalVisible, setOverrideModalVisible] = useState(false);
  const [blackoutStatus, setBlackoutStatus] = useState({});
  const [upcomingEvents, setUpcomingEvents] = useState([]);
  const [impactConfig, setImpactConfig] = useState({
    high: { pre: 60, post: 60 },
    medium: { pre: 30, post: 30 },
    low: { pre: 15, post: 15 }
  });
  const [manualOverrides, setManualOverrides] = useState({});
  const [form] = Form.useForm();
  const [overrideForm] = Form.useForm();

  // Load initial data
  useEffect(() => {
    loadImpactConfig();
    loadBlackoutStatus();
    loadUpcomingEvents();
  }, []);

  const loadImpactConfig = async () => {
    try {
      const response = await fetch('/api/news/config/impact-levels');
      const data = await response.json();
      if (data.success) {
        setImpactConfig(data.impact_level_config);
      }
    } catch (error) {
      console.error('Error loading impact config:', error);
    }
  };

  const loadBlackoutStatus = async () => {
    try {
      // Check common symbols
      const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD'];
      const response = await fetch(`/api/news/blackout/status?symbols=${symbols.join(',')}`);
      const data = await response.json();
      if (data.success) {
        setBlackoutStatus(data.blackout_status);
      }
    } catch (error) {
      console.error('Error loading blackout status:', error);
    }
  };

  const loadUpcomingEvents = async () => {
    try {
      const response = await fetch('/api/news/events/upcoming?hours=24');
      const data = await response.json();
      if (data.success) {
        setUpcomingEvents(data.events);
      }
    } catch (error) {
      console.error('Error loading upcoming events:', error);
    }
  };

  const getImpactColor = (impact) => {
    switch (impact.toLowerCase()) {
      case 'high': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'yellow';
      default: return 'default';
    }
  };

  const getImpactIcon = (impact) => {
    switch (impact.toLowerCase()) {
      case 'high': return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'medium': return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      case 'low': return <ExclamationCircleOutlined style={{ color: '#52c41a' }} />;
      default: return <CalendarOutlined />;
    }
  };

  const formatEventTime = (eventTime) => {
    const date = new Date(eventTime);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };

  const formatDateTime = (dateTime) => {
    const date = new Date(dateTime);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };

  const isEventActive = (event) => {
    const now = new Date();
    const eventTime = new Date(event.event_time);
    const preTime = new Date(eventTime.getTime() - (event.pre_minutes * 60000));
    const postTime = new Date(eventTime.getTime() + (event.post_minutes * 60000));

    return now >= preTime && now <= postTime;
  };

  const getTimeUntilEvent = (eventTime) => {
    const now = new Date();
    const event = new Date(eventTime);
    const diffMs = event.getTime() - now.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

    if (diffMs < 0) return 'Past';
    if (diffHours > 0) return `${diffHours}h ${diffMinutes}m`;
    return `${diffMinutes}m`;
  };

  const filterEvents = (eventList) => {
    if (!Array.isArray(eventList)) return [];
    return eventList.filter(event =>
      event?.impact_level && impactFilter.includes(event.impact_level.toLowerCase())
    );
  };

  const todayEvents = filterEvents((events || []).filter(event => {
    if (!event?.event_time) return false;
    const eventDate = new Date(event.event_time);
    const today = new Date();
    return eventDate.toDateString() === today.toDateString();
  }));

  const handleRefresh = async () => {
    try {
      await fetch('/api/news/sync', { method: 'POST' });
      message.success('News events refreshed successfully');
      if (onRefresh) onRefresh();
      loadBlackoutStatus();
      loadUpcomingEvents();
    } catch (error) {
      message.error('Failed to refresh news events');
    }
  };

  const handleConfigSave = async (values) => {
    try {
      for (const [level, config] of Object.entries(values)) {
        await fetch('/api/news/config/impact-levels', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            impact_level: level,
            pre_minutes: config.pre,
            post_minutes: config.post
          })
        });
      }

      setImpactConfig(values);
      setConfigModalVisible(false);
      message.success('Impact level configuration updated');
    } catch (error) {
      message.error('Failed to update configuration');
    }
  };

  const handleManualOverride = async (values) => {
    try {
      const response = await fetch('/api/news/override/enable', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values)
      });

      const data = await response.json();
      if (data.success) {
        setManualOverrides(prev => ({
          ...prev,
          [values.symbol]: {
            ...values,
            start_time: new Date(),
            end_time: new Date(Date.now() + values.duration_minutes * 60000)
          }
        }));
        setOverrideModalVisible(false);
        overrideForm.resetFields();
        message.success(`Manual override enabled for ${values.symbol}`);
        loadBlackoutStatus();
      } else {
        message.error(data.error || 'Failed to enable override');
      }
    } catch (error) {
      message.error('Failed to enable manual override');
    }
  };

  const disableOverride = async (symbol) => {
    try {
      const response = await fetch('/api/news/override/disable', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol })
      });

      const data = await response.json();
      if (data.success) {
        setManualOverrides(prev => {
          const updated = { ...prev };
          delete updated[symbol];
          return updated;
        });
        message.success(`Manual override disabled for ${symbol}`);
        loadBlackoutStatus();
      }
    } catch (error) {
      message.error('Failed to disable manual override');
    }
  };

  const renderEventItem = (event) => (
    <List.Item
      key={event.id}
      style={{
        padding: '8px 12px',
        backgroundColor: isEventActive(event) ? '#fff2e8' : 'transparent',
        borderRadius: '4px',
        marginBottom: '4px',
        border: isEventActive(event) ? '1px solid #ffa940' : '1px solid transparent'
      }}
    >
      <div style={{ width: '100%' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '4px'
        }}>
          <span style={{ fontSize: '12px', fontWeight: 'bold' }}>
            {formatEventTime(event.event_time)}
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            {getImpactIcon(event.impact_level)}
            <Tag
              size="small"
              color={getImpactColor(event.impact_level)}
            >
              {event.impact_level.toUpperCase()}
            </Tag>
          </div>
        </div>

        <div style={{ fontSize: '11px', marginBottom: '2px' }}>
          <Tag size="small" color="blue">{event.currency}</Tag>
          <span style={{ marginLeft: '8px', color: '#a6a6a6' }}>
            Blackout: {event.pre_minutes}m before / {event.post_minutes}m after
          </span>
        </div>

        <div style={{
          fontSize: '11px',
          color: '#a6a6a6',
          lineHeight: '1.3',
          marginBottom: '4px'
        }}>
          {event.description}
        </div>

        {isEventActive(event) && (
          <div style={{
            fontSize: '10px',
            color: '#fa8c16',
            fontWeight: 'bold',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}>
            <StopOutlined />
            Trading Restricted - Active Blackout
          </div>
        )}
      </div>
    </List.Item>
  );

  const renderBlackoutStatus = () => (
    <div style={{ padding: '8px 0' }}>
      <div style={{ marginBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ margin: 0, color: '#e0e0e0' }}>Trading Blackout Status</h4>
        <Button
          size="small"
          icon={<ReloadOutlined />}
          onClick={loadBlackoutStatus}
        >
          Refresh
        </Button>
      </div>

      {Object.entries(blackoutStatus).map(([symbol, status]) => (
        <div key={symbol} style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '4px 8px',
          marginBottom: '4px',
          backgroundColor: status.trading_allowed ? '#1f2f1f' : '#2f2419',
          borderRadius: '4px',
          border: `1px solid ${status.trading_allowed ? '#52c41a' : '#faad14'}`,
          color: '#e0e0e0'
        }}>
          <span style={{ fontWeight: 'bold', fontSize: '12px', color: '#e0e0e0' }}>{symbol}</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {status.trading_allowed ? (
              <Tag color="green" size="small">
                <PlayCircleOutlined /> Allowed
              </Tag>
            ) : (
              <Tag color="orange" size="small">
                <StopOutlined /> Restricted
              </Tag>
            )}
            {manualOverrides[symbol] && (
              <Tooltip title={`Override until ${formatDateTime(manualOverrides[symbol].end_time)}`}>
                <Tag color="purple" size="small">Override</Tag>
              </Tooltip>
            )}
          </div>
        </div>
      ))}

      {Object.keys(manualOverrides).length > 0 && (
        <>
          <Divider style={{ margin: '12px 0' }} />
          <div style={{ marginBottom: '8px' }}>
            <h5 style={{ margin: 0, color: '#b37feb' }}>Active Manual Overrides</h5>
          </div>
          {Object.entries(manualOverrides).map(([symbol, override]) => (
            <div key={symbol} style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '4px 8px',
              marginBottom: '4px',
              backgroundColor: '#2a1f3d',
              color: '#e0e0e0',
              borderRadius: '4px',
              border: '1px solid #d3adf7'
            }}>
              <div>
                <span style={{ fontWeight: 'bold', fontSize: '12px' }}>{symbol}</span>
                <div style={{ fontSize: '10px', color: '#a6a6a6' }}>
                  Until: {formatDateTime(override.end_time)}
                </div>
              </div>
              <Button
                size="small"
                type="text"
                danger
                onClick={() => disableOverride(symbol)}
              >
                Disable
              </Button>
            </div>
          ))}
        </>
      )}
    </div>
  );

  return (
    <Card
      title={
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span>News Events</span>
          <Space>
            <Badge count={todayEvents.length} showZero color="#1890ff" />
            <Button
              size="small"
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              className="glass-button"
            />
            <Button
              size="small"
              icon={<SettingOutlined />}
              onClick={() => setConfigModalVisible(true)}
              className="glass-button"
            />
          </Space>
        </div>
      }
      size="small"
      className="news-event-panel glass-card"
    >
      <div style={{ marginBottom: '12px' }}>
        <Space>
          <span style={{ fontSize: '12px', fontWeight: 'bold' }}>Impact Filter:</span>
          <Select
            mode="multiple"
            size="small"
            value={impactFilter}
            onChange={setImpactFilter}
            style={{ minWidth: '120px' }}
          >
            <Option value="high">High</Option>
            <Option value="medium">Medium</Option>
            <Option value="low">Low</Option>
          </Select>
          <Button
            size="small"
            type="primary"
            ghost
            onClick={() => setOverrideModalVisible(true)}
          >
            Manual Override
          </Button>
        </Space>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        size="small"
        items={[
          {
            key: 'today',
            label: `Today (${todayEvents.length})`,
            children: todayEvents.length === 0 ? (
              <Empty
                description="No news events today"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            ) : (
              <div className="news-scrollable-container">
                <List
                  size="small"
                  dataSource={todayEvents}
                  renderItem={renderEventItem}
                />
              </div>
            )
          },
          {
            key: 'upcoming',
            label: 'Upcoming',
            children: filterEvents(upcomingEvents).length === 0 ? (
              <Empty
                description="No upcoming events"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            ) : (
              <div className="news-scrollable-container">
                <List
                  size="small"
                  dataSource={filterEvents(upcomingEvents)}
                  renderItem={event => (
                    <List.Item
                      key={event.id}
                      style={{
                        padding: '8px 12px',
                        marginBottom: '4px',
                        borderRadius: '4px'
                      }}
                    >
                      <div style={{ width: '100%' }}>
                        <div style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          marginBottom: '4px'
                        }}>
                          <span style={{ fontSize: '12px', fontWeight: 'bold' }}>
                            {formatDateTime(event.event_time)}
                          </span>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <Tag size="small" color="cyan">
                              <ClockCircleOutlined /> {getTimeUntilEvent(event.event_time)}
                            </Tag>
                            <Tag
                              size="small"
                              color={getImpactColor(event.impact_level)}
                            >
                              {event.impact_level.toUpperCase()}
                            </Tag>
                          </div>
                        </div>

                        <div style={{ fontSize: '11px', marginBottom: '2px' }}>
                          <Tag size="small" color="blue">{event.currency}</Tag>
                        </div>

                        <div style={{
                          fontSize: '11px',
                          color: '#a6a6a6',
                          lineHeight: '1.3'
                        }}>
                          {event.description}
                        </div>
                      </div>
                    </List.Item>
                  )}
                />
              </div>
            )
          },
          {
            key: 'blackout',
            label: 'Blackout Status',
            children: (
              <div className="news-scrollable-container">
                {renderBlackoutStatus()}
              </div>
            )
          }
        ]}
      />

      {/* Impact Level Configuration Modal */}
      <Modal
        title="Impact Level Configuration"
        open={configModalVisible}
        onCancel={() => setConfigModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
        className="glass-modal"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={impactConfig}
          onFinish={handleConfigSave}
        >
          {['high', 'medium', 'low'].map(level => (
            <div key={level} style={{ marginBottom: '16px' }}>
              <h4 style={{
                color: getImpactColor(level) === 'red' ? '#ff4d4f' :
                  getImpactColor(level) === 'orange' ? '#faad14' : '#52c41a',
                textTransform: 'capitalize'
              }}>
                {level} Impact Events
              </h4>
              <div style={{ display: 'flex', gap: '16px' }}>
                <Form.Item
                  name={[level, 'pre']}
                  label="Minutes Before"
                  rules={[{ required: true, message: 'Required' }]}
                >
                  <InputNumber min={0} max={180} />
                </Form.Item>
                <Form.Item
                  name={[level, 'post']}
                  label="Minutes After"
                  rules={[{ required: true, message: 'Required' }]}
                >
                  <InputNumber min={0} max={180} />
                </Form.Item>
              </div>
            </div>
          ))}
        </Form>
      </Modal>

      {/* Manual Override Modal */}
      <Modal
        title="Manual Override"
        open={overrideModalVisible}
        onCancel={() => setOverrideModalVisible(false)}
        onOk={() => overrideForm.submit()}
        className="glass-modal"
      >
        <Alert
          message="Manual Override"
          description="This will temporarily allow trading for the selected symbol, ignoring news restrictions."
          type="warning"
          showIcon
          style={{ marginBottom: '16px' }}
        />
        <Form
          form={overrideForm}
          layout="vertical"
          onFinish={handleManualOverride}
        >
          <Form.Item
            name="symbol"
            label="Symbol"
            rules={[{ required: true, message: 'Please select a symbol' }]}
          >
            <Select placeholder="Select symbol">
              <Option value="EURUSD">EURUSD</Option>
              <Option value="GBPUSD">GBPUSD</Option>
              <Option value="USDJPY">USDJPY</Option>
              <Option value="XAUUSD">XAUUSD</Option>
              <Option value="USDCAD">USDCAD</Option>
              <Option value="AUDUSD">AUDUSD</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="duration_minutes"
            label="Duration (minutes)"
            rules={[{ required: true, message: 'Please enter duration' }]}
            initialValue={60}
          >
            <InputNumber min={5} max={480} />
          </Form.Item>
          <Form.Item
            name="reason"
            label="Reason"
            rules={[{ required: true, message: 'Please provide a reason' }]}
          >
            <Input.TextArea rows={3} placeholder="Reason for manual override..." />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default NewsEventPanel;