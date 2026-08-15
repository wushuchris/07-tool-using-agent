import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from src.audit import write_audit_record
from src.executor import execute_tool
from src.schemas import AgentRunResult, ToolCall
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
10. If a tool returns an error, do not hide the failure.
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


def run_agent(
    user_request: str,
    model: str | None = None,
    max_tool_rounds: int = 5,
) -> AgentRunResult:
    """
    Run the tool-using agent.

    The model may request approved tools. Every requested tool is passed
    through the controlled executor and written to the audit log.
    """

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

    for _ in range(max_tool_rounds):
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

            return AgentRunResult(
                user_request=user_request,
                final_answer=final_answer,
                tool_calls=executed_calls,
                tool_results=executed_results,
            )

        for model_tool_call in message.tool_calls:
            tool_name = model_tool_call.function.name

            try:
                arguments = json.loads(
                    model_tool_call.function.arguments
                )

                if not isinstance(arguments, dict):
                    raise ValueError(
                        "Tool arguments must decode to an object."
                    )

            except (
                json.JSONDecodeError,
                ValueError,
            ) as exc:
                arguments = {
                    "__invalid_arguments__": (
                        model_tool_call.function.arguments
                    )
                }

            call = ToolCall(
                call_id=model_tool_call.id,
                tool_name=tool_name,
                arguments=arguments,
            )

            result = execute_tool(call)

            write_audit_record(
                call=call,
                result=result,
            )

            executed_calls.append(call)
            executed_results.append(result)

            tool_payload = {
                "status": result.status,
                "output": result.output,
                "error": result.error,
            }

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": model_tool_call.id,
                    "content": json.dumps(
                        tool_payload,
                        default=str,
                    ),
                }
            )

    return AgentRunResult(
        user_request=user_request,
        final_answer=(
            "The agent reached the maximum number "
            "of tool-execution rounds before producing "
            "a final answer."
        ),
        tool_calls=executed_calls,
        tool_results=executed_results,
    )