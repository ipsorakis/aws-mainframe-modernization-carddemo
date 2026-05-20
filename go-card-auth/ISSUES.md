# Card Authorization Flow Migration to Go — Issue Tracker

> These issues break down the migration of the COBOL card authorization flow
> (`app/app-authorization-ims-db2-mq/`) to a Go microservice. Issues are ordered
> by dependency — earlier issues must be completed before later ones that depend
> on them.

---

## Dependency Graph

```
#1 (Scaffolding)
├── #2 (Data Models) ──────┬── #5 (Decision Logic)
│                          │
├── #3 (DB Schema) ────────┤
│                          ├── #4 (Repository) ──┬── #7 (Processor) ───┐
├── #6 (Messaging) ────────┘                     ├── #8 (Fraud)        │
│                                                ├── #9 (Purge)        │
│                                                └── #10 (REST API) ───┤
│                                                                      │
│                                                     #11 (Wiring) ────┤
│                                                                      │
│                                                     #12 (E2E Tests) ─┤
│                                                                      │
│                                                     #13 (Docker/CI) ─┘
```

**Critical path:** #1 → #2 → #4 → #7 → #11 → #12 → #13
**Parallelizable:** #3 and #6 can start alongside #2; #5 can start once #2 is done; #8, #9, #10 can start once #4 is done.

---

## Issue #1: Project scaffolding and Go module initialization

| Field | Value |
|-------|-------|
| **Labels** | `setup`, `priority/high` |
| **Dependencies** | None |
| **Status** | Open |

### Description

Create the `go-card-auth/` directory structure and initialize the Go module. Set up:

- `go.mod` with module name and Go 1.22+
- Directory skeleton: `cmd/authserver/`, `cmd/purge/`, `internal/model/`, `internal/auth/`, `internal/fraud/`, `internal/purge/`, `internal/store/`, `internal/store/migrations/`, `internal/messaging/`, `api/`
- Add core dependencies: `github.com/shopspring/decimal`, `github.com/jackc/pgx/v5`, `github.com/go-chi/chi/v5`
- Create placeholder `main.go` files in `cmd/authserver/` and `cmd/purge/`
- Add a starter `README.md` explaining the project
- Add a basic `Dockerfile` (multi-stage: build with `golang:1.22`, deploy with distroless)
- Add a `.gitignore` for Go

### Acceptance Criteria

- [ ] `go-card-auth/go.mod` exists with module name and Go 1.22+
- [ ] All directories in skeleton are created
- [ ] Core dependencies added to `go.mod`
- [ ] Placeholder `main.go` in `cmd/authserver/` and `cmd/purge/` compile
- [ ] `README.md` exists with project overview
- [ ] Multi-stage `Dockerfile` present
- [ ] `.gitignore` for Go present

---

## Issue #2: Define Go data models from COBOL copybooks

| Field | Value |
|-------|-------|
| **Labels** | `model`, `priority/high` |
| **Dependencies** | #1 |
| **Status** | Open |

### Description

Translate each COBOL copybook from `app/app-authorization-ims-db2-mq/cpy/` into Go structs in `go-card-auth/internal/model/`. Use `shopspring/decimal` for monetary fields (COMP-3 packed decimals). Include JSON struct tags on all fields.

Files and mappings:

