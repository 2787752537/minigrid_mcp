# MiniGrid Agent

一个用于练习 MiniGrid 和 MCP 接管的小项目。

这个仓库现在只做两件事：

- 提供一个可以直接手动游玩的 MiniGrid 图形化入口
- 提供一个 MCP server，让 Codex / agent 可以在你游玩中途接入同一局游戏

特点很简单：**你可以自己玩，也可以随时让 MCP 接手几步。**

## 安装

在项目根目录执行：

```powershell
python -m pip install -U pip
python -m pip install -e .
```

如果你已经把仓库传到 GitHub，也可以直接安装：

```powershell
python -m pip install "git+https://github.com/<你的用户名>/<仓库名>.git"
```

安装完成后，可以直接启动 MCP：

```powershell
minigrid-mcp
```

## 快速开始

### 1. 打开手动游戏

```powershell
python 游戏本体\play_minigrid.py
```

### 2. 启动 MCP server

```powershell
python minigrid_mcp_server.py
```

或者：

```powershell
minigrid-mcp
```

### 3. 在 Codex 里注册 MCP

```powershell
codex mcp add minigrid -- minigrid-mcp
```

如果你更想直接指定脚本路径：

```powershell
codex mcp add minigrid -- python D:\你的项目路径\minigrid_agent\minigrid_mcp_server.py
```

注册完成后，完全退出 Codex App，再重新打开项目。

## 手动游玩

操作按键：

- `↑`：前进
- `←`：左转
- `→`：右转
- `Space`：交互 / 开门 / 切换
- `PageUp` 或 `Tab`：拾取
- `PageDown` 或 `Left Shift`：放下
- `Enter`：done
- `Backspace`：重开当前局
- `Esc`：退出

当前手动模式会：

- 自动开启一个本地共享会话
- 成功时打印并弹窗提示 `通关了`
- 超时结束时打印并弹窗提示 `本局结束`

## MCP 工具

这个项目提供这些 MCP 工具：

- `list_levels`
- `start_game`
- `get_state`
- `step_game`
- `reset_game`
- `close_game`

行为逻辑：

- 如果你已经手动开了一局，`get_state / step_game / reset_game / close_game` 会优先接管这局手动游戏
- 如果当前没有手动游戏，仍然可以用 `start_game` 让 MCP 自己开一局
- 你和 MCP 可以交替操作同一局，不需要重新开局

## 目录

- `游戏本体/`：手动游玩入口
- `游戏接口/`：状态读取、动作执行、共享会话逻辑
- `minigrid_mcp_server.py`：MCP 启动入口
- `MCP安装说明.md`：更详细的 MCP 安装说明

## 文档

- [MCP安装说明.md](./MCP安装说明.md)
