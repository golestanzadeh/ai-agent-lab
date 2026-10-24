import struct

import pytest

from agent_lab.c09_named_pipe import (
    KERNEL_SID, MAX_FRAME_BYTES, PipeSecurityError, PinnedProcess, ProcessEvidence,
    authorize_connected_kernel, kernel_only_sddl, read_one_canonical_message, verify_process_evidence,
)
from agent_lab.ipc_wire_primitives import encode_frame


PIN = PinnedProcess(KERNEL_SID, r"C:\Program Files\AI-Tax-Agent\AITaxKernel.exe", "sha256:" + "a" * 64)


def evidence(**changes):
    values = dict(sid=PIN.sid, image_path=PIN.image_path, image_sha256=PIN.image_sha256, pid_before=101, pid_after=101)
    values.update(changes); return ProcessEvidence(**values)


def test_exact_actual_peer_evidence_passes_and_sddl_is_kernel_only():
    verify_process_evidence(evidence(), PIN)
    sddl = kernel_only_sddl()
    assert KERNEL_SID in sddl and ";;;BA" not in sddl and ";;;BU" not in sddl


def test_connected_client_authorization_uses_actual_token(monkeypatch):
    monkeypatch.setattr("agent_lab.c09_named_pipe.actual_named_pipe_client_sid", lambda handle: KERNEL_SID)
    authorize_connected_kernel(object())
    monkeypatch.setattr("agent_lab.c09_named_pipe.actual_named_pipe_client_sid", lambda handle: "S-1-5-18")
    with pytest.raises(PipeSecurityError, match="pinned Kernel"):
        authorize_connected_kernel(object())


@pytest.mark.parametrize("change", [
    {"sid": "S-1-5-18"}, {"image_path": r"C:\Temp\AITaxKernel.exe"},
    {"image_sha256": "sha256:" + "b" * 64}, {"pid_after": 102}, {"pid_before": 0},
])
def test_peer_substitution_and_pid_turnover_are_denied(change):
    with pytest.raises(PipeSecurityError): verify_process_evidence(evidence(**change), PIN)


def test_one_canonical_frame_is_accepted():
    frame = encode_frame({"kind": "PING"})
    actual, value = read_one_canonical_message(lambda limit: frame)
    assert actual == frame and value == {"kind": "PING"}


@pytest.mark.parametrize("frame", [b"", struct.pack("<I", 2) + b"{}x", b"x" * (MAX_FRAME_BYTES + 1)], ids=["empty", "trailing", "oversized"])
def test_malformed_trailing_and_oversized_messages_are_denied(frame):
    with pytest.raises(PipeSecurityError): read_one_canonical_message(lambda limit: frame)
