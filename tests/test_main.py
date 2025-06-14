import pytest
from src.bracket_city_mcp.main import mcp

async def test_add():
    """Test the add tool"""
    assert int((await mcp.call_tool("add", {"a": 1, "b": 2}))[0].text) == 3
    assert int((await mcp.call_tool("add", {"a": -1, "b": 1}))[0].text) == 0
    assert int((await mcp.call_tool("add", {"a": 0, "b": 0}))[0].text) == 0
    assert int((await mcp.call_tool("add", {"a": 100, "b": 200}))[0].text) == 300

async def test_get_greeting():
    """Test the get_greeting resource"""
    assert (await mcp.read_resource("greeting://Jules"))[0].content == "Hello, Jules!"
    assert (await mcp.read_resource("greeting://World"))[0].content == "Hello, World!"

async def test_counter():
    """Test the counter tool and resource"""
    # Check initial value
    assert int((await mcp.read_resource("counter://value"))[0].content) == 0

    # Increment and check tool return value and resource value
    assert int((await mcp.call_tool("increment_counter", {}))[0].text) == 1
    assert int((await mcp.read_resource("counter://value"))[0].content) == 1

    # Increment again and check
    assert int((await mcp.call_tool("increment_counter", {}))[0].text) == 2
    assert int((await mcp.read_resource("counter://value"))[0].content) == 2

    # Increment one more time
    assert int((await mcp.call_tool("increment_counter", {}))[0].text) == 3
    assert int((await mcp.read_resource("counter://value"))[0].content) == 3