| Go file | Struct | Source copybook | Notes |
|---------|--------|-----------------|-------|
| `request.go` | `AuthRequest` | `CCPAURQY.cpy` | 18 fields: AuthDate, AuthTime, CardNum string, AuthType, CardExpiryDate, MessageType, MessageSource, ProcessingCode int, TransactionAmt decimal, MerchantCategoryCode, AcqrCountryCode, POSEntryMode int, MerchantID, MerchantName, MerchantCity, MerchantState, MerchantZip, TransactionID |
| `response.go` | `AuthResponse` | `CCPAURLY.cpy` | 6 fields: CardNum, TransactionID, AuthIDCode, AuthRespCode, AuthRespReason, ApprovedAmt decimal |
| `authsummary.go` | `AuthSummary` | `CIPAUSMY.cpy` | AcctID, CustID, AuthStatus, AccountStatuses [5]string, CreditLimit decimal, CashLimit decimal, CreditBalance decimal, CashBalance decimal, ApprovedAuthCnt int, DeclinedAuthCnt int, ApprovedAuthAmt decimal, DeclinedAuthAmt decimal |
| `authdetail.go` | `AuthDetail` | `CIPAUDTY.cpy` | 25+ fields including AuthKey composite, fraud status with constants for 'F'/'R', match status with constants for 'P'/'D'/'E'/'M' |
| `account.go` | `Account` | `app/cpy/CVACT01Y.cpy` | Account record |
| `customer.go` | `Customer` | `app/cpy/CVCUS01Y.cpy` | Customer record |
| `cardxref.go` | `CardXref` | `app/cpy/CVACT03Y.cpy` | Card cross-reference |
| `error.go` | `ErrorLogRecord` | `CCPAUERY.cpy` | With severity/subsystem constants |

Also define a `LookupFlags` struct to track lookup outcomes:
```go
type LookupFlags struct {
    CardFound        bool
    AccountFound     bool
    CustomerFound    bool
    CardActive       bool
    AccountOpen      bool
    CardFraud        bool
    MerchantFraud    bool
    InsufficientFunds bool
}
```

Add helper methods: `AuthRequest.ParseCSV(line string)`, `AuthResponse.ToCSV() string`.

### Acceptance Criteria

- [ ] All Go struct files created in `internal/model/`
- [ ] `shopspring/decimal` used for all monetary fields
- [ ] JSON struct tags on every field
- [ ] `LookupFlags` struct defined
- [ ] `ParseCSV` and `ToCSV` helper methods implemented
- [ ] Constants defined for fraud status and match status codes

---

## Issue #3: Database schema and migrations

| Field | Value |
|-------|-------|
| **Labels** | `database`, `priority/high` |
| **Dependencies** | #1 |
| **Status** | Open |

### Description

Create the PostgreSQL schema in `go-card-auth/internal/store/migrations/001_initial.sql` that replaces VSAM, IMS DB, and DB2 stores.

Tables:

| Table | Replaces | Primary Key | Notable columns |
|-------|----------|-------------|-----------------|
| `card_xref` | XREFFILE VSAM | `card_num VARCHAR(16)` | acct_id BIGINT, cust_id BIGINT |
| `accounts` | ACCTFILE VSAM | `acct_id BIGINT` | credit_limit NUMERIC(11,2), curr_bal NUMERIC(11,2), cash_credit_limit NUMERIC(11,2), status VARCHAR(2), ... |
| `customers` | CUSTFILE VSAM | `cust_id BIGINT` | first_name, last_name, ... |
| `auth_summaries` | IMS PAUTSUM0 | `acct_id BIGINT` | cust_id BIGINT, auth_status CHAR(1), credit_limit NUMERIC(11,2), cash_limit NUMERIC(11,2), credit_balance NUMERIC(11,2), cash_balance NUMERIC(11,2), approved_auth_cnt INT, declined_auth_cnt INT, approved_auth_amt NUMERIC(11,2), declined_auth_amt NUMERIC(11,2) |
| `auth_details` | IMS PAUTDTL1 | `(acct_id, auth_date, auth_time)` | card_num VARCHAR(16), ..., match_status CHAR(1), auth_fraud CHAR(1), fraud_rpt_date VARCHAR(8) |
| `auth_frauds` | DB2 AUTHFRDS | — | card_num VARCHAR(16), transaction_id VARCHAR(15), ... — mirror the DDL from `app/app-authorization-ims-db2-mq/ddl/` |

Include appropriate indexes on `card_num`, `acct_id`, and `auth_date`.

### Acceptance Criteria

- [ ] `001_initial.sql` creates all six tables
- [ ] Primary keys match specification
- [ ] Indexes on card_num, acct_id, and auth_date created
- [ ] `auth_frauds` mirrors the DDL from the original DB2 definition
- [ ] NUMERIC precision matches COBOL COMP-3 field sizes

---

## Issue #4: Repository interface and PostgreSQL implementation

