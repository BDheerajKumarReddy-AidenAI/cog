from typing import TypedDict, Annotated, Sequence, AsyncGenerator, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from app.core.config import settings
from app.models.analytics import DATABASE_SCHEMA
from app.tools.sql_tools import SQL_TOOLS
from app.tools.chart_tools import CHART_TOOLS
from app.tools.ppt_tools import PPT_TOOLS
import logging
import operator
import json

logger = logging.getLogger(__name__)


class SlideConfig(TypedDict):
    id: str
    order: int
    title: str
    contentType: str
    content: str
    notes: str
    chartConfig: Optional[dict]


class PresentationMetadata(TypedDict):
    createdAt: str
    slideCount: int


class Presentation(TypedDict):
    type: str
    presentationId: str
    title: str
    slides: list[SlideConfig]
    metadata: PresentationMetadata


class ChartConfig(TypedDict):
    type: str
    chartType: str
    title: str
    data: list[dict]
    xAxisKey: str
    yAxisKeys: list[str]
    colors: list[str]
    config: dict


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_slide: int
    presentation: Optional[Presentation]
    suggestions: list[str]
    charts: list[ChartConfig]


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
- After each response, provide 2-4 suggestions for follow-up actions

Always be accurate with data. If you're unsure, query the database to get precise information.
"""


def create_analytics_graph():
    """Create the LangGraph workflow with state management."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=settings.openai_api_key,
    )

    all_tools = SQL_TOOLS + CHART_TOOLS + PPT_TOOLS
    llm_with_tools = llm.bind_tools(all_tools)
    tool_node = ToolNode(all_tools)

    async def agent_node(state: AgentState) -> AgentState:
        """Agent reasoning node - decides what to do next."""
        messages = state["messages"]

        if len(messages) == 1 or not any(isinstance(m, AIMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

        response = await llm_with_tools.ainvoke(messages)

        return {
            "messages": [response],
        }

    async def tools_node(state: AgentState) -> AgentState:
        """Execute tools and update state based on tool outputs."""
        messages = state["messages"]
        tool_outputs = await tool_node.ainvoke({"messages": messages})

        new_charts = []
        new_presentation = state.get("presentation")

        for tool_message in tool_outputs["messages"]:
            if isinstance(tool_message, ToolMessage):
                try:
                    output_data = json.loads(tool_message.content)
                    if isinstance(output_data, dict):
                        output_type = output_data.get("type", "")

                        if output_type == "presentation":
                            new_presentation = output_data
                            logger.info("Captured presentation: %s", output_data.get("title"))
                        elif output_type == "chart":
                            new_charts.append(output_data)
                            logger.info("Captured chart: %s", output_data.get("title"))
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning("Failed to parse tool output: %s", e)

        updates: AgentState = {
            "messages": tool_outputs["messages"],
        }

        if new_charts:
            updates["charts"] = state.get("charts", []) + new_charts

        if new_presentation:
            updates["presentation"] = new_presentation
            updates["current_slide"] = 0

        return updates

    async def process_response_node(state: AgentState) -> AgentState:
        """Process the final AI response to extract suggestions."""
        messages = state["messages"]
        last_message = messages[-1]

        if isinstance(last_message, AIMessage) and last_message.content:
            suggestions = extract_suggestions(last_message.content)
            return {
                "suggestions": suggestions,
            }

        return {}

    def should_continue(state: AgentState) -> str:
        """Determine if we should continue to tools or end."""
        messages = state["messages"]
        last_message = messages[-1]

        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"

        return "process"

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("process", process_response_node)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "process": "process",
        },
    )
    workflow.add_edge("tools", "agent")
    workflow.add_edge("process", END)

    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)

    return graph, memory


def extract_suggestions(text: str) -> list[str]:
    """Extract suggestions from the agent's response."""
    suggestions = []
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith(('-', '•', '*')) or (len(line) > 2 and line[0].isdigit() and line[1] in '.):'):
            suggestion = line.lstrip('-•*0123456789.): ').strip()
            if suggestion and len(suggestion) > 10:
                suggestions.append(suggestion)

    if not suggestions:
        suggestions = [
            "Analyze sales trends over time",
            "View top performing products",
            "Create a quarterly report",
            "Compare regional performance",
        ]

    return suggestions[:4]


