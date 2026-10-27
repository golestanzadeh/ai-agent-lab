"""Production read validator against separately frozen synthetic contract evidence."""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import threading
from unittest.mock import patch

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from agent_lab.ipc_operational_read import validate_request,validate_response
from agent_lab.ipc_wire_primitives import decode_frame,encode_frame
from agent_lab.c09_pipe_transport import OperationDeadline,PipeDeadlineError
from agent_lab.c09_identity_client import exchange_operational_identity_read,IdentityClientError

V=json.loads((Path(__file__).parents[1]/"fixtures/f07-operational-contract-v1.json").read_text())
KEY=serialization.load_pem_public_key(V["public_key_pem"].encode())
NOW=datetime(2026,1,1,0,0,1)
SCOPE={name:V["vectors"][1]["request"][name] for name in "deployment_id case_id tax_year run_id task_id manifest_id actor_instance_id role_id".split()}


def verify(request):validate_request(request,KEY,expected_scope=SCOPE,now=NOW,expected_key_id="TEST-KERNEL-KEY-1")


@pytest.mark.parametrize("vector",V["vectors"][1:],ids=lambda v:v["name"])
def test_golden_read_compatibility(vector):
    verify(vector["request"]);validate_response(vector["response"],vector["request"])


@pytest.mark.parametrize("vector",V["negative_vectors"],ids=lambda v:v["name"])
def test_hostile_frames_rejected(vector):
    frame=(bytes.fromhex(vector["header_hex"])+bytes.fromhex(vector["byte_hex"])*int(vector["count"])) if vector["kind"]=="wire-repeat" else bytes.fromhex(vector["frame_hex"])
    with pytest.raises((ValueError,InvalidSignature)):
        value=decode_frame(frame)
        if vector["kind"]=="response":validate_response(value,V["vectors"][int(vector["base"])]["request"])
        else:verify(value)


def test_mutation_and_incomplete_scope_fail_before_exchange():
    with pytest.raises(ValueError):verify(V["commit"])
    with pytest.raises(ValueError):validate_request(V["vectors"][1]["request"],KEY,expected_scope={"case_id":"TEST-CASE"},now=NOW,expected_key_id="TEST-KERNEL-KEY-1")


def test_client_correlates_actual_transport_bytes_and_rejects_substitution():
    vector=V["vectors"][1];frame=bytes.fromhex(vector["frame_hex"])
    with patch("agent_lab.c09_pipe_transport.exchange_operational_identity_read",return_value=bytes.fromhex(vector["response_frame_hex"])) as native:
        result=exchange_operational_identity_read(frame,None,KEY,expected_scope=SCOPE,now=NOW,expected_key_id="TEST-KERNEL-KEY-1")
        assert result==vector["response"];assert native.call_count==1
    wrong=deepcopy(vector["response"]);wrong["request_digest"]="sha256:"+"f"*64
    with patch("agent_lab.c09_pipe_transport.exchange_operational_identity_read",return_value=encode_frame(wrong)):
        with pytest.raises(IdentityClientError):exchange_operational_identity_read(frame,None,KEY,expected_scope=SCOPE,now=NOW,expected_key_id="TEST-KERNEL-KEY-1")


def test_deadline_and_cancellation_are_explicit():
    event=threading.Event();deadline=OperationDeadline(.01,event);assert 1<=deadline.milliseconds()<=50
    event.set()
    with pytest.raises(PipeDeadlineError):deadline.milliseconds()
    with patch("agent_lab.c09_pipe_transport.time.monotonic",return_value=100):deadline=OperationDeadline(1)
    with patch("agent_lab.c09_pipe_transport.time.monotonic",return_value=102):
        with pytest.raises(PipeDeadlineError):deadline.milliseconds()


@pytest.mark.parametrize("seconds",[0,-1,6,True,float("nan"),float("inf")])
def test_invalid_deadlines(seconds):
    with pytest.raises(ValueError):OperationDeadline(seconds)


def test_unacknowledged_io_is_retained_and_future_exchanges_halt(monkeypatch):
    import sys
    from types import SimpleNamespace
    import agent_lab.c09_pipe_transport as transport
    class NativeError(Exception):
        winerror=5
    closed=[]
    monkeypatch.setattr(transport,"_halted",threading.Event())
    monkeypatch.setattr(transport,"_quarantined",[])
    monkeypatch.setitem(sys.modules,"pywintypes",SimpleNamespace(OVERLAPPED=lambda:SimpleNamespace(hEvent=None),error=NativeError))
    monkeypatch.setitem(sys.modules,"win32event",SimpleNamespace(CreateEvent=lambda *a:"EVENT",WaitForSingleObject=lambda *a:258,WAIT_OBJECT_0=0))
    monkeypatch.setitem(sys.modules,"win32file",SimpleNamespace(CancelIoEx=lambda *a:None,CloseHandle=closed.append))
    cancellation=threading.Event();cancellation.set()
    with pytest.raises(PipeDeadlineError):transport.overlapped_io("PIPE",lambda ov:(997,b"buffer"),OperationDeadline(1,cancellation))
    assert transport._halted.is_set() and len(transport._quarantined)==1
    assert closed==[]
    with pytest.raises(PipeDeadlineError):transport.exchange_operational_identity_read(b"not-parsed",None)
