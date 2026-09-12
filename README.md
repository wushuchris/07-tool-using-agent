---
title: Governed Tool-Using Agent
emoji: 🛠️
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.50.0
app_file: app.py
pinned: false
license: mit
---

# 07. Governed Tool-Using Agent — Application-Controlled Capability Boundary

A business-facing demonstration of how an LLM can use approved capabilities without being given unrestricted access to code execution, databases, filesystems, or arbitrary network resources.

**Live Demo:** https://huggingface.co/spaces/FlyingNunchucks/07-tool-using-agent

The core pattern is:

> **The model proposes. Application code owns authorization, validation, execution, and auditability.**

## Why This Project Matters

Tool use is often described as function calling: the model decides it needs a function, calls it, receives a result, and continues reasoning.

That description hides the most important production question:

> **How do you let an AI use business systems without giving the model unrestricted authority over those systems?**

This project answers that with an explicit application-owned capability boundary. The model may decide that a tool is useful, but every requested action must pass through a controlled registry, schema validation, authorization, normalized execution, and audit logging before an approved capability can run.

## Business Scenario

The public demo presents a fictional operations copilot that may need three different classes of capability:

- deterministic local computation;
- controlled access to an internal inventory database;
- controlled access to an approved external reference API.

A representative request is:

```text
We may ship equipment to Japan. Find the Electronics items currently in
inventory, calculate an accessory budget of $347 per matching item, and
give me Japan's capital, region, and income classification.
```

The request is intentionally multi-tool. The workflow is not hardcoded: the model chooses which approved tools to request and when, while application code decides what is actually allowed to execute.

## Who Controls What?

| Model controls | Application code controls |
| --- | --- |
| Whether a tool appears necessary | Which tools exist at all |
| Which approved tool to request | Whether arguments match the approved schema |
| How to combine returned results | Whether execution is authorized |
| When enough information exists to answer | Tool execution |
| Final natural-language explanation | Failure normalization and audit logging |

This separation is the central engineering lesson of Agent 7.

## Approved Tool Belt

### `calculator`

A constrained deterministic arithmetic capability.

**Allowed:** approved arithmetic expressions.  
**Not allowed:** arbitrary Python or unrestricted `eval()`.

The implementation parses expressions through Python AST and permits only approved mathematical operations.

### `search_inventory`

A narrow SQLite inventory query interface.

**Allowed:** item/category inventory search.  
**Not allowed:** arbitrary SQL, writes, schema changes, or database administration.

The tool uses explicit parameters and parameterized SQL.

### `lookup_country`

A structured World Bank country-information lookup.

**Allowed:** approved country lookup through the intended endpoint.  
**Not allowed:** arbitrary URLs, open-ended browsing, or unrestricted network access.

The tool includes timeouts, HTTP error handling, response-shape checks, and normalized structured output.

## Architecture

```text
User request
    ↓
LLM decides whether it needs a capability
    ↓
Structured ToolCall
    ↓
Application authorization boundary
    ├─ blocked
    │    ↓
    │ normalized blocked ToolResult + audit record
    │
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

The model never receives unrestricted shell, Python, filesystem, SQL, or arbitrary network execution.

## Authorization and Failure Semantics

The retrofit made an important distinction explicit: **a rejected request and a failed authorized tool are not the same event.**

### Blocked before execution

The application refuses the request before the underlying capability runs. Examples include:

- unregistered tool name;
- missing required argument;
- unexpected argument;
- wrong argument type;
- arguments that violate the approved schema.

These outcomes are represented as structured `blocked` results.

### Approved but execution failed

The request crossed the authorization boundary successfully, but the approved capability itself encountered a runtime or dependency error. Examples include:

- division by zero;
- external API failure;
- other runtime exceptions inside an approved tool.

These outcomes are represented as structured `error` results.

### Successful execution

The tool was registered, its arguments passed validation, execution was authorized, and the capability returned a normalized result.

These outcomes are represented as `success`.

That three-way distinction makes the audit trail much more useful:

```text
blocked  = application refused authority
error    = authority was granted, execution failed
success  = authority was granted, execution succeeded
```

## Real Execution Observability

The original version returned the final answer, raw tool calls, raw results, and audit JSON only after the run completed.

The upgraded agent adds `run_agent_iter()` so the live UI can observe the real model/application interaction as it happens.

The existing `run_agent()` API remains intact and consumes the same generator path, so the demo does not use a second fake orchestration implementation.

The UI can expose real events such as:

```text
Request accepted
AI deciding
Model requested: search_inventory
Application approved
Tool completed
AI deciding
Model requested: calculator
Application approved
Tool completed
AI deciding
Final response
```

If an invalid capability is requested, the application can instead expose:

```text
Model requested
Application blocked
```

The generic Gradio progress indicator is hidden so the system's own authorization and execution events remain the primary run experience.

## Business-First Demo Presentation

The approved September 2026 presentation reframes the project from a generic function-calling demo into a **governed AI capability demo**.

The live Space now includes:

- a centered 1080px reading path;
- the business problem before implementation details;
- an approved tool belt showing both allowed and disallowed capability boundaries;
- an explicit **Model controls / Application controls** comparison;
- a flagship multi-tool operations request;
- **Live Controlled Execution** driven by real `run_agent_iter()` events;
- a business-facing result and controlled-execution summary;
- raw structured calls, results, and current-run audit records under **Engineering Audit**;
- dedicated **Security & Failure Semantics** and **Architecture** views.

The presentation principle is:

> **Business story first. Engineering evidence second. Make the trust boundary visible while the agent works.**

## Auditability

Every requested tool execution is associated with a structured call ID and normalized result. Audit records capture:

- tool name;
- structured arguments;
- result status;
- output or normalized error;
- start and completion timestamps;
- execution duration.

The audit log is persisted as JSONL in:

```text
logs/tool_audit.jsonl
```

The public interface displays only audit records associated with the current run. Historical records from other visitors are not exposed through the current-run view.

This is a privacy-conscious portfolio/demo design, not a production-certified multi-tenant security boundary.

## Multi-Tool Behavior

A model can request several approved capabilities over multiple rounds. Tool results are returned to the model as structured messages, allowing it to determine whether another tool is required before producing a final answer.

The maximum number of tool rounds is bounded, preventing an uncontrolled loop from running indefinitely.

This design keeps model reasoning flexible while keeping capability authority deterministic and application-owned.

## Testing

Run locally with:

```bash
python -m pytest -q
```

Final approved retrofit result:

```text
23 passed in 2.92s
```

The suite covers:

- calculator restrictions and deterministic arithmetic;
- SQLite inventory search;
- mocked external country lookup behavior;
- approved tool execution;
- unregistered-tool blocking;
- missing, unexpected, and incorrectly typed argument blocking;
- explicit authorization results;
- separation of `blocked` from execution `error`;
- normalized runtime failures;
- timing metadata;
- deterministic `run_agent_iter()` event sequencing;
- preservation of the original `run_agent()` behavior;
- business-first presentation framing;
- 1080px centered layout;
- visible intermediate model-request / application-approval / tool-completion events before the final answer.

The deterministic CI suite does not require a live model-provider call.

## CI/CD

The project was also upgraded to the current portfolio deployment standard.

```text
push to main
    ↓
