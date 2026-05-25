from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from desktop.api_client import ApiResult, UtaSamaApiClient


class WorkerSignals(QObject):
    finished = Signal(str, object)


class ApiWorker(QRunnable):
    def __init__(
        self,
        task: str,
        client: UtaSamaApiClient,
        message: str = "",
        session_id: Optional[str] = None,
    ):
        super().__init__()
        self.task = task
        self.client = client
        self.message = message
        self.session_id = session_id
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        if self.task == "health":
            result = self.client.health()
        elif self.task == "runtime":
            result = self.client.runtime_config()
        elif self.task == "chat":
            result = self.client.chat(self.message, self.session_id)
        else:
            result = ApiResult(ok=False, data={}, error=f"Unknown task: {self.task}")

        self.signals.finished.emit(self.task, result)
