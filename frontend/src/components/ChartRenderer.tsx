import React, { useRef, useCallback } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  AreaChart,
  Area,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import html2canvas from 'html2canvas';
import { saveAs } from 'file-saver';
import { ChartConfig } from '../types';
import './ChartRenderer.css';

interface ChartRendererProps {
  config: ChartConfig;
  onCapture?: (imageData: string) => void;
}

const ChartRenderer: React.FC<ChartRendererProps> = ({ config, onCapture }) => {
  const chartRef = useRef<HTMLDivElement>(null);

  const handleDownload = useCallback(async () => {
    if (!chartRef.current) return;

    try {
      const canvas = await html2canvas(chartRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
      });
      canvas.toBlob((blob) => {
        if (blob) {
          saveAs(blob, `${config.title.replace(/\s+/g, '_')}.png`);
        }
      });
    } catch (error) {
      console.error('Failed to download chart:', error);
    }
  }, [config.title]);

  const handleCapture = useCallback(async () => {
    if (!chartRef.current || !onCapture) return;

    try {
      const canvas = await html2canvas(chartRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
      });
      const imageData = canvas.toDataURL('image/png').split(',')[1];
      onCapture(imageData);
    } catch (error) {
      console.error('Failed to capture chart:', error);
    }
  }, [onCapture]);

  const renderChart = () => {
    const { chartType, data, xAxisKey, yAxisKeys, colors } = config;

    const commonProps = {
      data,
      margin: { top: 20, right: 30, left: 20, bottom: 5 },
    };

    switch (chartType) {
      case 'line':
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xAxisKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            {yAxisKeys.map((key, index) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={colors[index] || '#8884d8'}
                strokeWidth={2}
                dot={{ r: 4 }}
              />
            ))}
          </LineChart>
        );

      case 'bar':
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xAxisKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            {yAxisKeys.map((key, index) => (
              <Bar key={key} dataKey={key} fill={colors[index] || '#8884d8'} />
            ))}
          </BarChart>
        );

      case 'pie':
        return (
          <PieChart>
            <Pie
              data={data}
              dataKey={yAxisKeys[0]}
              nameKey={xAxisKey}
              cx="50%"
              cy="50%"
              outerRadius={100}
              label
            >
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        );

      case 'area':
        return (
          <AreaChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xAxisKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            {yAxisKeys.map((key, index) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stroke={colors[index] || '#8884d8'}
                fill={colors[index] || '#8884d8'}
                fillOpacity={0.3}
              />
            ))}
          </AreaChart>
        );

      case 'scatter':
        return (
          <ScatterChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xAxisKey} name={xAxisKey} />
            <YAxis dataKey={yAxisKeys[0]} name={yAxisKeys[0]} />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
            <Legend />
            <Scatter name={yAxisKeys[0]} data={data} fill={colors[0] || '#8884d8'} />
          </ScatterChart>
        );

      default:
        return <p>Unsupported chart type: {chartType}</p>;
    }
  };

  return (
    <div className="chart-renderer">
      <h3 className="chart-title">{config.title}</h3>
      <div ref={chartRef} className="chart-container">
        <ResponsiveContainer width="100%" height={300}>
          {renderChart()}
        </ResponsiveContainer>
      </div>
      <div className="chart-actions">
        <button onClick={handleDownload} className="chart-action-btn">
          Download PNG
        </button>
        {onCapture && (
          <button onClick={handleCapture} className="chart-action-btn secondary">
            Add to Presentation
          </button>
        )}
      </div>
    </div>
  );
};

export default ChartRenderer;
