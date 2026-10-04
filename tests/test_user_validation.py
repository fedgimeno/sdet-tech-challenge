import pytest

from tests.helpers import utils
from tests.helpers.api_client import ApiClient

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize(
    "user",
    [
        {"name": "John", "age": 21},
        {"name": "Charles", "email": "charles@test.com"},
        {"email": "charles@test.com", "age": 43},
    ],
    ids=["missing-email", "missing-age", "missing-name"],
)
def test_create_user_rejects_missing_required_fields(
    api_client: ApiClient, create_user_with_cleanup, validate_response_schema, user, get_api_schema
):
    response = create_user_with_cleanup(api_client, user)
    assert response.status_code == 400
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(response, get_api_schema("/users", "POST", response.status_code))


INVALID_NAME_XFAIL = pytest.mark.xfail(
    strict=True,
    reason="BUG-004: POST and PUT accept numeric and boolean names",
)
INVALID_EMAIL_XFAIL = pytest.mark.xfail(
    strict=True,
    reason="BUG-005: POST accepts non-string email; PUT returns 500",
)


INVALID_FIELD_VALUES = [
    pytest.param(
        "name",
        123,
        id="numeric-name",
        marks=INVALID_NAME_XFAIL,
    ),
    pytest.param("name", [], id="list-name"),
    pytest.param("name", {}, id="object-name"),
    pytest.param("name", None, id="null-name"),
    pytest.param(
        "email",
        123,
        id="numeric-email",
        marks=INVALID_EMAIL_XFAIL,
    ),
    pytest.param("email", [], id="list-email"),
    pytest.param("email", {}, id="object-email"),
    pytest.param("email", None, id="null-email"),
    pytest.param("age", "21", id="string-age"),
    pytest.param("age", [], id="list-age"),
    pytest.param("age", {}, id="object-age"),
    pytest.param("age", None, id="null-age"),
    pytest.param("age", True, id="boolean-age"),
    pytest.param("age", 21.5, id="fractional-age"),
    pytest.param("name", True, id="boolean-name", marks=INVALID_NAME_XFAIL),
    pytest.param("email", True, id="boolean-email", marks=INVALID_EMAIL_XFAIL),
    pytest.param("age", 31.0, id="integral-float-age"),
]


@pytest.mark.parametrize("field,bad_value", INVALID_FIELD_VALUES)
def test_create_user_rejects_invalid_field_types(
    api_client,
    make_user_payload,
    create_user_with_cleanup,
    validate_response_schema,
    field,
    bad_value,
    get_api_schema,
):
    payload = make_user_payload()
    payload[field] = bad_value
    response = create_user_with_cleanup(api_client, payload)
    assert response.status_code == 400
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(response, get_api_schema("/users", "POST", 400))


@pytest.mark.parametrize("field,bad_value", INVALID_FIELD_VALUES)
def test_update_user_rejects_invalid_field_types(
    user_path,
    api_client,
    create_prerequisite_user,
    validate_response_schema,
    field,
    bad_value,
    get_api_schema,
):
    original = create_prerequisite_user(api_client, {})
    payload = original.copy()
    path = user_path(original["email"])
    payload[field] = bad_value
    response = api_client.request("PUT", path, json_body=payload)
    stored = api_client.request("GET", path)
    assert stored.status_code == 200
    assert stored.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(stored, get_api_schema("/users/{email}", "GET", 200))
    utils.assert_user_values(stored, original)
    assert response.status_code == 400
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(response, get_api_schema("/users/{email}", "PUT", 400))


MALFORMED_EMAILS = ["not-an-email", "@test-user.com", "test-user@"]


@pytest.mark.xfail(
    strict=True,
    reason="BUG-006: POST accepts malformed email addresses",
)
@pytest.mark.parametrize("email", MALFORMED_EMAILS)
def test_create_user_rejects_malformed_email(
    api_client: ApiClient,
    make_user_payload,
    create_user_with_cleanup,
    validate_response_schema,
    email,
    get_api_schema,
):
    payload = make_user_payload(email=email)
    response = create_user_with_cleanup(api_client, payload)
    assert response.status_code == 400
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(response, get_api_schema("/users", "POST", 400))


