# Tool-Using Operations Agent — Structured Tool Router

This project demonstrates a controlled tool-using AI agent in which the language model may propose tool calls, but application code retains authority over:

- which tools exist
- which arguments are permitted
- argument validation
- tool execution
- failure handling
- result normalization
- audit logging

The central architectural principle is:

The model proposes. The application validates and executes.

## Project Summary

This repository presents a practical example of a structured tool router for an operations-oriented agent. Rather than giving the model unrestricted access to Python, shell, SQL, filesystem, or operating-system execution, the system exposes only a small set of approved tools with explicit schemas and controlled validation.

The agent is built with Python, Pydantic, an OpenAI-compatible client for Hugging Face Inference Providers, Gradio, SQLite, and the World Bank Countries API. The application records tool execution metadata in a JSONL audit log while keeping the public interface limited to the current request's tool activity.

## Architecture

```text
User Request
     ↓
LLM / Tool Selection
     ↓
Structured ToolCall
     ↓
Tool Registry / Allowlist
     ↓
Argument Validation
     ↓
Controlled Executor
     ↓
Approved Tool
     ↓
Normalized ToolResult
     ↓
Audit Log
     ↓
Result Returned to LLM
     ↓
Final Answer
```

The LLM never receives arbitrary Python, shell, SQL, filesystem, or operating-system execution capability. All privileged actions are mediated by the application layer before a tool is executed.

## Current Stack

- Python
- Pydantic
- OpenAI-compatible Python client
- Hugging Face Inference Providers
- `openai/gpt-oss-120b:cerebras`
- Gradio
- SQLite
- World Bank Countries API
- pytest

The Hugging Face credential is supplied through the environment variable:

```bash
HF_TOKEN
```

## Approved Tools

### calculator

A constrained deterministic arithmetic tool.

Important security characteristics:

- does not use unrestricted Python `eval()`
- parses expressions through Python AST
- permits only approved mathematical operations

### search_inventory

A constrained SQLite inventory lookup.

Important security characteristics:

- does not expose arbitrary SQL execution
- accepts only approved search parameters
- uses parameterized SQL
- initializes demo inventory data when needed

### lookup_country

Retrieves structured country information using the World Bank Countries API.

Important reliability characteristics:

- controlled HTTP timeout
- HTTP error handling
- response-shape validation
- normalized structured result
- no API key required for the World Bank lookup itself

## Agent Execution Flow

The agent runs in a tool loop. The model may propose a tool call, but the application validates the call and executes it through a controlled executor. Tool results are normalized and returned to the model in a structured form, which allows the model to decide whether additional tool calls are needed before delivering a final answer.

This design keeps the model largely responsible for reasoning and planning while the application remains responsible for trust boundaries and operational control.

## Multi-Tool Behavior

The project supports sequential tool orchestration. A request such as:

```text
How many Electronics items are in inventory, and what is 347 multiplied by that number?
```

can be handled in sequence:

1. the model selects `search_inventory`
2. it receives a count of 3 Electronics records
3. the model selects `calculator`
4. it calculates `347 * 3`
5. it returns `1041`

This is not a hardcoded workflow. The model chooses tools based on the request and the available tool schemas, while the application enforces safety and valid execution.

## Auditability

Every executed tool call is recorded with structured metadata:

- a call ID is assigned
- tool arguments are preserved
- status is recorded as success or error
- output or error is recorded
- start and completion timestamps are recorded
- execution duration is recorded

Audit entries are persisted as JSONL in:

```text
logs/tool_audit.jsonl
```

The public Gradio interface is privacy-conscious in a portfolio/demo sense:

- the complete audit log remains server-side
- the public UI displays only audit records associated with the current request
- historical calls from other visitors are not exposed through the current-run audit view

This is not presented as a multi-tenant security platform; it is a privacy-conscious demo design intended for a single local or deployed app instance.

## Failure Handling

The executor normalizes tool failures into structured results instead of allowing unhandled exceptions to break the agent loop. Examples of handled failure modes include:

- unknown or unregistered tool
- missing required argument
- unexpected argument
- wrong argument type
- division by zero
- external API failure

This keeps the model operating on consistent result objects, even when a tool fails or the dependency is unavailable.

## Repository Structure

```text
07-tool-using-agent/
├── app.py
├── requirements.txt
├── .env.example
├── data/
│   └── .gitkeep
├── logs/
│   └── .gitkeep
├── src/
│   ├── __init__.py
│   ├── agent.py
│   ├── schemas.py
│   ├── tool_registry.py
│   ├── executor.py
│   ├── audit.py
│   └── tools/
│       ├── __init__.py
│       ├── calculator.py
│       ├── database.py
│       └── external_api.py
└── tests/
    ├── __init__.py
    ├── test_tools.py
    └── test_executor.py
```

Runtime-generated artifacts such as `operations.db` and `tool_audit.jsonl` are not presented here as tracked repository files.

## Setup

```bash
git clone https://github.com/wushuchris/07-tool-using-agent.git
cd 07-tool-using-agent

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Create a local `.env` file with:

```bash
HF_TOKEN=your_huggingface_token_here
```

You may also optionally set:

```bash
MODEL_ID=openai/gpt-oss-120b:cerebras
```

Notes:

- `.env` is gitignored
- the real token must never be committed
- the token should be created with only the Hugging Face Inference Provider permissions required to run the model

## Running

```bash
python app.py
```

This starts the Gradio interface for the agent.

## Example Requests

- `What is 347 multiplied by 29?`
- `What electronics are currently in inventory?`
- `What is the capital, region, and income level of Japan?`
- `How many Electronics items are in inventory, and what is 347 multiplied by that number?`

## Testing

```bash
pytest -v
```

The repository currently reports:

**15 automated tests currently pass.**

The test suite covers:

- calculator behavior and restricted execution
- SQLite inventory search
- mocked World Bank response handling
- approved tool execution
- unregistered tool rejection
- missing arguments
- unexpected arguments
- incorrect argument types
- normalized tool failures
- execution timing metadata

The tests do not imply the live LLM provider is called as part of the unit test suite.

## Security and Guardrails

This project is designed around a narrow, explicit trust boundary:

- tool allowlisting
- constrained tool interfaces
- schema-based arguments
- rejection of unknown tools
- no unrestricted `eval`
- no arbitrary SQL
- no shell execution tool
- environment-based secret management
- runtime database and audit logs are gitignored
- public audit display is scoped to the current run

This should be understood as a disciplined portfolio/demo design, not as a production-certified security system.

## Design Lessons

This project demonstrates several engineering lessons:

1. Tool selection and tool execution should be separate concerns.
2. The model should not directly control privileged capabilities.
3. Tool calls should use explicit schemas.
4. Tool failures should become structured data.
5. External dependencies require validation and timeout/error handling.
6. Multi-step requests may require sequential tool calls.
7. Tool activity should be observable and auditable.

## Deployment

The application is designed to be deployable to Hugging Face Spaces with:

```bash
HF_TOKEN
```

configured as a Space secret.


## License

This project is distributed under the repository's existing license terms.
