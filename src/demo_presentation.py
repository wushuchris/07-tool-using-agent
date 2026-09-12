"""Business-first presentation helpers for the governed tool-using agent demo."""

from html import escape

from src.schemas import AgentRunEvent, AgentRunResult


APP_CSS = """
.gradio-container {
    max-width: 1080px !important;
    margin: 0 auto !important;
}
.agent-shell {
    max-width: 1080px;
    margin: 0 auto;
}
.hero {
    padding: 8px 0 4px 0;
}
.hero h1 {
    font-size: 2.35rem;
    line-height: 1.08;
    margin-bottom: 0.55rem;
}
.hero p {
    font-size: 1.08rem;
    line-height: 1.65;
    max-width: 820px;
}
.business-card, .tool-card, .authority-card, .activity-panel, .summary-card {
    border: 1px solid var(--border-color-primary);
    border-radius: 14px;
    padding: 18px;
    margin: 10px 0;
    background: var(--background-fill-secondary);
}
.tool-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 10px;
}
.tool-name {
    font-size: 1.06rem;
    font-weight: 700;
    margin-bottom: 5px;
}
.tool-boundary {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 10px;
}
.boundary-good, .boundary-no {
    padding: 10px 12px;
    border-radius: 10px;
    background: var(--background-fill-primary);
}
.authority-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
.authority-title {
    font-weight: 700;
    margin-bottom: 8px;
}
.activity-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
}
.status-badge {
    display: inline-block;
    border-radius: 999px;
    padding: 4px 10px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.04em;
}
.status-running { background: rgba(245, 158, 11, 0.16); }
.status-complete { background: rgba(34, 197, 94, 0.16); }
.status-stopped { background: rgba(239, 68, 68, 0.14); }
.spinner {
    width: 15px;
    height: 15px;
    border: 2px solid rgba(120,120,120,0.3);
    border-top-color: currentColor;
    border-radius: 50%;
    animation: spin 0.85s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.event-feed {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.event-feed-complete {
    max-height: 380px;
    overflow-y: auto;
    padding-right: 4px;
}
.event-row {
    padding: 10px 12px;
    border-radius: 10px;
    background: var(--background-fill-primary);
    line-height: 1.45;
}
.event-label {
    display: inline-block;
    min-width: 126px;
    font-weight: 700;
}
.event-meta {
    opacity: 0.72;
    font-size: 0.86rem;
    margin-top: 4px;
}
.summary-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-top: 8px;
}
.metric {
    text-align: center;
    padding: 12px;
    border-radius: 10px;
    background: var(--background-fill-primary);
}
.metric strong {
    display: block;
    font-size: 1.35rem;
}
@media (max-width: 760px) {
    .authority-grid, .tool-boundary, .summary-grid {
        grid-template-columns: 1fr;
    }
    .hero h1 { font-size: 1.9rem; }
}
"""


HERO_HTML = """
<div class="agent-shell hero">
  <h1>How can an AI use company tools without being given the keys to everything?</h1>
  <p>
    This demo shows a governed tool-using agent. The model can decide that it needs
    a capability, but it cannot execute arbitrary code, query arbitrary databases,
    or reach arbitrary systems. Every requested action must cross an
    application-controlled authorization and execution boundary.
  </p>
</div>
"""


BUSINESS_CASE_HTML = """
<div class="business-card">
  <strong>Business scenario</strong><br>
  Imagine an operations copilot helping a team answer routine questions that may
  require internal inventory data, deterministic calculations, or an approved
  external reference API. Giving the model unrestricted system access would be
  convenient—but unsafe. This agent demonstrates delegated authority instead:
  <strong>the model proposes; application code decides what may actually run.</strong>
</div>
"""


TOOL_BELT_HTML = """
<div class="tool-grid">
  <div class="tool-card">
    <div class="tool-name">🧮 Calculator — deterministic local computation</div>
    Safely evaluates approved arithmetic expressions through a constrained AST parser.
    <div class="tool-boundary">
      <div class="boundary-good"><strong>Allowed</strong><br>Approved arithmetic operations</div>
      <div class="boundary-no"><strong>Not allowed</strong><br>Arbitrary Python or unrestricted <code>eval()</code></div>
    </div>
  </div>
  <div class="tool-card">
    <div class="tool-name">📦 Inventory — controlled internal data access</div>
    Searches a small SQLite inventory database through a narrow parameterized interface.
    <div class="tool-boundary">
      <div class="boundary-good"><strong>Allowed</strong><br>Item/category inventory search</div>
      <div class="boundary-no"><strong>Not allowed</strong><br>Arbitrary SQL, writes, or database administration</div>
    </div>
  </div>
  <div class="tool-card">
    <div class="tool-name">🌍 Country lookup — controlled external API access</div>
    Retrieves structured country information through the approved World Bank endpoint.
    <div class="tool-boundary">
      <div class="boundary-good"><strong>Allowed</strong><br>Structured country lookup</div>
      <div class="boundary-no"><strong>Not allowed</strong><br>Arbitrary URLs, browsing, or open-ended network access</div>
    </div>
  </div>
</div>
"""


