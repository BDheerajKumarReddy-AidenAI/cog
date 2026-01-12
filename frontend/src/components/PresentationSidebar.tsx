import React, { useState, useCallback, useRef } from 'react';
import { saveAs } from 'file-saver';
import html2canvas from 'html2canvas';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, AreaChart, Area,
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell,
} from 'recharts';
import { PresentationConfig, SlideContent, ChartConfig } from '../types';
import { presentationApi } from '../services/api';
import './PresentationSidebar.css';

// Mini chart preview for slide thumbnails
const MiniChartPreview: React.FC<{ config: ChartConfig }> = ({ config }) => {
  const { chartType, data, xAxisKey, yAxisKeys, colors } = config;
  const width = 120;
  const height = 70;

  switch (chartType) {
    case 'line':
      return (
        <LineChart width={width} height={height} data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          {yAxisKeys.map((key, index) => (
            <Line key={key} type="monotone" dataKey={key} stroke={colors[index] || '#8884d8'} strokeWidth={1} dot={false} />
          ))}
        </LineChart>
      );
    case 'bar':
      return (
        <BarChart width={width} height={height} data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          {yAxisKeys.map((key, index) => (
            <Bar key={key} dataKey={key} fill={colors[index] || '#8884d8'} />
          ))}
        </BarChart>
      );
    case 'pie':
      return (
        <PieChart width={width} height={height}>
          <Pie data={data} dataKey={yAxisKeys[0]} nameKey={xAxisKey} cx="50%" cy="50%" outerRadius={25} innerRadius={0}>
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
        </PieChart>
      );
    case 'area':
      return (
        <AreaChart width={width} height={height} data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          {yAxisKeys.map((key, index) => (
            <Area key={key} type="monotone" dataKey={key} stroke={colors[index] || '#8884d8'} fill={colors[index] || '#8884d8'} fillOpacity={0.3} />
          ))}
        </AreaChart>
      );
    case 'scatter':
      return (
        <ScatterChart width={width} height={height} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          <Scatter data={data} fill={colors[0] || '#8884d8'} />
        </ScatterChart>
      );
    default:
      return null;
  }
};

// Helper component to render a chart for capture
const ChartForCapture: React.FC<{
  config: ChartConfig;
  onRef: (el: HTMLDivElement | null) => void;
}> = ({ config, onRef }) => {
  const { chartType, data, xAxisKey, yAxisKeys, colors } = config;

  const renderChart = () => {
    switch (chartType) {
      case 'line':
        return (
          <LineChart width={800} height={400} data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xAxisKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            {yAxisKeys.map((key, index) => (
              <Line key={key} type="monotone" dataKey={key} stroke={colors[index] || '#8884d8'} strokeWidth={2} />
            ))}
          </LineChart>
        );
      case 'bar':
        return (
          <BarChart width={800} height={400} data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
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
          <PieChart width={800} height={400}>
            <Pie data={data} dataKey={yAxisKeys[0]} nameKey={xAxisKey} cx="50%" cy="50%" outerRadius={150} label>
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
          <AreaChart width={800} height={400} data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xAxisKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            {yAxisKeys.map((key, index) => (
              <Area key={key} type="monotone" dataKey={key} stroke={colors[index] || '#8884d8'} fill={colors[index] || '#8884d8'} fillOpacity={0.3} />
            ))}
          </AreaChart>
        );
      case 'scatter':
        return (
          <ScatterChart width={800} height={400} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xAxisKey} />
            <YAxis dataKey={yAxisKeys[0]} />
            <Tooltip />
            <Legend />
            <Scatter name={yAxisKeys[0]} data={data} fill={colors[0] || '#8884d8'} />
          </ScatterChart>
        );
      default:
        return null;
    }
  };

  return (
    <div ref={onRef} style={{ background: 'white', padding: '20px' }}>
      <h3 style={{ textAlign: 'center', marginBottom: '20px' }}>{config.title}</h3>
      {renderChart()}
    </div>
  );
};

interface PresentationSidebarProps {
  presentation: PresentationConfig | null;
  onClose: () => void;
  onUpdatePresentation: (presentation: PresentationConfig) => void;
}

