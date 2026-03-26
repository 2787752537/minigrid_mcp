from __future__ import annotations

"""MiniGrid 图形化手动游玩入口。"""

import argparse
import runpy
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from 游戏接口.minigrid接口 import available_env_ids

# 这里写清楚官方 MiniGrid 手动控制的按键，方便以后查阅。
CONTROL_TEXT = (
    "操作按键: ↑ 前进 | ← 左转 | → 右转 | Space 交互/开门 | "
    "PageUp/Tab 拾取 | PageDown/Left Shift 放下 | Enter done | "
    "Backspace 重开 | Esc 退出"
)


def launch_manual_control(
    env_id: str,
    seed: int | None,
    tile_size: int,
    agent_view: bool,
    agent_view_size: int,
    screen_size: int,
) -> None:
    """直接转发到官方 `minigrid.manual_control`。"""
    # 这里不自己维护游戏循环，而是把参数拼给官方入口来运行。
    sys.argv = [
        "minigrid.manual_control",
        "--env-id",
        env_id,
        "--tile-size",
        str(tile_size),
        "--agent-view-size",
        str(agent_view_size),
        "--screen-size",
        str(screen_size),
    ]
    if seed is not None:
        sys.argv.extend(["--seed", str(seed)])
    if agent_view:
        sys.argv.append("--agent-view")

    print(CONTROL_TEXT)
    runpy.run_module("minigrid.manual_control", run_name="__main__")



def choose_level_gui(
    env_ids: list[str],
    seed: int | None,
    tile_size: int,
    agent_view: bool,
    agent_view_size: int,
    screen_size: int,
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

    ttk.Label(frame, text="搜索关卡").pack(anchor="w")
    search_entry = ttk.Entry(frame, textvariable=filter_text)
    search_entry.pack(fill="x", pady=(0, 12))

    listbox = tk.Listbox(frame, height=18, exportselection=False)
    listbox.pack(fill="both", expand=True)

    def populate_list(query: str = "") -> None:
        """按关键字过滤关卡，并尽量保持原来的选中项。"""
        query_lower = query.lower().strip()
        filtered = [
            env_id for env_id in env_ids if query_lower in env_id.lower()
        ] or env_ids
        listbox.delete(0, tk.END)
        for env_id in filtered:
            listbox.insert(tk.END, env_id)

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
        """把列表选中的关卡同步到状态变量。"""
        selection = listbox.curselection()
        if selection:
            selected_env.set(listbox.get(selection[0]))

    def launch_selected() -> None:
        """关闭选择窗口并进入游戏。"""
        sync_selection()
        root.destroy()
        launch_manual_control(
            env_id=selected_env.get(),
            seed=seed,
            tile_size=tile_size,
            agent_view=agent_view,
            agent_view_size=agent_view_size,
            screen_size=screen_size,
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
        )
        return

    choose_level_gui(
        env_ids=env_ids,
        seed=args.seed,
        tile_size=args.tile_size,
        agent_view=args.agent_view,
        agent_view_size=args.agent_view_size,
        screen_size=args.screen_size,
    )


if __name__ == "__main__":
    main()