@pytest.mark.parametrize("email", MALFORMED_EMAILS)
def test_update_user_rejects_malformed_email(
    user_path,
    api_client: ApiClient,
    create_prerequisite_user,
    validate_response_schema,
    email,
    get_api_schema,
):
    original = create_prerequisite_user(api_client, {})
    payload = {**original, "email": email}
    path = user_path(original["email"])
    response = api_client.request("PUT", path, json_body=payload)
    stored = api_client.request("GET", path)
    assert stored.status_code == 200
    assert stored.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(stored, get_api_schema("/users/{email}", "GET", 200))
    utils.assert_user_values(stored, original)
    assert response.status_code == 400
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(response, get_api_schema("/users/{email}", "PUT", 400))


@pytest.mark.parametrize("age", [1, 150])
def test_create_user_accepts_age_at_allowed_boundaries(
    api_client: ApiClient,
    create_user_with_cleanup,
    validate_response_schema,
    make_user_payload,
    age,
    get_api_schema,
):
    payload = make_user_payload()
    payload["age"] = age
    response = create_user_with_cleanup(api_client, payload)
    assert response.status_code == 201
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(response, get_api_schema("/users", "POST", response.status_code))
    body = response.json()
    assert body["name"] == payload["name"]
    assert body["email"] == payload["email"]
    assert body["age"] == payload["age"]


@pytest.mark.parametrize("age", [1, 150])
def test_update_user_accepts_age_at_allowed_boundaries(
    user_path,
    api_client: ApiClient,
    validate_response_schema,
    create_prerequisite_user,
    age,
    get_api_schema,
):
    user = create_prerequisite_user(api_client, {})
    payload = user.copy()
    payload["age"] = age
    response = api_client.request("PUT", user_path(user["email"]), json_body=payload)
    assert response.status_code == 200
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(
        response, get_api_schema("/users/{email}", "PUT", response.status_code)
    )
    body = response.json()
    assert body["name"] == payload["name"]
    assert body["email"] == payload["email"]
    assert body["age"] == payload["age"]


@pytest.mark.parametrize("age", [0, -1, 151])
def test_create_user_rejects_age_outside_allowed_range(
    api_client: ApiClient,
    create_user_with_cleanup,
    validate_response_schema,
    make_user_payload,
    age,
    get_api_schema,
):
    payload = make_user_payload(age=age)
    response = create_user_with_cleanup(api_client, payload)
    assert response.status_code == 400
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(response, get_api_schema("/users", "POST", 400))


@pytest.mark.parametrize("age", [0, -1, 151])
def test_update_user_rejects_age_outside_allowed_range(
    user_path,
    api_client: ApiClient,
    create_prerequisite_user,
    validate_response_schema,
    age,
    get_api_schema,
):
    original = create_prerequisite_user(api_client, {})
    payload = {**original, "age": age}
    path = user_path(original["email"])
    response = api_client.request("PUT", path, json_body=payload)
    stored = api_client.request("GET", path)
    assert stored.status_code == 200
    assert stored.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(stored, get_api_schema("/users/{email}", "GET", 200))
    utils.assert_user_values(stored, original)
    assert response.status_code == 400
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(response, get_api_schema("/users/{email}", "PUT", 400))


@pytest.mark.xfail(
    strict=True,
    reason="BUG-007: duplicate-email POST returns 500 instead of 409",
)
def test_create_user_rejects_duplicate_email(
    api_client, validate_response_schema, create_prerequisite_user, get_api_schema
):
    original_user = create_prerequisite_user(api_client, {})
    payload = original_user.copy()
    payload["name"] = "Duplicate Request"
    payload["age"] = 31
    response = api_client.create_user(payload)
    assert response.status_code == 409
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(response, get_api_schema("/users", "POST", response.status_code))


@pytest.mark.parametrize("field", ["name", "email", "age"])
def test_update_with_missing_required_field_preserves_user(
    user_path, api_client, create_prerequisite_user, validate_response_schema, field, get_api_schema
):
    original = create_prerequisite_user(api_client, {})
    payload = original.copy()
    del payload[field]
    response = api_client.request("PUT", user_path(original["email"]), json_body=payload)
    assert response.status_code == 400
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(
        response, get_api_schema("/users/{email}", "PUT", response.status_code)
    )
    stored = api_client.request("GET", user_path(original["email"]))
    assert stored.status_code == 200
    assert stored.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(stored, get_api_schema("/users/{email}", "GET", stored.status_code))
    body = stored.json()
    assert body["name"] == original["name"]
    assert body["email"] == original["email"]
    assert body["age"] == original["age"]