class AnalyticsAgentRunner:
    """Runner class to manage agent conversations with state streaming."""

    def __init__(self):
        self.graph, self.memory = create_analytics_graph()

    async def chat(self, conversation_id: str, message: str) -> dict:
        """Process a chat message and return the final response."""
        final_event = None
        async for event in self.chat_stream(conversation_id, message):
            if event.get("type") == "final":
                final_event = event

        if not final_event:
            return {
                "conversation_id": conversation_id,
                "response": "I've processed your request.",
                "current_slide": 0,
                "presentation": None,
                "charts": [],
                "suggestions": [],
            }

        return {
            "conversation_id": conversation_id,
            "response": final_event.get("response", "I've processed your request."),
            "current_slide": final_event.get("current_slide", 0),
            "presentation": final_event.get("presentation"),
            "charts": final_event.get("charts", []),
            "suggestions": final_event.get("suggestions", []),
        }

    def clear_conversation(self, conversation_id: str) -> None:
        """Clear a conversation history."""
        self.memory.delete_thread(conversation_id)

    async def chat_stream(
        self,
        conversation_id: str,
        message: str,
    ) -> AsyncGenerator[dict, None]:
        """Process a chat message and stream state updates."""
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "current_slide": 0,
            "presentation": None,
            "suggestions": [],
            "charts": [],
        }

        config = {
            "configurable": {"thread_id": conversation_id},
        }

        previous_state = initial_state.copy()

        async for event in self.graph.astream(initial_state, config, stream_mode="values"):
            state_update = self._get_state_diff(previous_state, event)

            if state_update:
                yield {
                    "type": "state_update",
                    "conversation_id": conversation_id,
                    **state_update,
                }

            previous_state = event.copy()

        final_state = previous_state
        final_message = None

        for msg in reversed(final_state["messages"]):
            if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                final_message = msg.content
                break

        yield {
            "type": "final",
            "conversation_id": conversation_id,
            "response": final_message or "I've processed your request.",
            "current_slide": final_state.get("current_slide", 0),
            "presentation": final_state.get("presentation"),
            "charts": final_state.get("charts", []),
            "suggestions": final_state.get("suggestions", []),
        }

    def _get_state_diff(self, previous: dict, current: dict) -> dict:
        """Get the differences between previous and current state."""
        diff = {}

        prev_msg_count = len([m for m in previous.get("messages", [])
                             if not isinstance(m, SystemMessage)])
        curr_msg_count = len([m for m in current.get("messages", [])
                             if not isinstance(m, SystemMessage)])

        if curr_msg_count > prev_msg_count:
            new_messages = current["messages"][prev_msg_count:]
            for msg in new_messages:
                if isinstance(msg, ToolMessage):
                    diff["tool_output"] = {
                        "name": msg.name,
                        "content": msg.content[:200],
                    }

        if current.get("presentation") != previous.get("presentation"):
            diff["presentation"] = current.get("presentation")

        prev_charts = previous.get("charts", [])
        curr_charts = current.get("charts", [])
        if len(curr_charts) > len(prev_charts):
            diff["new_charts"] = curr_charts[len(prev_charts):]

        if current.get("current_slide") != previous.get("current_slide"):
            diff["current_slide"] = current.get("current_slide")

        if current.get("suggestions") != previous.get("suggestions"):
            diff["suggestions"] = current.get("suggestions")

        return diff

    async def update_slide(self, conversation_id: str, slide_index: int) -> dict:
        """Update the current slide in the conversation state."""
        config = {"configurable": {"thread_id": conversation_id}}
        state = await self.graph.aget_state(config)

        if state and state.values:
            state.values["current_slide"] = slide_index
            return {
                "success": True,
                "current_slide": slide_index,
            }

        return {
            "success": False,
            "error": "Conversation not found",
        }


agent_runner = AnalyticsAgentRunner()
