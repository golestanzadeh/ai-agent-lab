"""Fail-closed Owner operational exception notification boundary."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import re
from typing import Protocol

DESTINATION_REFERENCE = "OWNER_CONTROLLED_EXCEPTION_EMAIL_PROTECTED_CONFIG"
ACTIVATION_EVENT = "NOTIFICATION_CHANNEL_ACTIVATION_TEST"
ACTIVATION_SUBJECT = "AI-Tax-Agent — Project Error Notification Channel Activation Test"
ACTIVATION_BODY = """This is an activation test of the authorized AI-Tax-Agent project-error notification channel.

The notification path has been configured and this message verifies real end-to-end delivery.

No taxpayer data or sensitive project information is included.

No action is required."""
EVENT_IDENTITY_PATTERN = re.compile(r"[A-Z0-9][A-Z0-9._:-]{0,95}\Z")

ELIGIBLE_EVENTS = frozenset({
    "HUMAN_REQUIRED", "GOVERNANCE_OR_SAFETY_CONFLICT", "PLAN_OR_ENTITLEMENT_BLOCKED",
    "SCHEDULER_ARM_FAILURE", "UNRECOVERABLE_HOST_RUNTIME_FAILURE", "LONG_LIVED_OWNER_BLOCKER",
    "CURRENT_SUPPORTED_PRODUCT_COMPLETE", "PROJECT_COMPLETE", ACTIVATION_EVENT,
})
EVENT_TEMPLATES = {
    event: (f"AI-Tax-Agent — {event}", f"Operational event: {event}\nReference: {{event_identity}}\nNo taxpayer or tax data is included.")
    for event in ELIGIBLE_EVENTS if event != ACTIVATION_EVENT
}

class NotificationError(RuntimeError): pass

class Transport(Protocol):
    def send(self, *, destination_reference: str, subject: str, body: str) -> str | None: ...

class DurableAttemptLedger(Protocol):
    def reserve(self, *, event_identity: str, event: str, content_sha256: str) -> str: ...
    def complete(self, *, event_identity: str, result: str, provider_receipt_id: str | None) -> None: ...

class KernelNotificationLedger:
    def __init__(self, kernel):
        self.kernel=kernel
    def reserve(self, **kwargs):
        return self.kernel.reserve_notification_attempt(**kwargs)
    def complete(self, **kwargs):
        self.kernel.complete_notification_attempt(**kwargs)

@dataclass(frozen=True)
class NotificationRequest:
    event: str
    event_identity: str
    destination_reference: str
    subject: str
    body: str
    attachments: tuple[str, ...] = ()

def validate(request: NotificationRequest) -> None:
    if request.event not in ELIGIBLE_EVENTS or EVENT_IDENTITY_PATTERN.fullmatch(request.event_identity) is None:
        raise NotificationError("event is not eligible")
    if request.destination_reference != DESTINATION_REFERENCE:
        raise NotificationError("destination is not registered")
    if request.attachments:
        raise NotificationError("attachments are forbidden")
    if request.event == ACTIVATION_EVENT and (request.subject != ACTIVATION_SUBJECT or request.body != ACTIVATION_BODY):
        raise NotificationError("activation message mismatch")
    if request.event != ACTIVATION_EVENT:
        subject, body = EVENT_TEMPLATES[request.event]
        if request.subject != subject or request.body != body.format(event_identity=request.event_identity):
            raise NotificationError("operational message mismatch")
    if len(request.subject) > 160 or len(request.body) > 1200:
        raise NotificationError("message exceeds operational metadata boundary")

def send_once(request: NotificationRequest, *, transport: Transport, ledger: DurableAttemptLedger) -> dict[str, str | bool | None]:
    validate(request)
    content_hash="sha256:"+sha256((request.subject+"\n"+request.body).encode()).hexdigest()
    reservation = ledger.reserve(event_identity=request.event_identity,event=request.event,content_sha256=content_hash)
    if reservation == "DEDUPLICATED":
        return {"status":"DEDUPLICATED","event_identity":request.event_identity}
    if reservation != "RESERVED":
        raise NotificationError("notification retry budget exhausted")
    try:
        receipt = transport.send(destination_reference=request.destination_reference, subject=request.subject, body=request.body)
    except Exception as exc:
        ledger.complete(event_identity=request.event_identity,result="FAILED",provider_receipt_id=None)
        raise NotificationError("notification transport failed") from exc
    status="SENT_DELIVERY_UNCONFIRMED" if receipt is None else "SENT_AND_CONFIRMED"
    ledger.complete(event_identity=request.event_identity,result=status,provider_receipt_id=receipt)
    return {"status":status,
            "event_identity":request.event_identity,"event":request.event,
            "destination_reference":request.destination_reference,"provider_receipt_id":receipt,
            "content_sha256":content_hash,
            "sensitive_data_transmitted":False,"attachment_transmitted":False}
