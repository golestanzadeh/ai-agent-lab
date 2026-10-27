from dataclasses import replace

import pytest

from agent_lab.case_number_reservation_policy import (
    ReservationEvidence,
    may_release_number,
)


BASE = ReservationEvidence(
    case_active=False,
    restorable_backup_count=0,
    protected_hold=False,
    pending_operation=False,
    inventory_verified=True,
    original_identity_verified=True,
)


def test_release_only_when_every_condition_passes():
    assert may_release_number(BASE)


@pytest.mark.parametrize("change", [
    {"case_active": True},
    {"restorable_backup_count": 1},
    {"restorable_backup_count": 2},
    {"restorable_backup_count": -1},
    {"protected_hold": True},
    {"pending_operation": True},
    {"inventory_verified": False},
    {"original_identity_verified": False},
    {"restorable_backup_count": None},
    {"restorable_backup_count": "0"},
    {"restorable_backup_count": False},
    {"case_active": None},
    {"protected_hold": None},
])
def test_fail_closed(change):
    assert not may_release_number(replace(BASE, **change))


def test_restored_case_emptied_and_deleted_still_reserved_if_backup_exists():
    assert not may_release_number(replace(BASE, restorable_backup_count=1))


def test_delete_one_of_two_backups_still_reserved():
    assert not may_release_number(replace(BASE, restorable_backup_count=1))


def test_trashed_but_restorable_backup_still_counts():
    assert not may_release_number(replace(BASE, restorable_backup_count=1))


def test_final_backup_removed_but_case_active_still_reserved():
    assert not may_release_number(replace(BASE, case_active=True))
