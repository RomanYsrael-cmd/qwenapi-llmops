"""Track child processes explicitly instead of using broad process-name kills."""

from __future__ import annotations

import subprocess
from typing import Any


class ProcessRegistry:
    """Own only the processes registered by this service instance."""

    def __init__(self) -> None:
        self._processes: dict[str, subprocess.Popen[Any]] = {}

    def register(self, name: str, process: subprocess.Popen[Any]) -> None:
        self._processes[name] = process

    def running(self) -> dict[str, int]:
        return {name: process.pid for name, process in self._processes.items() if process.poll() is None}

    def terminate_all(self, timeout_seconds: float = 5.0) -> list[str]:
        terminated: list[str] = []
        for name, process in list(self._processes.items()):
            if process.poll() is not None:
                terminated.append(name)
                continue
            process.terminate()
            try:
                process.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=timeout_seconds)
            terminated.append(name)
        self._processes.clear()
        return terminated
