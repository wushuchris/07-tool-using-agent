from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Dict

from src.schemas import ToolCall, ToolResult
from src.tool_registry import TOOL_REGISTRY, get_tool


def _validate_arguments(
    tool_name: str,
    arguments: Dict[str, Any],
) -> None:
    """
    Validate tool arguments against the registry's parameter schema.

    This is intentionally lightweight and supports the schema features
    used by the tools in this project.
    """

    if tool_name not in TOOL_REGISTRY:
        raise ValueError(
            f"Tool '{tool_name}' is not registered."
        )

    schema = TOOL_REGISTRY[tool_name]["parameters"]

    properties = schema.get("properties", {})
    required = schema.get("required", [])
    allow_additional = schema.get(
        "additionalProperties",
        True,
    )

    for required_argument in required:
        if required_argument not in arguments:
            raise ValueError(
                f"Missing required argument "
                f"'{required_argument}' for tool "
                f"'{tool_name}'."
            )

    if not allow_additional:
        unknown_arguments = (
            set(arguments.keys()) - set(properties.keys())
        )

        if unknown_arguments:
            unknown = ", ".join(
                sorted(unknown_arguments)
            )

            raise ValueError(
                f"Unexpected argument(s) for tool "
                f"'{tool_name}': {unknown}"
            )

    python_types = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "object": dict,
        "array": list,
    }

    for argument_name, argument_value in arguments.items():
        parameter_schema = properties.get(argument_name)

        if not parameter_schema:
            continue

        expected_type_name = parameter_schema.get("type")

        if not expected_type_name:
            continue

        expected_python_type = python_types.get(
            expected_type_name
        )

        if expected_python_type is None:
            continue

        if not isinstance(
            argument_value,
            expected_python_type,
        ):
            raise TypeError(
                f"Argument '{argument_name}' for tool "
                f"'{tool_name}' must be of type "
                f"'{expected_type_name}'."
            )


def execute_tool(call: ToolCall) -> ToolResult:
    """
    Validate and execute a tool call.

    All outcomes are normalized into ToolResult objects so callers do not
    need separate handling for every underlying tool.
    """

    started_at = datetime.now(timezone.utc)
    timer_start = perf_counter()

    try:
        _validate_arguments(
            tool_name=call.tool_name,
            arguments=call.arguments,
        )

        tool = get_tool(call.tool_name)

        output = tool(**call.arguments)

        status = "success"
        error = None

    except Exception as exc:
        output = None
        status = "error"
        error = f"{type(exc).__name__}: {exc}"

    timer_end = perf_counter()
    completed_at = datetime.now(timezone.utc)

    duration_ms = (
        timer_end - timer_start
    ) * 1000

    return ToolResult(
        call_id=call.call_id,
        tool_name=call.tool_name,
        status=status,
        output=output,
        error=error,
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=round(duration_ms, 3),
    )