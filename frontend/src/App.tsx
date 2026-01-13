import React, { useCallback } from 'react';
import { useChat } from './hooks/useChat';
import { ChartConfig } from './types';
import ChatWindow from './components/ChatWindow';
import PresentationSidebar from './components/PresentationSidebar';
import './App.css';

const App: React.FC = () => {
  const {
    messages,
    isLoading,
    currentPresentation,
    toolStatus,
    sendMessage,
    handleSuggestion,
    clearChat,
    updatePresentation,
    setCurrentPresentation,
    updateCurrentSlide,
  } = useChat();

  const handleAddChartToPresentation = useCallback((chart: ChartConfig, chartImage?: string) => {
    const normalizedImage = chartImage || '';

    if (currentPresentation) {
      const newSlide = {
        id: `slide-${currentPresentation.slides.length + 1}`,
        order: currentPresentation.slides.length + 1,
        title: chart.title,
        contentType: 'chart' as const,
        content: '',
        chartConfig: chart,
        chartImage: normalizedImage,
      };

      updatePresentation({
        ...currentPresentation,
        slides: [...currentPresentation.slides, newSlide],
      });
    } else {
      setCurrentPresentation({
        type: 'presentation',
        presentationId: `pres-${Date.now()}`,
        title: 'Analytics Report',
        slides: [
          {
            id: 'slide-1',
            order: 1,
            title: chart.title,
            contentType: 'chart',
            content: '',
            chartConfig: chart,
            chartImage: normalizedImage,
          },
        ],
      });
    }
  }, [currentPresentation, updatePresentation, setCurrentPresentation]);

  const handleCloseSidebar = useCallback(() => {
    setCurrentPresentation(null);
  }, [setCurrentPresentation]);

  return (
    <div className="app-container">
      <div className={`main-content ${currentPresentation ? 'with-sidebar' : ''}`}>
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          onSendMessage={sendMessage}
          onSuggestionClick={handleSuggestion}
          onAddChartToPresentation={handleAddChartToPresentation}
          onClearChat={clearChat}
          toolStatus={toolStatus}
        />
      </div>

      {currentPresentation && (
        <PresentationSidebar
          presentation={currentPresentation}
          onClose={handleCloseSidebar}
          onUpdatePresentation={updatePresentation}
          onSelectSlide={updateCurrentSlide}
        />
      )}
    </div>
  );
};

export default App;
