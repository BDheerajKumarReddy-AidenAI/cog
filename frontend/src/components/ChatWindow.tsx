import React, { useRef, useEffect } from 'react';
import { Message, ChartConfig } from '../types';
import ChatMessage from './ChatMessage';
import ChatInput, { ToolStatus } from './ChatInput';
import './ChatWindow.css';

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
  onSendMessage: (message: string) => void;
  onSuggestionClick: (suggestion: string) => void;
  onAddChartToPresentation?: (chart: ChartConfig, chartImage: string) => void;
  onClearChat: () => void;
  toolStatus?: ToolStatus;
}

const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  isLoading,
  onSendMessage,
  onSuggestionClick,
  onClearChat,
  toolStatus,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="chat-window">
      <div className="chat-header">
        <div className="chat-header-info">
          <h2>Analytics Assistant</h2>
          <span className="status-indicator">Online</span>
        </div>
        <button className="clear-chat-btn" onClick={onClearChat}>
          Clear Chat
        </button>
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h3>Welcome to Analytics Chatbot</h3>
            <p>Ask me anything about your sales, customers, or product data!</p>
            <div className="starter-suggestions">
              <button onClick={() => onSuggestionClick('Show me a summary of the database')}>
                Show database summary
              </button>
              <button onClick={() => onSuggestionClick('What were the total sales this year?')}>
                View total sales
              </button>
              <button onClick={() => onSuggestionClick('Show me the top 10 customers by revenue')}>
                Top customers
              </button>
              <button onClick={() => onSuggestionClick('Generate a monthly sales trend chart')}>
                Sales trend chart
              </button>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              onSuggestionClick={onSuggestionClick}
            />
          ))
        )}

        {isLoading && (
          <div className="loading-indicator">
            <div className="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <ChatInput onSend={onSendMessage} disabled={isLoading} toolStatus={toolStatus} />
    </div>
  );
};

export default ChatWindow;
