"""Wait for GET /users to return 200 and a JSON list before running tests.

The API has no dedicated health endpoint. This script polls the selected
environment until it is ready or the configured timeout expires.
"""

import argparse
import os
import time

import requests


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()

    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    environment = os.getenv("TARGET_ENV", "dev")
    base_url = os.getenv("BASE_URL", "http://localhost:3000").rstrip("/")
    url = f"{base_url}/{environment}/users"

    deadline = time.monotonic() + args.timeout
    last_result = "No response"
    with requests.Session() as session:
        session.trust_env = False
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                # Limit the request timeout to two seconds or the remaining time.
                response = session.get(url, timeout=min(2, remaining))
                if response.status_code == 200 and isinstance(response.json(), list):
                    print(f"API ready: {environment} user collection returned 200 and a JSON array")
                    return 0
                last_result = f"HTTP {response.status_code} or unexpected JSON shape"
            except (requests.RequestException, ValueError) as error:
                last_result = str(error)

            # Wait up to one second before trying again.
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(1, remaining))
    print(f"API not ready after {args.timeout:g}s: {last_result}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
