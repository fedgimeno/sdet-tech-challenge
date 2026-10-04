from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import uuid4

import jsonschema
import pytest
import requests
import yaml

from tests.helpers.api_client import ApiClient

ROOT = Path(__file__).resolve().parents[1]


def validate_response_schema(response: requests.Response, target_schema: dict[str, Any]) -> None:
    try:
        jsonschema.validate(
            instance=response.json(),
            schema=target_schema,
            cls=jsonschema.Draft4Validator,
            format_checker=jsonschema.FormatChecker(),
        )
    except jsonschema.exceptions.ValidationError as e:
        pytest.fail(f"Response broke the OpenAPI contract! Error: {e.message}")


def make_user_payload(**overrides: object) -> dict[str, Any]:
    return {
        "name": "API Test User",
        "email": f"sdet-{uuid4().hex}@example.com",
        "age": 30,
        **overrides,
    }


def user_path(email: str | int) -> str:
    return f"/users/{quote(str(email), safe='')}"


def assert_user_values(response: requests.Response, payload: dict[str, Any]) -> None:
    body = response.json()
    for field in ("name", "email", "age"):
        assert body[field] == payload[field], (
            f"Unexpected {field}: expected {payload[field]!r}, got {body[field]!r}"
        )


def delete_test_user(api_client: ApiClient, email: str) -> None:
    response = api_client.delete_user(email)
    assert response.status_code in (204, 404), (
        f"Failed to clean up test user {email}: HTTP {response.status_code}"
    )


def create_unique_user(api_client: ApiClient, payload: dict[str, Any]) -> dict[str, Any]:
    response: requests.Response = api_client.create_user(payload)
    assert response.status_code == 201
    assert_user_values(response, payload)
    return payload


def load_schema() -> dict[str, Any]:
    with (ROOT / "specs" / "sdet_challenge_api.yaml").open() as source:
        return yaml.safe_load(source)


def extract_schema(
    spec: dict[str, Any], path: str, method: str, status_code: int
) -> dict[str, Any]:
    try:
        response_block = spec["paths"][path][method.lower()]["responses"][str(status_code)]
        schema = deepcopy(response_block["content"]["application/json"]["schema"])

        if "components" in spec:
            schema["components"] = deepcopy(spec["components"])

        return schema
    except KeyError as e:
        raise ValueError(
            f"Schema not found for {method.upper()} {path} ({status_code}). Missing key: {e}"
        ) from e
