import React, { useState, useRef, useEffect } from 'react';
import './ChatInput.css';

export interface ToolStatus {
  isActive: boolean;
  currentTool: string | null;
  toolHistory: string[];
}

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  toolStatus?: ToolStatus;
  onClearChat: () => void;
}

const TOOL_DISPLAY_NAMES: Record<string, string> = {
  execute_sql_query: 'Querying database',
  get_table_info: 'Fetching table info',
  get_analytics_summary: 'Getting analytics summary',
  generate_chart: 'Generating chart',
  create_presentation: 'Creating presentation',
};

const ChatInput: React.FC<ChatInputProps> = ({ onSend, disabled = false, toolStatus, onClearChat }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const getToolDisplayName = (toolName: string) => {
    return TOOL_DISPLAY_NAMES[toolName] || `Running ${toolName}`;
  };

  return (
    <div className="chat-input-wrapper">
      {toolStatus?.isActive && toolStatus.currentTool && (
        <div className="tool-status-indicator">
          <div className="tool-status-spinner" />
          <span className="tool-status-text">
            {getToolDisplayName(toolStatus.currentTool)}...
          </span>
        </div>
      )}
      <form className="chat-input-container" onSubmit={handleSubmit}>
        <textarea
          ref={textareaRef}
          className="chat-input"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your analytics data..."
          disabled={disabled}
          rows={1}
        />
        <button
          type="button"
          className="clear-chat-btn"
          onClick={onClearChat}
          title="Clear Chat"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            <line x1="10" y1="11" x2="10" y2="17"></line>
            <line x1="14" y1="11" x2="14" y2="17"></line>
          </svg>
        </button>
        <button
          type="submit"
          className="send-button"
          disabled={disabled || !message.trim()}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </form>
    </div>
  );
};

export default ChatInput;
