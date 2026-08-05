"""Wire-protocol constants and auth shared by client and server.

Stdlib-only - the client must stay importable in environments without the
``mcp`` package (e.g. gis_utils' qgis_bridge connecting from a plain
conda env).
"""

import importlib.metadata
import os
import struct

# ---------------------------------------------------------------------------
# Protocol constants - single source of truth for defaults across all modules
# ---------------------------------------------------------------------------

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876
TIMEOUT_DEFAULT = 30  # seconds - most tool commands
TIMEOUT_LONG = 60  # seconds - execute_processing, render_map, execute_code, batch
RECV_CHUNK_SIZE = 65536  # bytes per recv/recv_into call
MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10 MB - plugin-side buffer/message limit
HEADER_STRUCT = struct.Struct(">I")  # 4-byte big-endian uint32 length prefix

BATCH_BLOCKED_COMMANDS = frozenset(
    {
        "execute_code",
        "remove_layer",
        "delete_features",
        "set_setting",
        "reload_plugin",
        "rollback_edits",
        "execute_connection_sql",
        "import_layer_to_connection",
    }
)


def get_auth_token():
    """Return the shared-secret socket token, or ``None`` when auth is disabled.

    Read from the ``QGIS_MCP_TOKEN`` environment variable. When unset or empty,
    authentication is off and behaviour is unchanged - the plugin accepts any
    command (the historical default). When set, the client attaches it to every
    command and the plugin rejects commands that don't present a matching token.
    """
    token = os.environ.get("QGIS_MCP_TOKEN", "").strip()
    return token or None


# Cap what goes on the wire and into a QGIS message bar: the plugin treats this
# as untrusted input, and no real version string is anywhere near this long.
MAX_VERSION_LENGTH = 32

_client_version = None


def get_client_version():
    """The qgis-mcp version this MCP server reports to the plugin.

    Read from the installed distribution metadata, which is what
    ``enrich_diagnose`` compares against the plugin's ``metadata.txt``. Running
    from a source checkout therefore reports the version recorded when the
    checkout was last installed, not what the working tree currently says - a
    stale record is a real mismatch, and the ``fix`` in the diagnose output says
    how to re-record it.

    Resolved once: it cannot change while the process lives, and this is on the
    path of every single command.
    """
    global _client_version
    if _client_version is None:
        try:
            _client_version = importlib.metadata.version("qgis-mcp")
        except importlib.metadata.PackageNotFoundError:
            _client_version = "unknown"
    return _client_version[:MAX_VERSION_LENGTH]
