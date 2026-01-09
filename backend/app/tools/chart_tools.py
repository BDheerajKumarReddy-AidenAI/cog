from typing import Any, Literal
from langchain_core.tools import tool
import json


ChartType = Literal["line", "bar", "pie", "area", "scatter"]


@tool
def generate_chart_config(
    chart_type: ChartType,
    title: str,
    data: list[dict[str, Any]],
    x_axis_key: str,
    y_axis_keys: list[str],
    colors: list[str] | None = None,
) -> str:
    """
    Generate a chart configuration for the frontend to render using Recharts.

    Args:
        chart_type: Type of chart - 'line', 'bar', 'pie', 'area', or 'scatter'
        title: Chart title to display
        data: List of data points as dictionaries
        x_axis_key: The key in data to use for x-axis
        y_axis_keys: List of keys to plot on y-axis
        colors: Optional list of colors for each y-axis series

    Returns:
        JSON string with chart configuration for frontend rendering.
    """
    default_colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff7300", "#0088fe"]

    if colors is None:
        colors = default_colors[: len(y_axis_keys)]

    config = {
        "type": "chart",
        "chartType": chart_type,
        "title": title,
        "data": data,
        "xAxisKey": x_axis_key,
        "yAxisKeys": y_axis_keys,
        "colors": colors,
        "config": {
            "responsive": True,
            "maintainAspectRatio": True,
            "legend": True,
            "tooltip": True,
            "grid": True,
        },
    }

    return json.dumps(config, default=str)


@tool
def suggest_visualization(data_description: str, query_intent: str) -> str:
    """
    Suggest the best visualization type based on data and user intent.

    Args:
        data_description: Description of the data structure and content
        query_intent: What the user wants to understand or analyze

    Returns:
        JSON string with visualization recommendation.
    """
    recommendations = {
        "trend": {
            "chart_type": "line",
            "reason": "Line charts are ideal for showing trends over time",
        },
        "comparison": {
            "chart_type": "bar",
            "reason": "Bar charts are great for comparing categories or groups",
        },
        "distribution": {
            "chart_type": "pie",
            "reason": "Pie charts show part-to-whole relationships",
        },
        "correlation": {
            "chart_type": "scatter",
            "reason": "Scatter plots reveal correlations between variables",
        },
        "cumulative": {
            "chart_type": "area",
            "reason": "Area charts show cumulative values over time",
        },
    }

    intent_lower = query_intent.lower()

    if any(word in intent_lower for word in ["trend", "over time", "monthly", "yearly", "growth"]):
        recommendation = recommendations["trend"]
    elif any(word in intent_lower for word in ["compare", "versus", "between", "top", "by region", "by category"]):
        recommendation = recommendations["comparison"]
    elif any(word in intent_lower for word in ["share", "percentage", "proportion", "distribution"]):
        recommendation = recommendations["distribution"]
    elif any(word in intent_lower for word in ["relationship", "correlation", "impact"]):
        recommendation = recommendations["correlation"]
    else:
        recommendation = recommendations["comparison"]

    return json.dumps(
        {
            "success": True,
            "recommendation": recommendation,
            "data_description": data_description,
            "query_intent": query_intent,
        }
    )


CHART_TOOLS = [generate_chart_config, suggest_visualization]
