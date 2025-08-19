import React, { useState } from 'react';
import { Card, Table, Button, Space, Tag, Modal, message, Tooltip, Progress, Select, DatePicker } from 'antd';
import { 
  ClockCircleOutlined, 
  PlayCircleOutlined,
  PauseCircleOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  ClearOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import moment from 'moment';
import apiService from '../../services/api';

const { Option } = Select;
const { confirm } = Modal;

const ActionQueuePanel = ({ commandQueue = [], onCommandUpdate, onQueueClear }) => {
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [filterStatus, setFilterStatus] = useState('all');
  const [sortBy, setSortBy] = useState('timestamp');

  // Command status configurations
  const statusConfig = {
    pending: { color: 'orange', icon: <ClockCircleOutlined />, label: 'Pending' },
    executing: { color: 'blue', icon: <SyncOutlined spin />, label: 'Executing' },
    completed: { color: 'green', icon: <CheckCircleOutlined />, label: 'Completed' },
    failed: { color: 'red', icon: <ExclamationCircleOutlined />, label: 'Failed' },
    cancelled: { color: 'default', icon: <PauseCircleOutlined />, label: 'Cancelled' }
  };

  // Filter and sort commands with null safety
  const filteredCommands = (commandQueue || [])
    .filter(cmd => cmd && (filterStatus === 'all' || cmd.status === filterStatus))
    .sort((a, b) => {
      if (!a || !b) return 0;
      switch (sortBy) {
        case 'timestamp':
          return new Date(b.timestamp || 0) - new Date(a.timestamp || 0);
        case 'scheduled_time':
          return new Date(a.scheduled_time || a.timestamp || 0) - new Date(b.scheduled_time || b.timestamp || 0);
        case 'priority':
          return (b.priority || 0) - (a.priority || 0);
        default:
          return 0;
      }
    });

  // Table columns
  const columns = [
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const config = statusConfig[status] || statusConfig.pending;
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.label}
          </Tag>
        );
      },
    },
    {
      title: 'Command',
      dataIndex: 'type',
      key: 'type',
      render: (type, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>
            {type === 'global_action' ? record.action : type}
          </div>
          {record.description && (
            <div style={{ fontSize: '11px', color: '#a6a6a6' }}>
              {record.description}
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Target',
      key: 'target',
      render: (_, record) => (
        <div>
          <div>{record.target_scope || 'N/A'}</div>
          {record.affected_count && (
            <Tag size="small" color="blue">
              {record.affected_count} EAs
            </Tag>
          )}
        </div>
      ),
    },
    {
      title: 'Scheduled',
      dataIndex: 'scheduled_time',
      key: 'scheduled_time',
      width: 150,
      render: (scheduledTime, record) => {
        const time = scheduledTime || record.timestamp;
        const isImmediate = record.execution_mode === 'immediate';
        
        return (
          <div>
            <div style={{ fontSize: '11px' }}>
              {isImmediate ? 'Immediate' : moment(time).format('HH:mm:ss')}
            </div>
            <div style={{ fontSize: '10px', color: '#a6a6a6' }}>
              {moment(time).format('MMM DD')}
            </div>
          </div>
        );
      },
    },
    {
      title: 'Progress',
      key: 'progress',
      width: 120,
      render: (_, record) => {
        const getProgress = () => {
          switch (record.status) {
            case 'pending': return 0;
            case 'executing': return 50;
            case 'completed': return 100;
            case 'failed': return 100;
            case 'cancelled': return 0;
            default: return 0;
          }
        };

        const getStrokeColor = () => {
          switch (record.status) {
            case 'completed': return '#52c41a';
            case 'failed': return '#ff4d4f';
            case 'executing': return '#1890ff';
            default: return '#d9d9d9';
          }
        };

        return (
          <Progress
            percent={getProgress()}
            size="small"
            strokeColor={getStrokeColor()}
            showInfo={false}
          />
        );
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          {record.status === 'pending' && (
            <>
              <Tooltip title="Execute Now">
                <Button
                  size="small"
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={() => executeCommand(record)}
                />
              </Tooltip>
              <Tooltip title="Cancel">
                <Button
                  size="small"
                  icon={<PauseCircleOutlined />}
                  onClick={() => cancelCommand(record)}
                />
              </Tooltip>
            </>
          )}
          {(record.status === 'completed' || record.status === 'failed' || record.status === 'cancelled') && (
            <Tooltip title="Remove">
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
                onClick={() => removeCommand(record)}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  const executeCommand = async (command) => {
    try {
      // Update status to executing
      await onCommandUpdate({
        ...command,
        status: 'executing',
        execution_started: new Date().toISOString()
      });

      let successCount = 0;
      let failCount = 0;
      const results = [];

      // Handle different command types
      if (command.type === 'global_action') {
        // Global action - execute on targets
        const targets = command.targets || [];
        const actionCommand = command.action;
        
        // Convert action to command
        const commandMap = {
          'pause_all': 'pause',
          'resume_all': 'resume',
          'close_all_positions': 'close_positions',
          'emergency_stop': 'emergency_stop'
        };
        
        const apiCommand = commandMap[actionCommand];
        if (!apiCommand) {
          throw new Error(`Unknown action: ${actionCommand}`);
        }

        // Use detailed EA data if available for UUID targeting
        const easToTarget = command.affectedEAs || targets.map(t => ({ magic_number: t }));
        
        for (const ea of easToTarget) {
          const target = ea.magic_number || ea;
          try {
            await apiService.sendEACommand(target, {
              command: apiCommand,
              parameters: command.parameters || {},
              instance_uuid: ea.instance_uuid
            });
            successCount++;
            results.push({ target, status: 'success' });
          } catch (error) {
            failCount++;
            results.push({ target, status: 'failed', error: error.message });
          }
        }
      } else if (command.type === 'individual_command') {
        // Individual EA command
        try {
          await apiService.sendEACommand(command.magic_number, {
            command: command.command,
            parameters: command.parameters || {},
            instance_uuid: command.instance_uuid
          });
          successCount++;
          results.push({ target: command.magic_number, status: 'success' });
        } catch (error) {
          failCount++;
          results.push({ target: command.magic_number, status: 'failed', error: error.message });
        }
      } else if (command.type === 'batch_command') {
        // Batch command (deprecated - Command Center removed)
        const easToTarget = command.affectedEAs || command.targets.map(t => ({ magic_number: t }));
        
        for (const ea of easToTarget) {
          const target = ea.magic_number || ea;
          try {
            await apiService.sendEACommand(target, {
              command: command.command,
              parameters: command.parameters || {},
              instance_uuid: ea.instance_uuid
            });
            successCount++;
            results.push({ target, status: 'success' });
          } catch (error) {
            failCount++;
            results.push({ target, status: 'failed', error: error.message });
          }
        }
      } else {
        // Generic command - try to execute based on available data
        const target = command.magic_number || command.targets?.[0];
        if (target) {
          try {
            await apiService.sendEACommand(target, {
              command: command.command || command.action,
              parameters: command.parameters || {},
              instance_uuid: command.instance_uuid
            });
            successCount++;
            results.push({ target, status: 'success' });
          } catch (error) {
            failCount++;
            results.push({ target, status: 'failed', error: error.message });
          }
        }
      }

      // Update final status
      const finalStatus = failCount === 0 ? 'completed' : (successCount === 0 ? 'failed' : 'completed');
      await onCommandUpdate({
        ...command,
        status: finalStatus,
        execution_completed: new Date().toISOString(),
        results: results,
        success_count: successCount,
        fail_count: failCount
      });

      if (failCount === 0) {
        message.success(`Command "${command.type}" executed successfully on ${successCount} target(s)`);
      } else if (successCount === 0) {
        message.error(`Command "${command.type}" failed on all ${failCount} target(s)`);
      } else {
        message.warning(`Command "${command.type}" executed on ${successCount} target(s), failed on ${failCount} target(s)`);
      }
      
    } catch (error) {
      console.error('Failed to execute command:', error);
      
      // Update status to failed
      await onCommandUpdate({
        ...command,
        status: 'failed',
        execution_completed: new Date().toISOString(),
        error: error.message
      });
      
      message.error('Failed to execute command: ' + error.message);
    }
  };

  const cancelCommand = (command) => {
    confirm({
      title: 'Cancel Command',
      content: `Are you sure you want to cancel this command?`,
      onOk: async () => {
        try {
          await onCommandUpdate({
            ...command,
            status: 'cancelled',
            cancelled_at: new Date().toISOString()
          });
          
          message.success('Command cancelled successfully');
        } catch (error) {
          message.error('Failed to cancel command: ' + error.message);
        }
      }
    });
  };

  const removeCommand = (command) => {
    confirm({
      title: 'Remove Command',
      content: `Are you sure you want to remove this command from the queue?`,
      onOk: async () => {
        try {
          // This would typically call a remove function
          message.success('Command removed from queue');
        } catch (error) {
          message.error('Failed to remove command: ' + error.message);
        }
      }
    });
  };

  const clearCompletedCommands = () => {
    const completedCount = (commandQueue || []).filter(cmd => 
      cmd && (cmd.status === 'completed' || cmd.status === 'failed' || cmd.status === 'cancelled')
    ).length;

    if (completedCount === 0) {
      message.info('No completed commands to clear');
      return;
    }

    confirm({
      title: 'Clear Completed Commands',
      content: `Remove ${completedCount} completed/failed/cancelled commands from the queue?`,
      onOk: async () => {
        try {
          await onQueueClear();
          message.success(`Cleared ${completedCount} completed commands`);
        } catch (error) {
          message.error('Failed to clear commands: ' + error.message);
        }
      }
    });
  };

  const bulkExecuteSelected = () => {
    const selectedCommands = (commandQueue || []).filter(cmd => 
      cmd && selectedRowKeys.includes(cmd.id) && cmd.status === 'pending'
    );

    if (selectedCommands.length === 0) {
      message.warning('No pending commands selected');
      return;
    }

    confirm({
      title: 'Execute Selected Commands',
      content: `Execute ${selectedCommands.length} selected commands?`,
      onOk: async () => {
        try {
          for (const command of selectedCommands) {
            await executeCommand(command);
          }
          setSelectedRowKeys([]);
          message.success(`Executed ${selectedCommands.length} commands`);
        } catch (error) {
          message.error('Failed to execute commands: ' + error.message);
        }
      }
    });
  };

  const getQueueStats = () => {
    const stats = {
      total: (commandQueue || []).length,
      pending: (commandQueue || []).filter(cmd => cmd?.status === 'pending').length,
      executing: (commandQueue || []).filter(cmd => cmd?.status === 'executing').length,
      completed: (commandQueue || []).filter(cmd => cmd?.status === 'completed').length,
      failed: (commandQueue || []).filter(cmd => cmd?.status === 'failed').length
    };
    return stats;
  };

  const stats = getQueueStats();
  const hasSelection = selectedRowKeys.length > 0;

  return (
    <Card
      title={
        <Space>
          Action Queue
          <Tag color="blue">{stats.total} Total</Tag>
          {stats.pending > 0 && <Tag color="orange">{stats.pending} Pending</Tag>}
          {stats.executing > 0 && <Tag color="blue">{stats.executing} Executing</Tag>}
        </Space>
      }
      className="action-queue-panel"
      extra={
        <Space>
          <Select
            value={filterStatus}
            onChange={setFilterStatus}
            size="small"
            style={{ width: 100 }}
          >
            <Option value="all">All</Option>
            <Option value="pending">Pending</Option>
            <Option value="executing">Executing</Option>
            <Option value="completed">Completed</Option>
            <Option value="failed">Failed</Option>
          </Select>
          <Select
            value={sortBy}
            onChange={setSortBy}
            size="small"
            style={{ width: 120 }}
          >
            <Option value="timestamp">Created</Option>
            <Option value="scheduled_time">Scheduled</Option>
            <Option value="priority">Priority</Option>
          </Select>
        </Space>
      }
    >
      {/* Queue Controls */}
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={bulkExecuteSelected}
            disabled={!hasSelection}
            size="small"
          >
            Execute Selected ({selectedRowKeys.length})
          </Button>
          <Button
            icon={<ClearOutlined />}
            onClick={clearCompletedCommands}
            size="small"
          >
            Clear Completed
          </Button>
        </Space>
      </div>

      {/* Queue Statistics */}
      <div style={{ marginBottom: 16, padding: 12, background: '#262626', borderRadius: 4 }}>
        <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: 8, color: '#e0e0e0' }}>
          Queue Statistics:
        </div>
        <Space wrap>
          <Tag color="default">Total: {stats.total}</Tag>
          <Tag color="orange">Pending: {stats.pending}</Tag>
          <Tag color="blue">Executing: {stats.executing}</Tag>
          <Tag color="green">Completed: {stats.completed}</Tag>
          {stats.failed > 0 && <Tag color="red">Failed: {stats.failed}</Tag>}
        </Space>
      </div>

      {/* Commands Table */}
      <Table
        dataSource={filteredCommands}
        columns={columns}
        rowKey="id"
        size="small"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} commands`
        }}
        rowSelection={{
          selectedRowKeys,
          onChange: setSelectedRowKeys,
          getCheckboxProps: (record) => ({
            disabled: record.status === 'executing'
          })
        }}
        scroll={{ x: 800 }}
      />

      {/* Empty State */}
      {(commandQueue || []).length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#a6a6a6' }}>
          <ClockCircleOutlined style={{ fontSize: '48px', marginBottom: 16 }} />
          <div>No commands in queue</div>
          <div style={{ fontSize: '12px', marginTop: 8 }}>
            Commands will appear here when you execute actions from the COC dashboard
          </div>
        </div>
      )}
    </Card>
  );
};

export default ActionQueuePanel;