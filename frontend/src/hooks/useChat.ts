import { useState, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Message, ChartConfig, PresentationConfig } from '../types';
import { chatApi, StreamEvent } from '../services/api';

export interface ToolStatus {
  isActive: boolean;
  currentTool: string | null;
  toolHistory: string[];
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPresentation, setCurrentPresentation] = useState<PresentationConfig | null>(null);
  const [toolStatus, setToolStatus] = useState<ToolStatus>({
    isActive: false,
    currentTool: null,
    toolHistory: [],
  });

  const sendMessage = useCallback(async (content: string) => {
    setIsLoading(true);
    setError(null);
    setToolStatus({ isActive: false, currentTool: null, toolHistory: [] });

    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev: Message[]) => [...prev, userMessage]);

    try {
      const newConvId = await chatApi.sendMessageStream(
        content,
        conversationId || undefined,
        (event: StreamEvent) => {
          switch (event.type) {
            case 'tool_start':
              setToolStatus((prev: ToolStatus) => ({
                isActive: true,
                currentTool: event.tool || null,
                toolHistory: [...prev.toolHistory, event.tool || ''],
              }));
              break;

            case 'tool_end':
              setToolStatus((prev: ToolStatus) => ({
                ...prev,
                isActive: false,
                currentTool: null,
              }));
              break;

            case 'presentation':
              // Immediately show presentation preview when created
              if (event.presentation) {
                setCurrentPresentation(event.presentation as PresentationConfig);
              }
              break;

            case 'final':
              const assistantMessage: Message = {
                id: uuidv4(),
                role: 'assistant',
                content: event.response || '',
                timestamp: new Date(),
                charts: event.charts,
                presentations: event.presentations,
                suggestions: event.suggestions,
              };

              setMessages((prev: Message[]) => [...prev, assistantMessage]);

              if (event.presentations && event.presentations.length > 0) {
                setCurrentPresentation(event.presentations[0]);
              }

              if (event.conversation_id && !conversationId) {
                setConversationId(event.conversation_id);
              }
              break;

            case 'error':
              setError(event.message || 'An error occurred');
              break;
          }
        }
      );

      if (!conversationId && newConvId) {
        setConversationId(newConvId);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
      setToolStatus({ isActive: false, currentTool: null, toolHistory: [] });
    }
  }, [conversationId]);

  const handleSuggestion = useCallback(async (suggestion: string) => {
    // Use the same streaming endpoint as sendMessage
    await sendMessage(suggestion);
  }, [sendMessage]);

  const clearChat = useCallback(async () => {
    if (conversationId) {
      try {
        await chatApi.clearConversation(conversationId);
      } catch {
        // Ignore errors when clearing
      }
    }
    setMessages([]);
    setConversationId(null);
    setCurrentPresentation(null);
    setError(null);
  }, [conversationId]);

  const updatePresentation = useCallback((presentation: PresentationConfig) => {
    setCurrentPresentation(presentation);
  }, []);

  const addChartToPresentation = useCallback((chart: ChartConfig, chartImage: string) => {
    if (!currentPresentation) return;

    const newSlide = {
      id: `slide-${currentPresentation.slides.length + 1}`,
      order: currentPresentation.slides.length + 1,
      title: chart.title,
      contentType: 'chart' as const,
      content: '',
      chartConfig: chart,
      chartImage,
    };

    setCurrentPresentation({
      ...currentPresentation,
      slides: [...currentPresentation.slides, newSlide],
    });
  }, [currentPresentation]);

  return {
    messages,
    conversationId,
    isLoading,
    error,
    currentPresentation,
    toolStatus,
    sendMessage,
    handleSuggestion,
    clearChat,
    updatePresentation,
    addChartToPresentation,
    setCurrentPresentation,
  };
}
