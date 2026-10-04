from __future__ import annotations

import pytest

from tests.helpers import utils
from tests.helpers.api_client import ApiClient

pytestmark = pytest.mark.e2e


def test_created_user_is_absent_from_other_environment_user_listing(
    user_path,
    api_client: ApiClient,
    create_prerequisite_user,
    validate_response_schema,
    get_api_schema,
) -> None:
    user = create_prerequisite_user(api_client, {})
    other_env = "prod" if api_client.environment == "dev" else "dev"
    other = ApiClient(api_client.session, api_client.base_url, other_env, api_client.token)
    listing = other.get_users()
    assert listing.status_code == 200
    assert listing.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(listing, get_api_schema("/users", "GET", listing.status_code))
    emails = [record["email"] for record in listing.json()]
    assert user["email"] not in emails
    original = api_client.request("GET", user_path(user["email"]))
    assert original.status_code == 200
    assert original.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(
        original, get_api_schema("/users/{email}", "GET", original.status_code)
    )
    body = original.json()
    assert body["name"] == user["name"]
    assert body["email"] == user["email"]
    assert body["age"] == user["age"]


@pytest.mark.xfail(
    strict=True,
    reason="BUG-001: GET in the other environment returns 500 instead of 404",
)
def test_get_user_from_other_environment_returns_not_found(
    user_path,
    api_client: ApiClient,
    create_prerequisite_user,
    validate_response_schema,
    get_api_schema,
) -> None:
    user = create_prerequisite_user(api_client, {})
    other_env = "prod" if api_client.environment == "dev" else "dev"
    response = ApiClient(
        api_client.session, api_client.base_url, other_env, api_client.token
    ).request("GET", user_path(user["email"]))
    assert response.status_code == 404
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(
        response, get_api_schema("/users/{email}", "GET", response.status_code)
    )


def test_update_preserves_same_email_user_in_other_environment(
    user_path,
    api_client,
    create_prerequisite_user,
    get_api_schema,
    validate_response_schema,
):
    original = create_prerequisite_user(api_client, {"name": "Original Environment User"})
    other_env = "prod" if api_client.environment == "dev" else "dev"
    other = ApiClient(api_client.session, api_client.base_url, other_env, api_client.token)
    other_user = create_prerequisite_user(
        other, {"email": original["email"], "name": "Other Environment User", "age": 45}
    )
    path = user_path(original["email"])
    updated = {**original, "name": "Updated Original User", "age": 35}
    response = api_client.request("PUT", path, json_body=updated)
    assert response.status_code == 200
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(response, get_api_schema("/users/{email}", "PUT", 200))
    utils.assert_user_values(response, updated)
    stored = other.request("GET", path)
    assert stored.status_code == 200
    assert stored.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(stored, get_api_schema("/users/{email}", "GET", 200))
    utils.assert_user_values(stored, other_user)


def test_delete_preserves_same_email_user_in_other_environment(
    user_path,
    api_client,
    create_prerequisite_user,
    get_api_schema,
    validate_response_schema,
):
    original = create_prerequisite_user(api_client, {"name": "Original Environment User"})
    other_env = "prod" if api_client.environment == "dev" else "dev"
    other = ApiClient(api_client.session, api_client.base_url, other_env, api_client.token)
    other_user = create_prerequisite_user(
        other, {"email": original["email"], "name": "Other Environment User", "age": 45}
    )
    path = user_path(original["email"])
    response = api_client.delete_user(original["email"])
    assert response.status_code == 204
    assert response.content == b""
    listing = api_client.get_users()
    assert listing.status_code == 200
    assert listing.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(listing, get_api_schema("/users", "GET", 200))
    assert original["email"] not in [user["email"] for user in listing.json()]
    stored = other.request("GET", path)
    assert stored.status_code == 200
    assert stored.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(stored, get_api_schema("/users/{email}", "GET", 200))
    utils.assert_user_values(stored, other_user)


def test_update_unknown_user_in_other_environment_preserves_original(
    user_path,
    api_client,
    create_prerequisite_user,
    get_api_schema,
    validate_response_schema,
):
    original = create_prerequisite_user(api_client, {})
    other_env = "prod" if api_client.environment == "dev" else "dev"
    other = ApiClient(api_client.session, api_client.base_url, other_env, api_client.token)
    path = user_path(original["email"])
    response = other.request("PUT", path, json_body={**original, "name": "Wrong Environment"})
    stored = api_client.request("GET", path)
    assert stored.status_code == 200
    assert stored.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(stored, get_api_schema("/users/{email}", "GET", 200))
    utils.assert_user_values(stored, original)
    assert response.status_code == 404
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(response, get_api_schema("/users/{email}", "PUT", 404))


def test_delete_unknown_user_in_other_environment_preserves_original(
    user_path,
    api_client,
    create_prerequisite_user,
    get_api_schema,
    validate_response_schema,
):
    original = create_prerequisite_user(api_client, {})
    other_env = "prod" if api_client.environment == "dev" else "dev"
    other = ApiClient(api_client.session, api_client.base_url, other_env, api_client.token)
    path = user_path(original["email"])
    response = other.delete_user(original["email"])
    stored = api_client.request("GET", path)
    assert stored.status_code == 200
    assert stored.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(stored, get_api_schema("/users/{email}", "GET", 200))
    utils.assert_user_values(stored, original)
    assert response.status_code == 404
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(response, get_api_schema("/users/{email}", "DELETE", 404))
