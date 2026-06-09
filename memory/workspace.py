"""
Workspace identification for the agentic loop memory system.

Provides stable, cross-clone / cross-worktree workspace IDs based on git remote,
following the proven patterns from the /implement skill's memory.py.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

# --- Regexes for remote canonicalization (adapted from memory.py) ---

_SSH_REMOTE_RE = re.compile(
    r"^(?:ssh://)?(?:[^@]+@)?([\w.-]+)(?::(\d+))?(?::|/)(.+?)(?:\.git)?/?$",
    re.IGNORECASE,
)
_SSH_BARE_REMOTE_RE = re.compile(r"^([\w-]+(?:\.[\w-]+)+):([^/].*)$")
_URL_REMOTE_RE = re.compile(
    r"^[a-z][a-z0-9+.-]*://(?:[^@]+@)?([\w.-]+)(?::\d+)?(/.+)$",
    re.IGNORECASE,
)

# Forges where owner/repo is treated case-insensitively for memory sharing
_CASE_INSENSITIVE_HOSTS = frozenset({"github.com", "gitlab.com", "bitbucket.org"})


def _run_git(*args: str) -> str:
    """Run a git command and return stripped stdout, or empty string on failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=False,
            cwd=Path.cwd(),
        )
        return result.stdout.strip()
    except Exception:
        return ""


def canonicalize_remote(url: str) -> str:
    """
    Normalize a git remote URL to a stable key.

    This ensures the same memory is shared across:
    - Different clones (HTTPS vs SSH)
    - Worktrees of the same repo
    - Repos with or without .git suffix
    """
    url = url.strip().rstrip("/")
    while url.endswith(".git"):
        url = url[:-4]

    m = _SSH_REMOTE_RE.match(url)
    if m:
        host = m.group(1).lower()
        path = m.group(3) or m.group(2)
        if host in _CASE_INSENSITIVE_HOSTS:
            path = path.lower()
        return f"{host}/{path.lstrip('/')}"

    m = _SSH_BARE_REMOTE_RE.match(url)
    if m:
        host = m.group(1).lower()
        path = m.group(2)
        if host in _CASE_INSENSITIVE_HOSTS:
            path = path.lower()
        return f"{host}/{path}"

    m = _URL_REMOTE_RE.match(url)
    if m:
        host = m.group(1).lower()
        path = m.group(2)
        if host in _CASE_INSENSITIVE_HOSTS:
            path = path.lower()
        return f"{host}{path}"

    return url


def get_workspace_id() -> str:
    """
    Return a stable "<safe-name>-<hash12>" identifier for the current workspace.

    Preference order:
    1. Canonicalized git remote.origin.url (best for sharing across clones/worktrees)
    2. Absolute path of the main .git directory (--git-common-dir)
    3. Current working directory (last resort)
    """
    raw_remote = _run_git("config", "--get", "remote.origin.url")
    id_source = canonicalize_remote(raw_remote) if raw_remote else ""

    if not id_source:
        common_dir = _run_git("rev-parse", "--git-common-dir")
        if common_dir:
            try:
                id_source = str(Path(common_dir).resolve(strict=False))
            except OSError:
                id_source = common_dir

    if not id_source:
        try:
            id_source = str(Path.cwd().resolve())
        except (OSError, FileNotFoundError):
            raise RuntimeError(
                "Could not determine workspace ID (no git remote, no .git dir, no usable cwd)"
            )

    digest = hashlib.sha256(id_source.encode("utf-8")).hexdigest()[:12]

    raw_name = id_source.rstrip("/").rsplit("/", 1)[-1]
    if raw_name.endswith(".git"):
        raw_name = raw_name[:-4]
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", raw_name).strip("_.-")
    safe_name = safe_name[:40].rstrip("_.-") or "workspace"

    return f"{safe_name}-{digest}"


def memory_paths(create_dir: bool = False) -> dict[str, Path]:
    """
    Return paths for the agentic loop memory for the current workspace.

    Returns:
        {
            "dir": Path to ~/.grok/agentic-loop-memory/,
            "file": Path to the memory markdown file,
            "lock": Path to the lock file
        }
    """
    try:
        home = Path.home()
    except RuntimeError:
        raise RuntimeError("Could not determine user home directory")

    base = home / ".grok" / "agentic-loop-memory"
    if create_dir:
        base.mkdir(parents=True, exist_ok=True)

    workspace_id = get_workspace_id()
    return {
        "dir": base,
        "file": base / f"{workspace_id}.md",
        "lock": base / f"{workspace_id}.lock",
    }
