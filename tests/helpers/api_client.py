from typing import Any
from urllib.parse import quote

import requests


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
    ):
        if json_body is not None and data_body is not None:
            raise ValueError("Provide either json_body or data_body, not both")
        url = f"{self.base_url}/{self.environment}{path}"
        return self.session.request(method, url, json=json_body, data=data_body, headers=headers)

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
