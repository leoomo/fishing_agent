import React, { useRef, useEffect } from 'react';
import { Card, Typography, Tag, Space, Tooltip, Badge } from 'antd';
import type { WorkflowStep } from '../api/workflow';

const { Title, Text } = Typography;

interface WorkflowDAGProps {
  steps: WorkflowStep[];
  onStepClick?: (step: WorkflowStep) => void;
  width?: number;
  height?: number;
}

const WorkflowDAG: React.FC<WorkflowDAGProps> = ({
  steps,
  onStepClick,
  width = 800,
  height = 400
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    canvas.width = width;
    canvas.height = height;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Group steps by order (level)
    const levels = new Map<number, WorkflowStep[]>();
    steps.forEach(step => {
      if (!levels.has(step.order)) {
        levels.set(step.order, []);
      }
      levels.get(step.order)!.push(step);
    });

    // Calculate positions
    const levelWidth = width / (levels.size + 1);
    const nodeWidth = 120;
    const nodeHeight = 60;
    const verticalGap = 30;

    // Draw edges first (so they appear behind nodes)
    ctx.strokeStyle = '#d9d9d9';
    ctx.lineWidth = 2;

    steps.forEach(step => {
      const dependsOn = step.depends_on || [];
      dependsOn.forEach(depId => {
        const depStep = steps.find(s => s.id === depId);
        if (depStep) {
          const fromX = levelWidth * depStep.order;
          const fromY = (levels.get(depStep.order)!.indexOf(depStep) + 1) * (nodeHeight + verticalGap);
          const toX = levelWidth * step.order;
          const toY = (levels.get(step.order)!.indexOf(step) + 1) * (nodeHeight + verticalGap);

          // Draw line
          ctx.beginPath();
          ctx.moveTo(fromX + nodeWidth / 2, fromY + nodeHeight / 2);

          // Create curved line
          const controlX = (fromX + toX) / 2;
          ctx.quadraticCurveTo(
            controlX, fromY + nodeHeight / 2,
            controlX, toY + nodeHeight / 2
          );
          ctx.quadraticCurveTo(
            controlX, toY + nodeHeight / 2,
            toX + nodeWidth / 2, toY + nodeHeight / 2
          );

          ctx.stroke();

          // Draw arrow
          const angle = Math.atan2(toY - fromY, toX - fromX);
          const arrowLength = 10;
          ctx.beginPath();
          ctx.moveTo(toX + nodeWidth / 2, toY + nodeHeight / 2);
          ctx.lineTo(
            toX + nodeWidth / 2 - arrowLength * Math.cos(angle - Math.PI / 6),
            toY + nodeHeight / 2 - arrowLength * Math.sin(angle - Math.PI / 6)
          );
          ctx.moveTo(toX + nodeWidth / 2, toY + nodeHeight / 2);
          ctx.lineTo(
            toX + nodeWidth / 2 - arrowLength * Math.cos(angle + Math.PI / 6),
            toY + nodeHeight / 2 - arrowLength * Math.sin(angle + Math.PI / 6)
          );
          ctx.stroke();
        }
      });
    });

    // Draw nodes
    steps.forEach(step => {
      const levelIndex = levels.get(step.order)!.indexOf(step);
      const x = levelWidth * step.order - nodeWidth / 2;
      const y = (levelIndex + 1) * (nodeHeight + verticalGap);

      // Node background
      ctx.fillStyle = '#ffffff';
      ctx.strokeStyle = '#1890ff';
      ctx.lineWidth = 2;

      // Draw rounded rectangle
      ctx.beginPath();
      ctx.roundRect(x, y, nodeWidth, nodeHeight, 8);
      ctx.fill();
      ctx.stroke();

      // Node content
      ctx.fillStyle = '#262626';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      // Step name
      const nameLines = wrapText(ctx, step.name, nodeWidth - 20);
      const lineHeight = 16;
      const startY = y + nodeHeight / 2 - (nameLines.length * lineHeight) / 2;

      nameLines.forEach((line, index) => {
        ctx.fillText(line, x + nodeWidth / 2, startY + index * lineHeight);
      });

      // Task type
      ctx.font = '10px sans-serif';
      ctx.fillStyle = '#8c8c8c';
      ctx.fillText(step.task_type.toUpperCase(), x + nodeWidth / 2, y + nodeHeight - 10);
    });

  }, [steps, width, height]);

  // Helper function to wrap text
  const wrapText = (ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string[] => {
    const words = text.split(' ');
    const lines: string[] = [];
    let currentLine = '';

    words.forEach(word => {
      const testLine = currentLine ? `${currentLine} ${word}` : word;
      const metrics = ctx.measureText(testLine);

      if (metrics.width > maxWidth && currentLine) {
        lines.push(currentLine);
        currentLine = word;
      } else {
        currentLine = testLine;
      }
    });

    if (currentLine) {
      lines.push(currentLine);
    }

    return lines;
  };

  // Handle canvas click
  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onStepClick) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Group steps by order
    const levels = new Map<number, WorkflowStep[]>();
    steps.forEach(step => {
      if (!levels.has(step.order)) {
        levels.set(step.order, []);
      }
      levels.get(step.order)!.push(step);
    });

    // Calculate positions and check if click is on a step
    const levelWidth = width / (levels.size + 1);
    const nodeWidth = 120;
    const nodeHeight = 60;
    const verticalGap = 30;

    steps.forEach(step => {
      const levelIndex = levels.get(step.order)!.indexOf(step);
      const nodeX = levelWidth * step.order - nodeWidth / 2;
      const nodeY = (levelIndex + 1) * (nodeHeight + verticalGap);

      // Check if click is within node bounds
      if (
        x >= nodeX && x <= nodeX + nodeWidth &&
        y >= nodeY && y <= nodeY + nodeHeight
      ) {
        onStepClick(step);
      }
    });
  };

  // Create legend for the task types
  const getTaskTypeColor = (taskType: string) => {
    const colors: Record<string, string> = {
      taobao: 'orange',
      jd: 'red',
      shop_crawl: 'blue',
      shop_analyze: 'purple',
      product_detail: 'green',
      category_crawl: 'cyan',
    };
    return colors[taskType] || 'default';
  };

  return (
    <Card>
      <Title level={4}>工作流可视化</Title>

      {/* Legend */}
      <Space wrap style={{ marginBottom: 16 }}>
        <Text strong>任务类型：</Text>
        {Array.from(new Set(steps.map(s => s.task_type))).map(taskType => (
          <Tag key={taskType} color={getTaskTypeColor(taskType)}>
            {taskType}
          </Tag>
        ))}
      </Space>

      {/* Canvas */}
      <div style={{ border: '1px solid #d9d9d9', borderRadius: '4px', overflow: 'auto' }}>
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          onClick={handleCanvasClick}
          style={{ cursor: onStepClick ? 'pointer' : 'default' }}
        />
      </div>

      {/* Step List */}
      <div style={{ marginTop: 16 }}>
        <Title level={5}>步骤列表</Title>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          {steps
            .sort((a, b) => a.order - b.order)
            .map((step, index) => (
              <div
                key={step.id}
                style={{
                  padding: '8px 12px',
                  border: '1px solid #d9d9d9',
                  borderRadius: '4px',
                  backgroundColor: '#fafafa',
                  cursor: onStepClick ? 'pointer' : 'default',
                }}
                onClick={() => onStepClick?.(step)}
              >
                <Space>
                  <Badge count={index + 1} style={{ backgroundColor: '#52c41a' }} />
                  <div>
                    <Text strong>{step.name}</Text>
                    <br />
                    <Space size="small">
                      <Tag color={getTaskTypeColor(step.task_type)}>
                        {step.task_type}
                      </Tag>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        ID: {step.id}
                      </Text>
                      {step.depends_on && step.depends_on.length > 0 && (
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          依赖: {step.depends_on.join(', ')}
                        </Text>
                      )}
                    </Space>
                  </div>
                </Space>
              </div>
            ))}
        </Space>
      </div>
    </Card>
  );
};

export default WorkflowDAG;