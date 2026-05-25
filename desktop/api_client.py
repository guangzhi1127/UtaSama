from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import requests


@dataclass
class ApiResult:
    ok: bool
    data: dict[str, Any]
    error: str = ""


class UtaSamaApiClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: int = 90):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def health(self) -> ApiResult:
        return self._get("/health")

    def runtime_config(self) -> ApiResult:
        return self._get("/runtime/config")

    def chat(self, message: str, session_id: Optional[str]) -> ApiResult:
        return self._post(
            "/chat",
            {
                "message": message,
                "session_id": session_id,
            },
        )

    def _get(self, path: str) -> ApiResult:
        try:
            response = requests.get(self._url(path), timeout=self.timeout)
            response.raise_for_status()
            return ApiResult(ok=True, data=response.json())
        except Exception as error:
            return ApiResult(ok=False, data={}, error=str(error))

    def _post(self, path: str, payload: dict[str, Any]) -> ApiResult:
        try:
            response = requests.post(self._url(path), json=payload, timeout=self.timeout)
            response.raise_for_status()
            return ApiResult(ok=True, data=response.json())
        except Exception as error:
            return ApiResult(ok=False, data={}, error=str(error))
