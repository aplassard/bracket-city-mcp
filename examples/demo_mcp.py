from mcp.server.fastmcp import FastMCP

counter = 0

mcp = FastMCP("Demo")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.tool()
def increment_counter() -> int:
    """Increment a counter and return its new value"""
    global counter
    counter += 1
    return counter


@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


@mcp.resource("counter://value")
def get_counter_value() -> int:
    """Get the current value of the counter"""
    global counter
    return counter
