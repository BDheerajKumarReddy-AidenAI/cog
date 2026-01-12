import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';
import remarkGfm from 'remark-gfm';
import { Message, ChartConfig } from '../types';
import ChartRenderer from './ChartRenderer';
import './ChatMessage.css';

interface ChatMessageProps {
  message: Message;
  onSuggestionClick?: (suggestion: string) => void;
  onAddChartToPresentation?: (chart: ChartConfig, chartImage?: string) => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  onSuggestionClick,
  onAddChartToPresentation,
}) => {
  const isUser = message.role === 'user';

  return (
    <div className={`message-container ${isUser ? 'user' : 'assistant'}`}>
      <div className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
        <div className="message-content">
          {isUser ? (
            message.content.split('\n').map((line, i) => <p key={i}>{line}</p>)
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {message.charts && message.charts.length > 0 && (
          <div className="message-charts">
            {message.charts.map((chart, index) => (
              <div key={index} className="chart-wrapper">
                <ChartRenderer
                  config={chart}
                  onCapture={onAddChartToPresentation ? (imageData) => onAddChartToPresentation(chart, imageData) : undefined}
                />
              </div>
            ))}
          </div>
        )}

        {message.suggestions && message.suggestions.length > 0 && (
          <div className="message-suggestions">
            {message.suggestions.map((suggestion, index) => (
              <button
                key={index}
                className="suggestion-btn"
                onClick={() => onSuggestionClick?.(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
      </div>
      <span className="message-time">
        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </span>
    </div>
  );
};

export default ChatMessage;