@pytest.mark.e2e
@pytest.mark.parametrize(
    "test_users",
    [
        [{"name": "John", "age": 31}, {"name": "Laura", "age": 22}, {"name": "Jesse", "age": 19}],
        [
            {"name": "Carlos", "age": 20},
            {"name": "Juan", "age": 12},
            {"name": "Mark", "age": 18},
            {"name": "Sarah", "age": 71},
            {"name": "Lucca", "age": 56},
        ],
    ],
)
def test_get_users_list_succeds(
    api_client: ApiClient,
    create_prerequisite_user,
    test_users,
    get_api_schema,
    validate_response_schema,
):
    payloads = []
    for user_payload in test_users:
        created_payload = create_prerequisite_user(api_client, user_payload)
        payloads.append(created_payload)
    response = api_client.get_users()
    assert response.status_code == 200
    target_schema = get_api_schema("/users", "get", 200)
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(response, target_schema)
    user_list = response.json()
    returned_emails = [user["email"] for user in user_list]
    for payload in payloads:
        assert returned_emails.count(payload["email"]) == 1, (
            f"Expected exactly one entry for {payload['email']} in GET /users"
        )
    users_by_email = {user["email"]: user for user in user_list}
    for payload in payloads:
        email = payload["email"]
        assert email in users_by_email, f"Created user {email} is missing from GET /users"
        returned_user = users_by_email[email]
        for field in ("name", "age"):
            assert returned_user[field] == payload[field], (
                f"Unexpected {field} for {email}: "
                f"expected {payload[field]!r}, got {returned_user[field]!r}"
            )


NON_OBJECT_BODY_XFAIL = pytest.mark.xfail(
    strict=True,
    reason="BUG-008: array and scalar JSON bodies return 500 instead of 400",
)


INVALID_REQUEST_BODIES = [
    pytest.param(None, id="missing-body"),
    pytest.param("null", id="null-body"),
    pytest.param("{}", id="empty-object"),
    pytest.param("[]", id="array-body", marks=NON_OBJECT_BODY_XFAIL),
    pytest.param('"user"', id="string-body", marks=NON_OBJECT_BODY_XFAIL),
    pytest.param("123", id="number-body", marks=NON_OBJECT_BODY_XFAIL),
    pytest.param("true", id="boolean-body", marks=NON_OBJECT_BODY_XFAIL),
    pytest.param("{", id="malformed-json"),
]


@pytest.mark.parametrize("body", INVALID_REQUEST_BODIES)
def test_create_user_rejects_invalid_request_body(
    api_client, get_api_schema, validate_response_schema, body
):
    response = api_client.request(
        "POST",
        "/users",
        data_body=body,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(response, get_api_schema("/users", "POST", 400))


@pytest.mark.parametrize("body", INVALID_REQUEST_BODIES)
def test_update_user_rejects_invalid_request_body(
    user_path, api_client, create_prerequisite_user, get_api_schema, validate_response_schema, body
):
    original = create_prerequisite_user(api_client, {})
    path = user_path(original["email"])
    response = api_client.request(
        "PUT",
        path,
        data_body=body,
        headers={"Content-Type": "application/json"},
    )

    stored = api_client.request("GET", path)
    assert stored.status_code == 200
    assert stored.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(stored, get_api_schema("/users/{email}", "GET", 200))
    utils.assert_user_values(stored, original)

    assert response.status_code == 400
    assert response.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(response, get_api_schema("/users/{email}", "PUT", 400))


def test_duplicate_email_request_preserves_original_user(
    user_path, api_client, create_prerequisite_user, get_api_schema, validate_response_schema
):
    original = create_prerequisite_user(api_client, {})
    duplicate = {**original, "name": "Duplicate Request", "age": 31}
    api_client.create_user(duplicate)

    stored = api_client.request("GET", user_path(original["email"]))
    assert stored.status_code == 200
    assert stored.headers.get("Content-Type", "").split(";")[0].strip() == "application/json"
    validate_response_schema(stored, get_api_schema("/users/{email}", "GET", 200))
    utils.assert_user_values(stored, original)