const PresentationSidebar: React.FC<PresentationSidebarProps> = ({
  presentation,
  onClose,
  onUpdatePresentation,
}) => {
  console.log("hello from PresentationSidebar" , presentation);
  const [selectedSlide, setSelectedSlide] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [editingSlide, setEditingSlide] = useState<SlideContent | null>(null);
  const [chartsToCapture, setChartsToCapture] = useState<{ slideId: string; config: ChartConfig }[]>([]);
  const chartRefs = useRef<Map<string, HTMLDivElement | null>>(new Map());

  const handleSlideClick = (slideId: string) => {
    setSelectedSlide(slideId === selectedSlide ? null : slideId);
    const slide = presentation?.slides.find(s => s.id === slideId);
    if (slide) {
      setEditingSlide({ ...slide });
    }
  };

  const handleSlideUpdate = useCallback(() => {
    if (!presentation || !editingSlide) return;

    const updatedSlides = presentation.slides.map(s =>
      s.id === editingSlide.id ? editingSlide : s
    );

    onUpdatePresentation({
      ...presentation,
      slides: updatedSlides,
    });

    setSelectedSlide(null);
    setEditingSlide(null);
  }, [presentation, editingSlide, onUpdatePresentation]);

  const handleDeleteSlide = useCallback((slideId: string) => {
    if (!presentation) return;

    const updatedSlides = presentation.slides
      .filter(s => s.id !== slideId)
      .map((s, index) => ({ ...s, order: index + 1 }));

    onUpdatePresentation({
      ...presentation,
      slides: updatedSlides,
    });
  }, [presentation, onUpdatePresentation]);

  const handleMoveSlide = useCallback((slideId: string, direction: 'up' | 'down') => {
    if (!presentation) return;

    const slideIndex = presentation.slides.findIndex(s => s.id === slideId);
    if (
      (direction === 'up' && slideIndex === 0) ||
      (direction === 'down' && slideIndex === presentation.slides.length - 1)
    ) {
      return;
    }

    const newSlides = [...presentation.slides];
    const targetIndex = direction === 'up' ? slideIndex - 1 : slideIndex + 1;
    [newSlides[slideIndex], newSlides[targetIndex]] = [newSlides[targetIndex], newSlides[slideIndex]];

    const reorderedSlides = newSlides.map((s, index) => ({ ...s, order: index + 1 }));

    onUpdatePresentation({
      ...presentation,
      slides: reorderedSlides,
    });
  }, [presentation, onUpdatePresentation]);

  // Capture chart images for slides that have chartConfig but no chartImage
  const captureChartImages = async (): Promise<SlideContent[]> => {
    if (!presentation) return [];

    const slidesWithCharts = presentation.slides.filter(
      slide => slide.contentType === 'chart' && slide.chartConfig && !slide.chartImage
    );

    if (slidesWithCharts.length === 0) {
      return presentation.slides;
    }

    // Identify slides that need chart capture
    setChartsToCapture(slidesWithCharts.map(slide => ({
      slideId: slide.id,
      config: slide.chartConfig!,
    })));

    // Wait for charts to render
    await new Promise(resolve => setTimeout(resolve, 500));

    // Capture each chart
    const updatedSlides = await Promise.all(
      presentation.slides.map(async (slide) => {
        if (slide.contentType === 'chart' && slide.chartConfig && !slide.chartImage) {
          const chartElement = chartRefs.current.get(slide.id);
          if (chartElement) {
            try {
              const canvas = await html2canvas(chartElement, {
                backgroundColor: '#ffffff',
                scale: 2,
              });
              const imageData = canvas.toDataURL('image/png').split(',')[1];
              return { ...slide, chartImage: imageData };
            } catch (error) {
              console.error(`Failed to capture chart for slide ${slide.id}:`, error);
            }
          }
        }
        return slide;
      })
    );

    setChartsToCapture([]);
    return updatedSlides;
  };

  const handleExport = async () => {
    if (!presentation) return;

    setIsExporting(true);
    try {
      // Capture any charts that need images
      const slidesWithImages = await captureChartImages();
      const blob = await presentationApi.generatePptx(presentation.title, slidesWithImages);
      saveAs(blob, `${presentation.title.replace(/\s+/g, '_')}.pptx`);
    } catch (error) {
      console.error('Failed to export presentation:', error);
    } finally {
      setIsExporting(false);
    }
  };

  if (!presentation) {
    return null;
  }

  return (
    <div className="presentation-sidebar">
      <div className="sidebar-header">
        <h3>Presentation Preview</h3>
        <button className="close-btn" onClick={onClose}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div className="presentation-title">
        <h4>{presentation.title}</h4>
        <span>{presentation.slides.length} slides</span>
      </div>

      <div className="slides-list">
        {presentation.slides.map((slide) => (
          <div key={slide.id} className="slide-item-wrapper">
            <div
              className={`slide-item ${selectedSlide === slide.id ? 'selected' : ''}`}
              onClick={() => handleSlideClick(slide.id)}
            >
              <div className="slide-thumbnail">
                <span className="slide-number">{slide.order}</span>
                <div className="thumbnail-content">
                  {slide.contentType === 'chart' && slide.chartConfig ? (
                    <MiniChartPreview config={slide.chartConfig} />
                  ) : slide.contentType === 'chart' ? (
                    <div className="chart-indicator">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M3 3v18h18v-2H5V3H3zm16 10h-2v6h2v-6zm-4-3h-2v9h2v-9zm-4 5h-2v4h2v-4zm-4-2H5v6h2v-6z"/>
                      </svg>
                    </div>
                  ) : (
                    <div className="content-placeholder">
                      {slide.contentType === 'text' && '📄'}
                      {slide.contentType === 'bullets' && '📋'}
                      {slide.contentType === 'mixed' && '📊'}
                    </div>
                  )}
                </div>
              </div>
              <div className="slide-info">
                <span className="slide-title">{slide.title}</span>
                <span className="slide-type">{slide.contentType}</span>
              </div>
              <div className="slide-actions">
                <button
                  className="action-btn"
                  onClick={(e) => { e.stopPropagation(); handleMoveSlide(slide.id, 'up'); }}
                  disabled={slide.order === 1}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="18 15 12 9 6 15"></polyline>
                  </svg>
                </button>
                <button
                  className="action-btn"
                  onClick={(e) => { e.stopPropagation(); handleMoveSlide(slide.id, 'down'); }}
                  disabled={slide.order === presentation.slides.length}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="6 9 12 15 18 9"></polyline>
                  </svg>
                </button>
                <button
                  className="action-btn delete"
                  onClick={(e) => { e.stopPropagation(); handleDeleteSlide(slide.id); }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                </button>
              </div>
            </div>

            {selectedSlide === slide.id && editingSlide && (
              <div className="slide-editor">
                <div className="editor-field">
                  <label>Title</label>
                  <input
                    type="text"
                    value={editingSlide.title}
                    onChange={(e) => setEditingSlide({ ...editingSlide, title: e.target.value })}
                  />
                </div>
                <div className="editor-field">
                  <label>Content Type</label>
                  <select
                    value={editingSlide.contentType}
                    onChange={(e) => setEditingSlide({
                      ...editingSlide,
                      contentType: e.target.value as SlideContent['contentType'],
                    })}
                  >
                    <option value="text">Text</option>
                    <option value="bullets">Bullets</option>
                    <option value="chart">Chart</option>
                    <option value="mixed">Mixed</option>
                  </select>
                </div>
                {editingSlide.contentType === 'text' && (
                  <div className="editor-field">
                    <label>Content</label>
                    <textarea
                      value={typeof editingSlide.content === 'string' ? editingSlide.content : ''}
                      onChange={(e) => setEditingSlide({ ...editingSlide, content: e.target.value })}
                    />
                  </div>
                )}
                {editingSlide.contentType === 'bullets' && (
                  <div className="editor-field">
                    <label>Bullet Points (one per line)</label>
                    <textarea
                      value={Array.isArray(editingSlide.content) ? editingSlide.content.join('\n') : ''}
                      onChange={(e) => setEditingSlide({
                        ...editingSlide,
                        content: e.target.value.split('\n'),
                      })}
                    />
                  </div>
                )}
                <div className="editor-field">
                  <label>Speaker Notes</label>
                  <textarea
                    value={editingSlide.notes || ''}
                    onChange={(e) => setEditingSlide({ ...editingSlide, notes: e.target.value })}
                    placeholder="Add speaker notes..."
                  />
                </div>
                <div className="editor-actions">
                  <button className="save-btn" onClick={handleSlideUpdate}>Save Changes</button>
                  <button className="cancel-btn" onClick={() => { setSelectedSlide(null); setEditingSlide(null); }}>
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <button
          className="export-btn"
          onClick={handleExport}
          disabled={isExporting}
        >
          {isExporting ? 'Exporting...' : 'Download PPTX'}
        </button>
      </div>

      {/* Hidden chart rendering area for capture */}
      {chartsToCapture.length > 0 && (
        <div style={{ position: 'absolute', left: '-9999px', top: 0 }}>
          {chartsToCapture.map(({ slideId, config }) => (
            <ChartForCapture
              key={slideId}
              config={config}
              onRef={(el) => {
                if (el) chartRefs.current.set(slideId, el);
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default PresentationSidebar;