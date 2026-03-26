from __future__ import annotations

"""手动游戏进程和 MCP 服务之间共享状态的小桥接层。"""

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
import time
import uuid
from typing import Any

SESSION_ROOT = Path(tempfile.gettempdir()) / "minigrid_mcp_bridge" / "default"
STATE_PATH = SESSION_ROOT / "state.json"
REQUESTS_DIR = SESSION_ROOT / "requests"
RESPONSES_DIR = SESSION_ROOT / "responses"


@dataclass(slots=True)
class PendingRequest:
    """表示一个等待主游戏进程处理的远程请求。"""

    request_id: str
    payload: dict[str, Any]


class SharedSessionBridge:
    """用文件轮询实现的最小跨进程共享通道。"""

    def __init__(self) -> None:
        self.root = SESSION_ROOT
        self.state_path = STATE_PATH
        self.requests_dir = REQUESTS_DIR
        self.responses_dir = RESPONSES_DIR

    def prepare_host(self) -> None:
        """为手动游戏进程准备会话目录。"""
        self.root.mkdir(parents=True, exist_ok=True)
        self.requests_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir.mkdir(parents=True, exist_ok=True)
        self._clear_dir(self.requests_dir)
        self._clear_dir(self.responses_dir)
        self.write_state({"has_game": False, "state": None, "session_root": str(self.root)})

    def write_state(self, payload: dict[str, Any]) -> None:
        """把当前状态写入共享文件，供 MCP 侧随时读取。"""
        enriched = {
            **payload,
            "session_root": str(self.root),
            "updated_at": time.time(),
        }
        self.state_path.write_text(
            json.dumps(enriched, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def clear_state(self) -> None:
        """把共享状态标记为空闲。"""
        self.write_state({"has_game": False, "state": None})

    def has_live_state(self) -> bool:
        """判断当前是否存在可读取的共享游戏状态。"""
        if not self.state_path.exists():
            return False
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return False
        return bool(payload.get("has_game"))

    def read_state(self) -> dict[str, Any]:
        """读取共享状态。"""
        if not self.state_path.exists():
            return {"has_game": False, "state": None}
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def submit_request(self, payload: dict[str, Any], timeout: float = 8.0) -> dict[str, Any]:
        """向手动游戏进程发送一个请求，并等待处理结果。"""
        if not self.has_live_state():
            raise RuntimeError("当前没有可接管的手动游戏，请先手动启动游戏窗口。")

        self.requests_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir.mkdir(parents=True, exist_ok=True)

        request_id = f"{time.time_ns()}-{uuid.uuid4().hex}"
        request_path = self.requests_dir / f"{request_id}.json"
        response_path = self.responses_dir / f"{request_id}.json"
        request_path.write_text(
            json.dumps({"id": request_id, **payload}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        deadline = time.time() + timeout
        while time.time() < deadline:
            if response_path.exists():
                data = json.loads(response_path.read_text(encoding="utf-8"))
                response_path.unlink(missing_ok=True)
                request_path.unlink(missing_ok=True)
                return data
            time.sleep(0.03)

        request_path.unlink(missing_ok=True)
        raise TimeoutError("等待手动游戏响应超时，可能是游戏窗口已经关闭。")

    def poll_requests(self) -> list[PendingRequest]:
        """让手动游戏进程取走待处理请求。"""
        self.requests_dir.mkdir(parents=True, exist_ok=True)
        requests: list[PendingRequest] = []
        for path in sorted(self.requests_dir.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                path.unlink(missing_ok=True)
                continue
            requests.append(PendingRequest(request_id=payload["id"], payload=payload))
            path.unlink(missing_ok=True)
        return requests

    def write_response(self, request_id: str, payload: dict[str, Any]) -> None:
        """把手动游戏处理好的结果回写给 MCP 端。"""
        self.responses_dir.mkdir(parents=True, exist_ok=True)
        (self.responses_dir / f"{request_id}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _clear_dir(path: Path) -> None:
        for item in path.glob("*"):
            if item.is_file():
                item.unlink(missing_ok=True)