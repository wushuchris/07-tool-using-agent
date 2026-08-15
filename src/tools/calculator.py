import ast
import operator
from typing import Any, Dict


_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _evaluate(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants are allowed.")

    if isinstance(node, ast.BinOp):
        operator_type = type(node.op)

        if operator_type not in _ALLOWED_OPERATORS:
            raise ValueError(
                f"Operator {operator_type.__name__} is not allowed."
            )

        left = _evaluate(node.left)
        right = _evaluate(node.right)

        return _ALLOWED_OPERATORS[operator_type](left, right)

    if isinstance(node, ast.UnaryOp):
        operator_type = type(node.op)

        if operator_type not in _ALLOWED_OPERATORS:
            raise ValueError(
                f"Operator {operator_type.__name__} is not allowed."
            )

        value = _evaluate(node.operand)

        return _ALLOWED_OPERATORS[operator_type](value)

    raise ValueError(
        f"Unsupported expression element: {type(node).__name__}"
    )


def calculator(expression: str) -> Dict[str, Any]:
    """
    Safely evaluate a basic mathematical expression.

    Supported operations:
    +, -, *, /, //, %, **, unary +, unary -
    """

    if not isinstance(expression, str):
        raise TypeError("expression must be a string.")

    expression = expression.strip()

    if not expression:
        raise ValueError("expression cannot be empty.")

    if len(expression) > 200:
        raise ValueError("expression is too long.")

    try:
        parsed = ast.parse(expression, mode="eval")
        result = _evaluate(parsed)
    except ZeroDivisionError as exc:
        raise ValueError("Division by zero is not allowed.") from exc
    except SyntaxError as exc:
        raise ValueError("Invalid mathematical expression.") from exc

    return {
        "expression": expression,
        "result": result,
    }