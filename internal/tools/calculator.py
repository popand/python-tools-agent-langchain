from langchain_community.tools import BaseTool
from pydantic import BaseModel, Field
import operator
from typing import Optional, Dict, Any, Literal, ClassVar
import json

class CalculatorInput(BaseModel):
    """Input for Calculator Tool."""
    tool_input: str = Field(description="A JSON string containing operation, a, and b values")

class CalculatorTool(BaseTool):
    name: str = "calculator"
    description: str = """Useful for performing basic mathematical operations.
    The input should be a JSON string with three fields:
    - operation: one of "add", "subtract", "multiply", "divide"
    - a: first number or a nested operation
    - b: second number or a nested operation"""
    
    args_schema: type[CalculatorInput] = CalculatorInput

    operations: ClassVar[Dict[str, Any]] = {
        "add": operator.add,
        "subtract": operator.sub,
        "multiply": operator.mul,
        "divide": operator.truediv
    }

    def _evaluate_operand(self, operand: Any) -> float:
        """Evaluate an operand which could be a number or a nested operation."""
        if isinstance(operand, dict):
            # Handle nested operation
            operation = operand.get("operation")
            a = self._evaluate_operand(operand.get("a"))
            b = self._evaluate_operand(operand.get("b"))
            
            if operation not in self.operations:
                raise ValueError(f"Unknown operation: {operation}")
            
            if operation == "divide" and b == 0:
                raise ValueError("Division by zero")
            
            return self.operations[operation](a, b)
        else:
            # Handle direct number
            return float(operand)

    def _run(self, tool_input: str) -> Dict[str, Any]:
        """Execute the calculator operation."""
        try:
            # Parse the input JSON
            params = json.loads(tool_input)
            operation = params["operation"]
            
            if operation not in self.operations:
                raise ValueError(f"Unknown operation: {operation}")
            
            # Evaluate both operands which could be numbers or nested operations
            a = self._evaluate_operand(params["a"])
            b = self._evaluate_operand(params["b"])
            
            if operation == "divide" and b == 0:
                raise ValueError("Division by zero")
            
            result = self.operations[operation](a, b)
            return {"result": result}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON input"}
        except (KeyError, ValueError) as e:
            return {"error": str(e)}

    async def _arun(self, tool_input: str) -> Dict[str, Any]:
        """Execute the calculator operation asynchronously."""
        return self._run(tool_input) 