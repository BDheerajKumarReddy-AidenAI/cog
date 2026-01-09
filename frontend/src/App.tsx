import React, { useCallback, useRef } from 'react';
import { useChat } from './hooks/useChat';
import ChatWindow from './components/ChatWindow';
import PresentationSidebar from './components/PresentationSidebar';
import html2canvas from 'html2canvas';
import './App.css';

const App: React.FC = () => {
  const {
    messages,
    isLoading,
    currentPresentation,
    sendMessage,
    handleSuggestion,
    clearChat,
    updatePresentation,
    setCurrentPresentation,
  } = useChat();

  const chartRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  const handleAddChartToPresentation = useCallback(async (chartIndex: number) => {
    const lastAssistantMessage = [...messages].reverse().find(m => m.role === 'assistant');
    if (!lastAssistantMessage?.charts?.[chartIndex]) return;

    const chart = lastAssistantMessage.charts[chartIndex];
    const chartElement = chartRefs.current.get(chartIndex);

    let chartImage = '';
    if (chartElement) {
      try {
        const canvas = await html2canvas(chartElement, {
          backgroundColor: '#ffffff',
          scale: 2,
        });
        chartImage = canvas.toDataURL('image/png').split(',')[1];
      } catch (error) {
        console.error('Failed to capture chart:', error);
      }
    }

    if (currentPresentation) {
      const newSlide = {
        id: `slide-${currentPresentation.slides.length + 1}`,
        order: currentPresentation.slides.length + 1,
        title: chart.title,
        contentType: 'chart' as const,
        content: '',
        chartConfig: chart,
        chartImage,
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
            chartImage,
          },
        ],
      });
    }
  }, [messages, currentPresentation, updatePresentation, setCurrentPresentation]);

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
        />
      </div>

      {currentPresentation && (
        <PresentationSidebar
          presentation={currentPresentation}
          onClose={handleCloseSidebar}
          onUpdatePresentation={updatePresentation}
        />
      )}
    </div>
  );
};

export default App;
