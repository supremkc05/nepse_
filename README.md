# NEPSE MCP Server

An MCP (Model Context Protocol) server that exposes Nepal Stock Exchange (NEPSE) market data from the unofficial [NepaliPaisa](https://nepalipaisa.com) API to Claude and other LLM clients.

> **Note:** This server uses an unofficial, reverse-engineered API created strictly for studying the Model Context Protocol (MCP). Availability, rate limits, and terms of use are not guaranteed. It is not intended or suitable for providing financial advice or predictions. Use responsibly.

## Features

- **Resource:** `nepse://companies` — full list of NEPSE-listed companies and tickers
- **Tools:**
  - `search_companies` — compact ticker/company lookup without loading the full directory
  - `get_stock_snapshot` — compact live overview for one stock
  - `get_price_history_summary` — derived trend/performance metrics for a date range
  - `compare_stocks` — ranked side-by-side stock comparison by fixed metric
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
| Windows | `%APPDATA%\\Claude\\claude_desktop_config.json` |

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
| Windows | `%APPDATA%\\Claude\\logs\\mcp-server-nepse-market-data.log` |

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

```text
Claude Desktop
    |  stdio
    v
FastMCP Server (src/nepse_mcp/main.py)
    |- tools.py      --> NepseAPIClient (client.py)
    |- resources.py  --> NepseAPIClient (client.py)
    `- prompts.py    --> (static, no HTTP)
                             |
                             v
             https://nepalipaisa.com/api
```

## Recommended Workflow

For lower token usage and more reliable analysis, prefer this order:

1. Use `search_companies` to find the correct ticker.
2. Use `get_stock_snapshot` for a quick live overview.
3. Use `get_price_history_summary` for trend and performance analysis.
4. Use `compare_stocks` when ranking multiple symbols.
5. Use `nepse://companies` or `get_price_history` only when you truly need the full raw payload.

## Compact Tool Reference

### `search_companies`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `query` | string | Yes | — | Exact or partial company name / ticker. |
| `limit` | integer | No | `5` | Maximum matches to return (max 20). |

### `get_stock_snapshot`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `stock_symbol` | string | Yes | — | Ticker (e.g. `NABIL`). |

### `get_price_history_summary`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `stock_symbol` | string | Yes | — | Ticker (e.g. `NABIL`) |
| `from_date` | string | Yes | — | Start date `YYYY-MM-DD` |
| `to_date` | string | Yes | — | End date `YYYY-MM-DD` |

Returns compact derived metrics such as record count, first/last close, absolute return, percentage return, highest close, lowest close, average volume, average turnover, volatility, and trend.

### `compare_stocks`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `stock_symbols` | string[] | Yes | — | Tickers to compare. |
| `metric` | enum | Yes | — | One of `closing_price`, `percent_change`, `volume`, `turnover`, or `30d_return`. |

## Raw Tool Reference

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

Returns the complete list of NEPSE-listed companies and securities with ticker symbols and sector classifications. Read this resource when you need the full directory; prefer `search_companies` when you only need a few likely matches.
