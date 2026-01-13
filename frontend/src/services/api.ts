import axios from 'axios';
import { ChatResponse, PresentationConfig, SlideContent } from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface StreamEvent {
  type: 'state_update' | 'final' | 'error' | 'tool_start' | 'tool_end' | 'presentation' | 'presentation_update';
  tool?: string;
  input?: Record<string, unknown>;
  conversation_id?: string;
  response?: string;
  charts?: ChatResponse['charts'];
  presentation?: ChatResponse['presentation'];
  new_charts?: ChatResponse['charts'];
  current_slide?: number;
  tool_output?: {
    name: string;
    content: string;
  };
  presentationUpdate?: {
    action?: string;
    presentationId: string;
    slideId: string;
    chartConfig?: ChatResponse['charts'][0];
    chartImage?: string;
  };
  suggestions?: string[];
  message?: string;
}

export const chatApi = {
  sendMessage: async (message: string, conversationId?: string): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat/', {
      message,
      conversation_id: conversationId,
    });
    return response.data;
  },

  sendMessageStream: async (
    message: string,
    conversationId: string | undefined,
    onEvent: (event: StreamEvent) => void
  ): Promise<string> => {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const convId = response.headers.get('X-Conversation-Id') || conversationId || '';
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No response body');
    }

    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6)) as StreamEvent;
            onEvent(event);
          } catch {
            // Ignore parse errors
          }
        }
      }
    }

    return convId;
  },

  clearConversation: async (conversationId: string): Promise<void> => {
    await api.delete(`/chat/${conversationId}`);
  },

  updateSlide: async (conversationId: string, slideIndex: number): Promise<void> => {
    await api.post(`/chat/conversations/${conversationId}/slide`, {
      slide_index: slideIndex,
    });
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
