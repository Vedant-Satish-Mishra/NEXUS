"""
NEXUS Tool Registry
Exposes registered tools and default ToolExecutor instance.
"""
from app.tools.base import Tool, ToolContext, ToolExecutor, ToolResult
from app.tools.calculator import CalculatorTool
from app.tools.file_reader import FileReaderTool
from app.tools.local_search import LocalSearchTool
from app.tools.python_tool import PythonTool
from app.tools.web_search import WebSearchTool

# Global default executor
executor = ToolExecutor()

# Register core tools
calculator_tool = CalculatorTool()
file_reader_tool = FileReaderTool()
local_search_tool = LocalSearchTool()
python_tool = PythonTool()
web_search_tool = WebSearchTool()

executor.register(calculator_tool)
executor.register(file_reader_tool)
executor.register(local_search_tool)
executor.register(python_tool)
executor.register(web_search_tool)

TOOLS = {
    "calculator": calculator_tool,
    "file_reader": file_reader_tool,
    "local_search": local_search_tool,
    "python": python_tool,
    "web_search": web_search_tool,
}

__all__ = [
    "Tool",
    "ToolContext",
    "ToolExecutor",
    "ToolResult",
    "executor",
    "TOOLS",
    "CalculatorTool",
    "FileReaderTool",
    "LocalSearchTool",
    "PythonTool",
    "WebSearchTool",
]
