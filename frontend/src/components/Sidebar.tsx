import React from 'react';
import { FileText, MessageSquare, Database } from 'lucide-react';
import './Sidebar.css';

type Props = {
  collapsed?: boolean;
  onToggle?: () => void;
};

const Sidebar: React.FC<Props> = ({ collapsed = false, onToggle }) => {
  return (
    <aside className={`app-sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-top">
        <div className="brand"></div>
        <button className="collapse-btn" onClick={onToggle} aria-label="Toggle sidebar">
          {collapsed ? '›' : '‹'}
        </button>
      </div>

      <nav className="sidebar-nav">
        <ul>
          <li className="sidebar-item">
            <div className="icon"><FileText /></div>
            <div className="label">My Presentations</div>
          </li>
          <li className="sidebar-item">
            <div className="icon"><MessageSquare /></div>
            <div className="label">Chat History</div>
          </li>
          <li className="sidebar-item">
            <div className="icon"><Database /></div>
            <div className="label">Data Sources</div>
          </li>
        </ul>
      </nav>

    </aside>
  );
};

export default Sidebar;
