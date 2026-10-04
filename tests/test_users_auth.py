from __future__ import annotations

import os

import pytest

from tests.helpers.api_client import ApiClient

pytestmark = pytest.mark.e2e


@pytest.mark.xfail(
    os.getenv("TARGET_ENV", "dev") == "dev",
    strict=True,
    reason="BUG-003: dev deletion ignores missing or invalid Authentication",
)
@pytest.mark.parametrize(
    "token",
    [None, "Bearer invalid-token", "invalid-token"],
    ids=["missing", "malformed", "invalid"],
)
def test_delete_user_rejects_missing_or_invalid_authentication_and_preserves_user(
    user_path,
    api_client: ApiClient,
    create_prerequisite_user,
    validate_response_schema,
    token: str | None,
    get_api_schema,
) -> None:
    user = create_prerequisite_user(api_client, {})
    headers = {} if token is None else {"Authentication": token}
    response = api_client.request("DELETE", user_path(user["email"]), headers=headers)
    assert response.status_code == 401
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(
        response, get_api_schema("/users/{email}", "DELETE", response.status_code)
    )
    retrieved = api_client.request("GET", user_path(user["email"]))
    assert retrieved.status_code == 200
    assert retrieved.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(
        retrieved, get_api_schema("/users/{email}", "GET", retrieved.status_code)
    )
    body = retrieved.json()
    assert body["name"] == user["name"]
    assert body["email"] == user["email"]
    assert body["age"] == user["age"]
