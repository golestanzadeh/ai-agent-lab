import pytest

from agent_lab.google_drive_mutation import (
    GoogleDriveMutationAdapter,
    GoogleDriveMutationError,
    GoogleDriveMutationScopeError,
)


class Request:
    def __init__(self, fn):
        self._fn = fn

    def execute(self):
        return self._fn()


class FakeFiles:
    def __init__(self):
        self.parents = {"obj-1": "source", "obj-2": "source"}
        self.trashed = set()
        self.list_queries = []
        self.update_calls = []
        self.force_update_response = None
        self.fail_update = False

    def list(self, **kwargs):
        self.list_queries.append(dict(kwargs))
        q = kwargs["q"]
        assert " in parents and trashed = false" in q
        parent = q.split("'", 2)[1]

        def result():
            files = [
                {"id": obj, "parents": [p], "trashed": obj in self.trashed}
                for obj, p in sorted(self.parents.items())
                if p == parent and obj not in self.trashed
            ]
            return {"files": files}

        return Request(result)

    def get(self, **kwargs):
        object_id = kwargs["fileId"]

        def result():
            if object_id not in self.parents:
                raise RuntimeError("missing")
            parent = self.parents[object_id]
            parents = parent if isinstance(parent, list) else [parent]
            return {
                "id": object_id,
                "parents": parents,
                "trashed": object_id in self.trashed,
            }

        return Request(result)

    def update(self, **kwargs):
        self.update_calls.append(dict(kwargs))
        object_id = kwargs["fileId"]
        new_parent = kwargs["addParents"]
        old_parent = kwargs["removeParents"]

        def result():
            if self.fail_update:
                raise RuntimeError("provider failure")
            if self.parents[object_id] != old_parent:
                raise RuntimeError("provider old parent mismatch")
            self.parents[object_id] = new_parent
            if self.force_update_response is not None:
                return dict(self.force_update_response)
            return {"id": object_id, "parents": [new_parent], "trashed": False}

        return Request(result)


class FakeDrive:
    def __init__(self):
        self._files = FakeFiles()

    def files(self):
        return self._files


def test_list_children_is_explicit_parent_scoped_only():
    drive = FakeDrive()
    adapter = GoogleDriveMutationAdapter(drive_service=drive)
    assert adapter.list_children("source") == ("obj-1", "obj-2")
    assert len(drive._files.list_queries) == 1
    assert drive._files.list_queries[0]["q"] == "'source' in parents and trashed = false"
    assert "name" not in drive._files.list_queries[0]["q"]


def test_get_parent_requires_exactly_one_parent():
    drive = FakeDrive()
    drive._files.parents["obj-1"] = ["source", "other"]
    adapter = GoogleDriveMutationAdapter(drive_service=drive)
    with pytest.raises(GoogleDriveMutationScopeError, match="exactly one parent"):
        adapter.get_parent("obj-1")


def test_guarded_move_preserves_object_id_and_verifies_parent():
    drive = FakeDrive()
    adapter = GoogleDriveMutationAdapter(drive_service=drive)
    adapter.move("obj-1", "target", expected_old_parent_id="source")
    assert drive._files.parents["obj-1"] == "target"
    assert drive._files.update_calls == [
        {
            "fileId": "obj-1",
            "addParents": "target",
            "removeParents": "source",
            "fields": "id,parents,trashed",
        }
    ]
    assert adapter.get_parent("obj-1") == "target"


def test_guarded_move_rejects_stale_old_parent_before_update():
    drive = FakeDrive()
    adapter = GoogleDriveMutationAdapter(drive_service=drive)
    with pytest.raises(GoogleDriveMutationScopeError, match="old parent mismatch"):
        adapter.move("obj-1", "target", expected_old_parent_id="wrong")
    assert drive._files.update_calls == []


def test_provider_failure_is_normalized():
    drive = FakeDrive()
    drive._files.fail_update = True
    adapter = GoogleDriveMutationAdapter(drive_service=drive)
    with pytest.raises(GoogleDriveMutationError, match="parent move failed"):
        adapter.move("obj-1", "target", expected_old_parent_id="source")


def test_mismatched_provider_response_fails_closed():
    drive = FakeDrive()
    drive._files.force_update_response = {
        "id": "different-object",
        "parents": ["target"],
        "trashed": False,
    }
    adapter = GoogleDriveMutationAdapter(drive_service=drive)
    with pytest.raises(GoogleDriveMutationError, match="object mismatch"):
        adapter.move("obj-1", "target", expected_old_parent_id="source")


def test_trashed_object_is_not_mutable():
    drive = FakeDrive()
    drive._files.trashed.add("obj-1")
    adapter = GoogleDriveMutationAdapter(drive_service=drive)
    with pytest.raises(GoogleDriveMutationError, match="identity/state mismatch"):
        adapter.move("obj-1", "target", expected_old_parent_id="source")
    assert drive._files.update_calls == []
