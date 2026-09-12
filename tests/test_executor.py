from src.executor import authorize_tool_call, execute_tool
from src.schemas import ToolCall


def test_authorization_approves_registered_valid_call():
    call = ToolCall(
        tool_name="calculator",
        arguments={"expression": "12 * 4"},
    )

    authorization = authorize_tool_call(call)

    assert authorization.status == "approved"
    assert authorization.call_id == call.call_id
    assert authorization.tool_name == "calculator"
    assert "approved schema" in authorization.reason


def test_authorization_blocks_unregistered_tool_before_execution():
    call = ToolCall(
        tool_name="run_shell_command",
        arguments={"command": "whoami"},
    )

    authorization = authorize_tool_call(call)

    assert authorization.status == "blocked"
    assert "not registered" in authorization.reason


def test_executor_runs_approved_tool():
    call = ToolCall(
        tool_name="calculator",
        arguments={
            "expression": "12 * 4",
        },
    )

    result = execute_tool(call)

    assert result.status == "success"
    assert result.output is not None
    assert result.output["result"] == 48
    assert result.error is None
    assert result.call_id == call.call_id
    assert result.tool_name == "calculator"


def test_executor_blocks_unregistered_tool():
    call = ToolCall(
        tool_name="run_shell_command",
        arguments={
            "command": "whoami",
        },
    )

    result = execute_tool(call)

    assert result.status == "blocked"
    assert result.output is None
    assert result.error is not None
    assert "not registered" in result.error


def test_executor_blocks_missing_required_argument():
    call = ToolCall(
        tool_name="calculator",
        arguments={},
    )

    result = execute_tool(call)

    assert result.status == "blocked"
    assert result.output is None
    assert result.error is not None
    assert "Missing required argument" in result.error
    assert "expression" in result.error


def test_executor_blocks_unexpected_argument():
    call = ToolCall(
        tool_name="calculator",
        arguments={
            "expression": "10 + 5",
            "unexpected": "value",
        },
    )

    result = execute_tool(call)

    assert result.status == "blocked"
    assert result.output is None
    assert result.error is not None
    assert "Unexpected argument" in result.error
    assert "unexpected" in result.error


def test_executor_blocks_wrong_argument_type():
    call = ToolCall(
        tool_name="calculator",
        arguments={
            "expression": 123,
        },
    )

    result = execute_tool(call)

    assert result.status == "blocked"
    assert result.output is None
    assert result.error is not None
    assert "must be of type 'string'" in result.error


def test_executor_marks_authorized_tool_failure_as_execution_error():
    call = ToolCall(
        tool_name="calculator",
        arguments={
            "expression": "10 / 0",
        },
    )

    authorization = authorize_tool_call(call)
    result = execute_tool(call)

    assert authorization.status == "approved"
    assert result.status == "error"
    assert result.output is None
    assert result.error is not None
    assert "Division by zero" in result.error


def test_executor_records_timing_information():
    call = ToolCall(
        tool_name="calculator",
        arguments={
            "expression": "2 + 2",
        },
    )

    result = execute_tool(call)

    assert result.started_at is not None
    assert result.completed_at is not None
    assert result.completed_at >= result.started_at
    assert result.duration_ms >= 0
