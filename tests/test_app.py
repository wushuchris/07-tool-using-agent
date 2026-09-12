from datetime import datetime, timezone

import app
from src.demo_presentation import APP_CSS, AUTHORITY_HTML, HERO_HTML, idle_activity_html
from src.schemas import (
    AgentRunEvent,
    AgentRunResult,
    ToolAuthorization,
    ToolCall,
    ToolResult,
)


def test_business_presentation_centers_the_trust_boundary():
    assert "max-width: 1080px" in APP_CSS
    assert "How can an AI use company tools" in HERO_HTML
    assert "The model controls" in AUTHORITY_HTML
    assert "Application code controls" in AUTHORITY_HTML
    assert "READY" in idle_activity_html()


def test_stream_request_yields_real_control_events_before_final(monkeypatch):
    call = ToolCall(
        call_id="call-demo",
        tool_name="calculator",
        arguments={"expression": "12 * 4"},
    )
    authorization = ToolAuthorization(
        call_id=call.call_id,
        tool_name=call.tool_name,
        status="approved",
        reason="Tool is registered and arguments match the approved schema.",
    )
    now = datetime.now(timezone.utc)
    result = ToolResult(
        call_id=call.call_id,
        tool_name=call.tool_name,
        status="success",
        output={"result": 48},
        error=None,
        started_at=now,
        completed_at=now,
        duration_ms=0.1,
    )
    final_result = AgentRunResult(
        user_request="What is 12 multiplied by 4?",
        final_answer="The result is 48.",
        tool_calls=[call],
        tool_results=[result],
    )

    def fake_run_agent_iter(_request):
        yield AgentRunEvent(
            event="run_started",
            message="Request accepted.",
        )
        yield AgentRunEvent(
            event="model_thinking",
            round_index=1,
            message="The model is deciding whether an approved tool is needed.",
        )
        yield AgentRunEvent(
            event="tool_requested",
            round_index=1,
            message="The model requested the 'calculator' tool.",
            call=call,
        )
        yield AgentRunEvent(
            event="tool_approved",
            round_index=1,
            message="Application approved 'calculator'.",
            call=call,
            authorization=authorization,
        )
        yield AgentRunEvent(
            event="tool_succeeded",
            round_index=1,
            message="Approved tool 'calculator' executed successfully.",
            call=call,
            authorization=authorization,
            result=result,
        )
        yield AgentRunEvent(
            event="final_answer",
            round_index=2,
            message="The model produced the final answer.",
            final_result=final_result,
        )

    monkeypatch.setattr(app, "run_agent_iter", fake_run_agent_iter)
    monkeypatch.setattr(app, "get_run_audit_records", lambda _ids: [])

    frames = list(app.stream_request("What is 12 multiplied by 4?"))

    assert len(frames) == 7
    assert all(len(frame) == 6 for frame in frames)
    assert "RUNNING" in frames[0][0]
    assert any("Model requested" in frame[0] for frame in frames[1:-1])
    assert any("Application approved" in frame[0] for frame in frames[1:-1])
    assert any("Tool completed" in frame[0] for frame in frames[1:-1])
    assert "COMPLETE" in frames[-1][0]
    assert frames[-1][1] == "The result is 48."
    assert "1</strong>requested" in frames[-1][2]
    assert "1</strong>executed" in frames[-1][2]


def test_stream_request_keeps_blocked_calls_distinct_from_execution_failures(monkeypatch):
    call = ToolCall(
        call_id="call-blocked",
        tool_name="run_shell_command",
        arguments={"command": "whoami"},
    )
    authorization = ToolAuthorization(
        call_id=call.call_id,
        tool_name=call.tool_name,
        status="blocked",
        reason="ValueError: Tool 'run_shell_command' is not registered.",
    )
    now = datetime.now(timezone.utc)
    result = ToolResult(
        call_id=call.call_id,
        tool_name=call.tool_name,
        status="blocked",
        output=None,
        error=authorization.reason,
        started_at=now,
        completed_at=now,
        duration_ms=0.1,
    )
    final_result = AgentRunResult(
        user_request="Run whoami.",
        final_answer="That capability is not available.",
        tool_calls=[call],
        tool_results=[result],
    )

    def fake_run_agent_iter(_request):
        yield AgentRunEvent(
            event="tool_requested",
            round_index=1,
            message="The model requested the 'run_shell_command' tool.",
            call=call,
        )
        yield AgentRunEvent(
            event="tool_blocked",
            round_index=1,
            message="Application blocked the tool before execution.",
            call=call,
            authorization=authorization,
            result=result,
        )
        yield AgentRunEvent(
            event="final_answer",
            round_index=2,
            message="The model produced the final answer.",
            final_result=final_result,
        )

    monkeypatch.setattr(app, "run_agent_iter", fake_run_agent_iter)
    monkeypatch.setattr(app, "get_run_audit_records", lambda _ids: [])

    frames = list(app.stream_request("Run whoami."))

    assert any("Application blocked" in frame[0] for frame in frames)
    assert "1</strong>blocked" in frames[-1][2]
    assert "0</strong>failed" in frames[-1][2]
