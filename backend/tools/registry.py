from typing import Callable, Dict, Any, Optional
from pydantic import BaseModel, Field
import inspect

class Tool(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any] = {"type": "string"}
    permission: str = "read_only"
    risk_level: str = "low"
    execute_method: Callable[..., Any] = Field(exclude=True)

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> list[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
                "permission": t.permission,
                "risk_level": t.risk_level
            }
            for t in self._tools.values()
        ]

    def execute(self, name: str, args: Dict[str, Any]) -> Any:
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}. Cannot execute unregistered tools.")
        
        tool = self._tools[name]
        try:
            # Simple invocation, assuming arguments match signature
            return tool.execute_method(**args)
        except Exception as e:
            return f"Error executing tool {name}: {str(e)}"

# Global registry instance
registry = ToolRegistry()
