from __future__ import annotations

"""把 MiniGrid 封装成 MCP 工具服务器。"""

from dataclasses import asdict
from typing import Any

from mcp.server.fastmcp import FastMCP

from 游戏接口.minigrid接口 import MiniGridInterface, available_env_ids

mcp = FastMCP(
    name="MiniGrid MCP",
    instructions="提供 MiniGrid 关卡列表、启动游戏、读取状态、执行动作、重置和关闭游戏的工具。",
)

# 这个服务器保持一个“当前游戏实例”，这样客户端可以多次 step 同一局。
_current_game: MiniGridInterface | None = None
_current_state: dict[str, Any] | None = None


def _serialize_state(state: dict[str, Any] | None) -> dict[str, Any]:
    """把内部状态转换成便于 MCP 返回的纯字典。"""
    if state is None:
        return {"has_game": False, "state": None}

    return {
        "has_game": True,
        "state": {
            "env_id": state["env_id"],
            "mission": state["mission"],
            "step_count": state["step_count"],
            "agent_pos": list(state["agent_pos"]),
            "agent_dir": state["agent_dir"],
            "carrying": state["carrying"],
            "width": state["width"],
            "height": state["height"],
            "action_names": state["action_names"],
            "world": [[asdict(cell) for cell in row] for row in state["world"]],
        },
    }



def _require_game() -> MiniGridInterface:
    """确保当前已经启动了一局游戏。"""
    if _current_game is None:
        raise RuntimeError("当前还没有启动游戏，请先调用 start_game。")
    return _current_game


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
    return _serialize_state(_current_state)


@mcp.tool()
def get_state() -> dict[str, Any]:
    """读取当前游戏状态。"""
    return _serialize_state(_current_state)


@mcp.tool()
def step_game(action_name: str) -> dict[str, Any]:
    """执行一步动作，并返回新状态和奖励。"""
    global _current_state

    game = _require_game()
    state, reward, terminated, truncated, info = game.step(action_name)
    _current_state = state
    return {
        "reward": reward,
        "terminated": terminated,
        "truncated": truncated,
        "info": info,
        **_serialize_state(state),
    }


@mcp.tool()
def reset_game(seed: int | None = None) -> dict[str, Any]:
    """重置当前游戏。"""
    global _current_state

    game = _require_game()
    _current_state = game.reset(seed=seed)
    return _serialize_state(_current_state)


@mcp.tool()
def close_game() -> dict[str, Any]:
    """关闭当前游戏实例。"""
    global _current_game, _current_state

    if _current_game is not None:
        _current_game.close()
    _current_game = None
    _current_state = None
    return {"closed": True}


if __name__ == "__main__":
    mcp.run(transport="stdio")