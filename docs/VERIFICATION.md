# Verification

Verified on **2026-10-28** on macOS arm64. The local evaluation application is running; the separate fresh-install test stack was stopped after verification, with its volumes preserved.

## Baseline

- Helpdesk: 1.31.0, `7d7e394e7571fbdbdda04a65a279566b0ac9ce7f` (official `main`).
- Frappe: 15.124.0, `f1cf50cf9bbc641bb015adb7008bf2ea1c8483ab` (`version-15`).
- Telephony: `9447577500a25d242088398157b72c654fa34b20` (`develop`, upstream's available default).
- Docker Engine 29.1.3 / Docker Desktop 4.55.0; Compose 2.40.3.
- Bench image: Python 3.14.7, Node 24.21.0, Yarn 1.22.22, Bench 5.31.0.
- MariaDB 10.11 and Redis 7 images pinned by digest in `compose.yaml`.

## Results

| Check | Result |
| --- | --- |
| Initialization, app installation and compiled frontend | Passed; application, database and Redis healthy; Bench doctor reports a worker online |
| Administrator authentication | Passed through a separate HTTP session |
| Agent interface | Browser login, populated ticket list and ticket detail rendered successfully |
| Agent operations | Browser assignment, reply, private comment and change to Resolved succeeded |
| Customer portal | Browser login, own-ticket list, new ticket submission and follow-up reply succeeded |
| Permissions | HTTP checks confirmed another customer cannot retrieve the test ticket and customer responses exclude private comments |
| Knowledge base | Ten published articles checked through HTTP; categories and article body rendered in the browser |
| Seed | Five agents, twenty customer users/contacts, five companies, fifty demo tickets, three teams, two SLAs, four saved replies and ten published articles |
| Seed repeatability | Second run in both environments created zero additional demo tickets; fifty stable demo subjects remained |
| Historical data | Demo ticket creation and conversation timestamps span several weeks |
| Restart persistence | Restarted the main application container, then passed the complete HTTP smoke check with existing demo data |
| Fresh installation | Separate local clone with the proposed additions, independent credentials and empty named volumes initialized successfully; seed twice and HTTP checks passed on port 8301 |
| Static checks | Python compilation, Black, Ruff, Bash syntax, Compose configuration and Git whitespace checks passed |
| Credentials | Generator preserves existing credentials; `.env` has mode 0600 and is ignored; generated secrets are absent from candidate source files |

The fresh test used the uncommitted candidate files over a clone of the `dev` baseline so validation preceded the requested initial commit. The optional Vite port mapping was subsequently corrected and checked in the main environment: Frappe UI chooses `HTTP_PORT + 80` internally.

## Repeating the checks

Run `make seed` twice and confirm the second run reports zero created demo tickets, then run `make verify`. The HTTP script creates a `[VERIFY]` ticket and checks login, list/detail, assets, assignments, agent/customer replies, private comments, status transitions, customer isolation and published articles using independent sessions. It does not send email or call third-party providers. Its tickets remain available for inspection.

For a clean installation, use a separate checkout and Compose project name with empty volumes. Generate a separate `.env`, choose unused HTTP/Socket.IO/Vite host ports, and set `VITE_INTERNAL_PORT` to `HTTP_PORT + 80`. Follow the README initialization and seed commands, passing the separate project name consistently to Compose.

## Scope and limitations

This validates a local development/evaluation setup, not a production deployment or the complete upstream test suite. External email delivery/ingestion, telephony providers, OAuth and ERP integrations are not configured or exercised. Outgoing email is muted. Frappe emits a MariaDB-version compatibility warning, and the upstream build/worker dependencies emit nonfatal component, bundle-size and deprecation warnings; the checked workflows pass with the pinned versions above.
