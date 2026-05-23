# QGIS MCP

Connect [QGIS](https://qgis.org/) to [Claude AI](https://claude.ai/) through the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), enabling Claude to directly control QGIS — manage layers, edit features, run processing algorithms, render maps, and more.

51 MCP tools covering layer management, feature editing, processing, rendering, styling, plugin development, and system management. Compatible with QGIS 3.28–4.x. Works with Claude Code, Codex CLI, Gemini CLI, opencode, Claude Desktop, Cursor, VS Code, Windsurf, Zed, and more.

## Architecture

```
Claude ←→ MCP Server (FastMCP) ←→ TCP socket ←→ QGIS Plugin (QTimer) ←→ PyQGIS API
```

1. **QGIS Plugin** (`qgis_mcp_plugin/`) — Runs inside QGIS. Non-blocking TCP socket server that processes JSON commands within QGIS's event loop.
2. **MCP Server** (`src/qgis_mcp/server.py`) — Runs outside QGIS. Exposes QGIS operations as MCP tools via [FastMCP](https://gofastmcp.com/).

## Installation

No clone needed. Requires QGIS 3.28+ and [uv](https://docs.astral.sh/uv/getting-started/installation/).

### 1. Install the QGIS plugin

In QGIS: `Plugins` > `Manage and Install Plugins` > search **QGIS MCP** > Install.

Restart QGIS and click **Start Server** in the QGIS MCP dock widget.

### 2. Connect your coding agent

**Claude Code**

```bash
claude mcp add -s user qgis -- uvx --from git+https://github.com/nkarasiak/qgis-mcp qgis-mcp-server
```

Scope reference:

| Flag | Stored in | Visible to |
|------|-----------|-----------|
| `-s local` (default) | `.mcp.json` (gitignored) | You, this project |
| `-s project` | `.mcp.json` (committed) | Whole team, this project |
| `-s user` | `~/.claude.json` | You, every project |

**Codex CLI**

```bash
codex mcp add qgis -- uvx --from git+https://github.com/nkarasiak/qgis-mcp qgis-mcp-server
```

Or edit `~/.codex/config.toml` directly:

```toml
[mcp_servers.qgis]
command = "uvx"
args = ["--from", "git+https://github.com/nkarasiak/qgis-mcp", "qgis-mcp-server"]
```

**Gemini CLI** — add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "qgis": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/nkarasiak/qgis-mcp", "qgis-mcp-server"]
    }
  }
}
```

**opencode** — add to `opencode.json` at your project root:

```json
{
  "mcp": {
    "qgis": {
      "type": "local",
      "command": ["uvx", "--from", "git+https://github.com/nkarasiak/qgis-mcp", "qgis-mcp-server"],
      "enabled": true
    }
  }
}
```

**Claude Desktop and other clients** (Cursor, VS Code, Windsurf, …) — use the standard JSON block in your client's MCP config file:

```json
{
  "mcpServers": {
    "qgis": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/nkarasiak/qgis-mcp",
        "qgis-mcp-server"
      ]
    }
  }
}
```

## Usage

1. **Start the plugin** — In QGIS, click the MCP toolbar button (or `Plugins` > `QGIS MCP`) and click "Start Server"
2. **Talk to Claude** — The MCP tools will appear automatically. Ask Claude to work with your QGIS project.

### Example prompt

```
You have access to QGIS tools. Do the following:
1. Ping to check the connection
2. Create a new project and save it at "/tmp/my_project.qgz"
3. Load the vector layer "/data/cities.shp" and name it "Cities"
4. Get field statistics for the "population" field
5. Create a graduated symbology on the "population" field with 5 classes
6. Render the map and show me the result
7. Save the project
```

## Tools (51)

| Category | Tools |
|----------|-------|
| **Project** | `load_project`, `create_new_project`, `save_project`, `get_project_info` |
| **Layers** | `get_layers`, `add_vector_layer`, `add_raster_layer`, `remove_layer`, `find_layer`, `create_memory_layer`, `set_layer_visibility`, `zoom_to_layer`, `get_layer_extent`, `set_layer_property` |
| **Features** | `get_layer_features`, `add_features`, `update_features`, `delete_features`, `select_features`, `get_selection`, `clear_selection`, `get_field_statistics` |
| **Styling** | `set_layer_style` (single, categorized, graduated) |
| **Rendering** | `render_map`, `get_canvas_screenshot`, `get_canvas_extent`, `set_canvas_extent` |
| **Processing** | `execute_processing`, `list_processing_algorithms`, `get_algorithm_help` |
| **Layouts** | `list_layouts`, `export_layout` |
| **Layer tree** | `get_layer_tree`, `create_layer_group`, `move_layer_to_group` |
| **Plugins** | `list_plugins`, `get_plugin_info`, `reload_plugin` |
| **System** | `ping`, `diagnose`, `get_qgis_info`, `get_raster_info`, `get_message_log`, `execute_code`, `batch_commands`, `validate_expression`, `get_project_variables`, `set_project_variable`, `get_setting`, `set_setting`, `transform_coordinates` |

All tools are async with human-readable titles and annotations (`readOnly`, `destructive`, `idempotent`). Destructive tools ask for confirmation via MCP elicitation when supported; clients without elicitation proceed normally (fail-open) since tools are already gated by `ToolAnnotations`. Long-running tools report progress via MCP logging.

### Compound tool mode

Set `QGIS_MCP_TOOL_MODE=compound` to reduce the 51 granular tools to ~19 grouped tools, cutting schema overhead per LLM turn. Each compound tool takes an `action` parameter:

```bash
QGIS_MCP_TOOL_MODE=compound uv run --no-sync src/qgis_mcp/server.py
```

Groups: `system`, `project`, `layer`, `features`, `selection`, `style`, `canvas`, `render`, `processing`, `code`, `batch`, `layer_tree`, `plugins`, `variables`, `settings`, `expression`, `transform`, `message_log`, `layer_property`.

## Configuration

| Environment variable | Default | Description |
|---------------------|---------|-------------|
| `QGIS_MCP_HOST` | `localhost` | Host for socket connection |
| `QGIS_MCP_PORT` | `9876` | Port for socket connection |
| `QGIS_MCP_TRANSPORT` | `stdio` | MCP transport: `stdio` or `streamable-http` |
| `QGIS_MCP_LOG_FILE` | `~/.local/share/qgis-mcp/server.log` | Log file path (empty to disable) |
| `QGIS_MCP_LOG_LEVEL` | `INFO` | File log level |
| `QGIS_MCP_TOOL_MODE` | `granular` | `granular` (51 tools) or `compound` (~19 grouped) |

## Contributing

```bash
git clone https://github.com/nkarasiak/qgis-mcp.git
cd qgis-mcp
python install.py   # symlinks plugin + configures your MCP client
```

`install.py` options: `--clients claude-desktop,cursor`, `--remote` (uvx instead of uv run), `--profile myprofile`, `--uninstall`.

```bash
# Unit tests (no QGIS needed — mocked socket)
uv run --no-sync pytest tests/test_mcp_tools.py -v

# Integration tests (requires QGIS plugin running)
uv run --no-sync pytest tests/test_qgis_live.py -v
```

## License

This project is licensed under the GNU GPL v2 or later.
