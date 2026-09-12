from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A structured request from the model to use one tool."""

    call_id: str = Field(default_factory=lambda: str(uuid4()))
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ToolAuthorization(BaseModel):
    """Application-owned decision about whether a tool call may execute."""

    call_id: str
    tool_name: str
    status: Literal["approved", "blocked"]
    reason: str


class ToolResult(BaseModel):
    """Normalized result returned by the controlled execution layer."""

    call_id: str
    tool_name: str
    status: Literal["success", "blocked", "error"]
    output: Optional[Any] = None
    error: Optional[str] = None
    started_at: datetime
    completed_at: datetime
    duration_ms: float


class AuditRecord(BaseModel):
    """Persistent record of one requested tool execution."""

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


class AgentRunEvent(BaseModel):
    """Observable event emitted while a tool-using agent request is running."""

    event: Literal[
        "run_started",
        "model_thinking",
        "tool_requested",
        "tool_approved",
        "tool_blocked",
        "tool_succeeded",
        "tool_failed",
        "final_answer",
        "max_rounds_reached",
    ]
    round_index: Optional[int] = None
    message: str
    call: Optional[ToolCall] = None
    authorization: Optional[ToolAuthorization] = None
    result: Optional[ToolResult] = None
    final_result: Optional[AgentRunResult] = None
