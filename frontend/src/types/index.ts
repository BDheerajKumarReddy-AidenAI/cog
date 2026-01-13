export interface ChartConfig {
  type: 'chart';
  chartType: 'line' | 'bar' | 'pie' | 'area' | 'scatter';
  title: string;
  data: Record<string, unknown>[];
  xAxisKey: string;
  yAxisKeys: string[];
  colors: string[];
  config?: {
    responsive?: boolean;
    maintainAspectRatio?: boolean;
    legend?: boolean;
    tooltip?: boolean;
    grid?: boolean;
  };
}

export interface SlideContent {
  id: string;
  order: number;
  title: string;
  contentType: 'text' | 'chart' | 'bullets' | 'mixed';
  content: string | string[];
  notes?: string;
  chartConfig?: ChartConfig;
  chartImage?: string;
}

export interface PresentationConfig {
  type: 'presentation';
  presentationId: string;
  title: string;
  slides: SlideContent[];
  metadata?: {
    createdAt: string;
    slideCount: number;
  };
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  charts?: ChartConfig[];
  suggestions?: string[];
}

export interface ChatResponse {
  conversation_id: string;
  response: string;
  current_slide: number;
  presentation?: PresentationConfig | null;
  charts: ChartConfig[];
  suggestions: string[];
}

export interface Conversation {
  id: string;
  messages: Message[];
  createdAt: Date;
}
