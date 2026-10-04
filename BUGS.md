# Confirmed API defects

Observed through public HTTP requests against the supplied challenge API.
Image: `ghcr.io/danielsilva-loanpro/sdet-interview-challenge:latest`

The [OpenAPI document](tests/specs/sdet_challenge_api.yaml) is the contract.

## BUG-001: Unknown-user GET returns 500 instead of 404

- **Status:** Confirmed.
- **Endpoint:** `GET /{env}/users/{email}`.
- **Affected environments:** `dev` and `prod`.
- **Contract:** `paths./users/{email}.get.responses.'404'`.
- **Expected:** `404` with a JSON `ErrorResponse` when the user does not exist.
- **Actual:** `500` with `{"error":"Internal server error"}`.
- **Severity:** Medium.
- **Impact:** Clients cannot reliably distinguish a missing user from a server failure.

### Steps to reproduce

1. Choose a unique valid email that has not been created, such as
   `sdet-<uuid>@example.com`.
2. Send `GET /dev/users/sdet-<uuid>@example.com` without authentication.
3. Observe `500` instead of `404`.
4. Repeat in `prod`; observe the same result.


## BUG-002: Successful PUT does not persist updated fields

- **Status:** Confirmed.
- **Endpoint:** `PUT /{env}/users/{email}`.
- **Affected environments:** `dev` and `prod`.
- **Contract:** `paths./users/{email}.put`, including response `200: User updated successfully`.
- **Expected:** `200` with the updated user; a subsequent GET retrieves the updated values.
- **Actual:** PUT returns `200` and echoes the new name and age, but GET returns the original values.
- **Severity:** High.
- **Impact:** A successful update silently loses the client's changes.

### Steps to reproduce

1. Send `POST /dev/users` with
   `{"name":"API Test User","email":"sdet-<uuid>@example.com","age":30}`.
   Observe `201`.
2. Send `PUT /dev/users/sdet-<uuid>@example.com` with
   `{"name":"Updated API Test User","email":"sdet-<uuid>@example.com","age":31}`.
   Observe `200` with the updated fields.
3. Send `GET /dev/users/sdet-<uuid>@example.com`.
   Observe the original name `API Test User` and age `30`.
4. Delete the user with `Authentication: <API_TOKEN>`.
5. Repeat in `prod` with a fresh email; observe the same result.


## BUG-003: Dev deletion ignores authentication

- **Status:** Confirmed.
- **Endpoint:** `DELETE /{env}/users/{email}`.
- **Affected environments:** `dev` only; the negative authentication cases pass in `prod`.
- **Contract:** `paths./users/{email}.delete.parameters` and response `401`.
- **Expected:** `401` with a JSON `ErrorResponse` for missing or invalid authentication; the user remains available.
- **Actual:** Missing, malformed, and invalid tokens return `204` with an empty body and delete the user.
- **Severity:** High.
- **Impact:** Users can be deleted without the required credential.

### Steps to reproduce

1. Create a valid user with a fresh email through `POST /dev/users`.
2. Send `DELETE /dev/users/sdet-<uuid>@example.com` without an authentication header.
3. Observe `204`; list the users and confirm the email is absent.
4. Repeat with fresh users and a malformed bearer-style token or an invalid plain token.
   Observe the same result.
5. Repeat in `prod`; observe `401` and confirm the user remains available.
6. Delete remaining users with `Authentication: <API_TOKEN>`.


## BUG-004: POST and PUT accept numeric and boolean names

- **Status:** Confirmed by targeted test runs in both environments.
- **Endpoint:** `POST /{env}/users` and `PUT /{env}/users/{email}`.
- **Affected environments:** `dev` and `prod`.
- **Contract:** `CreateUserRequest.properties.name.type: string`, `UpdateUserRequest.properties.name.type: string`, and each operation's response `400`.
- **Expected:** `400` with a JSON `ErrorResponse` when `name` is a number or boolean.
- **Actual:** For `name: 123` or `name: true`, POST returns `201` and PUT returns `200`; the responses echo the invalid value.
- **Severity:** Medium.
- **Impact:** Invalid field types are accepted, and successful responses violate the `User` schema.

### Steps to reproduce

1. Send `POST /dev/users` with
   `{"name":123,"email":"sdet-<uuid>@example.com","age":30}`.
   Observe `201` with numeric `name: 123`.
2. Create another valid user with a fresh email and a string name.
3. Send PUT to that user's URL with the original email and age, but `name: 123`.
   Observe `200` with numeric `name: 123`.
4. Using fresh emails, repeat the POST and PUT requests with `name: true`.
   Observe `201` and `200`, respectively, with boolean `name: true` in the responses.
5. Delete the created users with `Authentication: <API_TOKEN>`.
6. Repeat in `prod` with fresh emails; observe the same results.


## BUG-005: Non-string email is accepted on POST and causes a server error on PUT

- **Status:** Confirmed by targeted test runs in both environments.
- **Endpoint:** `POST /{env}/users` and `PUT /{env}/users/{email}`.
- **Affected environments:** `dev` and `prod`.
- **Contract:** `CreateUserRequest.properties.email` and `UpdateUserRequest.properties.email` require `type: string` and `format: email`; both operations define response `400`.
- **Expected:** `400` with a JSON `ErrorResponse` when `email` is a number or boolean.
- **Actual:** For `email: 123` or `email: true`, POST returns `201` and echoes the invalid value; PUT returns `500` with `{"error":"Internal server error"}`. The stored email is coerced to `"123"` or `"1"`, respectively.
- **Severity:** Medium.
- **Impact:** Creation persists an invalid email, while updating with the same invalid type reports a server failure instead of a validation error.

