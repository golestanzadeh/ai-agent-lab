import pytest
from agent_lab.owner_exception_notification import *

class TransportStub:
    def __init__(self): self.calls=[]
    def send(self,**kwargs): self.calls.append(kwargs); return "receipt-safe"
class FailingTransport:
    def send(self,**kwargs): raise RuntimeError("provider down")
class LedgerStub:
    def __init__(self): self.reserved=set(); self.completed=[]
    def reserve(self,**kwargs):
        if kwargs["event_identity"] in self.reserved: return "DEDUPLICATED"
        self.reserved.add(kwargs["event_identity"]); return "RESERVED"
    def complete(self,**kwargs): self.completed.append(kwargs)

def activation(**changes):
    data=dict(event=ACTIVATION_EVENT,event_identity="ACTIVATION-20261005",destination_reference=DESTINATION_REFERENCE,subject=ACTIVATION_SUBJECT,body=ACTIVATION_BODY)
    data.update(changes); return NotificationRequest(**data)

def test_activation_is_exact_and_single():
    transport=TransportStub(); ledger=LedgerStub(); result=send_once(activation(),transport=transport,ledger=ledger)
    assert result["status"] == "SENT_AND_CONFIRMED" and len(transport.calls)==1
    assert send_once(activation(),transport=transport,ledger=ledger)["status"] == "DEDUPLICATED"
    assert len(transport.calls)==1

@pytest.mark.parametrize("changes",[
    {"destination_reference":"arbitrary@example.invalid"},
    {"attachments":("tax.pdf",)},
    {"subject":"arbitrary"},
    {"body":"taxpayer data"},
])
def test_activation_variants_fail_closed(changes):
    with pytest.raises(NotificationError): validate(activation(**changes))

def test_routine_event_is_ineligible():
    with pytest.raises(NotificationError): validate(activation(event="PACKAGE_PASS"))

def test_operational_event_rejects_free_form_content():
    with pytest.raises(NotificationError,match="operational message mismatch"):
        validate(activation(event="HUMAN_REQUIRED",subject="tax",body="private"))

@pytest.mark.parametrize("event_identity",[
    "Steuer-ID: 12 345 678 901\nBank: DE00PRIVATE",
    "contains whitespace",
    "lowercase",
    "X" * 97,
])
def test_event_identity_rejects_free_form_or_sensitive_content(event_identity):
    with pytest.raises(NotificationError,match="event is not eligible"):
        validate(activation(event_identity=event_identity))

def test_transport_exception_is_durably_completed_failed():
    ledger=LedgerStub()
    with pytest.raises(NotificationError,match="transport failed"):
        send_once(activation(),transport=FailingTransport(),ledger=ledger)
    assert ledger.completed[0]["result"] == "FAILED"
