import json
from pathlib import Path
from typing import List

from src.schemas import AuditRecord, ToolCall, ToolResult


AUDIT_LOG_PATH = Path("logs/tool_audit.jsonl")


def write_audit_record(
    call: ToolCall,
    result: ToolResult,
) -> AuditRecord:
    """
    Write one tool execution record to the JSONL audit log.
    """

    AUDIT_LOG_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    record = AuditRecord(
        call=call,
        result=result,
    )

    with AUDIT_LOG_PATH.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            record.model_dump_json()
            + "\n"
        )

    return record


def read_audit_records() -> List[AuditRecord]:
    """
    Read all valid audit records from the JSONL log.
    """

    if not AUDIT_LOG_PATH.exists():
        return []

    records: List[AuditRecord] = []

    with AUDIT_LOG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            try:
                payload = json.loads(line)
                records.append(
                    AuditRecord.model_validate(
                        payload
                    )
                )
            except (
                json.JSONDecodeError,
                ValueError,
            ):
                # Ignore malformed lines rather than
                # crashing the whole audit reader.
                continue

    return records


def clear_audit_log() -> None:
    """
    Delete the audit log if it exists.

    Primarily useful for tests and demo resets.
    """

    if AUDIT_LOG_PATH.exists():
        AUDIT_LOG_PATH.unlink()