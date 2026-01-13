from typing import TypedDict, Annotated, Sequence, AsyncGenerator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from app.core.config import settings
from app.models.analytics import DATABASE_SCHEMA
from app.tools.sql_tools import SQL_TOOLS
from app.tools.chart_tools import CHART_TOOLS
from app.tools.ppt_tools import PPT_TOOLS
import logging

logger = logging.getLogger(__name__)
import operator
import json
from langchain.agents import create_agent

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
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=settings.openai_api_key,
    )

    all_tools = SQL_TOOLS + CHART_TOOLS + PPT_TOOLS

    agent = create_agent(
        llm,
        all_tools,
        system_prompt=SYSTEM_PROMPT,
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


def dedupe_charts(charts: list[dict]) -> list[dict]:
    """Remove duplicate chart configs while preserving order."""
    seen = set()
    unique = []
    for chart in charts:
        try:
            signature = json.dumps(chart, sort_keys=True)
        except (TypeError, ValueError):
            signature = str(chart)
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(chart)
    return unique


def apply_presentation_update(presentation: dict, update: dict) -> dict:
    """Apply a presentation update event to a presentation config."""
    if not presentation or not update:
        return presentation

    if presentation.get("presentationId") != update.get("presentationId"):
        return presentation

    if update.get("action") != "add_chart":
        return presentation

    slide_id = update.get("slideId")
    chart_config = update.get("chartConfig")

    if isinstance(chart_config, str):
        try:
            chart_config = json.loads(chart_config)
        except json.JSONDecodeError:
            chart_config = {"raw": chart_config}

    updated_slides = []
    for slide in presentation.get("slides", []):
        if slide.get("id") == slide_id:
            updated_slides.append({
                **slide,
                "contentType": "chart",
                "chartConfig": chart_config,
            })
        else:
            updated_slides.append(slide)

    return {
        **presentation,
        "slides": updated_slides,
    }


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

    async def chat_stream(self, conversation_id: str, message: str) -> AsyncGenerator[dict, None]:
        """Process a chat message and stream events including tool calls."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        self.conversations[conversation_id].append(HumanMessage(content=message))

        state = {"messages": self.conversations[conversation_id]}
        final_sent = False

        # Track presentations and charts created via tools
        collected_presentations = []
        collected_charts = []
        collected_presentation_updates = []

        # Stream events from the agent
        async for event in self.agent.astream_events(state, version="v2"):
            event_type = event.get("event")

            if event_type == "on_tool_start":
                tool_name = event.get("name", "unknown")
                tool_input = event.get("data", {}).get("input", {})
                yield {
                    "type": "tool_start",
                    "tool": tool_name,
                    "input": tool_input,
                }

            elif event_type == "on_tool_end":
                tool_name = event.get("name", "unknown")
                # Tool output can be in different locations depending on LangGraph version
                event_data = event.get("data", {})
                tool_output = event_data.get("output", "")

                # Handle different output formats
                if isinstance(tool_output, ToolMessage):
                    tool_output = tool_output.content
                elif hasattr(tool_output, "content"):
                    tool_output = tool_output.content
                elif isinstance(tool_output, dict) and "content" in tool_output:
                    tool_output = tool_output["content"]

                logger.info(f"Tool {tool_name} ended. Output type: {type(tool_output).__name__}")

                # Parse tool output to capture presentations and charts
                if tool_output and isinstance(tool_output, str):
                    try:
                        output_data = json.loads(tool_output)
                        if isinstance(output_data, dict):
                            output_type = output_data.get("type", "")

                            # Capture and immediately stream presentation
                            if output_type == "presentation":
                                print(f"Parsed tool output data of type presentation: {output_data}")
                                collected_presentations.append(output_data)
                                yield {
                                    "type": "presentation",
                                    "presentation": output_data,
                                }
                            elif output_type == "presentation_update":
                                collected_presentation_updates.append(output_data)
                                yield {
                                    "type": "presentation_update",
                                    "presentationUpdate": output_data,
                                }
                            # Capture charts from chart tools
                            elif output_type == "chart":
                                collected_charts.append(output_data)
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Failed to parse tool output: {e}")

                yield {
                    "type": "tool_end",
                    "tool": tool_name,
                }

            elif event_type == "on_chain_end" and not final_sent:
                # Check if this is the final output from the root chain
                output = event.get("data", {}).get("output", {})

                # Only process the final output from the agent (not intermediate chains)
                if isinstance(output, dict) and "messages" in output:
                    messages = output["messages"]
                    if messages:
                        final_message = messages[-1]
                        # Check it's an AI message with actual content (not a tool call)
                        if (hasattr(final_message, "content")
                            and final_message.content
                            and isinstance(final_message, AIMessage)
                            and not getattr(final_message, "tool_calls", None)):
                            self.conversations[conversation_id].append(final_message)
                            parsed = parse_agent_response(final_message.content)

                            # Merge collected presentations/charts with parsed ones
                            all_presentations = collected_presentations + parsed["presentations"]
                            all_charts = dedupe_charts(collected_charts + parsed["charts"])

                            if collected_presentation_updates and all_presentations:
                                updated_presentations = []
                                for pres in all_presentations:
                                    updated_pres = pres
                                    for update in collected_presentation_updates:
                                        updated_pres = apply_presentation_update(updated_pres, update)
                                    updated_presentations.append(updated_pres)
                                all_presentations = updated_presentations

                            final_sent = True
                            yield {
                                "type": "final",
                                "conversation_id": conversation_id,
                                "response": parsed["text"],
                                "charts": all_charts,
                                "presentations": all_presentations,
                                "suggestions": parsed["suggestions"],
                            }


agent_runner = AnalyticsAgentRunner()
