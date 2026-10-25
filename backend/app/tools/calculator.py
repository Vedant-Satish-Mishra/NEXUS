"""
NEXUS Safe Calculator Tool
Uses AST-based evaluation with strict node allowlisting to prevent code execution.
Guards against large exponents (9**9**9), attribute traversal, and dangerous names.
"""
import ast
import math
import operator
from typing import Any, Dict
from pydantic import BaseModel, Field

from app.tools.base import Tool, ToolContext, ToolResult


class CalculatorInput(BaseModel):
    expression: str = Field(..., max_length=200, description="Mathematical expression to evaluate")


SAFE_NAMES: Dict[str, Any] = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
    "pi": math.pi,
    "e": math.e,
}

BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class CalculatorTool:
    name: str = "calculator"
    description: str = (
        "Calculates safe mathematical expressions (+, -, *, /, //, %, **, sqrt, round, min, max, log, etc.)."
    )
    input_model = CalculatorInput
    requires_approval: bool = False
    timeout_s: float = 3.0

    async def run(self, ctx: ToolContext, args: CalculatorInput) -> ToolResult:
        expr = args.expression.strip()
        if len(expr) > 200:
            return ToolResult(
                status="error",
                output="Expression exceeds 200 character limit.",
                message="Expression too long",
            )

        try:
            parsed = ast.parse(expr, mode="eval")
            result = self._eval_node(parsed.body)
            # Format nicely
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return ToolResult(status="success", output=str(result))
        except (ValueError, TypeError, ZeroDivisionError, OverflowError) as math_err:
            return ToolResult(status="error", output=f"Calculation error: {str(math_err)}", message="Math error")
        except Exception as e:
            return ToolResult(status="error", output=f"Evaluation failed: {str(e)}", message="Evaluation failed")

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Literal '{node.value}' is not a number")

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in BINARY_OPS:
                raise ValueError(f"Unsupported binary operator: {op_type.__name__}")

            left = self._eval_node(node.left)
            right = self._eval_node(node.right)

            if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
                raise ValueError("Binary operands must be numeric")

            # Guard against exponent explosion like 9**9**9 or large powers
            if op_type == ast.Pow:
                if abs(right) > 500 or (abs(left) > 1000 and abs(right) > 20):
                    raise OverflowError("Exponentiation exceeds safety limits (potential exponent bomb)")

            op_fn = BINARY_OPS[op_type]
            res = op_fn(left, right)
            if isinstance(res, (int, float)) and abs(res) > 1e100:
                raise OverflowError("Result magnitude exceeds safety limits")
            return res

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in UNARY_OPS:
                raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
            operand = self._eval_node(node.operand)
            if not isinstance(operand, (int, float)):
                raise ValueError("Unary operand must be numeric")
            return UNARY_OPS[op_type](operand)

        if isinstance(node, ast.Name):
            if node.id in SAFE_NAMES:
                val = SAFE_NAMES[node.id]
                if isinstance(val, (int, float)):
                    return val
                return val
            raise ValueError(f"Forbidden name or identifier: '{node.id}'")

        if isinstance(node, ast.Call):
            func = self._eval_node(node.func)
            if not callable(func):
                raise ValueError("Target is not a callable function")
            args = [self._eval_node(arg) for arg in node.args]
            for a in args:
                if not isinstance(a, (int, float)):
                    raise ValueError("Function arguments must be numeric")
            res = func(*args)
            if isinstance(res, (int, float)) and abs(res) > 1e100:
                raise OverflowError("Result magnitude exceeds safety limits")
            return res

        raise ValueError(f"Unsupported AST syntax node: {type(node).__name__}")
