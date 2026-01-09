import { useState, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Message, ChartConfig, PresentationConfig } from '../types';
import { chatApi } from '../services/api';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPresentation, setCurrentPresentation] = useState<PresentationConfig | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    setIsLoading(true);
    setError(null);

    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await chatApi.sendMessage(content, conversationId || undefined);

      if (!conversationId) {
        setConversationId(response.conversation_id);
      }

      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        charts: response.charts,
        presentations: response.presentations,
        suggestions: response.suggestions,
      };

      setMessages(prev => [...prev, assistantMessage]);

      if (response.presentations && response.presentations.length > 0) {
        setCurrentPresentation(response.presentations[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);

  const handleSuggestion = useCallback(async (suggestion: string) => {
    if (!conversationId) return;

    setIsLoading(true);
    setError(null);

    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content: suggestion,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await chatApi.handleSuggestion(suggestion, conversationId);

      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        charts: response.charts,
        presentations: response.presentations,
        suggestions: response.suggestions,
      };

      setMessages(prev => [...prev, assistantMessage]);

      if (response.presentations && response.presentations.length > 0) {
        setCurrentPresentation(response.presentations[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);

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
    sendMessage,
    handleSuggestion,
    clearChat,
    updatePresentation,
    addChartToPresentation,
    setCurrentPresentation,
  };
}
