from __future__ import annotations

"""MiniGrid 图形化手动游玩入口。"""

import argparse
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import gymnasium as gym
import pygame
from minigrid.core.actions import Actions
from minigrid.manual_control import ManualControl
from minigrid.wrappers import FullyObsWrapper

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from 游戏接口.minigrid接口 import ACTION_NAME_TO_ENUM, available_env_ids, build_state_from_env, serialize_state
from 游戏接口.共享会话 import SharedSessionBridge

# 这里写清楚官方 MiniGrid 手动控制的按键，方便以后查阅。
CONTROL_TEXT = (
    "操作按键: ↑ 前进 | ← 左转 | → 右转 | Space 交互/开门 | "
    "PageUp/Tab 拾取 | PageDown/Left Shift 放下 | Enter done | "
    "Backspace 重开 | Esc 退出"
)


class SharedManualControl(ManualControl):
    """在保留手动按键控制的同时，把状态共享给 MCP。"""

    def __init__(self, env, env_id: str, seed: int | None) -> None:
        super().__init__(env, seed=seed)
        self.env_id = env_id
        self.bridge = SharedSessionBridge()
        self.last_state = None

    def start(self):
        """启动带共享能力的阻塞循环。"""
        self.bridge.prepare_host()
        self.reset(self.seed)
        print(f"MCP 共享会话已开启: {self.bridge.root}")

        while not self.closed:
            self._process_remote_requests()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.closed = True
                    break
                if event.type == pygame.KEYDOWN:
                    event.key = pygame.key.name(int(event.key))
                    self.key_handler(event)
            pygame.time.wait(30)

        self.bridge.clear_state()
        self.env.close()

    def step(self, action: Actions):
        """处理一步动作，并把结果同步给 MCP。"""
        observation, reward, terminated, truncated, info = self.env.step(action)
        self.last_state = build_state_from_env(self.env, self.env_id, observation, info)
        self.bridge.write_state(serialize_state(self.last_state))
        print(f"step={self.env.unwrapped.step_count}, reward={reward:.2f}")

        if terminated:
            print("通关了")
            messagebox.showinfo("MiniGrid", "通关了")
        elif truncated:
            print("本局结束")
            messagebox.showinfo("MiniGrid", "本局结束")
        else:
            self.env.render()
        return {
            "reward": float(reward),
            "terminated": bool(terminated),
            "truncated": bool(truncated),
            "info": info,
            **serialize_state(self.last_state),
        }

    def reset(self, seed=None):
        """重置并同步初始状态。"""
        observation, info = self.env.reset(seed=seed)
        self.last_state = build_state_from_env(self.env, self.env_id, observation, info)
        self.bridge.write_state(serialize_state(self.last_state))
        self.env.render()
        return serialize_state(self.last_state)

    def key_handler(self, event):
        """复用官方按键映射。"""
        key: str = event.key
        print("pressed", key)

        if key == "escape":
            self.closed = True
            return
        if key == "backspace":
            self.reset(self.seed)
            return

        key_to_action = {
            "left": Actions.left,
            "right": Actions.right,
            "up": Actions.forward,
            "space": Actions.toggle,
            "pageup": Actions.pickup,
            "pagedown": Actions.drop,
            "tab": Actions.pickup,
            "left shift": Actions.drop,
            "enter": Actions.done,
        }
        if key in key_to_action:
            self.step(key_to_action[key])

    def _process_remote_requests(self) -> None:
        """处理 MCP 侧排队发来的请求。"""
        for pending in self.bridge.poll_requests():
            payload = pending.payload
            request_type = payload.get("type")
            try:
                if request_type == "step":
                    action_name = payload["action_name"]
                    action = ACTION_NAME_TO_ENUM[action_name]
                    response = self.step(action)
                elif request_type == "reset":
                    response = self.reset(payload.get("seed"))
                elif request_type == "close":
                    self.closed = True
                    self.bridge.clear_state()
                    response = {"closed": True}
                else:
                    response = {"error": f"未知请求类型: {request_type}"}
            except Exception as exc:
                response = {"error": str(exc)}
            self.bridge.write_response(pending.request_id, response)



def launch_manual_control(
    env_id: str,
    seed: int | None,
    tile_size: int,
    agent_view: bool,
    agent_view_size: int,
    screen_size: int,
    fully_observable: bool,
) -> None:
    """启动可与 MCP 共享的手动游戏窗口。"""
    env = gym.make(
        env_id,
        tile_size=tile_size,
        render_mode="human",
        agent_pov=agent_view,
        agent_view_size=agent_view_size,
        screen_size=screen_size,
    )
    if fully_observable:
        env = FullyObsWrapper(env)

    print(CONTROL_TEXT)
    print("提示: 现在你可以手动操作，同时也可以让 MCP 中途接管。")
    manual_control = SharedManualControl(env, env_id=env_id, seed=seed)
    manual_control.start()



