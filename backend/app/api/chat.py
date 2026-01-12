from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any
from app.agents.analytics_agent import agent_runner
import uuid
import json

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    charts: list[dict[str, Any]]
    presentations: list[dict[str, Any]]
    suggestions: list[str]


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the analytics agent and get a response."""
    conversation_id = request.conversation_id or str(uuid.uuid4())

    try:
        result = await agent_runner.chat(conversation_id, request.message)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear a conversation history."""
    agent_runner.clear_conversation(conversation_id)
    return {"status": "success", "message": "Conversation cleared"}


async def generate_stream(conversation_id: str, message: str):
    """Generate SSE stream from agent events."""
    try:
        async for event in agent_runner.chat_stream(conversation_id, message):
            yield f"data: {json.dumps(event)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Send a message to the analytics agent and stream the response with tool events."""
    conversation_id = request.conversation_id or str(uuid.uuid4())

    return StreamingResponse(
        generate_stream(conversation_id, request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Conversation-Id": conversation_id,
        },
    )