### Steps to reproduce

1. Ensure the disposable target collection has no existing user with email `"123"` or `"1"`.
2. Send `POST /dev/users` with
   `{"name":"API Test User","email":123,"age":30}`.
   Observe `201` with numeric `email: 123`.
3. List users; observe the stored email as the string `"123"`.
4. Delete that user through `DELETE /dev/users/123` with `Authentication: <API_TOKEN>`.
5. Repeat the POST with `email: true`. Observe `201` with boolean `email: true`;
   list users and observe stored email `"1"`. Delete it through `DELETE /dev/users/1`
   with `Authentication: <API_TOKEN>`.
6. Create a valid user with a fresh email.
7. Send PUT to the valid user's original URL with
   `{"name":"API Test User","email":123,"age":30}`.
   Observe `500` with `{"error":"Internal server error"}`.
8. Repeat the PUT with `email: true`; observe the same `500` response.
9. Delete the original user with `Authentication: <API_TOKEN>`.
10. Repeat in `prod`; observe the same results.


## BUG-006: POST accepts malformed email addresses

- **Status:** Confirmed by targeted test runs in both environments.
- **Endpoint:** `POST /{env}/users`.
- **Affected environments:** `dev` and `prod`.
- **Contract:** `CreateUserRequest.properties.email.format: email` and `paths./users.post.responses.'400'`.
- **Expected:** `400` with a JSON `ErrorResponse` when the email address is malformed.
- **Actual:** POST returns `201` and stores users with emails `not-an-email`, `@test-user.com`, and `test-user@`.
- **Severity:** Medium.
- **Impact:** Creation persists invalid email addresses, allowing collection responses to violate the documented email format.

### Steps to reproduce

1. Ensure the disposable target collection has no user with the email being tested.
2. Send `POST /dev/users` with
   `{"name":"API Test User","email":"not-an-email","age":30}`.
3. Observe `201` instead of `400`; list users and confirm the invalid email was stored.
4. Delete that user through `DELETE /dev/users/not-an-email` with
   `Authentication: <API_TOKEN>`.
5. Repeat with `@test-user.com` (missing local part) and `test-user@` (missing domain).
   Observe `201` and a stored user for each; delete each user using its URL-encoded email.
6. Repeat in `prod`; observe the same results.


## BUG-007: Duplicate-email POST returns 500 instead of 409

- **Status:** Confirmed by targeted test runs in both environments.
- **Endpoint:** `POST /{env}/users`.
- **Affected environments:** `dev` and `prod`.
- **Contract:** `paths./users.post.responses.'409'` defines `Duplicate email` with a JSON `ErrorResponse`.
- **Expected:** `409` with a JSON `ErrorResponse` when creating a user with an existing user's email.
- **Actual:** The initial POST returns `201`; a second POST with the same payload returns `500` with `{"error":"Internal server error"}`.
- **Severity:** Medium.
- **Impact:** Clients receive a server failure instead of the documented conflict response and cannot reliably identify duplicate emails.

### Steps to reproduce

1. Send `POST /dev/users` with a fresh email:
   `{"name":"API Test User","email":"sdet-<uuid>@example.com","age":30}`.
   Observe `201`.
2. Send another `POST /dev/users` with the identical payload.
3. Observe `500` with `{"error":"Internal server error"}` instead of `409`.
4. Delete the user through `DELETE /dev/users/sdet-<uuid>@example.com` with
   `Authentication: <API_TOKEN>`.
5. Repeat in `prod` with a fresh email; observe the same results.


## BUG-008: Array and scalar JSON request bodies return 500 instead of 400

- **Status:** Confirmed by targeted test runs in both environments.
- **Endpoint:** `POST /{env}/users` and `PUT /{env}/users/{email}`.
- **Affected environments:** `dev` and `prod`.
- **Contract:** Both operations require an `application/json` object request body and define a `400` validation response with a JSON `ErrorResponse`.
- **Expected:** `400` when the request body is a JSON array, string, number, or boolean.
- **Actual:** Both operations return `500` with `{"error":"Internal server error"}` for `[]`, `"user"`, `123`, and `true`.
- **Severity:** Medium.
- **Impact:** Clients receive a server failure for input that should be rejected as invalid, obscuring the cause and inflating server-error metrics.

### Steps to reproduce

1. Send `POST /dev/users` with `Content-Type: application/json` and the raw body
   `[]`. Observe `500` instead of `400`.
2. Repeat with the raw bodies `"user"`, `123`, and `true`. Observe `500` for each.
3. Create a valid user with a fresh email.
4. Send `PUT /dev/users/sdet-<uuid>@example.com` with the same content type and
   each of those four raw bodies. Observe `500` for each; the original user remains unchanged.
5. Delete the user with `Authentication: <API_TOKEN>`.
6. Repeat in `prod` with a fresh user; observe the same results.


## Missing requirement: Changing a user's email on PUT

The OpenAPI document identifies the URL email as the user's primary key, but
also requires an email in the PUT body. It defines a `409` response for a
duplicate email without stating whether the body email may differ from the URL
email, or what should happen to the user record if it does. This includes the
case where the new email belongs to another user. Clarify the expected behavior
before asserting it in an automated test.
