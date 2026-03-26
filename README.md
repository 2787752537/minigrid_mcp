# MiniGrid Agent

这个仓库现在只保留两部分核心内容：

- `游戏本体/`：官方 MiniGrid 的图形化手动游玩入口
- `游戏接口/` + `minigrid_mcp_server.py`：供 Codex / MCP 调用的游戏控制服务

## 安装

建议先创建一个 Python 3.10+ 虚拟环境，然后在项目根目录安装依赖：

```powershell
python -m pip install -U pip
python -m pip install -e .
```

如果你已经把项目传到 GitHub，也可以直接从仓库安装：

```powershell
python -m pip install "git+https://github.com/<你的用户名>/<仓库名>.git"
```

## 手动玩游戏

运行：

```powershell
python 游戏本体\play_minigrid.py
```

现在手动游玩入口会默认开启一个本地共享会话：

- 你可以自己用键盘操作
- 也可以在游戏运行中途让 MCP 接管几步
- 两边可以交替操作，不需要重新开局

## 游戏操作按键

官方 `manual_control` 的默认按键如下：

- `↑`：前进
- `←`：左转
- `→`：右转
- `Space`：交互 / 开门 / 切换
- `PageUp` 或 `Tab`：拾取
- `PageDown` 或 `Left Shift`：放下
- `Enter`：done
- `Backspace`：重开当前局
- `Esc`：退出

## MCP 服务

这个项目提供了一个可直接启动的 MCP 入口：

```powershell
python minigrid_mcp_server.py
```

如果你已经用 `pip install -e .` 安装过，也可以直接这样启动：

```powershell
minigrid-mcp
```

### 新的配合方式

1. 你先手动启动游戏窗口
2. 再启动 MCP server
3. 之后 MCP 可以随时通过 `get_state` / `step_game` 接入当前这局
4. 你也可以继续手动按键，两边可以交替操作

### 在 Codex 里注册 MCP

推荐方式一：

```powershell
codex mcp add minigrid -- minigrid-mcp
```

推荐方式二：

```powershell
codex mcp add minigrid -- python D:\你的项目路径\minigrid_agent\minigrid_mcp_server.py
```

注册完成后，完全退出 Codex App，再重新打开项目。

### MCP 工具

- `list_levels`
- `start_game`
- `get_state`
- `step_game`
- `reset_game`
- `close_game`

说明：

- 如果你已经手动开了一局，`get_state / step_game / reset_game / close_game` 会优先接管这局手动游戏
- 如果没有手动游戏，仍然可以继续使用原来的 `start_game` 让 MCP 自己开一局

更详细的安装说明见：

- [MCP安装说明.md](./MCP安装说明.md)