GitHub Actions installs dependencies
    ↓
pytest
    ↓
only if tests pass
    ↓
GitHub → Hugging Face sync
    ↓
Space rebuild
```

The previous workflow synced directly to Hugging Face without a test gate. The final version deploys only after the automated suite passes.

GitHub remains the source of truth.

## Security and Public-Demo Boundaries

The project intentionally keeps the capability surface narrow:

- explicit tool registry / allowlist;
- schema-based arguments;
- application-owned authorization;
- no unrestricted `eval()`;
- no arbitrary SQL;
- no shell tool;
- no filesystem tool;
- no arbitrary-network tool;
- bounded tool rounds;
- normalized failures;
- current-run audit scoping;
- environment-based secret management;
- runtime database and audit files excluded from source control.

Runtime inference uses `HF_TOKEN` in the Hugging Face Space. Deployment uses the separate GitHub repository secret `HF_DEPLOY_TOKEN`.

The public demo uses synthetic inventory data and should not be used for confidential, client, financial, personal, or proprietary information.

## Repository Structure

```text
.
├── app.py
├── requirements.txt
├── .env.example
├── data/
├── logs/
├── src/
│   ├── agent.py
│   ├── audit.py
│   ├── demo_presentation.py
│   ├── executor.py
│   ├── schemas.py
│   ├── tool_registry.py
│   └── tools/
│       ├── calculator.py
│       ├── database.py
│       └── external_api.py
└── tests/
    ├── test_agent.py
    ├── test_app.py
    ├── test_executor.py
    └── test_tools.py
```

## Local Setup

```bash
git clone https://github.com/wushuchris/07-tool-using-agent.git
cd 07-tool-using-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a local `.env` containing your own inference credential:

```bash
HF_TOKEN=your_huggingface_token_here
```

Optionally set:

```bash
MODEL_ID=openai/gpt-oss-120b:cerebras
```

Then run:

```bash
python app.py
```

## Production Upgrade Path

A production system could extend this primitive with:

- per-tool identity and authorization policy;
- user- or role-specific capability scopes;
- approval workflows for high-impact tools;
- stronger JSON Schema validation;
- idempotency keys for side-effecting tools;
- retry / circuit-breaker policy by tool;
- rate limits and budgets;
- secret brokering instead of direct credential exposure;
- persistent centralized audit storage;
- policy decision telemetry;
- sandboxing for selected execution classes;
- stronger tool-result provenance and downstream verification.

## Reusable Agent Primitive

The reusable primitive demonstrated here is an **application-owned capability boundary**:

```text
Governed tool use
= model-selected intent
+ explicit capability registry
+ typed arguments
+ authorization
+ controlled execution
+ normalized outcomes
+ bounded loops
+ auditability
```

The important idea is not that the LLM can call functions.

It is that the LLM **cannot grant itself authority**.

## Design Lessons

1. Function calling is a model interface; authorization is an application responsibility.
2. Tool selection and tool execution should remain separate concerns.
3. A model request is not permission to execute.
4. Blocked requests should be distinguishable from authorized execution failures.
5. Explicit schemas and allowlists create inspectable trust boundaries.
6. Tool failures should become normalized data rather than uncontrolled exceptions.
7. Multi-tool reasoning can remain flexible while execution authority remains deterministic.
8. Auditability should be tied to actual capability calls, not inferred afterward.
9. The strongest demo makes the model/application authority boundary visible while the system is running.

## License

MIT License.