AUTHORITY_HTML = """
<div class="authority-card authority-grid">
  <div>
    <div class="authority-title">🤖 The model controls</div>
    <ul>
      <li>whether a tool appears necessary;</li>
      <li>which approved tool to request;</li>
      <li>how to combine returned results;</li>
      <li>when enough information exists to answer.</li>
    </ul>
  </div>
  <div>
    <div class="authority-title">🛡️ Application code controls</div>
    <ul>
      <li>which tools exist at all;</li>
      <li>whether arguments match the approved schema;</li>
      <li>whether execution is authorized;</li>
      <li>tool execution, error normalization, and audit logging.</li>
    </ul>
  </div>
</div>
"""


ARCHITECTURE_MARKDOWN = """
### Architecture

```text
User request
    ↓
LLM proposes an action
    ↓
Structured ToolCall
    ↓
Application authorization boundary
    ├─ blocked → normalized blocked result + audit record
    └─ approved
          ↓
     Controlled executor
          ↓
     Approved capability
          ↓
     Normalized ToolResult + audit record
          ↓
     Result returned to model
          ↓
     Additional approved tool request or final answer
```

The model never receives unrestricted shell, Python, filesystem, SQL, or arbitrary
network execution. The reusable primitive is the **application-owned capability boundary**.
"""


SECURITY_MARKDOWN = """
### Security and failure semantics

The demo distinguishes two classes of failure that should not be conflated:

**Blocked before execution** — the application refuses the model's request because the
tool is not registered or the arguments violate the approved schema. The underlying
capability never runs.

**Approved but execution failed** — the requested capability was allowed, but the tool
encountered a runtime or dependency error such as division by zero or an external API
failure.

Both outcomes are normalized into structured results and written to the current-run
audit trail. This is a portfolio demonstration of a narrow trust boundary, not a
production-certified sandbox or multi-tenant security platform.
"""


EVENT_LABELS = {
    "run_started": "Request accepted",
    "model_thinking": "AI deciding",
    "tool_requested": "Model requested",
    "tool_approved": "Application approved",
    "tool_blocked": "Application blocked",
    "tool_succeeded": "Tool completed",
    "tool_failed": "Execution failed",
    "final_answer": "Final response",
    "max_rounds_reached": "Safety stop",
}


def starting_activity_html() -> str:
    """Return an immediate visible state before provider work begins."""

    return """
    <div class="activity-panel">
      <div class="activity-header">
        <span class="status-badge status-running">RUNNING</span>
        <span class="spinner"></span>
        <strong>Live Controlled Execution</strong>
      </div>
      <div class="event-row">
        Request submitted. Preparing the approved tool registry and model context.
      </div>
    </div>
    """


def render_activity(
    events: list[AgentRunEvent],
    complete: bool = False,
) -> str:
    """Render real run events as a readable control-boundary timeline."""

    stopped = bool(
        events
        and events[-1].event in {"max_rounds_reached", "tool_blocked"}
        and not any(event.event == "final_answer" for event in events)
    )

    if complete:
        badge_class = "status-complete" if not stopped else "status-stopped"
        badge_text = "COMPLETE" if not stopped else "STOPPED"
        spinner = ""
        visible_events = events
        feed_class = "event-feed event-feed-complete"
    else:
        badge_class = "status-running"
        badge_text = "RUNNING"
        spinner = '<span class="spinner"></span>'
        visible_events = events[-9:]
        feed_class = "event-feed"

    rows = []
    for event in visible_events:
        label = EVENT_LABELS[event.event]
        message = escape(event.message)
        meta_parts = []

        if event.round_index is not None:
            meta_parts.append(f"round {event.round_index}")
        if event.call is not None:
            meta_parts.append(f"tool: {escape(event.call.tool_name)}")
            meta_parts.append(f"call: {escape(event.call.call_id)}")
        if event.result is not None:
            meta_parts.append(f"status: {escape(event.result.status)}")

        meta = ""
        if meta_parts:
            meta = (
                '<div class="event-meta">'
                + " · ".join(meta_parts)
                + "</div>"
            )

        rows.append(
            '<div class="event-row">'
            f'<span class="event-label">{escape(label)}</span>'
            f"{message}{meta}</div>"
        )

    if not rows:
        rows.append(
            '<div class="event-row">Waiting for the run to begin.</div>'
        )

    return (
        '<div class="activity-panel">'
        '<div class="activity-header">'
        f'<span class="status-badge {badge_class}">{badge_text}</span>'
        f"{spinner}<strong>Live Controlled Execution</strong>"
        "</div>"
        f'<div class="{feed_class}">{"".join(rows)}</div>'
        "</div>"
    )


def render_summary(result: AgentRunResult | None) -> str:
    """Summarize the authority boundary for the completed request."""

    if result is None:
        return '<div class="summary-card">Run a request to see the execution summary.</div>'

    succeeded = sum(item.status == "success" for item in result.tool_results)
    blocked = sum(item.status == "blocked" for item in result.tool_results)
    failed = sum(item.status == "error" for item in result.tool_results)

    return f"""
    <div class="summary-card">
      <strong>Controlled execution summary</strong>
      <div class="summary-grid">
        <div class="metric"><strong>{len(result.tool_calls)}</strong>requested</div>
        <div class="metric"><strong>{succeeded}</strong>executed</div>
        <div class="metric"><strong>{blocked}</strong>blocked</div>
        <div class="metric"><strong>{failed}</strong>failed</div>
      </div>
      <p style="margin-bottom:0;margin-top:12px;">
        A model request is not authority. Every tool call shown above had to pass through
        the application-owned registry and argument checks before an approved capability
        could execute.
      </p>
    </div>
    """
