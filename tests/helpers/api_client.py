import logging
import time
from typing import Any
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(
        self, session: requests.Session, base_url: str, environment: str, token: str
    ) -> None:
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.environment = environment
        self.token = token

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: object | None = None,
        data_body: str | bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        if json_body is not None and data_body is not None:
            raise ValueError("Provide either json_body or data_body, not both")
        url = f"{self.base_url}/{self.environment}{path}"
        request_headers = {key.lower(): value for key, value in self.session.headers.items()}
        request_headers.update({key.lower(): value for key, value in (headers or {}).items()})
        auth_present = bool(self.session.auth) or any(
            request_headers.get(name) is not None for name in ("authentication", "authorization")
        )
        started = time.perf_counter()

        try:
            response = self.session.request(
                method, url, json=json_body, data=data_body, headers=headers
            )
        except requests.RequestException as error:
            logger.info(
                "%s %s auth_present=%s failed=%s elapsed=%.3fs",
                method,
                url,
                auth_present,
                type(error).__name__,
                time.perf_counter() - started,
            )
            raise

        body = response.text
        preview = body[:500] + ("…" if len(body) > 500 else "")
        logger.info(
            "%s %s auth_present=%s status=%s elapsed=%.3fs body=%r",
            method,
            url,
            auth_present,
            response.status_code,
            time.perf_counter() - started,
            preview,
        )
        return response

    def get_users(self) -> requests.Response:
        return self.request("GET", "/users")

    def create_user(self, payload: dict[str, Any]) -> requests.Response:
        return self.request("POST", "/users", json_body=payload)

    def delete_user(self, email: str) -> requests.Response:
        return self.request(
            "DELETE",
            f"/users/{quote(email, safe='')}",
            headers={"Authentication": self.token},
        )
