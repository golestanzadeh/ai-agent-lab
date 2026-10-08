"""Synthetic-only tests; never open live Kernel or identity databases."""
import sqlite3

import pytest

from agent_lab.identity_continuity_authority import (
    IdentityContinuityAuthority,
    IdentityContinuityError,
)


def authority(tmp_path):
    root = tmp_path / "kernel"
    root.mkdir()
    kernel = root / "control.sqlite"
    sqlite3.connect(kernel).close()
    identity_root = tmp_path / "identity"
    identity_root.mkdir()
    return IdentityContinuityAuthority(kernel, identity_root / "identity.sqlite"), kernel


def test_monotonic_head_rejects_rollback(tmp_path):
    control, _ = authority(tmp_path)
    control.initialize("synthetic-case", "h0")
    control.reserve("synthetic-case", 0, "h0", "h1")
    with pytest.raises(IdentityContinuityError):
        control.verify("synthetic-case", 0, "h0")
    control.finalize("synthetic-case", 0, "h1")
    control.verify("synthetic-case", 1, "h1")
    with pytest.raises(IdentityContinuityError):
        control.verify("synthetic-case", 0, "h0")
    control.close()


def test_pending_crash_remains_fail_closed(tmp_path):
    control, kernel = authority(tmp_path)
    control.initialize("synthetic-case", "h0")
    control.reserve("synthetic-case", 0, "h0", "h1")
    control.close()
    reopened = IdentityContinuityAuthority(kernel, tmp_path / "identity" / "identity.sqlite")
    with pytest.raises(IdentityContinuityError):
        reopened.verify("synthetic-case", 0, "h0")
    with pytest.raises(IdentityContinuityError):
        reopened.reserve("synthetic-case", 0, "h0", "h2")
    reopened.close()


def test_rejects_same_custody_root(tmp_path):
    kernel = tmp_path / "control.sqlite"
    sqlite3.connect(kernel).close()
    with pytest.raises(IdentityContinuityError):
        IdentityContinuityAuthority(kernel, tmp_path / "identity.sqlite")
