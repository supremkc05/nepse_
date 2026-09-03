# NEPSE MCP Server

An MCP (Model Context Protocol) server that exposes Nepal Stock Exchange (NEPSE) market data from the unofficial [NepaliPaisa](https://nepalipaisa.com) API to Claude and other LLM clients.

> **Note:** This server uses an unofficial, reverse-engineered API. Availability, rate limits, and terms of use are not guaranteed. Use responsibly.

## Features

- **Resource:** `nepse://companies` — full list of NEPSE-listed companies and tickers
- **Tools:**
  - `get_live_market_data` — live trading data for one or all stocks
  - `get_price_history` — daily OHLC price history with date range and pagination
  - `get_dividend_history` — bonus share and cash dividend history
  - `get_top_market_movers` — ranked market leaders by gainers, turnover, or volume
- **Prompt:** `analyze_nepse_stock` — guided multi-step stock analysis

## Installation

Requires Python 3.12+ and [uv](https://github.com/astral-sh/uv).

```bash
git clone <repo>
cd Nepse_Mcp
uv sync
```

Copy the environment template:

```bash
cp .env.example .env
```

Edit `.env` if you need to override defaults (the defaults work out of the box).

## Running the Server

```bash
uv run nepse-mcp
```

## Claude Desktop Integration

Add the following to your Claude Desktop config:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "nepse": {
      "command": "uv",
      "args": [
       "--dire ctory",
        "/absolute/path/to/Nepse_Mcp",
        "run",
        "nepse-mcp"
      ]
    }
  }
}
```

Replace `/absolute/path/to/Nepse_Mcp` with the actual absolute path to this project on your machine.

Replace  command : "uv" with  the output  form the which uv 

## Development

Run tests:

```bash
uv run pytest
```

Run tests with verbose output:

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
| `stock_symbol` | string | No | `""` | Ticker (e.g. `NABIL`). Empty returns all stocks + market summary. |

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
Returns the complete list of NEPSE-listed companies and securities with ticker symbols and sector classifications. Read this resource first to find the correct `stockSymbol` for a company before calling any tool.
