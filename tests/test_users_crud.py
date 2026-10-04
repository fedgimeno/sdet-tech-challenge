from __future__ import annotations

import pytest

from tests.helpers import utils
from tests.helpers.api_client import ApiClient

pytestmark = pytest.mark.e2e


def test_create_user_returns_created_user(
    api_client: ApiClient,
    make_user_payload,
    create_user_with_cleanup,
    validate_response_schema,
    get_api_schema,
) -> None:
    payload = make_user_payload()
    response = create_user_with_cleanup(api_client, payload)
    assert response.status_code == 201
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(response, get_api_schema("/users", "POST", response.status_code))
    body = response.json()
    assert body["name"] == payload["name"]
    assert body["email"] == payload["email"]
    assert body["age"] == payload["age"]


def test_created_user_appears_in_user_listing(
    api_client: ApiClient, create_prerequisite_user, validate_response_schema, get_api_schema
) -> None:
    user = create_prerequisite_user(api_client, {})
    response = api_client.get_users()
    assert response.status_code == 200
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(response, get_api_schema("/users", "GET", response.status_code))
    matches = [record for record in response.json() if record["email"] == user["email"]]
    assert len(matches) == 1
    assert matches[0]["name"] == user["name"]
    assert matches[0]["email"] == user["email"]
    assert matches[0]["age"] == user["age"]


def test_get_user_by_email_returns_matching_user(
    user_path,
    api_client: ApiClient,
    create_prerequisite_user,
    validate_response_schema,
    get_api_schema,
) -> None:
    user = create_prerequisite_user(api_client, {})
    response = api_client.request("GET", user_path(user["email"]))
    assert response.status_code == 200
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(
        response, get_api_schema("/users/{email}", "GET", response.status_code)
    )
    body = response.json()
    assert body["name"] == user["name"]
    assert body["email"] == user["email"]
    assert body["age"] == user["age"]


@pytest.mark.parametrize(
    "name,email_tag",
    [
        pytest.param("José 李", "", id="unicode-name"),
        pytest.param("API Test User", "+qa", id="email-with-plus"),
    ],
)
def test_created_user_preserves_valid_name_and_email_on_retrieval(
    user_path,
    api_client,
    make_user_payload,
    create_user_with_cleanup,
    validate_response_schema,
    name,
    email_tag,
    get_api_schema,
):
    payload = make_user_payload(name=name)
    payload["email"] = payload["email"].replace("@", f"{email_tag}@")
    created = create_user_with_cleanup(api_client, payload)
    assert created.status_code == 201
    assert created.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(created, get_api_schema("/users", "POST", created.status_code))
    body = created.json()
    assert body["name"] == payload["name"]
    assert body["email"] == payload["email"]
    assert body["age"] == payload["age"]
    retrieved = api_client.request("GET", user_path(payload["email"]))
    assert retrieved.status_code == 200
    assert retrieved.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(
        retrieved, get_api_schema("/users/{email}", "GET", retrieved.status_code)
    )
    body = retrieved.json()
    assert body["name"] == payload["name"]
    assert body["email"] == payload["email"]
    assert body["age"] == payload["age"]


def test_update_user_returns_updated_values(
    user_path,
    api_client: ApiClient,
    create_prerequisite_user,
    validate_response_schema,
    get_api_schema,
) -> None:
    user = create_prerequisite_user(api_client, {})
    updated = {**user, "name": "Updated API Test User", "age": 31}
    response = api_client.request("PUT", user_path(user["email"]), json_body=updated)
    assert response.status_code == 200
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(
        response, get_api_schema("/users/{email}", "PUT", response.status_code)
    )
    body = response.json()
    assert body["name"] == updated["name"]
    assert body["email"] == updated["email"]
    assert body["age"] == updated["age"]


def test_deleted_user_is_absent_from_user_listing(
    api_client: ApiClient, create_prerequisite_user, validate_response_schema, get_api_schema
) -> None:
    user = create_prerequisite_user(api_client, {})
    response = api_client.delete_user(str(user["email"]))
    assert response.status_code == 204
    assert response.content == b""
    listing = api_client.get_users()
    assert listing.status_code == 200
    assert listing.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(listing, get_api_schema("/users", "GET", listing.status_code))
    emails = [record["email"] for record in listing.json()]
    assert user["email"] not in emails


