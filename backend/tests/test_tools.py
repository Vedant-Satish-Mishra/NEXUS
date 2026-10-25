"""
Unit Tests for NEXUS Tools and Isolation (Step 4.B.1 & Step 4.D.1)
"""
import pytest
from app.schemas.core import Principal
from app.tools.base import ToolContext
from app.tools.calculator import CalculatorInput, CalculatorTool
from app.tools.file_reader import FileReaderInput, FileReaderTool
from app.tools.local_search import LocalSearchInput, LocalSearchTool
from app.tools.python_tool import PythonInput, PythonTool
from app.tools import executor, TOOLS


@pytest.mark.asyncio
async def test_calculator_valid():
    calc = CalculatorTool()
    ctx = ToolContext(principal=Principal(user_id="u1", conversation_id="c1"), run_id="r1")
    
    res = await calc.run(ctx, CalculatorInput(expression="2 + 3 * 4"))
    assert res.status == "success"
    assert res.output == "14"

    res = await calc.run(ctx, CalculatorInput(expression="sqrt(16) + abs(-5)"))
    assert res.status == "success"
    assert res.output == "9"


@pytest.mark.asyncio
async def test_calculator_security_attacks():
    calc = CalculatorTool()
    ctx = ToolContext(principal=Principal(user_id="u1", conversation_id="c1"), run_id="r1")

    # 1. __import__ attack
    res = await calc.run(ctx, CalculatorInput(expression="__import__('os').system('ls')"))
    assert res.status == "error"

    # 2. Attribute access attack
    res = await calc.run(ctx, CalculatorInput(expression="(1).__class__"))
    assert res.status == "error"

    # 3. Exponent bomb: 9**9**9
    res = await calc.run(ctx, CalculatorInput(expression="9**9**9"))
    assert res.status == "error"
    assert "exceeds safety limits" in res.output or "potential exponent bomb" in res.output

    # 4. Long expression over 200 chars handled gracefully by ToolExecutor
    res = await executor.execute("calculator", {"expression": "1 + " * 100 + "1"}, ctx)
    assert res.status == "error"
    assert "Invalid arguments" in res.output or "validation error" in res.output.lower()


@pytest.mark.asyncio
async def test_tool_executor_unlisted_and_unknown():
    ctx = ToolContext(principal=Principal(user_id="u1", conversation_id="c1"), run_id="r1")

    # Unknown tool
    res = await executor.execute("non_existent_tool", {}, ctx)
    assert res.status == "error"
    assert "not registered" in res.output

    # Disallowed tool
    res = await executor.execute("calculator", {"expression": "1+1"}, ctx, allowed_tools=["file_reader"])
    assert res.status == "error"
    assert "not allowed for this run" in res.output

    # Allowed tool
    res = await executor.execute("calculator", {"expression": "2*8"}, ctx, allowed_tools=["calculator"])
    assert res.status == "success"
    assert res.output == "16"


@pytest.mark.asyncio
async def test_file_reader_isolation(test_db):
    ctx = ToolContext(principal=Principal(user_id="user_alice", conversation_id="c1"), run_id="r1", db=test_db)
    reader = FileReaderTool()

    # Attempt reading file not in database
    res = await reader.run(ctx, FileReaderInput(file_id="non_existent_id"))
    assert res.status == "error"
    assert "not found or access denied" in res.output


@pytest.mark.asyncio
async def test_python_tool_execution():
    py_tool = PythonTool()
    ctx = ToolContext(principal=Principal(user_id="u1", conversation_id="c1"), run_id="r1")

    # Simple execution
    res = await py_tool.run(ctx, PythonInput(code="print('Hello from sandbox')"))
    assert res.status == "success"
    assert "Hello from sandbox" in res.output


@pytest.mark.asyncio
async def test_python_tool_timeout():
    py_tool = PythonTool()
    ctx = ToolContext(principal=Principal(user_id="u1", conversation_id="c1"), run_id="r1")

    # Fast timeout test via custom code
    res = await py_tool.run(ctx, PythonInput(code="import time; time.sleep(12)", timeout_s=1.0))
    assert res.status == "error"
    assert "timed out" in res.output.lower() or "timeout" in res.output.lower()