| Field | Value |
|-------|-------|
| **Labels** | `database`, `priority/high` |
| **Dependencies** | #2, #3 |
| **Status** | Open |

### Description

Create the data access layer in `go-card-auth/internal/store/`:

**`repository.go`** — Define the `Repository` interface:

```go
type Repository interface {
    FindCardXref(ctx context.Context, cardNum string) (*model.CardXref, error)
    FindAccount(ctx context.Context, acctID int64) (*model.Account, error)
    FindCustomer(ctx context.Context, custID int64) (*model.Customer, error)
    FindAuthSummary(ctx context.Context, acctID int64) (*model.AuthSummary, error)
    UpsertAuthSummary(ctx context.Context, summary *model.AuthSummary) error
    InsertAuthDetail(ctx context.Context, detail *model.AuthDetail) error
    UpsertFraudRecord(ctx context.Context, detail *model.AuthDetail, action string) error
    DeleteExpiredAuthDetails(ctx context.Context, acctID int64, expiryJulianDay int) (int64, error)
    DeleteAuthSummary(ctx context.Context, acctID int64) error
    ListAuthSummaries(ctx context.Context) ([]*model.AuthSummary, error)
    ListAuthDetails(ctx context.Context, acctID int64) ([]*model.AuthDetail, error)
}
```

**`postgres.go`** — Implement the interface using `pgx/v5` connection pool. Use transactions where needed (e.g., `UpsertAuthSummary`). Handle not-found cases by returning a sentinel error or nil.

Include unit tests with a mock implementation and integration tests using `testcontainers-go` with a PostgreSQL container.

### Acceptance Criteria

- [ ] `Repository` interface defined in `repository.go`
- [ ] `postgres.go` implements all interface methods using `pgx/v5`
- [ ] Transactions used where appropriate
- [ ] Not-found cases handled consistently (sentinel error or nil)
- [ ] Mock implementation for unit tests
- [ ] Integration tests with `testcontainers-go` and PostgreSQL

---

## Issue #5: Core authorization decision logic

| Field | Value |
|-------|-------|
| **Labels** | `business-logic`, `priority/high` |
| **Dependencies** | #2 |
| **Status** | Open |

### Description

Implement the approve/decline decision engine in `go-card-auth/internal/auth/decision.go`, porting the logic from `COPAUA0C.cbl` section `6000-MAKE-DECISION` (lines 657–717).

Function signature:

```go
func MakeDecision(req *model.AuthRequest, summary *model.AuthSummary, account *model.Account, flags LookupFlags) *model.AuthResponse
```

Business rules (exact port from COBOL):

1. Default to approve
2. If summary exists: `availableAmt = summary.CreditLimit - summary.CreditBalance`; if `req.TransactionAmt > availableAmt` → decline, reason `4100`
3. If no summary but account found: `availableAmt = account.CreditLimit - account.CurrBal`; if `req.TransactionAmt > availableAmt` → decline, reason `4100`
4. If neither found: decline
5. Response field mapping: `AuthRespCode = "00"` (approved) or `"05"` (declined)
6. Decline reason codes:
   - `3100` — card/account/customer not found
   - `4100` — insufficient funds
   - `4200` — card not active
   - `4300` — account closed
   - `5100` — card fraud
   - `5200` — merchant fraud
   - `9000` — other
7. If approved: `ApprovedAmt = req.TransactionAmt`; if declined: `ApprovedAmt = 0`
8. `AuthRespReason = "0000"` when approved

Write comprehensive unit tests in `decision_test.go` covering every decline path, the approval path, edge cases (zero balance, exact limit), and all 7 reason codes.

### Acceptance Criteria

- [ ] `MakeDecision` function implemented in `decision.go`
- [ ] All 7 decline reason codes handled
- [ ] Approval path sets correct response fields
- [ ] Unit tests cover every decline path
- [ ] Unit tests cover edge cases (zero balance, exact limit)
- [ ] Logic matches COBOL `6000-MAKE-DECISION` section

---

## Issue #6: Messaging layer (consumer/producer interfaces and implementation)

| Field | Value |
|-------|-------|
| **Labels** | `messaging`, `priority/high` |
| **Dependencies** | #1, #2 |
| **Status** | Open |