def test_deleting_last_user_returns_empty_user_listing(
    api_client, create_prerequisite_user, validate_response_schema, get_api_schema
):
    user = create_prerequisite_user(api_client, {})
    listing = api_client.get_users()
    assert listing.status_code == 200
    assert listing.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(listing, get_api_schema("/users", "GET", listing.status_code))
    users = listing.json()
    assert len(users) == 1, "Expected one user in the disposable collection"
    assert users[0]["name"] == user["name"]
    assert users[0]["email"] == user["email"]
    assert users[0]["age"] == user["age"]
    deleted = api_client.delete_user(str(user["email"]))
    assert deleted.status_code == 204
    assert deleted.content == b""
    listing = api_client.get_users()
    assert listing.status_code == 200
    assert listing.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(listing, get_api_schema("/users", "GET", listing.status_code))
    assert listing.json() == []


def test_update_unknown_user_returns_not_found(
    user_path,
    api_client: ApiClient,
    make_user_payload,
    validate_response_schema,
    get_api_schema,
) -> None:
    payload = make_user_payload()
    response = api_client.request("PUT", user_path(payload["email"]), json_body=payload)
    assert response.status_code == 404
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(
        response, get_api_schema("/users/{email}", "PUT", response.status_code)
    )


def test_delete_unknown_user_returns_not_found(
    api_client: ApiClient,
    make_user_payload,
    validate_response_schema,
    get_api_schema,
) -> None:
    email = make_user_payload()["email"]
    response = api_client.delete_user(str(email))
    assert response.status_code == 404
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(
        response, get_api_schema("/users/{email}", "DELETE", response.status_code)
    )


@pytest.mark.xfail(
    strict=True,
    reason="BUG-001: GET of an unknown email returns 500 instead of 404",
)
def test_get_unknown_user_returns_not_found(
    user_path, api_client: ApiClient, make_user_payload, validate_response_schema, get_api_schema
) -> None:
    response = api_client.request("GET", user_path(make_user_payload()["email"]))
    assert response.status_code == 404
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(
        response, get_api_schema("/users/{email}", "GET", response.status_code)
    )


@pytest.mark.xfail(
    strict=True,
    reason="BUG-001: GET after successful deletion returns 500 instead of 404",
)
def test_get_deleted_user_returns_not_found(
    user_path,
    api_client: ApiClient,
    create_prerequisite_user,
    validate_response_schema,
    get_api_schema,
) -> None:
    user = create_prerequisite_user(api_client, {})
    deleted = api_client.delete_user(str(user["email"]))
    assert deleted.status_code == 204
    assert deleted.content == b""
    response = api_client.request("GET", user_path(user["email"]))
    assert response.status_code == 404
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(
        response, get_api_schema("/users/{email}", "GET", response.status_code)
    )


@pytest.mark.xfail(
    strict=True,
    reason="BUG-002: PUT reports success but updated fields are not persisted",
)
def test_updated_user_values_are_persisted(
    user_path,
    api_client: ApiClient,
    create_prerequisite_user,
    validate_response_schema,
    get_api_schema,
) -> None:
    user = create_prerequisite_user(api_client, {})
    updated = {**user, "name": "Updated API Test User", "age": 31}
    response = api_client.request("PUT", user_path(user["email"]), json_body=updated)
    assert response.status_code == 200
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(
        response, get_api_schema("/users/{email}", "PUT", response.status_code)
    )
    body = response.json()
    assert body["name"] == updated["name"]
    assert body["email"] == updated["email"]
    assert body["age"] == updated["age"]
    retrieved = api_client.request("GET", user_path(user["email"]))
    assert retrieved.status_code == 200
    assert retrieved.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(
        retrieved, get_api_schema("/users/{email}", "GET", retrieved.status_code)
    )
    stored = retrieved.json()
    assert stored["email"] == user["email"]
    assert stored["name"] == updated["name"]
    assert stored["age"] == updated["age"]


def test_deleting_user_preserves_other_user(
    user_path, api_client, create_prerequisite_user, get_api_schema, validate_response_schema
):
    removed = create_prerequisite_user(api_client, {"name": "Removed User"})
    survivor = create_prerequisite_user(api_client, {"name": "Surviving User", "age": 41})
    deleted = api_client.delete_user(removed["email"])
    assert deleted.status_code == 204
    assert deleted.content == b""
    stored = api_client.request("GET", user_path(survivor["email"]))
    assert stored.status_code == 200
    assert stored.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(stored, get_api_schema("/users/{email}", "GET", 200))
    utils.assert_user_values(stored, survivor)
    listing = api_client.get_users()
    assert listing.status_code == 200
    assert listing.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(listing, get_api_schema("/users", "GET", 200))
    emails = [user["email"] for user in listing.json()]
    assert removed["email"] not in emails
    assert emails.count(survivor["email"]) == 1
