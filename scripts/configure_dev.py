"""Create private, local-only credentials without overwriting an existing setup."""

import os
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / ".env"
if path.exists():
    print(".env already exists; keeping existing credentials.")
else:
    content = root.joinpath(".env.example").read_text()
    for key in ("DB_ROOT_PASSWORD", "ADMIN_PASSWORD", "DEMO_PASSWORD"):
        content = content.replace(f"{key}=\n", f"{key}={secrets.token_urlsafe(24)}\n")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(content)
    print("Created .env (mode 0600). Credentials are local and ignored by Git.")