### Description

Create a pluggable messaging abstraction in `go-card-auth/internal/messaging/`:

**`consumer.go`:**

```go
type Consumer interface {
    Consume(ctx context.Context) (<-chan Message, error)
    Ack(ctx context.Context, msg Message) error
    Close() error
}

type Message struct {
    Body      []byte
    ReplyTo   string
    CorrelID  string
}
```

**`producer.go`:**

```go
type Producer interface {
    Send(ctx context.Context, queueName string, correlID string, body []byte) error
    Close() error
}
```

Provide a **RabbitMQ implementation** using `rabbitmq/amqp091-go`. The default queue names should mirror the COBOL originals:
- `AWS.M2.CARDDEMO.PAUTH.REQUEST` (request queue)
- `AWS.M2.CARDDEMO.PAUTH.REPLY` (reply queue)

Also provide an **in-memory implementation** for testing.

### Acceptance Criteria

- [ ] `Consumer` and `Producer` interfaces defined
- [ ] `Message` struct defined with Body, ReplyTo, CorrelID
- [ ] RabbitMQ implementation using `amqp091-go`
- [ ] Default queue names match COBOL originals
- [ ] In-memory implementation for testing
- [ ] Unit tests for in-memory implementation

---

## Issue #7: Authorization request processor (message loop)

| Field | Value |
|-------|-------|
| **Labels** | `business-logic`, `priority/high` |
| **Dependencies** | #4, #5, #6 |
| **Status** | Open |

### Description

Implement the main processing loop in `go-card-auth/internal/auth/processor.go`, porting `COPAUA0C.cbl` sections `2000-MAIN-PROCESS` through `8000-WRITE-AUTH-TO-DB`.

The `Processor` struct takes a `Repository`, `Consumer`, and `Producer` as dependencies.

Flow for each message:

