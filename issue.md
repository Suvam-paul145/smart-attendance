# Smart Attendance System – Issue Tracker

This document catalogs **30 issues** identified in the Smart Attendance System after a thorough review of the codebase. Issues are grouped into three difficulty tiers: **Hard (H-01 – H-10)**, **Moderate (M-01 – M-10)**, and **Easy (E-01 – E-10)**. Each issue includes a clear problem description and an expected solution.

---

## Table of Contents

- [Hard Issues (H-01 – H-10)](#hard-issues)
- [Moderate Issues (M-01 – M-10)](#moderate-issues)
- [Easy Issues (E-01 – E-10)](#easy-issues)

---

## Hard Issues

---

### H-01 · Replace Trivial Face Embeddings with Deep-Learning Model

**Problem Description**

The ML service (`server/ml-service/app/ml/face_encoder.py`) generates face embeddings by converting a face crop to 96 × 96 greyscale pixels, flattening the array, and applying L2 normalisation. This naive approach produces low-quality, non-discriminative feature vectors that yield high false-positive and false-negative rates, especially under variations in lighting, angle, or partial occlusion. The cosine-similarity thresholds (`ML_CONFIDENT_THRESHOLD = 0.50`, `ML_UNCERTAIN_THRESHOLD = 0.60`) are arbitrary and not backed by any evaluation on real data.

**Expected Solution**

Replace the pixel-flattening encoder with a pre-trained deep-learning face embedding model:

1. Integrate **FaceNet** (via `facenet-pytorch`) or **InsightFace** (`insightface` library) to generate 128D or 512D embeddings that are robust to pose and illumination changes.
2. Keep the existing `FaceEncoder` interface (`encode_face(image) → np.ndarray`) so no other code needs to change.
3. Evaluate accuracy on a held-out dataset; document False Acceptance Rate (FAR) and False Rejection Rate (FRR) in `server/ml-service/README.md`.
4. Tune confidence thresholds empirically and store them in `server/ml-service/app/core/constants.py`.
5. Add unit tests in `server/ml-service/tests/test_face_encoder.py` that assert embedding dimensionality and cosine distance for identical versus different faces.

---

### H-02 · Implement Liveness / Anti-Spoofing Detection

**Problem Description**

The attendance marking flow captures a webcam snapshot and attempts to match every detected face against the enrolled student database. There is no check for whether the faces in the frame belong to live persons. An attacker can hold a printed photograph or display a student's picture on a mobile screen in front of the webcam to fraudulently mark attendance. The entire security model of the system is undermined by this gap.

**Expected Solution**

Add a liveness detection step before matching:

1. Integrate a lightweight passive liveness model such as **MiniVGG** or a depth-map estimator, or use **challenge–response** (e.g., blink detection via MediaPipe Face Mesh landmark tracking).
2. Expose a new internal function `is_live(face_crop: np.ndarray) → bool` in `server/ml-service/app/ml/`.
3. Call `is_live()` for each detected face in the `batch_match` route and return a `liveness: false` flag for spoofed faces instead of marking them present.
4. Make liveness checking configurable via an env variable (`ML_LIVENESS_CHECK=true/false`) so it can be disabled during development/testing.
5. Document the anti-spoofing strategy in `server/ml-service/README.md` and add integration tests simulating still-photo attacks.

---

### H-03 · Build a Full CI/CD Pipeline with GitHub Actions

**Problem Description**

The `.github/workflows/` directory is empty. There are no automated workflows for testing, linting, security scanning, Docker image building, or deployment. Every pull request merges without any programmatic quality gate. This makes it trivially easy to introduce regressions, security vulnerabilities, or broken builds into the main branch.

**Expected Solution**

Create the following GitHub Actions workflow files:

1. **`ci.yml`** – Triggered on every push and pull request:
   - Matrix test Python 3.10 / 3.11 / 3.12 against `server/backend-api` and `server/ml-service` using `pytest`.
   - Matrix test Node 18 / 20 against `frontend` using `vitest` (or Jest).
   - Run ESLint on the frontend and `ruff` + `black --check` on Python code.
   - Fail the workflow if any step exits non-zero.
2. **`security.yml`** – Weekly or on push:
   - Run `bandit -r server/` for Python security issues.
   - Run `npm audit --audit-level=high` in `frontend/`.
   - Scan for hardcoded secrets with `gitleaks`.
3. **`docker-build.yml`** – On merge to `main`:
   - Build `backend-api`, `ml-service`, and `frontend` Docker images.
   - Push tagged images to GitHub Container Registry (GHCR).
4. **`deploy.yml`** – On tag push (`v*`):
   - Deploy to a staging environment using environment secrets.
5. Add a branch-protection rule on `main` requiring all CI checks to pass before merging.

---

### H-04 · Implement Comprehensive Automated Test Suite

**Problem Description**

Backend test coverage is effectively 0%: there are no pytest files under `server/backend-api/`. The ML service has two rudimentary test scripts (`test_detection.py`, `test_opencv.py`) that are not connected to any test runner. The frontend has no configured test tool (no `vitest`/`jest`, no `@testing-library/react`). This means bugs in critical paths — authentication, attendance marking, face matching — can go undetected indefinitely.

**Expected Solution**

1. **Backend API** (`server/backend-api/`):
   - Add `pytest`, `httpx`, `pytest-asyncio`, and `mongomock` (or `pytest-mongo`) to `requirements-dev.txt`.
   - Write tests for every route in `app/api/routes/`: auth (register, login, OAuth), students (profile, face upload), attendance (mark, confirm), teacher-settings (subjects, schedule).
   - Use `TestClient` from `fastapi.testclient` for route-level tests and mock MongoDB with `mongomock` for unit tests.
   - Target ≥ 80 % line coverage, enforced by `pytest --cov=app --cov-fail-under=80`.

2. **ML Service** (`server/ml-service/`):
   - Convert existing ad-hoc scripts to proper `pytest` tests.
   - Add tests for face detection, encoding, and matching with synthetic images generated by `Pillow`.
   - Test edge cases: blank image, image with no face, image with multiple faces.

3. **Frontend** (`frontend/`):
   - Install `vitest`, `@testing-library/react`, and `msw` (Mock Service Worker).
   - Add component tests for `MarkAttendance`, `Dashboard`, `StudentDashboard`, and form components.
   - Add API mock tests for `src/api/` modules.
   - Add a `test` script to `package.json` and configure `vite.config.js` for `vitest`.

---

### H-05 · Implement Redis Caching Layer

**Problem Description**

Every request to the backend hits MongoDB directly with no caching. High-traffic operations such as loading the teacher dashboard (which aggregates attendance across all subjects and students), fetching student lists, and building analytics data execute full collection scans on every page load. As data grows, response times will degrade linearly. There is also no caching for face embeddings, meaning each attendance-marking session re-fetches all student embeddings from the database.

**Expected Solution**

1. Add `redis` and `fastapi-cache2` (or `aiocache`) to `server/backend-api/requirements.txt`.
2. Configure a Redis connection in `server/backend-api/app/core/config.py` using `REDIS_URL` from the environment.
3. Apply caching decorators to expensive service functions:
   - `get_dashboard_stats()` – 60 s TTL.
   - `get_subject_students()` – 30 s TTL, invalidated on student add/remove.
   - `get_student_embeddings_for_subject()` – 5 min TTL, invalidated on face upload.
4. Add a Redis health check to the `/health` endpoint.
5. Add `redis` to `docker-compose.yml` (see H-08) as a dependency service.
6. Document cache keys and invalidation strategy in `server/backend-api/README.md`.

---

### H-06 · Implement JWT Refresh Tokens and Token Revocation

**Problem Description**

The system issues a single JWT access token on login with no refresh token mechanism. Once issued, a token is valid until it expires — there is no way to revoke it (e.g., on logout, password change, or account compromise). The default session secret falls back to the hardcoded string `"kuch-to12hai-mujhse-raita"` if `SECRET_KEY` is not set in the environment, making all tokens trivially forgeable in development setups accidentally used in production.

**Expected Solution**

1. Generate two tokens on login:
   - **Access token** (short-lived, 15 min) signed with `SECRET_KEY`.
   - **Refresh token** (long-lived, 7 days) stored as a hashed value in MongoDB collection `refresh_tokens`.
2. Add a `POST /auth/refresh` endpoint that accepts the refresh token (via HTTP-only cookie or request body), validates it against the database, and issues a new access token.
3. Add a `POST /auth/logout` endpoint that deletes the refresh token document, effectively revoking the session.
4. Remove the hardcoded fallback secret from `server/backend-api/app/core/config.py`; raise a startup error if `SECRET_KEY` is not set.
5. Add a TTL index on `refresh_tokens.expires_at` so MongoDB automatically cleans up expired documents.
6. Write unit tests covering token issuance, refresh, expiry, and revocation.

---

### H-07 · Add Real-Time WebSocket Support for Attendance Marking

**Problem Description**

Attendance marking is currently a two-step HTTP polling flow: the teacher captures an image, sends a `POST /api/attendance/mark` request, waits for synchronous ML processing, then manually calls `POST /api/attendance/confirm`. If the ML service is slow (MediaPipe model load, large class size), the teacher's browser hangs with no incremental feedback. There is no way for the frontend to receive live updates as each face is matched.

**Expected Solution**

1. Add a WebSocket endpoint `WS /ws/attendance/{session_id}` to `server/backend-api/app/api/routes/attendance.py` using FastAPI's native `WebSocket` support.
2. When a teacher initiates an attendance session, the backend:
   - Accepts the WebSocket connection.
   - Sends a `{"status": "processing", "matched": [], "pending": N}` message immediately.
   - Streams incremental match results as the ML service returns them (per-face).
   - Sends a final `{"status": "complete", "matched": [...], "unmatched": [...]}` message.
3. Update the frontend `MarkAttendance` page to open a WebSocket connection and render matched students in real time as messages arrive.
4. Implement connection management (ping/pong keep-alive, clean disconnection on page close).
5. Add integration tests using `websockets` library to simulate a client and assert the message sequence.

---

### H-08 · Create Docker Compose Orchestration for All Services

**Problem Description**

The repository requires manual setup of three separate services (backend API, ML service, frontend dev server) plus external dependencies (MongoDB, optionally Redis). Individual `Dockerfile`s exist but there is no `docker-compose.yml` to wire them together. A new developer must manually start each service in the correct order, configure environment variables, and ensure ports do not conflict. This drastically increases onboarding friction and makes it impossible to reproduce the full stack in CI.

**Expected Solution**

Create a `docker-compose.yml` at the repository root:

```yaml
services:
  mongo:        # MongoDB with a named volume
  redis:        # Redis for caching (H-05)
  backend-api:  # FastAPI backend, depends_on: [mongo, redis]
  ml-service:   # FastAPI ML service, depends_on: [mongo]
  frontend:     # Vite dev server (or Nginx for prod build)
```

Requirements:
1. Use `depends_on` with `condition: service_healthy` and define `healthcheck` for MongoDB (`mongosh --eval 'db.runCommand("ping")'`) and Redis (`redis-cli ping`).
2. Populate all environment variables from a single root `.env` file (generated from `env.example`).
3. Mount `server/backend-api` and `server/ml-service` as volumes in development mode so hot-reload works.
4. Add a `docker-compose.prod.yml` override that uses multi-stage production builds and disables hot-reload.
5. Update `README.md` with a "Quick Start" section: `cp env.example .env && docker-compose up --build`.

---

### H-09 · Implement Fine-Grained Role-Based Access Control (RBAC)

**Problem Description**

The current access-control model has only two roles: `teacher` and `student`. Authorization is enforced by checking `current_user.role` inside individual route functions — often inconsistently — with no centralised permission registry. A teacher can call student-only endpoints if they know the URL, and there is no audit log of privileged operations. As the system grows (e.g., admin role, department head), adding new roles will require editing every affected route.

**Expected Solution**

1. Define a `Permission` enum in `server/backend-api/app/core/permissions.py` with granular actions: `MARK_ATTENDANCE`, `VIEW_OWN_ATTENDANCE`, `MANAGE_SUBJECTS`, `MANAGE_STUDENTS`, `VIEW_REPORTS`, `ADMIN_ALL`.
2. Create a `ROLE_PERMISSIONS` dict mapping each role to its set of permissions.
3. Write a FastAPI dependency `require_permission(permission: Permission)` that reads the current user's role, looks up permissions, and raises `HTTP 403` if the permission is missing.
4. Replace all ad-hoc role checks in route files with `Depends(require_permission(...))`.
5. Add an `admin` role with `ADMIN_ALL` permission, protected by an environment variable `ADMIN_SECRET` used during registration.
6. Create an audit log collection in MongoDB that records every write operation (who, what endpoint, timestamp, result).
7. Add tests asserting that forbidden routes return 403 for the wrong role.

---

### H-10 · Implement ML Model Performance Tracking and Adaptive Thresholds

**Problem Description**

There is no mechanism to measure or track the real-world accuracy of the face-matching system. The confidence thresholds (`ML_CONFIDENT_THRESHOLD`, `ML_UNCERTAIN_THRESHOLD`) are hard-coded constants with no evaluation baseline. Teachers have no way to know how many false matches occurred in past sessions. Without feedback data, the thresholds cannot be tuned and model quality cannot be monitored over time.

**Expected Solution**

1. Add a MongoDB collection `attendance_feedback` where teachers can flag incorrect matches (false positives) or missed students (false negatives) after reviewing an attendance session.
2. Expose `POST /api/attendance/{session_id}/feedback` to record corrections.
3. Build an offline analysis script `server/ml-service/scripts/evaluate_thresholds.py` that:
   - Reads `attendance_feedback` records.
   - Re-runs matching at a range of threshold values.
   - Computes Precision, Recall, F1 for each threshold.
   - Outputs a report and recommends optimal thresholds.
4. Add a `/api/ml/metrics` endpoint (teacher-only) that returns aggregate accuracy statistics: total sessions, confirmed correct, flagged incorrect, FAR, FRR.
5. Store threshold changes in a `model_config_history` collection with timestamps so rollback is possible.
6. Display a "Recognition Accuracy" card on the teacher dashboard using the `/api/ml/metrics` data.

---

## Moderate Issues

---

### M-01 · Add API Rate Limiting to Prevent Abuse

**Problem Description**

No rate limiting is applied to any API endpoint. The `POST /auth/login` endpoint can be brute-forced indefinitely. The `POST /api/attendance/mark` endpoint, which triggers expensive ML inference, can be flooded with requests. The ML service itself has no authentication and is directly reachable on port 8001, meaning any client on the network can send arbitrary payloads to the face-matching routes.

**Expected Solution**

1. Add `slowapi` to `server/backend-api/requirements.txt`.
2. Configure a `Limiter` in `server/backend-api/app/core/` using Redis as the backend (falling back to in-memory for development).
3. Apply limits:
   - `POST /auth/login` → 10 req / min per IP.
   - `POST /auth/register` → 5 req / min per IP.
   - `POST /api/attendance/mark` → 30 req / min per teacher.
   - All other endpoints → 100 req / min per user.
4. Return `HTTP 429 Too Many Requests` with a `Retry-After` header when the limit is exceeded.
5. Add an `X-API-Key` header requirement to all ML service routes, validated against an env variable `ML_API_KEY`; reject requests without a valid key with `HTTP 401`.
6. Document the rate limits in the API reference section of `README.md`.

---

### M-02 · Add HTTP Security Headers Middleware

**Problem Description**

The FastAPI backend does not set any security-related HTTP response headers. Browsers connecting to the frontend are therefore exposed to clickjacking (missing `X-Frame-Options`), reflected XSS attacks (missing `Content-Security-Policy`), protocol downgrade attacks (missing `Strict-Transport-Security`), and MIME sniffing attacks (missing `X-Content-Type-Options`). The CORS configuration uses a hardcoded list of origins rather than reading from environment variables.

**Expected Solution**

1. Add `secure` (or implement a custom Starlette middleware class) to `server/backend-api/requirements.txt`.
2. Register middleware in `server/backend-api/app/main.py` that adds the following headers to every response:
   - `Strict-Transport-Security: max-age=63072000; includeSubDomains`
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `X-XSS-Protection: 1; mode=block`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Content-Security-Policy: default-src 'self'; ...` (configured per env).
3. Move the CORS `allow_origins` list to an env variable `CORS_ORIGINS` (comma-separated) read in `app/core/config.py`.
4. Write a test that sends a request to any endpoint and asserts all required headers are present.

---

### M-03 · Add MongoDB Indexes for Performance

**Problem Description**

No indexes are defined on any MongoDB collection. As the number of attendance records, students, and subjects grows, queries will degrade to full collection scans (O(n)). Critical query patterns that currently lack indexes include: looking up attendance records by `subject_id + date`, finding students by `email`, fetching all subjects for a `teacher_id`, and retrieving face embeddings by `student_id`.

**Expected Solution**

1. Create `server/backend-api/app/db/indexes.py` with an async function `create_indexes(db)`.
2. Define the following indexes:
   - `users`: unique index on `email`; index on `role`.
   - `students`: index on `user_id`; index on `subject_ids`.
   - `subjects`: index on `teacher_id`; index on `student_ids`.
   - `attendance_records`: compound index on `(subject_id, date)`; index on `student_id`.
   - `refresh_tokens` (H-06): TTL index on `expires_at`.
3. Call `await create_indexes(db)` during application startup in `main.py` (inside the `lifespan` context).
4. Add a comment in `indexes.py` explaining each index and the query it optimises.
5. Write a test that connects to a test database and asserts the expected indexes exist on each collection.

---

### M-04 · Implement Structured JSON Logging with Correlation IDs

**Problem Description**

Logging throughout the application is ad-hoc: some modules use `print()`, others use Python's `logging` module at the `DEBUG` level, and some operations log nothing at all. There are no request correlation IDs, making it impossible to trace a single request across the backend API and ML service logs. In a production environment this makes debugging incidents extremely difficult.

**Expected Solution**

1. Add `structlog` (or `python-json-logger`) to both `server/backend-api/requirements.txt` and `server/ml-service/requirements.txt`.
2. Configure structured JSON logging in both `main.py` files, outputting fields: `timestamp`, `level`, `service`, `correlation_id`, `method`, `path`, `status_code`, `duration_ms`, `user_id`.
3. Add a middleware to both services that:
   - Reads an `X-Correlation-ID` request header (or generates a UUID if absent).
   - Attaches it to the request state.
   - Includes it in every log line emitted during that request.
   - Returns it in the response as `X-Correlation-ID`.
4. Replace all `print()` calls and bare `logging.debug()` calls with structured logger calls.
5. Update `docker-compose.yml` (H-08) to label logs with the service name for aggregation.

---

### M-05 · Implement API Versioning

**Problem Description**

All backend routes are mounted without a version prefix (`/auth`, `/students`, `/api/attendance`). This means any breaking change to the API immediately affects all clients. There is no way to deprecate an old endpoint while rolling out a new version. The `nem-web/smart-attendance` parent repository is a public open-source project that may be consumed by external integrations that would break silently.

**Expected Solution**

1. Create an `APIRouter` with prefix `/api/v1` in `server/backend-api/app/api/v1/__init__.py`.
2. Move all existing routers (`auth`, `students`, `attendance`, `teacher_settings`) under this new versioned router.
3. Mount the versioned router in `main.py`: `app.include_router(v1_router, prefix="/api/v1")`.
4. Add redirect middleware that maps legacy paths (e.g., `/auth/login` → `/api/v1/auth/login`) with a `301 Moved Permanently` response and logs a deprecation warning.
5. Update `frontend/src/api/` axios base URLs to point to `/api/v1/`.
6. Update `README.md` API documentation to reflect the new versioned paths.

---

### M-06 · Add Pagination to All List Endpoints

**Problem Description**

List endpoints (e.g., student list, attendance records, subject list) use `cursor.to_list(length=500)` — a hardcoded upper limit that loads up to 500 documents into memory per request. With a growing institution this will: (a) cause memory pressure on the server, (b) send unnecessarily large JSON payloads to the frontend, and (c) eventually silently truncate results when counts exceed 500.

**Expected Solution**

1. Define a reusable `PaginationParams` dependency in `server/backend-api/app/schemas/pagination.py`:
   ```python
   class PaginationParams(BaseModel):
       page: int = Field(1, ge=1)
       page_size: int = Field(20, ge=1, le=100)
   ```
2. Define a generic `PaginatedResponse[T]` response schema with fields: `items`, `total`, `page`, `page_size`, `total_pages`.
3. Update all service functions that return lists to accept `skip` and `limit` derived from `PaginationParams` and use `collection.count_documents()` for the total.
4. Update every affected route to use `Depends(PaginationParams)` and return `PaginatedResponse`.
5. Update the frontend API clients and list components to support pagination controls (page selector, next/previous buttons).
6. Write tests asserting correct page boundaries, total counts, and edge cases (empty page, last page).

---

### M-07 · Resolve N+1 Query Problem in Attendance Marking

**Problem Description**

In `server/backend-api/app/services/attendance.py`, when processing the ML service's batch-match result, the code iterates over each matched student and issues a separate MongoDB query to fetch the corresponding user document (name, email). For a class of 40 students, this generates 40 sequential queries. This pattern is a classic N+1 problem and increases attendance marking latency proportionally with class size.

**Expected Solution**

1. Identify all occurrences of per-student user lookups in `attendance.py` (and any similar patterns in other service files).
2. Replace them with a single aggregation or bulk `find` query:
   - Collect all `student_id` values from the ML result first.
   - Execute one `db.users.find({"_id": {"$in": student_ids}})` query.
   - Build an in-memory dict `{student_id: user_doc}` for O(1) lookups in the result-processing loop.
3. Apply the same pattern to any other list-processing code that performs per-item lookups (e.g., building subject student lists with user info).
4. Write a performance test using `mongomock` that asserts the number of database calls does not exceed a fixed bound regardless of result size.

---

### M-08 · Validate Environment Configuration at Startup

**Problem Description**

Required environment variables (e.g., `MONGODB_URL`, `SECRET_KEY`, `CLOUDINARY_*`, `BREVO_API_KEY`, `GOOGLE_CLIENT_ID`) are read lazily throughout the codebase. If a variable is missing, the application starts successfully but crashes only when the first request that needs that variable is handled — which may be minutes or hours after deployment. There is also no validation that the values conform to expected formats (e.g., `MONGODB_URL` must be a valid connection string).

**Expected Solution**

1. Use Pydantic `BaseSettings` (already partially used in `core/config.py`) with all required fields declared without defaults so that Pydantic raises a `ValidationError` at import time if any required variable is absent.
2. For optional variables (e.g., Google OAuth is optional), use `Optional[str] = None` and add a startup warning log if the value is absent.
3. Add validators using `@field_validator` for:
   - `MONGODB_URL` – must start with `mongodb://` or `mongodb+srv://`.
   - `SECRET_KEY` – must be at least 32 characters.
   - `CLOUDINARY_URL` – must start with `cloudinary://`.
4. Test startup failure by temporarily unset required variables in a pytest fixture and assert that `ValidationError` is raised before any route is registered.
5. Update `env.example` to mark required vs optional variables clearly with comments.

---

### M-09 · Add React Error Boundaries and Improve Frontend Error Handling

**Problem Description**

The React frontend has no error boundaries. An unhandled JavaScript exception in any component — for example a failed API call returning unexpected data, or a null reference during face detection rendering — will crash the entire page and display a blank white screen to the user with no recovery path. Loading and error states are also missing or inconsistently implemented across pages.

**Expected Solution**

1. Create a reusable `ErrorBoundary` class component in `frontend/src/components/ErrorBoundary.jsx` that:
   - Catches render errors via `componentDidCatch`.
   - Displays a friendly error card with a "Reload Page" button.
   - Optionally reports the error to a monitoring service (e.g., Sentry).
2. Wrap each top-level page component in `App.jsx` (or the router) with `<ErrorBoundary>`.
3. Audit all React Query `useQuery` / `useMutation` hooks and ensure every one has an `onError` handler that shows a toast notification (use MUI `Snackbar` or `react-hot-toast`).
4. Add skeleton loaders (MUI `Skeleton`) for the Dashboard stats cards, student list, and attendance table while data is loading.
5. Add a global Axios response interceptor in `frontend/src/api/` that catches 401 responses and redirects to the login page, and catches 5xx errors and shows a generic "Server error" toast.

---

### M-10 · Fix Inconsistent and Bare `except` Clauses in Backend

**Problem Description**

Several backend service and route files use bare `except:` or overly broad `except Exception as e:` clauses that silently swallow errors. For example, in `server/backend-api/app/services/attendance.py` and ML route handlers, exceptions are caught, a generic error message is returned, and the original exception is not logged with its traceback. This makes debugging failures in production nearly impossible and can mask data integrity issues.

**Expected Solution**

1. Audit all `try/except` blocks in `server/backend-api/app/` and `server/ml-service/app/`.
2. Replace bare `except:` with specific exception types (e.g., `except httpx.HTTPError`, `except pymongo.errors.PyMongoError`).
3. For any `except Exception as e:` that is intentionally broad, add `logger.exception("Descriptive message", exc_info=e)` to capture the full traceback in the log.
4. Define custom exception classes in `server/backend-api/app/core/exceptions.py` (e.g., `MLServiceError`, `FaceMatchingError`, `StudentNotFoundError`) and raise them from service functions.
5. Register FastAPI exception handlers in `main.py` for each custom exception class, returning standardised JSON error responses with `error_code`, `message`, and `detail` fields.
6. Add tests that assert the correct HTTP status code and error shape is returned for each custom exception.

---

## Easy Issues

---

### E-01 · Remove Hardcoded Fallback Secret Key

**Problem Description**

In `server/backend-api/app/core/config.py`, the `SECRET_KEY` setting falls back to the hardcoded string `"kuch-to12hai-mujhse-raita"` when the environment variable is not set. If a developer accidentally deploys without setting `SECRET_KEY`, all JWTs are signed with this publicly known secret, allowing any attacker who reads the source code to forge valid tokens.

**Expected Solution**

1. Remove the default value from the `SECRET_KEY` field in the `Settings` class so that Pydantic raises a `ValidationError` on startup if it is missing.
2. Add a comment in `env.example` explaining that `SECRET_KEY` must be generated with `openssl rand -hex 32` and must not be committed.
3. Add a `.env.example` pre-commit hook check (or CI step) that rejects any commit where `SECRET_KEY` contains the known weak default.

---

### E-02 · Fix CORS Configuration to Use Environment Variables

**Problem Description**

The `CORSMiddleware` in `server/backend-api/app/main.py` has `allow_origins` hardcoded to a list of local development URLs. Deploying the backend to a different domain requires manually editing the source code, which is error-prone and not suitable for a multi-environment deployment strategy.

**Expected Solution**

1. Add a `CORS_ORIGINS` variable to `server/backend-api/app/core/config.py` as a `List[str]` parsed from a comma-separated env variable (e.g., `CORS_ORIGINS=https://app.example.com,https://staging.example.com`).
2. Replace the hardcoded `allow_origins` list in `main.py` with `settings.CORS_ORIGINS`.
3. Add `CORS_ORIGINS=http://localhost:5173,http://localhost:3000` to `env.example` as the default development value.
4. Validate that `allow_credentials=True` is only used when origins are not `["*"]` (a common misconfiguration).

---

### E-03 · Add `Content-Type` and File Size Validation to All Upload Endpoints

**Problem Description**

File upload endpoints (`POST /students/me/face-image`, `POST /api/teacher-settings/avatar`, `POST /api/teacher-settings/schedule`) check file size in some places but not all, and none consistently validate that the uploaded `Content-Type` matches the actual file magic bytes. A malicious user can upload a PHP or Python script with a `.jpg` extension, potentially causing issues in downstream processing.

**Expected Solution**

1. Create a utility function `validate_upload(file: UploadFile, allowed_mime_types: list[str], max_bytes: int)` in `server/backend-api/app/core/utils.py`.
2. Inside the function:
   - Read the first 512 bytes of the file to detect the MIME type using `python-magic`.
   - Raise `HTTP 415 Unsupported Media Type` if the detected type is not in `allowed_mime_types`.
   - Raise `HTTP 413 Content Too Large` if `file.size` exceeds `max_bytes`.
   - Seek the file back to position 0 after validation so callers can read the full content.
3. Call `validate_upload()` at the start of every upload route handler.
4. Add `python-magic` to `server/backend-api/requirements.txt`.
5. Write unit tests for the utility covering valid files, oversized files, and mismatched MIME types.

---

### E-04 · Replace All `print()` Calls with Proper Logger Calls

**Problem Description**

Across both `server/backend-api/` and `server/ml-service/`, many debugging `print()` statements were left in the code after development. In a production deployment these clutter `stdout`, are not controllable by log level, do not include timestamps or context, and cannot be aggregated by log management systems.

**Expected Solution**

1. Run `grep -r "print(" server/` to enumerate all occurrences.
2. For each `print()` call, replace it with the appropriate `logging` call (`logger.debug()`, `logger.info()`, or `logger.warning()`) using the module-level logger: `logger = logging.getLogger(__name__)`.
3. Set the global log level from an env variable `LOG_LEVEL` (default `INFO`) in both `main.py` files.
4. Verify no `print()` calls remain by adding a CI lint step: `grep -r "print(" server/ && exit 1 || exit 0`.

---

### E-05 · Add Descriptive `README` Section for Troubleshooting Common Issues

**Problem Description**

The `README.md` covers installation and feature descriptions but provides no troubleshooting guidance. New contributors and self-hosted deployers routinely encounter the same errors: MediaPipe installation failures on certain OS/Python versions, MongoDB connection refused, Cloudinary credentials not recognised, and Google OAuth redirect URI mismatch. Without documentation, each person must debug from scratch.

**Expected Solution**

Add a **Troubleshooting** section to `README.md` that covers at minimum:

1. **MediaPipe install fails on Python 3.13+** – Note that `mediapipe==0.10.9` is yanked; recommend Python ≤ 3.11 or using the `mediapipe-silicon` package on Apple Silicon.
2. **MongoDB connection refused** – Check that `MONGODB_URL` is set and that `mongod` is running; provide the `docker run` command for a quick local MongoDB.
3. **Google OAuth `redirect_uri_mismatch`** – Explain how to add `http://localhost:8000/auth/google/callback` to the Google Cloud Console authorised redirect URIs.
4. **Cloudinary upload fails** – Confirm all three `CLOUDINARY_*` variables are set; show how to get them from the Cloudinary dashboard.
5. **CORS errors in browser** – Explain `CORS_ORIGINS` env variable and how to verify the frontend URL is included.

---

### E-06 · Document MongoDB Collection Schema

**Problem Description**

There is no documentation of the MongoDB collection schemas used by the system. Collections such as `users`, `students`, `subjects`, `attendance_records`, and any others are implied only by reading the Pydantic models and database query code. This makes onboarding new contributors and database administrators unnecessarily hard, and increases the risk of schema drift across environments.

**Expected Solution**

Create `server/backend-api/DATABASE_SCHEMA.md` that documents every collection:

1. Collection name, purpose, and estimated read/write ratio.
2. A table of fields: field name, BSON type, required/optional, description, example value.
3. Which fields have indexes and what type (unique, compound, TTL).
4. Relationships to other collections (e.g., `students.user_id` → `users._id`).
5. Link to the corresponding Pydantic model file in `app/schemas/` for each collection.

---

### E-07 · Fix Hardcoded `to_list(length=500)` Query Limits

**Problem Description**

Throughout the MongoDB query code in `server/backend-api/app/db/` and service files, `cursor.to_list(length=500)` is used as the default way to materialise query results. This silently truncates results beyond 500 documents (for example, if an institution has more than 500 students in a subject) and loads up to 500 documents into memory even when only a few are needed.

**Expected Solution**

1. Search for all occurrences of `to_list(length=` in `server/backend-api/`.
2. For endpoints that genuinely need all results (e.g., fetching all student embeddings for attendance marking), replace with an appropriate explicit limit constant defined in `app/core/constants.py` (e.g., `MAX_STUDENTS_PER_SUBJECT = 1000`) with a comment explaining the rationale.
3. For endpoints that return data to the frontend, replace with paginated queries (see M-06).
4. Add a log warning when the number of returned documents equals the limit (indicating possible truncation).

---

### E-08 · Add Input Sanitisation for User-Supplied Text Fields

**Problem Description**

User-supplied text fields — such as student names, subject names, and schedule descriptions — are stored in MongoDB without sanitisation beyond Pydantic type validation. While MongoDB is not vulnerable to SQL injection, stored data can be reflected in API responses and rendered in the React frontend without HTML-encoding, creating a potential stored XSS vector if the frontend ever renders raw HTML strings.

**Expected Solution**

1. Add `bleach` to `server/backend-api/requirements.txt`.
2. Create a `sanitise_text(value: str) -> str` helper in `app/core/utils.py` that calls `bleach.clean(value, tags=[], strip=True)` to strip all HTML tags.
3. Apply `sanitise_text` as a `@field_validator` on all `str` fields in Pydantic request schemas that accept free text (name fields, description fields, schedule titles).
4. On the frontend, ensure all user-supplied content rendered in JSX uses React's default text interpolation (`{variable}`, not `dangerouslySetInnerHTML`) — audit all components for `dangerouslySetInnerHTML` usage.

---

### E-09 · Add Accessibility (a11y) Attributes to Frontend Components

**Problem Description**

The React frontend does not include ARIA labels, roles, or keyboard navigation support for interactive elements. The webcam capture button, face detection overlay, attendance confirmation dialog, and navigation menu are inaccessible to users relying on screen readers or keyboard-only navigation. This violates WCAG 2.1 AA guidelines.

**Expected Solution**

1. Run `npx axe-cli` (or install `@axe-core/react` in development mode) against the main pages and capture the full list of violations.
2. Address at minimum the following:
   - Add `aria-label` to all icon-only buttons (e.g., the webcam capture button, theme toggle, close icons).
   - Add `role="alert"` to error and success notification components.
   - Ensure all form inputs have an associated `<label>` element (or `aria-label`).
   - Add `alt` text to all `<img>` elements, including student avatar images.
   - Ensure the attendance confirmation modal traps focus and can be closed with `Escape`.
3. Add `eslint-plugin-jsx-a11y` to `frontend/package.json` devDependencies and configure it in `.eslintrc` to enforce a11y rules automatically.

---

### E-10 · Add a `/health` Endpoint That Verifies Downstream Connectivity

**Problem Description**

The ML service exposes a `GET /health` endpoint, but the backend API does not have one (or it exists but only returns a static `{"status": "ok"}` without actually checking downstream dependencies). Container orchestrators (Kubernetes, Docker Compose with `healthcheck`) and load balancers need a health endpoint that reports `unhealthy` when MongoDB is unreachable, the ML service is down, or Redis (H-05) is unavailable — so that traffic is not routed to a broken instance.

**Expected Solution**

1. Add or update `GET /api/v1/health` in `server/backend-api/app/api/routes/health.py`:
   - Ping MongoDB with `await db.command("ping")` — report `"mongo": "ok"` or `"mongo": "error"`.
   - Ping the ML service with `GET http://ml-service:8001/health` via httpx — report `"ml_service": "ok"` or `"ml_service": "error"`.
   - Optionally ping Redis with `await redis.ping()` — report `"redis": "ok"` or `"redis": "error"`.
2. Return `HTTP 200` with `{"status": "healthy", "checks": {...}}` if all checks pass, or `HTTP 503` with `{"status": "degraded", "checks": {...}}` if any check fails.
3. Ensure the endpoint does not require authentication (needed by infrastructure).
4. Add a Docker Compose `healthcheck` that calls `curl -f http://localhost:8000/api/v1/health || exit 1`.
5. Write a test that mocks a failed MongoDB ping and asserts the endpoint returns 503.

---

*Last reviewed: March 2026 | Repository: Suvam-paul145/smart-attendance*
