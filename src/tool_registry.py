from typing import Any, Callable, Dict

from src.tools.calculator import calculator
from src.tools.database import search_inventory
from src.tools.external_api import lookup_country


ToolFunction = Callable[..., Dict[str, Any]]


TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "calculator": {
        "function": calculator,
        "description": (
            "Safely evaluate a mathematical expression. "
            "Use this tool for arithmetic and calculations."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": (
                        "A mathematical expression such as "
                        "'125 * 4' or '(100 / 4) + 7'."
                    ),
                }
            },
            "required": ["expression"],
            "additionalProperties": False,
        },
    },

    "search_inventory": {
        "function": search_inventory,
        "description": (
            "Search the local inventory database by item name, "
            "category, or both."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "item_name": {
                    "type": "string",
                    "description": (
                        "Optional item name or partial item name."
                    ),
                },
                "category": {
                    "type": "string",
                    "description": (
                        "Optional exact inventory category such as "
                        "'Electronics', 'Furniture', or "
                        "'Office Supplies'."
                    ),
                },
            },
            "additionalProperties": False,
        },
    },

    "lookup_country": {
        "function": lookup_country,
        "description": (
            "Look up structured information about a country "
            "using the World Bank Countries API."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "country_name": {
                    "type": "string",
                    "description": (
                        "The country name to look up, such as "
                        "'Japan' or 'Canada'."
                    ),
                }
            },
            "required": ["country_name"],
            "additionalProperties": False,
        },
    },
}


def get_tool(name: str) -> ToolFunction:
    """Return an approved tool function by name."""

    if name not in TOOL_REGISTRY:
        raise ValueError(
            f"Tool '{name}' is not registered."
        )

    return TOOL_REGISTRY[name]["function"]


def get_tool_definitions() -> list[Dict[str, Any]]:
    """
    Return tool definitions in OpenAI-compatible function-call format.
    """

    definitions = []

    for name, config in TOOL_REGISTRY.items():
        definitions.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": config["description"],
                    "parameters": config["parameters"],
                },
            }
        )

    return definitions


def list_tools() -> list[str]:
    """Return the names of all approved tools."""

    return sorted(TOOL_REGISTRY.keys())