1. Read CSV message from consumer (comma-delimited, 18 fields — port `2100-EXTRACT-REQUEST-MSG` from lines 354–379)
2. Parse into `AuthRequest` using the CSV parser from Issue #2
3. Look up card xref (`FindCardXref`), then account (`FindAccount`), then customer (`FindCustomer`) — set `LookupFlags` appropriately
4. If card found, read auth summary (`FindAuthSummary`)
5. Call `MakeDecision` from Issue #5
6. Build CSV response string and send via producer to reply queue (using original message's correlation ID)
7. If card was found: update auth summary counters (approved: increment approved count + add amount to credit balance; declined: increment declined count + add amount to declined total) via `UpsertAuthSummary`, and insert auth detail via `InsertAuthDetail`
8. Loop up to configurable process limit (default 500, from `WS-REQSTS-PROCESS-LIMIT`)
9. Log errors using structured logging (`log/slog`)

Write integration tests using the in-memory messaging implementation and a mock repository.

### Acceptance Criteria

- [ ] `Processor` struct with `Repository`, `Consumer`, `Producer` dependencies
- [ ] CSV message parsing matches 18-field format
- [ ] Lookup chain: card xref → account → customer → auth summary
- [ ] `MakeDecision` called with correct parameters
- [ ] Response sent to reply queue with correct correlation ID
- [ ] Auth summary counters updated correctly (approved vs declined)
- [ ] Auth detail inserted for each processed request
- [ ] Process limit configurable (default 500)
- [ ] Structured logging via `log/slog`
- [ ] Integration tests with in-memory messaging and mock repository

---

## Issue #8: Fraud marking service

| Field | Value |
|-------|-------|
| **Labels** | `business-logic`, `priority/medium` |
| **Dependencies** | #4 |
| **Status** | Open |

### Description

Implement fraud marking/unmarking in `go-card-auth/internal/fraud/service.go`, porting `COPAUS2C.cbl`.

```go
type Service struct { repo store.Repository }

func (s *Service) MarkFraud(ctx context.Context, authDetail *model.AuthDetail) error
func (s *Service) RemoveFraud(ctx context.Context, authDetail *model.AuthDetail) error
```

Logic:
- **`MarkFraud`**: Set `AuthFraud = "F"`, `FraudRptDate = today`, call `UpsertFraudRecord` with action `"F"`. Handle duplicate (already marked) gracefully.
- **`RemoveFraud`**: Set `AuthFraud = "R"`, call `UpsertFraudRecord` with action `"R"`.

Write unit tests covering mark, remove, duplicate, and not-found scenarios.

### Acceptance Criteria

- [ ] `Service` struct with `Repository` dependency
- [ ] `MarkFraud` sets fraud flag and date, calls `UpsertFraudRecord`
- [ ] `RemoveFraud` clears fraud flag, calls `UpsertFraudRecord`
- [ ] Duplicate marking handled gracefully
- [ ] Unit tests for mark, remove, duplicate, and not-found

---

## Issue #9: Batch expired authorization purge

| Field | Value |
|-------|-------|
| **Labels** | `batch`, `priority/medium` |
| **Dependencies** | #4 |
| **Status** | Open |

### Description

Implement the expired authorization purge in `go-card-auth/internal/purge/purger.go` and `go-card-auth/cmd/purge/main.go`, porting `CBPAUP0C.cbl`.

`Purger` struct takes a `Repository`.

Logic:

1. Accept `expiryDays` parameter (default 5)
2. List all auth summaries
3. For each summary, list auth details
4. Delete details where `currentJulianDay - authDate >= expiryDays`; adjust summary counters accordingly
5. If summary has `ApprovedAuthCnt == 0 && DeclinedAuthCnt == 0`, delete it
6. Commit/checkpoint periodically (every N records)
7. Log final stats: summaries read, summaries deleted, details read, details deleted

CLI in `cmd/purge/main.go`: accept `--expiry-days` flag, connect to DB, run purge, exit.

Write unit tests with a mock repository.

### Acceptance Criteria

- [ ] `Purger` struct with `Repository` dependency
- [ ] Expiry days configurable (default 5)
- [ ] Expired details deleted based on Julian day comparison
- [ ] Summary counters adjusted after detail deletion
- [ ] Empty summaries deleted
- [ ] Periodic checkpoint/commit logic
- [ ] Final stats logged
- [ ] CLI in `cmd/purge/main.go` with `--expiry-days` flag
- [ ] Unit tests with mock repository

---

## Issue #10: REST API endpoints (replaces CICS screens)

| Field | Value |
|-------|-------|
| **Labels** | `api`, `priority/medium` |
| **Dependencies** | #4, #8 |
| **Status** | Open |

### Description

Implement REST API handlers in `go-card-auth/api/handler.go` using `chi` router, replacing the CICS BMS screens from `COPAUS0C.cbl` and `COPAUS1C.cbl`.

Endpoints:

| Method | Path | Description | Replaces |
|--------|------|-------------|----------|
| `GET` | `/api/v1/accounts/{acctId}/authorizations` | Auth summary + list of auth details for an account | COPAUS0C / transaction CPVS |
| `GET` | `/api/v1/authorizations/{acctId}/{authDate}/{authTime}` | Single auth detail record | COPAUS1C / transaction CPVD |
| `POST` | `/api/v1/authorizations/{acctId}/{authDate}/{authTime}/fraud` | Mark or remove fraud; body: `{"action": "mark"}` or `{"action": "remove"}` | COPAUS2C |
| `GET` | `/health` | Health check endpoint | — |

Response format: JSON with appropriate HTTP status codes (200, 404, 400, 500). Include pagination for the list endpoint.

Write handler tests using `httptest`.

### Acceptance Criteria

- [ ] All four endpoints implemented
- [ ] `chi` router used
- [ ] JSON responses with correct HTTP status codes
- [ ] Pagination for the list endpoint
- [ ] Fraud endpoint accepts mark/remove actions
- [ ] Health check returns 200
- [ ] Handler tests using `httptest`

---

## Issue #11: Application configuration and dependency wiring

| Field | Value |
|-------|-------|
| **Labels** | `setup`, `priority/medium` |
| **Dependencies** | #7, #10 |
| **Status** | Open |

### Description

Wire everything together in `go-card-auth/cmd/authserver/main.go`:

- Load configuration from environment variables (with sensible defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_URL` | — | PostgreSQL connection string |
| `BROKER_URL` | — | RabbitMQ connection string |
| `REQUEST_QUEUE` | `AWS.M2.CARDDEMO.PAUTH.REQUEST` | Request queue name |
| `REPLY_QUEUE` | `AWS.M2.CARDDEMO.PAUTH.REPLY` | Reply queue name |
| `PROCESS_LIMIT` | `500` | Max messages per processing cycle |
| `HTTP_PORT` | `8080` | HTTP server port |
| `LOG_LEVEL` | `info` | Log level |

- Create DB connection pool
- Create messaging consumer and producer
- Create repository, processor, fraud service
- Start HTTP server (API handlers from Issue #10) in a goroutine
- Start message processor loop (from Issue #7) in a goroutine
- Handle graceful shutdown on SIGINT/SIGTERM

### Acceptance Criteria

- [ ] All environment variables loaded with defaults
- [ ] DB connection pool created
- [ ] Messaging consumer and producer created
- [ ] Repository, processor, and fraud service wired
- [ ] HTTP server started in goroutine
- [ ] Message processor loop started in goroutine
- [ ] Graceful shutdown on SIGINT/SIGTERM

---

## Issue #12: Integration and end-to-end tests

| Field | Value |
|-------|-------|
| **Labels** | `testing`, `priority/medium` |
| **Dependencies** | #7, #8, #9, #10, #11 |
| **Status** | Open |

### Description

Create end-to-end integration tests that validate the full card auth flow:

1. Use `testcontainers-go` to spin up PostgreSQL and RabbitMQ
2. Run database migrations
3. Seed test data (card xref, accounts, customers)
4. **Test the full auth approval flow**: send CSV request to request queue → verify CSV response on reply queue → verify `auth_details` and `auth_summaries` tables updated
5. **Test decline flows**: insufficient funds (reason 4100), card not found (3100), card not active (4200), account closed (4300)
6. **Test fraud marking** via REST API
7. **Test batch purge**
8. **Test the REST API** list/detail endpoints
9. Use the MQ message format from `app/app-authorization-ims-db2-mq/README.md` (lines 287–306 for request, 312–318 for response) as test fixtures

### Acceptance Criteria

- [ ] `testcontainers-go` spins up PostgreSQL and RabbitMQ
- [ ] Database migrations run successfully
- [ ] Test data seeded
- [ ] Full approval flow tested end-to-end
- [ ] All decline reason codes tested (3100, 4100, 4200, 4300)
- [ ] Fraud marking tested via REST API
- [ ] Batch purge tested
- [ ] REST API list/detail endpoints tested
- [ ] MQ message format from README used as test fixtures

---

## Issue #13: Dockerfile, CI, and documentation

| Field | Value |
|-------|-------|
| **Labels** | `devops`, `documentation`, `priority/low` |
| **Dependencies** | #11, #12 |
| **Status** | Open |

### Description

Finalize deployment artifacts and documentation:

- **Finalize `Dockerfile`**: multi-stage build (`golang:1.22` builder, `gcr.io/distroless/static` runtime), expose port 8080, health check
- **Add `docker-compose.yml`** with authserver, purge (one-off), PostgreSQL, and RabbitMQ services
- **Update `go-card-auth/README.md`** with:
  - Architecture diagram (message flow, DB, API)
  - Mapping table: COBOL program → Go package/file
  - Configuration reference (all env vars)
  - How to run locally, run tests, build Docker image
  - Migration notes from mainframe message format (CSV over MQ) to the new service
- **Add GitHub Actions CI workflow** (`.github/workflows/go-card-auth.yml`): lint, test, build

### Acceptance Criteria

- [ ] Multi-stage `Dockerfile` finalized with distroless runtime
- [ ] `docker-compose.yml` with all services
- [ ] `README.md` includes architecture diagram
- [ ] `README.md` includes COBOL → Go mapping table
- [ ] `README.md` includes configuration reference
- [ ] `README.md` includes local run/test/build instructions
- [ ] `README.md` includes migration notes
- [ ] GitHub Actions CI workflow in `.github/workflows/go-card-auth.yml`