def choose_level_gui(
    env_ids: list[str],
    seed: int | None,
    tile_size: int,
    agent_view: bool,
    agent_view_size: int,
    screen_size: int,
    fully_observable: bool,
) -> None:
    """显示关卡选择窗口。"""
    root = tk.Tk()
    root.title("MiniGrid 关卡选择")
    root.geometry("760x560")

    selected_env = tk.StringVar(value="MiniGrid-Empty-8x8-v0")
    filter_text = tk.StringVar()
    status_text = tk.StringVar(value=f"官方 MiniGrid 关卡数: {len(env_ids)}")

    frame = ttk.Frame(root, padding=16)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="MiniGrid 官方关卡选择").pack(anchor="w")
    ttk.Label(frame, textvariable=status_text).pack(anchor="w", pady=(4, 8))
    ttk.Label(frame, text=CONTROL_TEXT, wraplength=700).pack(anchor="w", pady=(0, 12))
    ttk.Label(frame, text="MCP 可在游戏运行中途接入控制。", wraplength=700).pack(anchor="w", pady=(0, 12))

    ttk.Label(frame, text="搜索关卡").pack(anchor="w")
    search_entry = ttk.Entry(frame, textvariable=filter_text)
    search_entry.pack(fill="x", pady=(0, 12))

    listbox = tk.Listbox(frame, height=18, exportselection=False)
    listbox.pack(fill="both", expand=True)

    def populate_list(query: str = "") -> None:
        """按关键字过滤关卡，并尽量保持原来的选中项。"""
        query_lower = query.lower().strip()
        filtered = [env_id for env_id in env_ids if query_lower in env_id.lower()] or env_ids
        listbox.delete(0, tk.END)
        for item in filtered:
            listbox.insert(tk.END, item)

        current_value = selected_env.get()
        try:
            index = filtered.index(current_value)
        except ValueError:
            index = 0
            selected_env.set(filtered[0])

        listbox.selection_set(index)
        listbox.see(index)
        status_text.set(f"官方 MiniGrid 关卡数: {len(env_ids)} | 当前显示: {len(filtered)}")

    def sync_selection(_: object | None = None) -> None:
        selection = listbox.curselection()
        if selection:
            selected_env.set(listbox.get(selection[0]))

    def launch_selected() -> None:
        sync_selection()
        root.destroy()
        launch_manual_control(
            env_id=selected_env.get(),
            seed=seed,
            tile_size=tile_size,
            agent_view=agent_view,
            agent_view_size=agent_view_size,
            screen_size=screen_size,
            fully_observable=fully_observable,
        )

    search_entry.bind("<KeyRelease>", lambda _event: populate_list(filter_text.get()))
    listbox.bind("<<ListboxSelect>>", sync_selection)
    listbox.bind("<Double-Button-1>", lambda _event: launch_selected())

    button_row = ttk.Frame(frame)
    button_row.pack(fill="x", pady=(12, 0))
    ttk.Button(button_row, text="开始游玩", command=launch_selected).pack(side="left")
    ttk.Button(button_row, text="退出", command=root.destroy).pack(side="right")

    populate_list()
    search_entry.focus_set()
    root.mainloop()



def main() -> None:
    """命令行入口。"""
    parser = argparse.ArgumentParser(description="MiniGrid 图形化关卡选择与手动游玩入口")
    parser.add_argument("--env-id", default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--tile-size", type=int, default=32)
    parser.add_argument("--agent-view", action="store_true")
    parser.add_argument("--agent-view-size", type=int, default=7)
    parser.add_argument("--screen-size", type=int, default=640)
    parser.add_argument("--fully-observable", action="store_true")
    parser.add_argument("--list-levels", action="store_true")
    args = parser.parse_args()

    env_ids = available_env_ids()

    if args.list_levels:
        print(f"官方 MiniGrid 关卡数: {len(env_ids)}")
        print(CONTROL_TEXT)
        for env_id in env_ids:
            print(env_id)
        return

    if args.env_id is not None:
        launch_manual_control(
            env_id=args.env_id,
            seed=args.seed,
            tile_size=args.tile_size,
            agent_view=args.agent_view,
            agent_view_size=args.agent_view_size,
            screen_size=args.screen_size,
            fully_observable=args.fully_observable,
        )
        return

    choose_level_gui(
        env_ids=env_ids,
        seed=args.seed,
        tile_size=args.tile_size,
        agent_view=args.agent_view,
        agent_view_size=args.agent_view_size,
        screen_size=args.screen_size,
        fully_observable=args.fully_observable,
    )


if __name__ == "__main__":
    main()