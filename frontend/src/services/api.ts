import axios from 'axios';
import { ChatResponse, PresentationConfig, SlideContent } from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatApi = {
  sendMessage: async (message: string, conversationId?: string): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat/', {
      message,
      conversation_id: conversationId,
    });
    return response.data;
  },

  handleSuggestion: async (suggestion: string, conversationId: string): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat/suggestion', {
      suggestion,
      conversation_id: conversationId,
    });
    return response.data;
  },

  clearConversation: async (conversationId: string): Promise<void> => {
    await api.delete(`/chat/${conversationId}`);
  },
};

export const presentationApi = {
  generatePptx: async (title: string, slides: SlideContent[]): Promise<Blob> => {
    const response = await api.post(
      '/presentation/generate',
      { title, slides },
      { responseType: 'blob' }
    );
    return response.data;
  },

  preview: async (title: string, slides: SlideContent[]): Promise<PresentationConfig> => {
    const response = await api.post<PresentationConfig>('/presentation/preview', {
      title,
      slides,
    });
    return response.data;
  },
};

export default api;
