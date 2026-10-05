# User Management API tests

Pytest end-to-end tests for the challenge API in `dev` and `prod`. Tests use the
[OpenAPI contract](tests/specs/sdet_challenge_api.yaml) as the expected behavior.
Discrepancies are documented in [BUGS.md](BUGS.md).

## Run locally

Requires Python 3.12 and Docker Compose. From the project root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
docker compose up -d

TARGET_ENV=dev python -m scripts.wait_for_api --timeout 60
TARGET_ENV=dev python -m pytest -m e2e

TARGET_ENV=prod python -m scripts.wait_for_api --timeout 60
TARGET_ENV=prod python -m pytest -m e2e
```

The Compose stack runs the API at `http://localhost:3000` and Swagger UI at
`http://localhost:8080`. In Swagger UI, select `/dev` or `/prod` to try requests
against the same API instance used by the tests. Stop and remove the stack with
`docker compose down`; this also removes container-local user data.

## Results

Some tests are marked as expected failures for the defects in [BUGS.md](BUGS.md).
An unexpected pass fails the run so the marker can be reviewed.

The API client logs each request's method, URL, authentication presence, status,
elapsed time, and up to 500 characters of the response body. Pytest captures these
logs with each test, keeping normal output quiet while showing them for failures.
Request bodies and authentication header values are never logged. Request errors
log the exception type before being raised again.

To create an HTML and JUnit report locally, run, for example:

```bash
TARGET_ENV=dev python -m pytest -m e2e \
  --html=reports/dev-report.html --self-contained-html \
  --junitxml=reports/dev-junit.xml
```

The [GitHub Actions workflow](.github/workflows/e2e.yml) runs `dev` and `prod`
in parallel and uploads reports for each environment as artifacts.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `BASE_URL` | `http://localhost:3000` | API address. |
| `TARGET_ENV` | `dev` | API environment (`dev` or `prod`). |
| `API_TOKEN` | `mysecrettoken` | Token for authenticated deletion. |
