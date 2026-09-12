from types import SimpleNamespace

import src.agent as agent_module


class FakeToolCall:
    def __init__(self, call_id: str, name: str, arguments: str):
        self.id = call_id
        self.function = SimpleNamespace(
            name=name,
            arguments=arguments,
        )

    def model_dump(self):
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.function.name,
                "arguments": self.function.arguments,
            },
        }


class FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class FakeResponse:
    def __init__(self, message):
        self.choices = [SimpleNamespace(message=message)]


class FakeCompletions:
    def __init__(self, responses):
        self._responses = iter(responses)

    def create(self, **_kwargs):
        return next(self._responses)


class FakeClient:
    def __init__(self, responses):
        self.chat = SimpleNamespace(
            completions=FakeCompletions(responses)
        )


def _patch_client(monkeypatch, responses):
    monkeypatch.setattr(
        agent_module,
        "get_client",
        lambda: FakeClient(responses),
    )
    monkeypatch.setattr(
        agent_module,
        "write_audit_record",
        lambda call, result: None,
    )


def test_run_agent_iter_emits_real_authorization_and_execution_events(monkeypatch):
    _patch_client(
        monkeypatch,
        [
            FakeResponse(
                FakeMessage(
                    tool_calls=[
                        FakeToolCall(
                            "call-1",
                            "calculator",
                            '{"expression": "12 * 4"}',
                        )
                    ]
                )
            ),
            FakeResponse(
                FakeMessage(
                    content="The result is 48.",
                    tool_calls=None,
                )
            ),
        ],
    )

    events = list(
        agent_module.run_agent_iter("What is 12 multiplied by 4?")
    )

    event_names = [event.event for event in events]

    assert event_names == [
        "run_started",
        "model_thinking",
        "tool_requested",
        "tool_approved",
        "tool_succeeded",
        "model_thinking",
        "final_answer",
    ]

    approved = next(event for event in events if event.event == "tool_approved")
    succeeded = next(event for event in events if event.event == "tool_succeeded")
    final = events[-1]

    assert approved.authorization is not None
    assert approved.authorization.status == "approved"
    assert succeeded.result is not None
    assert succeeded.result.status == "success"
    assert succeeded.result.output["result"] == 48
    assert final.final_result is not None
    assert final.final_result.final_answer == "The result is 48."


def test_run_agent_iter_reports_blocked_call_before_execution(monkeypatch):
    _patch_client(
        monkeypatch,
        [
            FakeResponse(
                FakeMessage(
                    tool_calls=[
                        FakeToolCall(
                            "call-blocked",
                            "run_shell_command",
                            '{"command": "whoami"}',
                        )
                    ]
                )
            ),
            FakeResponse(
                FakeMessage(
                    content="That capability is not available.",
                    tool_calls=None,
                )
            ),
        ],
    )

    events = list(
        agent_module.run_agent_iter("Run a shell command.")
    )

    blocked = next(event for event in events if event.event == "tool_blocked")

    assert blocked.authorization is not None
    assert blocked.authorization.status == "blocked"
    assert blocked.result is not None
    assert blocked.result.status == "blocked"
    assert "not registered" in blocked.message
    assert not any(event.event == "tool_succeeded" for event in events)


def test_run_agent_preserves_final_result_api(monkeypatch):
    _patch_client(
        monkeypatch,
        [
            FakeResponse(
                FakeMessage(
                    content="No tool was needed.",
                    tool_calls=None,
                )
            )
        ],
    )

    result = agent_module.run_agent("Say hello without tools.")

    assert result.final_answer == "No tool was needed."
    assert result.tool_calls == []
    assert result.tool_results == []
