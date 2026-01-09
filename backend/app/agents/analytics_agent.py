from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from app.core.config import settings
from app.models.analytics import DATABASE_SCHEMA
from app.tools.sql_tools import SQL_TOOLS
from app.tools.chart_tools import CHART_TOOLS
from app.tools.ppt_tools import PPT_TOOLS
import operator
import json


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    suggestions: list[dict]


SYSTEM_PROMPT = f"""You are an intelligent analytics assistant that helps users understand their business data.
You have access to a PostgreSQL database with sales, customer, and product data.

{DATABASE_SCHEMA}

YOUR CAPABILITIES:
1. **Data Analysis**: Execute SQL queries to fetch and analyze data from the database
2. **Visualization**: Generate interactive charts (line, bar, pie, area, scatter) for data visualization
3. **Presentations**: Create PowerPoint presentations with data insights and charts
4. **Insights**: Provide actionable business insights based on data analysis

RESPONSE GUIDELINES:
- Always be conversational and helpful
- When showing data, provide clear explanations of what it means
- Proactively suggest relevant analyses or visualizations
- When generating charts, format the response with a special JSON block
- For presentations, provide a structured outline that can be previewed

SUGGESTIONS:
After each response, provide 2-4 clickable suggestions for the user. Format them as:
[SUGGESTIONS]
- Generate a sales trend chart
- View top customers by revenue
- Create a quarterly report presentation
[/SUGGESTIONS]

CHART OUTPUT FORMAT:
When generating charts, include the chart config in your response like this:
```chart
{{
    "type": "chart",
    "chartType": "bar|line|pie|area|scatter",
    "title": "Chart Title",
    "data": [...],
    "xAxisKey": "key_name",
    "yAxisKeys": ["value1", "value2"],
    "colors": ["#8884d8", "#82ca9d"]
}}
```

PRESENTATION OUTPUT FORMAT:
When creating presentations, include the presentation config like this:
```presentation
{{
    "type": "presentation",
    "title": "Presentation Title",
    "slides": [...]
}}
```

Always be accurate with data. If you're unsure, query the database to get precise information.
"""


def create_analytics_agent():
    """Create the LangGraph analytics agent with all tools."""
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.7,
        api_key=settings.openai_api_key,
    )

    all_tools = SQL_TOOLS + CHART_TOOLS + PPT_TOOLS

    agent = create_react_agent(
        llm,
        all_tools,
        state_modifier=SYSTEM_PROMPT,
    )

    return agent


def parse_agent_response(response: str) -> dict:
    """Parse the agent response to extract charts, presentations, and suggestions."""
    result = {
        "text": response,
        "charts": [],
        "presentations": [],
        "suggestions": [],
    }

    if "```chart" in response:
        parts = response.split("```chart")
        for part in parts[1:]:
            if "```" in part:
                chart_json = part.split("```")[0].strip()
                try:
                    chart_config = json.loads(chart_json)
                    result["charts"].append(chart_config)
                except json.JSONDecodeError:
                    pass

    if "```presentation" in response:
        parts = response.split("```presentation")
        for part in parts[1:]:
            if "```" in part:
                ppt_json = part.split("```")[0].strip()
                try:
                    ppt_config = json.loads(ppt_json)
                    result["presentations"].append(ppt_config)
                except json.JSONDecodeError:
                    pass

    if "[SUGGESTIONS]" in response:
        suggestions_match = response.split("[SUGGESTIONS]")[1].split("[/SUGGESTIONS]")[0]
        suggestions = [
            s.strip().lstrip("- ").strip()
            for s in suggestions_match.strip().split("\n")
            if s.strip().startswith("-")
        ]
        result["suggestions"] = suggestions

    clean_text = response
    for marker in ["```chart", "```presentation", "[SUGGESTIONS]"]:
        if marker in clean_text:
            clean_text = clean_text.split(marker)[0]
    result["text"] = clean_text.strip()

    return result


class AnalyticsAgentRunner:
    """Runner class to manage agent conversations."""

    def __init__(self):
        self.agent = create_analytics_agent()
        self.conversations: dict[str, list[BaseMessage]] = {}

    async def chat(self, conversation_id: str, message: str) -> dict:
        """Process a chat message and return the agent response."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        self.conversations[conversation_id].append(HumanMessage(content=message))

        state = {"messages": self.conversations[conversation_id]}

        result = await self.agent.ainvoke(state)

        ai_message = result["messages"][-1]
        self.conversations[conversation_id].append(ai_message)

        parsed = parse_agent_response(ai_message.content)

        return {
            "conversation_id": conversation_id,
            "response": parsed["text"],
            "charts": parsed["charts"],
            "presentations": parsed["presentations"],
            "suggestions": parsed["suggestions"],
        }

    def clear_conversation(self, conversation_id: str):
        """Clear a conversation history."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]


agent_runner = AnalyticsAgentRunner()
