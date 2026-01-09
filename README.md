# Analytics Chatbot

An AI-powered analytics chatbot application that helps users analyze business data through natural conversation. The application features a React frontend, FastAPI backend, LangGraph agent with tool calling, and supports chart generation and PowerPoint presentation creation.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Chat Window  │  │ Chart Render │  │ Presentation Sidebar   │ │
│  │  (Recharts)  │  │  (Download)  │  │  (Preview & Export)    │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │  Chat API    │  │Presentation  │  │   LangGraph Agent      │ │
│  │  Endpoints   │  │  Generator   │  │   (Tool Calling)       │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Data Layer                                   │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                    PostgreSQL                                ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                   ││
│  │  │  Sales   │  │ Customers│  │ Products │                   ││
│  │  └──────────┘  └──────────┘  └──────────┘                   ││
│  └──────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Features

### Chat Interface
- Natural language interaction with an AI agent
- Contextual conversation memory
- Clickable suggestions for quick actions

### Data Analysis
- Dynamic SQL query generation based on user intent
- Database schema injected into agent system prompt
- Structured data responses

### Data Visualization
- Interactive charts using Recharts (Line, Bar, Pie, Area, Scatter)
- Chart download as PNG
- Add charts to presentations

### Presentation Generation
- Create PowerPoint presentations with insights
- Preview and edit slides
- Embed charts into slides
- Download as .pptx file

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- OpenAI API key

## Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file from example:
```bash
cp .env.example .env
```

5. Update `.env` with your configuration:
```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/analytics_db
OPENAI_API_KEY=your-openai-api-key-here
```

6. Create the PostgreSQL database:
```bash
createdb analytics_db
```

7. Seed the database with sample data:
```bash
python -m scripts.seed_data
```

8. Start the backend server:
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open your browser to `http://localhost:3000`

## Project Structure

```
analytics-chatbot/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py           # Chat endpoints
│   │   │   └── presentation.py   # PPTX generation
│   │   ├── agents/
│   │   │   └── analytics_agent.py # LangGraph agent
│   │   ├── core/
│   │   │   ├── config.py         # Configuration
│   │   │   └── database.py       # Database setup
│   │   ├── models/
│   │   │   └── analytics.py      # SQLAlchemy models
│   │   ├── tools/
│   │   │   ├── sql_tools.py      # SQL execution tools
│   │   │   ├── chart_tools.py    # Chart configuration tools
│   │   │   └── ppt_tools.py      # Presentation tools
│   │   └── main.py               # FastAPI application
│   ├── scripts/
│   │   └── seed_data.py          # Database seeding
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx    # Main chat interface
│   │   │   ├── ChatMessage.tsx   # Message component
│   │   │   ├── ChatInput.tsx     # Input component
│   │   │   ├── ChartRenderer.tsx # Recharts wrapper
│   │   │   └── PresentationSidebar.tsx
│   │   ├── hooks/
│   │   │   └── useChat.ts        # Chat state management
│   │   ├── services/
│   │   │   └── api.ts            # API client
│   │   ├── types/
│   │   │   └── index.ts          # TypeScript types
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## API Endpoints

### Chat
- `POST /api/chat/` - Send a message to the agent
- `POST /api/chat/suggestion` - Handle a clicked suggestion
- `DELETE /api/chat/{conversation_id}` - Clear conversation

### Presentation
- `POST /api/presentation/generate` - Generate PPTX file
- `POST /api/presentation/preview` - Preview presentation

## Agent Tools

### SQL Tools
- `execute_sql_query` - Execute SELECT queries
- `get_table_info` - Get table structure and sample data
- `get_analytics_summary` - Get database summary

### Chart Tools
- `generate_chart_config` - Create chart configuration
- `suggest_visualization` - Recommend chart type

### Presentation Tools
- `create_presentation_outline` - Create slide structure
- `add_chart_to_presentation` - Add chart to slide
- `generate_presentation_suggestions` - Suggest slides

## Database Schema

### Tables
- **sales_data**: Sales transactions with date, product, customer, region
- **customers**: Customer information with segments
- **products**: Product catalog with categories

## Example Queries

Try these in the chat:
- "Show me a summary of the database"
- "What were the total sales by region?"
- "Generate a monthly sales trend chart"
- "Show me top 10 customers by revenue"
- "Create a quarterly sales presentation"
- "Compare product categories by revenue"

## License

MIT License
