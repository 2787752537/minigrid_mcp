from __future__ import annotations

"""把 MiniGrid 封装成 MCP 工具服务器。"""

from typing import Any

from mcp.server.fastmcp import FastMCP

from 游戏接口.minigrid接口 import MiniGridInterface, available_env_ids, serialize_state
from 游戏接口.共享会话 import SharedSessionBridge

mcp = FastMCP(
    name="MiniGrid MCP",
    instructions="提供 MiniGrid 关卡列表、启动游戏、读取状态、执行动作、重置和关闭游戏的工具。",
)

# 保留原来的“由 MCP 自己启动游戏”的能力。
_current_game: MiniGridInterface | None = None
_current_state: dict[str, Any] | None = None
_bridge = SharedSessionBridge()



def _remote_session_available() -> bool:
    """判断是否存在一个手动启动且可接管的共享游戏会话。"""
    return _bridge.has_live_state()



def _read_remote_state() -> dict[str, Any]:
    """读取手动游戏进程共享出来的状态。"""
    return _bridge.read_state()



def _require_game_mode() -> str:
    """确定当前应该操作本地环境还是手动共享会话。"""
    if _current_game is not None:
        return "local"
    if _remote_session_available():
        return "remote"
    raise RuntimeError("当前没有启动游戏。你可以先手动打开游戏窗口，或者调用 start_game。")


@mcp.tool()
def list_levels() -> dict[str, Any]:
    """返回当前环境里可用的官方 MiniGrid 关卡列表。"""
    levels = available_env_ids()
    return {"count": len(levels), "levels": levels}


@mcp.tool()
def start_game(
    env_id: str = "MiniGrid-Empty-8x8-v0",
    seed: int = 0,
    render_mode: str = "none",
    tile_size: int = 32,
    screen_size: int = 640,
    fully_observable: bool = True,
) -> dict[str, Any]:
    """启动一局新的 MiniGrid 游戏。"""
    global _current_game, _current_state

    if _current_game is not None:
        _current_game.close()

    resolved_render_mode = None if render_mode == "none" else "human"
    _current_game = MiniGridInterface(
        env_id,
        render_mode=resolved_render_mode,
        seed=seed,
        tile_size=tile_size,
        screen_size=screen_size,
        fully_observable=fully_observable,
    )
    _current_state = _current_game.reset(seed=seed)
    return serialize_state(_current_state)


@mcp.tool()
def get_state() -> dict[str, Any]:
    """读取当前游戏状态。优先读手动启动的共享会话，其次读本地托管游戏。"""
    if _remote_session_available():
        return _read_remote_state()
    return serialize_state(_current_state)


@mcp.tool()
def step_game(action_name: str) -> dict[str, Any]:
    """执行一步动作，并返回新状态和奖励。"""
    global _current_state

    mode = _require_game_mode()
    if mode == "remote":
        return _bridge.submit_request({"type": "step", "action_name": action_name})

    state, reward, terminated, truncated, info = _current_game.step(action_name)
    _current_state = state
    return {
        "reward": reward,
        "terminated": terminated,
        "truncated": truncated,
        "info": info,
        **serialize_state(state),
    }


@mcp.tool()
def reset_game(seed: int | None = None) -> dict[str, Any]:
    """重置当前游戏。"""
    global _current_state

    mode = _require_game_mode()
    if mode == "remote":
        return _bridge.submit_request({"type": "reset", "seed": seed})

    _current_state = _current_game.reset(seed=seed)
    return serialize_state(_current_state)


@mcp.tool()
def close_game() -> dict[str, Any]:
    """关闭当前游戏实例。"""
    global _current_game, _current_state

    mode = _require_game_mode()
    if mode == "remote":
        return _bridge.submit_request({"type": "close"})

    if _current_game is not None:
        _current_game.close()
    _current_game = None
    _current_state = None
    return {"closed": True}


if __name__ == "__main__":
    mcp.run(transport="stdio")