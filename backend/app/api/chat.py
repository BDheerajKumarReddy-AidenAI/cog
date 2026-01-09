from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any
from app.agents.analytics_agent import agent_runner
import uuid

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


class SuggestionRequest(BaseModel):
    suggestion: str
    conversation_id: str


@router.post("/suggestion", response_model=ChatResponse)
async def handle_suggestion(request: SuggestionRequest):
    """Handle a clicked suggestion as a new message."""
    try:
        result = await agent_runner.chat(request.conversation_id, request.suggestion)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
