# NEPSE MCP Server

An MCP (Model Context Protocol) server that exposes Nepal Stock Exchange (NEPSE) market data from the unofficial [NepaliPaisa](https://nepalipaisa.com) API to Claude and other LLM clients.

> **Note:**This server uses an unofficial, reverse-engineered API created strictly for studying the Model Context Protocol (MCP). Availability, rate limits, and terms of use are not guaranteed. It is not intended or suitable for providing financial advice or predictions. Use responsi.

## Features

- **Resource:** `nepse://companies` — full list of NEPSE-listed companies and tickers
- **Tools:**
  - `get_live_market_data` — live trading data for one or all stocks
  - `get_price_history` — daily OHLC price history with date range and pagination
  - `get_dividend_history` — bonus share and cash dividend history
  - `get_top_market_movers` — ranked market leaders by gainers, turnover, or volume
- **Prompt:** `analyze_nepse_stock` — guided multi-step stock analysis

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Installation

```bash
git clone <repo>
cd Nepse_Mcp
uv sync
```

Copy the environment template and edit if needed (defaults work out of the box):

```bash
cp .env.example .env
```

## Running the Server

```bash
uv run nepse-mcp
```

## Claude Desktop Integration

Add the following entry to your Claude Desktop config file:

| Platform | Config path |
|---|---|
| Linux | `~/.config/Claude/claude_desktop_config.json` |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

```json
{
  "mcpServers": {
    "nepse-market-data": {
      "command": "/home/ajay/.local/bin/uv",
      "args": [
        "run",
        "--with",
        "fastmcp",
        "--with-editable",
        "/absolute/path/to/Nepse_Mcp",
        "fastmcp",
        "run",
        "/absolute/path/to/Nepse_Mcp/src/nepse_mcp/main.py"
      ]
    }
  }
}
```

Replace `/absolute/path/to/Nepse_Mcp` with the actual path on your machine. Use `which uv` to confirm the correct path to the `uv` binary for the `command` field.

### Applying config changes

Claude Desktop does not hot-reload its MCP config. After editing `claude_desktop_config.json` you need to fully restart the app. On Linux/macOS you can do this from the terminal:

```bash
# Kill all Claude Desktop processes, then relaunch the app normally
pkill -f "claude" && echo "Killed" || echo "No Claude process found"
```

On Windows, close Claude Desktop from the system tray before reopening it.

### Troubleshooting MCP connection issues

If the server shows as disconnected in Claude Desktop, check the MCP log file:

| Platform | Log path |
|---|---|
| Linux | `~/.config/Claude/logs/mcp-server-nepse-market-data.log` |
| macOS | `~/Library/Logs/Claude/mcp-server-nepse-market-data.log` |
| Windows | `%APPDATA%\Claude\logs\mcp-server-nepse-market-data.log` |

Common causes:
- **Wrong `uv` path** — run `which uv` and update the `command` field accordingly.
- **Environment variable conflict** — `uv` reserves `HTTP_TIMEOUT` for its own use. This project uses `NEPSE_HTTP_TIMEOUT` to avoid the collision.
- **Server not starting** — run the exact command from the config manually in a terminal to see the raw error output.

## Development

Run the test suite:

```bash
uv run pytest
```

Run with verbose output:

```bash
uv run pytest -v
```

## Architecture

```
Claude Desktop
    │  stdio
    ▼
FastMCP Server (src/nepse_mcp/main.py)
    ├── tools.py      ──► NepseAPIClient (client.py)
    ├── resources.py  ──► NepseAPIClient (client.py)
    └── prompts.py    ──► (static, no HTTP)
                              │
                              ▼
              https://nepalipaisa.com/api
```

## Tool Reference

### `get_live_market_data`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `stock_symbol` | string | No | `""` | Ticker (e.g. `NABIL`). Empty string returns all stocks and a market summary. |

### `get_price_history`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `stock_symbol` | string | Yes | — | Ticker (e.g. `NABIL`) |
| `from_date` | string | Yes | — | Start date `YYYY-MM-DD` |
| `to_date` | string | Yes | — | End date `YYYY-MM-DD` |
| `limit` | integer | No | `20` | Records per page (max 100) |
| `page_no` | integer | No | `1` | Page number; increment when `has_more_data` is `true` |

### `get_dividend_history`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `stock_symbol` | string | Yes | — | Ticker (e.g. `NABIL`) |
| `fiscal_year_id` | integer | No | `0` | `0` = all fiscal years |
| `limit` | integer | No | `20` | Records per page (max 100) |
| `page_no` | integer | No | `1` | Page number; increment when `has_more_data` is `true` |

### `get_top_market_movers`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `indicator` | enum | Yes | — | `gainers`, `turnover`, or `sharestraded` |
| `sector_code` | string | No | `""` | Sector filter (empty = all sectors) |
| `limit` | integer | No | `20` | Max results (max 100) |

## Resource Reference

### `nepse://companies`

Returns the complete list of NEPSE-listed companies and securities with ticker symbols and sector classifications. Read this resource first to find the correct `stock_symbol` for a company before calling any tool.
