from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A validated request to execute one approved tool."""

    call_id: str = Field(default_factory=lambda: str(uuid4()))
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Normalized result returned by every tool."""

    call_id: str
    tool_name: str
    status: Literal["success", "error"]
    output: Optional[Any] = None
    error: Optional[str] = None
    started_at: datetime
    completed_at: datetime
    duration_ms: float


class AuditRecord(BaseModel):
    """Persistent record of one tool execution."""

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    call: ToolCall
    result: ToolResult


class AgentRunResult(BaseModel):
    """Top-level result returned after an agent run."""

    user_request: str
    final_answer: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tool_results: List[ToolResult] = Field(default_factory=list)