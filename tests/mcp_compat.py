"""Client-session helper that works on both mcp 1.x and 2.x.

mcp 1.x ships ``create_connected_server_and_client_session``; 2.0 dropped it
and renamed ``FastMCP._mcp_server`` to ``MCPServer._lowlevel_server``.
"""

from contextlib import asynccontextmanager

import anyio
from mcp.client.session import ClientSession
from mcp.shared.memory import create_client_server_memory_streams


def lowlevel_server(mcp):
    """The low-level Server behind a FastMCP (1.x) / MCPServer (2.x) instance."""
    server = getattr(mcp, "_mcp_server", None) or getattr(mcp, "_lowlevel_server", None)
    if server is None:
        raise AttributeError(f"No low-level server on {type(mcp).__name__}")
    return server


@asynccontextmanager
async def connect(mcp):
    """Yield an initialized ClientSession talking to `mcp` over memory streams."""
    try:
        from mcp.shared.memory import create_connected_server_and_client_session
    except ImportError:
        create_connected_server_and_client_session = None

    if create_connected_server_and_client_session is not None:
        async with create_connected_server_and_client_session(lowlevel_server(mcp)) as client:
            yield client
        return

    server = lowlevel_server(mcp)
    async with create_client_server_memory_streams() as (client_streams, server_streams):
        client_read, client_write = client_streams
        server_read, server_write = server_streams
        async with anyio.create_task_group() as tg:
            tg.start_soon(
                lambda: server.run(
                    server_read,
                    server_write,
                    server.create_initialization_options(),
                    raise_exceptions=True,
                )
            )
            async with ClientSession(client_read, client_write) as client:
                await client.initialize()
                yield client
            tg.cancel_scope.cancel()
