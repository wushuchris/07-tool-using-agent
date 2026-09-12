import json
import os
from collections.abc import Iterator
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from src.audit import write_audit_record
from src.executor import authorize_tool_call, execute_authorized_tool
from src.schemas import AgentRunEvent, AgentRunResult, ToolCall
from src.tool_registry import get_tool_definitions


load_dotenv(dotenv_path=".env")


HF_BASE_URL = "https://router.huggingface.co/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b:cerebras"

SYSTEM_PROMPT = """
You are a controlled tool-using operations agent.

You have access only to the tools explicitly provided to you.

Rules:
1. Use tools when they are needed to answer the user's request accurately.
2. Do not claim that a tool was used unless you actually called it.
3. Never invent tool results.
4. Do not invent tools that are not available.
5. Use the calculator for arithmetic rather than calculating mentally.
6. Use search_inventory for questions about the inventory database.
7. Use lookup_country for structured country information.
8. You may call multiple tools when the user's request requires them.
9. After receiving tool results, use those results to construct your answer.
10. If a tool is blocked or returns an error, do not hide the failure.
11. Do not expose internal chain-of-thought. Provide concise conclusions only.
"""


def get_client() -> OpenAI:
    """Create the Hugging Face OpenAI-compatible client."""

    token = os.getenv("HF_TOKEN")

    if not token:
        raise RuntimeError(
            "HF_TOKEN is not configured. "
            "Set it as an environment variable before running the agent."
        )

    return OpenAI(
        base_url=HF_BASE_URL,
        api_key=token,
    )


def _parse_tool_arguments(raw_arguments: str) -> Dict[str, Any]:
    """Decode model-provided tool arguments into an object for validation."""

    try:
        arguments = json.loads(raw_arguments)

        if not isinstance(arguments, dict):
            raise ValueError(
                "Tool arguments must decode to an object."
            )

        return arguments

    except (json.JSONDecodeError, ValueError):
        return {
            "__invalid_arguments__": raw_arguments,
        }


def run_agent_iter(
    user_request: str,
    model: str | None = None,
    max_tool_rounds: int = 5,
) -> Iterator[AgentRunEvent]:
    """Run the agent while emitting real control-boundary events."""

    if not isinstance(user_request, str):
        raise TypeError("user_request must be a string.")

    user_request = user_request.strip()

    if not user_request:
        raise ValueError("user_request cannot be empty.")

    if max_tool_rounds < 1:
        raise ValueError(
            "max_tool_rounds must be at least 1."
        )

    client = get_client()

    selected_model = (
        model
        or os.getenv("MODEL_ID")
        or DEFAULT_MODEL
    )

    tools = get_tool_definitions()

    messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_request,
        },
    ]

    executed_calls: List[ToolCall] = []
    executed_results = []

    yield AgentRunEvent(
        event="run_started",
        message=(
            "Request accepted. The model may propose only tools exposed "
            "through the approved registry."
        ),
    )

    for round_index in range(1, max_tool_rounds + 1):
        yield AgentRunEvent(
            event="model_thinking",
            round_index=round_index,
            message="The model is deciding whether an approved tool is needed.",
        )

        response = client.chat.completions.create(
            model=selected_model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            reasoning_effort="low",
        )

        message = response.choices[0].message

        assistant_message: Dict[str, Any] = {
            "role": "assistant",
            "content": message.content,
        }

        if message.tool_calls:
            assistant_message["tool_calls"] = [
                tool_call.model_dump()
                for tool_call in message.tool_calls
            ]

        messages.append(assistant_message)

        if not message.tool_calls:
            final_answer = (
                message.content
                or "The agent returned no final answer."
            )

            final_result = AgentRunResult(
                user_request=user_request,
                final_answer=final_answer,
                tool_calls=executed_calls,
                tool_results=executed_results,
            )

            yield AgentRunEvent(
                event="final_answer",
                round_index=round_index,
                message="The model produced the final answer from the available results.",
                final_result=final_result,
            )
            return

        for model_tool_call in message.tool_calls:
            call = ToolCall(
                call_id=model_tool_call.id,
                tool_name=model_tool_call.function.name,
                arguments=_parse_tool_arguments(
                    model_tool_call.function.arguments
                ),
            )

            yield AgentRunEvent(
                event="tool_requested",
                round_index=round_index,
                message=f"The model requested the '{call.tool_name}' tool.",
                call=call,
            )

            authorization = authorize_tool_call(call)

            if authorization.status == "approved":
                yield AgentRunEvent(
                    event="tool_approved",
                    round_index=round_index,
                    message=(
                        f"Application approved '{call.tool_name}': "
                        f"{authorization.reason}"
                    ),
                    call=call,
                    authorization=authorization,
                )
            else:
                result = execute_authorized_tool(
                    call=call,
                    authorization=authorization,
                )
                write_audit_record(call=call, result=result)
                executed_calls.append(call)
                executed_results.append(result)

                yield AgentRunEvent(
                    event="tool_blocked",
                    round_index=round_index,
                    message=(
                        f"Application blocked '{call.tool_name}' before execution: "
                        f"{authorization.reason}"
                    ),
                    call=call,
                    authorization=authorization,
                    result=result,
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": model_tool_call.id,
                        "content": json.dumps(
                            {
                                "status": result.status,
                                "output": result.output,
                                "error": result.error,
                            },
                            default=str,
                        ),
                    }
                )
                continue

            result = execute_authorized_tool(
                call=call,
                authorization=authorization,
            )

            write_audit_record(
                call=call,
                result=result,
            )

            executed_calls.append(call)
            executed_results.append(result)

            event_name = (
                "tool_succeeded"
                if result.status == "success"
                else "tool_failed"
            )

            event_message = (
                f"Approved tool '{call.tool_name}' executed successfully."
                if result.status == "success"
                else (
                    f"Approved tool '{call.tool_name}' failed during execution: "
                    f"{result.error}"
                )
            )

            yield AgentRunEvent(
                event=event_name,
                round_index=round_index,
                message=event_message,
                call=call,
                authorization=authorization,
                result=result,
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": model_tool_call.id,
                    "content": json.dumps(
                        {
                            "status": result.status,
                            "output": result.output,
                            "error": result.error,
                        },
                        default=str,
                    ),
                }
            )

    final_result = AgentRunResult(
        user_request=user_request,
        final_answer=(
            "The agent reached the maximum number "
            "of tool-execution rounds before producing "
            "a final answer."
        ),
        tool_calls=executed_calls,
        tool_results=executed_results,
    )

    yield AgentRunEvent(
        event="max_rounds_reached",
        round_index=max_tool_rounds,
        message="The configured tool-round limit was reached.",
        final_result=final_result,
    )


def run_agent(
    user_request: str,
    model: str | None = None,
    max_tool_rounds: int = 5,
) -> AgentRunResult:
    """Run the tool-using agent and return the final structured result."""

    final_result: AgentRunResult | None = None

    for event in run_agent_iter(
        user_request=user_request,
        model=model,
        max_tool_rounds=max_tool_rounds,
    ):
        if event.final_result is not None:
            final_result = event.final_result

    if final_result is None:
        raise RuntimeError(
            "Agent run ended without a final result."
        )

    return final_result
