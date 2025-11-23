"""
Tests for tool database system.
"""

import pytest
from datetime import datetime
from backend.orchestration.tool_database import (
    ToolDatabaseManager,
    Tool,
    ToolExecution
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_tool(db_session, sample_tool_data):
    """Test registering a new tool."""
    manager = ToolDatabaseManager()

    tool = await manager.register_tool(
        name=sample_tool_data["name"],
        description=sample_tool_data["description"],
        category=sample_tool_data["category"],
        parameters=sample_tool_data["parameters"]
    )

    assert tool is not None
    assert tool.name == "test_calculator"
    assert tool.description == "A test calculator tool"
    assert tool.category == "math"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_tool_by_name(db_session, sample_tool_data):
    """Test retrieving a tool by name."""
    manager = ToolDatabaseManager()

    # Register tool first
    await manager.register_tool(
        name=sample_tool_data["name"],
        description=sample_tool_data["description"],
        category=sample_tool_data["category"],
        parameters=sample_tool_data["parameters"]
    )

    # Retrieve tool
    tool = await manager.get_tool_by_name("test_calculator")
    assert tool is not None
    assert tool.name == "test_calculator"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_all_tools(db_session, sample_tool_data):
    """Test retrieving all tools."""
    manager = ToolDatabaseManager()

    # Register multiple tools
    for i in range(5):
        await manager.register_tool(
            name=f"test_tool_{i}",
            description=f"Test tool {i}",
            category="test",
            parameters={}
        )

    # Retrieve all tools
    tools = await manager.get_all_tools()
    assert len(tools) >= 5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_record_tool_execution(db_session, sample_tool_data):
    """Test recording tool execution."""
    manager = ToolDatabaseManager()

    # Register tool first
    tool = await manager.register_tool(
        name=sample_tool_data["name"],
        description=sample_tool_data["description"],
        category=sample_tool_data["category"],
        parameters=sample_tool_data["parameters"]
    )

    # Record execution
    execution = await manager.record_execution(
        tool_id=tool.id,
        agent_id="test_agent",
        input_data={"operation": "add", "a": 5, "b": 3},
        output_data={"result": 8},
        success=True,
        execution_time=0.5
    )

    assert execution is not None
    assert execution.tool_id == tool.id
    assert execution.success is True
    assert execution.execution_time == 0.5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_tool_statistics(db_session, sample_tool_data):
    """Test getting tool usage statistics."""
    manager = ToolDatabaseManager()

    # Register tool
    tool = await manager.register_tool(
        name=sample_tool_data["name"],
        description=sample_tool_data["description"],
        category=sample_tool_data["category"],
        parameters=sample_tool_data["parameters"]
    )

    # Record multiple executions
    for i in range(10):
        await manager.record_execution(
            tool_id=tool.id,
            agent_id=f"agent_{i % 3}",
            input_data={"test": i},
            output_data={"result": i * 2},
            success=i % 5 != 0,  # 20% failure rate
            execution_time=0.1 * (i + 1)
        )

    # Get statistics
    stats = await manager.get_tool_statistics(tool.id)

    assert stats is not None
    assert stats["total_executions"] == 10
    assert stats["success_count"] == 8
    assert stats["failure_count"] == 2
    assert stats["success_rate"] == 0.8


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_tool_metadata(db_session, sample_tool_data):
    """Test updating tool metadata."""
    manager = ToolDatabaseManager()

    # Register tool
    tool = await manager.register_tool(
        name=sample_tool_data["name"],
        description=sample_tool_data["description"],
        category=sample_tool_data["category"],
        parameters=sample_tool_data["parameters"]
    )

    # Update tool
    updated_tool = await manager.update_tool(
        tool_id=tool.id,
        description="Updated description",
        metadata={"version": "2.0"}
    )

    assert updated_tool.description == "Updated description"
    assert updated_tool.metadata["version"] == "2.0"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_tools_by_category(db_session):
    """Test searching tools by category."""
    manager = ToolDatabaseManager()

    # Register tools in different categories
    categories = ["math", "text", "web", "math", "text"]
    for i, category in enumerate(categories):
        await manager.register_tool(
            name=f"tool_{i}",
            description=f"Tool {i}",
            category=category,
            parameters={}
        )

    # Search for math tools
    math_tools = await manager.search_tools(category="math")
    assert len(math_tools) == 2

    # Search for text tools
    text_tools = await manager.search_tools(category="text")
    assert len(text_tools) == 2
