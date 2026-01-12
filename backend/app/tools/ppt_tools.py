from typing import Any
from langchain_core.tools import tool
import json
import uuid


@tool
def create_presentation_outline(
    title: str,
    slides: list[dict[str, Any]],
) -> str:
    """
    Create a PowerPoint presentation outline for the frontend to preview and edit.

    Args:
        title: Presentation title
        slides: List of slide configurations, each with:
            - title: Slide title
            - content_type: 'text', 'chart', 'bullets', or 'mixed'
            - content: Text content, bullet points, or chart reference
            - notes: Optional speaker notes

    Returns:
        JSON string with presentation configuration for frontend preview.
    """
    presentation_id = str(uuid.uuid4())

    formatted_slides = []
    for i, slide in enumerate(slides):
        print(slide.get("chart_config"))
        formatted_slide = {
            "id": f"slide-{i + 1}",
            "order": i + 1,
            "title": slide.get("title", f"Slide {i + 1}"),
            "contentType": slide.get("content_type", "text"),
            "content": slide.get("content", ""),
            "notes": slide.get("notes", ""),
            "chartConfig": slide.get("chart_config"),
        }
        formatted_slides.append(formatted_slide)
    
    
    config = {
        "type": "presentation",
        "presentationId": presentation_id,
        "title": title,
        "slides": formatted_slides,
        "metadata": {
            "createdAt": str(uuid.uuid4()),
            "slideCount": len(formatted_slides),
        },
    }

    return json.dumps(config, default=str)


@tool
def add_chart_to_presentation(
    presentation_id: str,
    slide_id: str,
    chart_config: dict[str, Any],
) -> str:
    """
    Add a chart to a specific slide in the presentation.

    Args:
        presentation_id: ID of the presentation
        slide_id: ID of the slide to add chart to
        chart_config: Chart configuration from generate_chart_config

    Returns:
        JSON string confirming the chart addition.
    """
    return json.dumps(
        {
            "type": "presentation_update",
            "action": "add_chart",
            "presentationId": presentation_id,
            "slideId": slide_id,
            "chartConfig": chart_config,
            "success": True,
        }
    )


@tool
def generate_presentation_suggestions(topic: str, data_summary: str) -> str:
    """
    Generate slide suggestions for a presentation based on topic and available data.

    Args:
        topic: Main topic or theme of the presentation
        data_summary: Summary of available data for the presentation

    Returns:
        JSON string with suggested slide structure.
    """
    suggestions = {
        "type": "presentation_suggestions",
        "topic": topic,
        "suggestedSlides": [
            {
                "title": "Executive Summary",
                "content_type": "bullets",
                "description": "Key findings and highlights",
            },
            {
                "title": "Data Overview",
                "content_type": "mixed",
                "description": "High-level metrics and KPIs",
            },
            {
                "title": "Trend Analysis",
                "content_type": "chart",
                "description": "Time-based trends and patterns",
                "suggestedChartType": "line",
            },
            {
                "title": "Category Breakdown",
                "content_type": "chart",
                "description": "Comparison across categories",
                "suggestedChartType": "bar",
            },
            {
                "title": "Distribution Analysis",
                "content_type": "chart",
                "description": "Proportional distribution",
                "suggestedChartType": "pie",
            },
            {
                "title": "Key Insights",
                "content_type": "bullets",
                "description": "Main takeaways and findings",
            },
            {
                "title": "Recommendations",
                "content_type": "bullets",
                "description": "Actionable recommendations",
            },
            {
                "title": "Next Steps",
                "content_type": "text",
                "description": "Proposed action items",
            },
        ],
    }

    return json.dumps(suggestions)


PPT_TOOLS = [create_presentation_outline, add_chart_to_presentation, generate_presentation_suggestions]
