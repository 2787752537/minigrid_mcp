from __future__ import annotations

import argparse
import runpy
import sys
import tkinter as tk
from tkinter import ttk

import gymnasium as gym
import minigrid


def available_env_ids() -> list[str]:
    # 直接从 Gymnasium 注册表里读取当前已安装的官方 MiniGrid 关卡。
    return sorted(
        env_id for env_id in gym.envs.registry.keys() if env_id.startswith("MiniGrid-")
    )


def launch_manual_control(
    env_id: str,
    seed: int | None,
    tile_size: int,
    agent_view: bool,
    agent_view_size: int,
    screen_size: int,
) -> None:
    # 直接复用官方的手动控制入口，避免自己维护一套游戏逻辑。
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

    runpy.run_module("minigrid.manual_control", run_name="__main__")


def choose_level_gui(
    env_ids: list[str],
    seed: int | None,
    tile_size: int,
    agent_view: bool,
    agent_view_size: int,
    screen_size: int,
) -> None:
    root = tk.Tk()
    root.title("MiniGrid Level Select")
    root.geometry("720x520")

    selected_env = tk.StringVar(value="MiniGrid-Empty-8x8-v0")
    filter_text = tk.StringVar()
    status_text = tk.StringVar(value=f"Official MiniGrid levels: {len(env_ids)}")

    frame = ttk.Frame(root, padding=16)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="MiniGrid Official Level Select").pack(anchor="w")
    ttk.Label(frame, textvariable=status_text).pack(anchor="w", pady=(4, 12))

    ttk.Label(frame, text="Search").pack(anchor="w")
    search_entry = ttk.Entry(frame, textvariable=filter_text)
    search_entry.pack(fill="x", pady=(0, 12))

    listbox = tk.Listbox(frame, height=18, exportselection=False)
    listbox.pack(fill="both", expand=True)

    def populate_list(query: str = "") -> None:
        # 搜索过滤后，如果当前关卡还在列表里，就继续保持选中状态。
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
        status_text.set(
            f"Official MiniGrid levels: {len(env_ids)} | visible: {len(filtered)}"
        )

    def sync_selection(_: object | None = None) -> None:
        selection = listbox.curselection()
        if selection:
            selected_env.set(listbox.get(selection[0]))

    def launch_selected() -> None:
        # 先关闭选择窗口，再交给官方 MiniGrid 窗口接管。
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
    ttk.Button(button_row, text="Play Selected Level", command=launch_selected).pack(
        side="left"
    )
    ttk.Button(button_row, text="Quit", command=root.destroy).pack(
        side="right"
    )

    populate_list()
    search_entry.focus_set()
    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser()
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
        print(f"Official MiniGrid levels: {len(env_ids)}")
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
