"""
Single source of the Repository instance, injected via FastAPI's Depends
rather than each router constructing its own — this was a real critique
of the earlier version and it's fixed here from the start.
"""
from __future__ import annotations

from orchestrator.storage.repository import Repository

_repo: Repository | None = None


def get_repository() -> Repository:
    global _repo
    if _repo is None:
        _repo = Repository()
    return _repo


def set_repository(repo: Repository) -> None:
    """Test hook — swap in a temp-dir-backed repository."""
    global _repo
    _repo = repo
