"""MiniGrid MCP server entrypoint."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    """Start the MiniGrid MCP server over stdio."""
    module = import_module("游戏接口.minigrid_mcp服务器")
    module.mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
