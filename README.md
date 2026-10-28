# Frappe Helpdesk — development and evaluation fork

This is our internal development/evaluation fork of **Frappe Helpdesk**, maintained by Vati's engineering team. It preserves the official application and Git history. The evaluation tooling lives on `dev`; `main` stays aligned with the official stable branch.

**Upstream:** https://github.com/frappe/helpdesk

**Our fork:** https://github.com/Kellybrackets/helpdesk

**Baseline:** Helpdesk 1.31.0, upstream `main` at `7d7e394e7571fbdbdda04a65a279566b0ac9ce7f`.

The original project is copyright Frappe Technologies and contributors and licensed under [AGPL-3.0](LICENSE). See the [original README](docs/UPSTREAM_README.md) and [official documentation](https://docs.frappe.io/helpdesk).

## Requirements

- Git 2.x; Docker Engine/Desktop with Compose v2 (tested versions are recorded in [verification](docs/VERIFICATION.md)).
- Python 3.9+ on the host for the credential generator and HTTP verification script; `make` is convenient but optional.
- A working Internet connection for GitHub, PyPI, npm, and Docker image downloads on the first start.
- Recommended: at least 8 GB available to Docker and 15 GB free disk; initial dependency installation can take a while.
- Host Node, Yarn, MariaDB, Redis and Bench are **not required**. The pinned Bench image provides Python, Node, Yarn and Bench. Framework and Telephony commits are pinned in `docker/versions.env`; JS dependencies use the upstream lockfiles.

## First-time setup

```bash
git clone --branch dev https://github.com/Kellybrackets/helpdesk.git
cd helpdesk
git remote add upstream https://github.com/frappe/helpdesk.git
python3 scripts/configure_dev.py
docker compose up -d
docker compose logs -f --tail=100 frappe
```

Wait for `bench start` to report that the web server is listening. Exit the log viewer with Ctrl-C, then:

```bash
make seed
make verify
```

`docker compose up -d` starts initialization in the background; it does not mean initialization has finished. Use `docker compose ps -a` and the logs to confirm readiness. `make seed` can be repeated: existing demo records are preserved, including developer edits and passwords.

| Interface | URL |
| --- | --- |
| Agent desk | http://helpdesk.localhost:8300/helpdesk/tickets |
| Customer portal | http://helpdesk.localhost:8300/helpdesk/my-tickets |
| Public knowledge base | http://helpdesk.localhost:8300/helpdesk/kb-public |
| Login | http://helpdesk.localhost:8300/login |
| Framework Desk | http://helpdesk.localhost:8300/app |

Port 8300 avoids an existing local application on port 8000. HTTP, Socket.IO (9300), and optional Vite (8083) bind only to `127.0.0.1`; MariaDB and Redis are not exposed on the host. Browsers normally resolve `*.localhost` automatically. If yours does not, add `127.0.0.1 helpdesk.localhost` to your hosts file. CLI checks use `127.0.0.1` and an explicit site header, so they do not require DNS changes.

## Local credentials

Open the ignored `.env` file locally. `ADMIN_PASSWORD` is the password for `Administrator`; `DEMO_PASSWORD` is shared by the fake demo users. Passwords are generated per checkout, never committed. The generator preserves an existing `.env` and writes new files with mode 0600.

| Persona | Username |
| --- | --- |
| Administrator | `Administrator` |
| Support Admin | `support.admin@helpdesk.example.test` |
| Tier 1 Agent | `tier1@helpdesk.example.test` |
| Tier 2 Agent | `tier2@helpdesk.example.test` |
| Technical Support Agent | `technical@helpdesk.example.test` |
| Service Manager | `manager@helpdesk.example.test` |
| Customer manager | `customer1@cedar.example.test` |
| Customer member | `customer2@cedar.example.test` |

There are also `customer1`–`customer4` accounts at `copper.example.test`, `cloudline.example.test`, `meadow.example.test`, and `maple.example.test`. Use a separate browser profile/private window for customer testing. Changing `.env` after initialization does not reset existing site or user passwords.

## Demo contents

- Five agents, three teams and their native assignment rules.
- Twenty customer users and contacts across five fictional organizations: finance, retail, telecom, public services and advisory.
- Fifty `[DEMO-001]`–`[DEMO-050]` tickets across four priorities and four native statuses: Open, Replied, Resolved and Closed. Replied appears as Awaiting Response to customers.
- Native ticket types, category tags, assignments, internal comments, agent/customer replies and resolution notes. Demo timestamps span roughly four weeks.
- Two example SLA policies, a service calendar, four saved replies and ten published knowledge-base articles.
- Urgent examples are routed to Demo Escalations with a tighter SLA. This demonstrates a manual escalation process and native routing; it does not introduce a custom escalation engine.

The seeder is `helpdesk/demo/seed.py`, invoked with:

```bash
docker compose exec -T -w /home/frappe/frappe-bench frappe \
  bench --site helpdesk.localhost execute helpdesk.demo.seed.run
```

It requires Administrator, `developer_mode`, `allow_demo_seed`, `mute_emails`, and a `DEMO_PASSWORD` environment variable. These are configured by the Docker initializer. It does not delete records. Stable natural keys prevent duplicates. Existing fixture records are left unchanged; delete/rebuild an expendable site if you need a complete reset. Synthetic conversation dates are explicitly backdated; this is demonstration history, not an audit log of real events. Upstream's welcome ticket and draft article remain present alongside the fixtures.

## Daily workflow

```bash
make up         # configure if needed, then start containers
make logs       # application logs
make shell      # shell in the Bench directory
make seed       # add missing demo fixtures
make build      # rebuild Helpdesk frontend after edits
make migrate    # apply schema/patch changes after updating code
make verify     # live HTTP checks, including ticket mutations
make down       # stop containers; preserve site/database volumes
```

The checkout is mounted at `/home/frappe/frappe-bench/apps/helpdesk`. Python code is used directly; compiled frontend assets are served by Bench. For frontend hot reload, open a second terminal:

```bash
docker compose exec -w /home/frappe/frappe-bench/apps/helpdesk/desk frappe \
  yarn dev --host 0.0.0.0
```

Then visit `http://helpdesk.localhost:8083/helpdesk`. Keep Bench running for API requests, assets and realtime events. The normal 8300 URL serves the built frontend. Frappe UI derives its internal Vite port as `HTTP_PORT + 80` (8380 by default). If you change `HTTP_PORT`, set `VITE_INTERNAL_PORT` in `.env` to that sum; `VITE_PORT` is the separate host-facing port.

The official minimal Docker example remains in `docker/docker-compose.yml` and `docker/init.sh` for reference. Use the root `compose.yaml` for this fork: it provides persistent Bench storage, mounts this checkout, pins dependencies, generates credentials and isolates ports.

## Safety, persistence and troubleshooting

This is a local evaluation environment. Outgoing email is muted and Helpdesk email workflows are disabled; no SMTP, OAuth, API tokens or real customer data are configured. Telephony is installed as an upstream dependency without a provider account. Do not use these demo accounts or the development server in production.

- `.env`, `.dev/`, database dumps, logs and generated assets are ignored. Never commit site configurations, credentials, production data or private keys.
- Named volumes hold the database, installed apps and site files. Ordinary `docker compose down` preserves them. `docker compose down -v` **permanently deletes this project's database and Bench volumes**; use it only to reset an expendable evaluation environment.
- Do not delete `.env` while retaining the database volume. Its root password must match the initialized database.
- If initialization exits, read `docker compose logs --tail=150 frappe`, fix the reported cause, and run `docker compose up -d` again. A `.bench-ready` marker is written only after app installation/configuration succeeds.
- Restarting does not silently upgrade apps or migrate schemas. Follow [UPSTREAM.md](docs/UPSTREAM.md).
- Ports can be changed in `.env` before first initialization. For an existing Bench, also update `webserver_port`, `socketio_port`, site `host_name`, and regenerate its Procfile, then restart.
- To back up: `docker compose exec -w /home/frappe/frappe-bench frappe bench --site helpdesk.localhost backup --with-files`. Backups inside the Bench volume must be copied to a secure location before deleting that volume.

## Engineering documentation

- [Architecture and request/data flow](docs/ARCHITECTURE.md)
- [Where to explore and change code](docs/DEVELOPER_GUIDE.md)
- [Safe upstream updates and branch workflow](docs/UPSTREAM.md)
- [Verification results and limitations](docs/VERIFICATION.md)
