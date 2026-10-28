# Upstream synchronization and Git workflow

This fork preserves the full upstream Git history. `origin` is our fork, `upstream` is official Frappe. Helpdesk `main` is the stable baseline even though the upstream repository's default branch is `develop`.

```bash
git remote -v
# origin    https://github.com/Kellybrackets/helpdesk.git
# upstream  https://github.com/frappe/helpdesk.git
```

A fresh clone only creates `origin`. Add the official remote once:

```bash
git remote add upstream https://github.com/frappe/helpdesk.git
git fetch upstream
```

## Branches

- `main`: upstream stable application, without evaluation customizations.
- `dev`: development environment, demo data and team integration branch.
- `feature/*`: focused changes based on `dev`, merged through reviewed pull requests.

Never force-push shared branches or rewrite upstream history. Keep the evaluation scripts/docs in separate commits from future product customizations.

## Update safely

Start with a clean working tree and back up the site, files and current `.env` securely. Record the previous commit and dependency pins. Read upstream release notes and review migration/dependency changes before updating.

```bash
git status --short
git fetch origin
git fetch upstream
git switch main
git merge --ff-only upstream/main
git push origin main

git switch dev
git pull --ff-only origin dev
git switch -c integration/upstream-YYYY-MM-DD
git merge main
```

If the fast-forward on `main` fails, inspect the divergence instead of force-pushing. Keep team customizations on `dev`; if `main` has acquired custom commits, resolve the branch policy explicitly. Resolve integration-branch conflicts one file at a time. Preserve upstream behavior and reapply the smallest necessary local change.

Review `pyproject.toml`, both JS lockfiles, the official Docker initializer, new patches and framework compatibility. Update `docker/versions.env` and image digests intentionally in the integration branch. Existing Bench installations do not automatically switch framework/Telephony revisions on restart. In a disposable update-test environment, update those checkouts to the reviewed pins, install Python/JS dependencies, build assets and migrate the site. Recreating an **expendable** environment from empty volumes is the most reliable test of the pinned setup.

For Helpdesk-only updates on an existing compatible Bench:

```bash
docker compose exec -w /home/frappe/frappe-bench frappe bench setup requirements
make build
make migrate
docker compose restart frappe
make seed
make verify
```

Also test the agent/customer flows in the browser, then repeat the README on a fresh clone and fresh Compose volumes. Update `docs/VERIFICATION.md` with evidence. Push the integration branch, open a PR to `dev`, and merge only after review and passing checks. Publishing `main` does not upgrade the running `dev` checkout.

## Feature branches

```bash
git switch dev
git pull --ff-only origin dev
git switch -c feature/my-change
# edit, run targeted checks, commit, push, open PR to dev
```

Merge updated `dev` into long-lived shared feature branches. Rebasing is optional only for private unpublished work; do not rewrite collaborators' branches. Prefer Frappe extension points or separate apps for substantial future business customizations when appropriate, and contribute generally useful fixes upstream.

Database migrations can be irreversible. Rolling code back is not a database rollback. If an update fails after migration, restore a compatible database/files backup into an isolated environment and validate it before replacing anything valuable.
