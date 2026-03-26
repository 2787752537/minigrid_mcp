from __future__ import annotations

"""MiniGrid 的本地代码控制接口。"""

from dataclasses import asdict, dataclass
from typing import Any

import gymnasium as gym
import minigrid
from minigrid.core.actions import Actions
from minigrid.wrappers import FullyObsWrapper

# 这里把字符串动作名统一映射到官方动作枚举，方便人和代码都用同一套名字。
ACTION_NAME_TO_ENUM = {
    "left": Actions.left,
    "right": Actions.right,
    "forward": Actions.forward,
    "pickup": Actions.pickup,
    "drop": Actions.drop,
    "toggle": Actions.toggle,
    "done": Actions.done,
}


@dataclass(slots=True)
class CellInfo:
    """把网格里的单元格信息整理成更容易消费的结构。"""

    x: int
    y: int
    type: str
    color: str | None
    is_open: bool = False
    is_locked: bool = False
    can_overlap: bool = False



def available_env_ids() -> list[str]:
    """读取当前环境里可用的官方 MiniGrid 关卡。"""
    return sorted(
        env_id for env_id in gym.envs.registry.keys() if env_id.startswith("MiniGrid-")
    )



def _world_cells_from_env(env: Any) -> list[list[CellInfo]]:
    """把底层网格对象转成纯 Python 结构，方便序列化和推理。"""
    unwrapped = env.unwrapped
    cells: list[list[CellInfo]] = []
    for y in range(unwrapped.height):
        row: list[CellInfo] = []
        for x in range(unwrapped.width):
            obj = unwrapped.grid.get(x, y)
            if obj is None:
                row.append(CellInfo(x=x, y=y, type="empty", color=None, can_overlap=True))
                continue
            row.append(
                CellInfo(
                    x=x,
                    y=y,
                    type=obj.type,
                    color=getattr(obj, "color", None),
                    is_open=getattr(obj, "is_open", False),
                    is_locked=getattr(obj, "is_locked", False),
                    can_overlap=bool(obj.can_overlap()),
                )
            )
        cells.append(row)
    return cells



def build_state_from_env(
    env: Any,
    env_id: str,
    observation: dict[str, Any] | None = None,
    info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """把当前环境整理成统一状态字典。"""
    observation = observation or {}
    info = info or {}
    unwrapped = env.unwrapped
    carrying = None if unwrapped.carrying is None else unwrapped.carrying.type
    mission = observation.get("mission") or getattr(unwrapped, "mission", "")
    return {
        "env_id": env_id,
        "mission": mission,
        "observation": observation,
        "info": info,
        "step_count": int(unwrapped.step_count),
        "agent_pos": tuple(int(v) for v in unwrapped.agent_pos),
        "agent_dir": int(unwrapped.agent_dir),
        "carrying": carrying,
        "width": int(unwrapped.width),
        "height": int(unwrapped.height),
        "world": _world_cells_from_env(env),
        "action_names": list(ACTION_NAME_TO_ENUM.keys()),
    }



def serialize_state(state: dict[str, Any] | None) -> dict[str, Any]:
    """把内部状态转换成便于 MCP 和跨进程传输的纯字典。"""
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


class MiniGridInterface:
    """通过代码控制官方 MiniGrid 环境的最小接口。"""

    def __init__(
        self,
        env_id: str,
        *,
        render_mode: str | None = "human",
        seed: int | None = None,
        tile_size: int = 32,
        agent_view: bool = False,
        agent_view_size: int = 7,
        screen_size: int = 640,
        fully_observable: bool = True,
    ) -> None:
        self.env_id = env_id
        self.seed = seed

        # 这里直接创建官方环境；是否全图可见由 fully_observable 控制。
        env = gym.make(
            env_id,
            tile_size=tile_size,
            render_mode=render_mode,
            agent_pov=agent_view,
            agent_view_size=agent_view_size,
            screen_size=screen_size,
        )
        if fully_observable:
            env = FullyObsWrapper(env)

        self.env = env
        self.last_state: dict[str, Any] | None = None

    def reset(self, seed: int | None = None) -> dict[str, Any]:
        """重置游戏并返回第一帧状态。"""
        if seed is not None:
            self.seed = seed
        observation, info = self.env.reset(seed=self.seed)
        self.last_state = build_state_from_env(self.env, self.env_id, observation, info)
        return self.last_state

    def step(
        self, action_name: str
    ) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        """执行一步动作，返回新状态、奖励和结束标记。"""
        if action_name not in ACTION_NAME_TO_ENUM:
            raise ValueError(f"不支持的动作: {action_name}")

        observation, reward, terminated, truncated, info = self.env.step(
            ACTION_NAME_TO_ENUM[action_name]
        )
        state = build_state_from_env(self.env, self.env_id, observation, info)
        self.last_state = state
        return state, float(reward), bool(terminated), bool(truncated), info

    def render(self) -> Any:
        """主动触发一次渲染。"""
        return self.env.render()

    def close(self) -> None:
        """关闭环境窗口和底层资源。"""
        self.env.close()

    def action_names(self) -> list[str]:
        """返回当前接口允许发送的动作名。"""
        return list(ACTION_NAME_TO_ENUM.keys())