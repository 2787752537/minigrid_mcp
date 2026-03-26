# MiniGrid MCP 安装说明

这份说明用于把当前项目里的 MiniGrid MCP 服务接到 Codex。

## 1. 安装项目依赖

在项目根目录执行：

```powershell
python -m pip install -U pip
python -m pip install -e .
```

如果你已经把仓库传到 GitHub，也可以直接安装：

```powershell
python -m pip install "git+https://github.com/<你的用户名>/<仓库名>.git"
```

安装完成后，你会得到一个可直接启动的命令：

```powershell
minigrid-mcp
```

## 2. 本地测试 MCP 服务

你可以先确认服务能启动：

```powershell
python minigrid_mcp_server.py
```

或者：

```powershell
minigrid-mcp
```

这是一个 `stdio` MCP 服务。它启动后会等待客户端连接，终端里没有图形界面是正常的。

## 3. 注册到 Codex

推荐方式一：直接注册命令行入口

```powershell
codex mcp add minigrid -- minigrid-mcp
```

推荐方式二：直接注册项目脚本路径

```powershell
codex mcp add minigrid -- python D:\你的项目路径\minigrid_agent\minigrid_mcp_server.py
```

注册完成后：

1. 完全退出 Codex App
2. 重新打开 Codex
3. 回到项目对话里测试 MCP

## 4. MCP 暴露的工具

- `list_levels`：列出官方 MiniGrid 关卡
- `start_game`：启动一局游戏
- `get_state`：读取当前游戏状态
- `step_game`：执行一步动作
- `reset_game`：重置当前游戏
- `close_game`：关闭当前游戏

## 5. 常见问题

### 1. 我手动运行了 MCP 服务，为什么 Codex 还是调不到？

因为这是 `stdio` MCP。通常不需要你手动双击运行它，而是应该先 `codex mcp add ...`，再让 Codex 自己拉起它。

### 2. 注册后还是看不到工具怎么办？

先检查：

- 依赖是否已经安装成功
- `minigrid_mcp_server.py` 能否本地启动
- Codex 是否已经完全重启

### 3. 路径里有中文会不会有问题？

这个项目已经额外提供了根目录入口：

- `minigrid_mcp_server.py`

这样注册时可以优先使用英文文件名入口，通常更稳。