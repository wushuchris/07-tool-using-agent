from typing import Any, Dict, List

import gradio as gr

from src.agent import run_agent, run_agent_iter
from src.audit import read_audit_records
from src.demo_presentation import (
    APP_CSS,
    ARCHITECTURE_MARKDOWN,
    AUTHORITY_HTML,
    BUSINESS_CASE_HTML,
    HERO_HTML,
    SECURITY_MARKDOWN,
    TOOL_BELT_HTML,
    render_activity,
    render_summary,
    starting_activity_html,
)
from src.schemas import AgentRunEvent, AgentRunResult


def get_run_audit_records(
    call_ids: List[str],
) -> List[Dict[str, Any]]:
    """Return audit records belonging only to the current agent run."""

    if not call_ids:
        return []

    records = read_audit_records()

    matching_records = [
        record
        for record in records
        if record.call.call_id in call_ids
    ]

    return [
        record.model_dump(mode="json")
        for record in matching_records
    ]


def handle_request(user_request: str):
    """Preserve the original programmatic callback contract."""

    if not user_request or not user_request.strip():
        return (
            "Please enter a request.",
            [],
            [],
            [],
        )

    try:
        result = run_agent(user_request.strip())

        tool_calls = [
            call.model_dump(mode="json")
            for call in result.tool_calls
        ]
        tool_results = [
            tool_result.model_dump(mode="json")
            for tool_result in result.tool_results
        ]
        call_ids = [
            call.call_id
            for call in result.tool_calls
        ]

        return (
            result.final_answer,
            tool_calls,
            tool_results,
            get_run_audit_records(call_ids),
        )

    except Exception:
        return (
            (
                "Agent execution failed. "
                "Please review the server logs for details."
            ),
            [],
            [],
            [],
        )


def _current_calls(events: list[AgentRunEvent]) -> list[Dict[str, Any]]:
    calls: dict[str, Dict[str, Any]] = {}

    for event in events:
        if event.call is not None:
            calls[event.call.call_id] = event.call.model_dump(mode="json")

    return list(calls.values())


def _current_results(events: list[AgentRunEvent]) -> list[Dict[str, Any]]:
    results: dict[str, Dict[str, Any]] = {}

    for event in events:
        if event.result is not None:
            results[event.result.call_id] = event.result.model_dump(mode="json")

    return list(results.values())


def _stream_outputs(
    events: list[AgentRunEvent],
    final_result: AgentRunResult | None = None,
    complete: bool = False,
):
    calls = (
        [call.model_dump(mode="json") for call in final_result.tool_calls]
        if final_result is not None
        else _current_calls(events)
    )
    results = (
        [result.model_dump(mode="json") for result in final_result.tool_results]
        if final_result is not None
        else _current_results(events)
    )
    call_ids = [call["call_id"] for call in calls]
    audits = get_run_audit_records(call_ids) if complete else []

    answer = (
        final_result.final_answer
        if final_result is not None
        else "*The final business answer will appear after controlled execution completes.*"
    )

    return (
        render_activity(events, complete=complete),
        answer,
        render_summary(final_result),
        calls,
        results,
        audits,
    )


def stream_request(user_request: str):
    """Stream real model/application boundary events into the Gradio demo."""

    if not user_request or not user_request.strip():
        yield (
            render_activity([], complete=True),
            "Please enter a request.",
            render_summary(None),
            [],
            [],
            [],
        )
        return

    events: list[AgentRunEvent] = []

    yield (
        starting_activity_html(),
        "*The final business answer will appear after controlled execution completes.*",
        render_summary(None),
        [],
        [],
        [],
    )

    try:
        for event in run_agent_iter(user_request.strip()):
            events.append(event)
            final_result = event.final_result
            complete = final_result is not None

            yield _stream_outputs(
                events=events,
                final_result=final_result,
                complete=complete,
            )

    except Exception:
        error_event = AgentRunEvent(
            event="max_rounds_reached",
            message=(
                "The request could not complete. The application stopped the run "
                "without exposing internal server details."
            ),
        )
        events.append(error_event)

        yield (
            render_activity(events, complete=True),
            (
                "Agent execution failed. Please review the server logs for details."
            ),
            render_summary(None),
            _current_calls(events),
            _current_results(events),
            [],
        )


FLAGSHIP_REQUEST = (
    "We may ship equipment to Japan. Find the Electronics items currently in "
    "inventory, calculate an accessory budget of $347 per matching item, and "
    "give me Japan's capital, region, and income classification."
)


with gr.Blocks(
    title="Governed Tool-Using Agent",
    css=APP_CSS,
) as demo:
    with gr.Column(elem_classes=["agent-shell"]):
        gr.HTML(HERO_HTML)
        gr.HTML(BUSINESS_CASE_HTML)

        gr.Markdown("## The approved tool belt")
        gr.HTML(TOOL_BELT_HTML)

        gr.Markdown("## Who controls what?")
        gr.HTML(AUTHORITY_HTML)

        gr.Markdown("## Try a controlled business request")
        request_box = gr.Textbox(
            label="Operations request",
            value=FLAGSHIP_REQUEST,
            placeholder="Ask for work that may require one or more approved tools.",
            lines=4,
        )

        gr.Examples(
            examples=[
                [FLAGSHIP_REQUEST],
                ["What is 347 multiplied by 29?"],
                ["What electronics are currently in inventory?"],
                ["What is the capital, region, and income level of Japan?"],
                [
                    (
                        "How many Electronics items are in inventory, "
                        "and what is 347 multiplied by that number?"
                    )
                ],
            ],
            inputs=request_box,
        )

        run_button = gr.Button(
            "Run controlled request",
            variant="primary",
        )

        activity_output = gr.HTML(starting_activity_html())

        with gr.Tabs():
            with gr.Tab("Business Result"):
                gr.Markdown(
                    "The answer below is produced only after requested capabilities "
                    "pass through the application-controlled boundary."
                )
                final_answer = gr.Markdown(
                    "*Run a request to produce a business answer.*"
                )
                summary_output = gr.HTML(render_summary(None))

            with gr.Tab("Engineering Audit"):
                gr.Markdown(
                    "These are the structured requests, normalized results, and "
                    "current-run audit records behind the business-facing view."
                )
                tool_calls_output = gr.JSON(label="Model-proposed Tool Calls")
                tool_results_output = gr.JSON(label="Controlled Tool Results")
                audit_output = gr.JSON(label="Current Run Audit Records")

            with gr.Tab("Security & Failure Semantics"):
                gr.Markdown(SECURITY_MARKDOWN)

            with gr.Tab("Architecture"):
                gr.Markdown(ARCHITECTURE_MARKDOWN)

        run_button.click(
            fn=stream_request,
            inputs=request_box,
            outputs=[
                activity_output,
                final_answer,
                summary_output,
                tool_calls_output,
                tool_results_output,
                audit_output,
            ],
            show_progress="hidden",
        )


if __name__ == "__main__":
    demo.launch()
