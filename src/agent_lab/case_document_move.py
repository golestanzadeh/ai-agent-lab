"""Case-scoped document movement validation. No live mutation entrypoint."""
from dataclasses import dataclass


class MoveBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class MoveIntent:
    case_id: str
    tax_year: int
    file_id: str
    source_parent_id: str
    destination_parent_id: str
    intent_id: str


def validate_intent(intent, *, authorized_id, case_id, tax_year, file_id, parent_id):
    if not isinstance(intent, MoveIntent):
        raise MoveBlocked('Typed move intent required')
    if not all((intent.case_id, intent.file_id, intent.source_parent_id, intent.destination_parent_id, intent.intent_id)):
        raise MoveBlocked('Incomplete move intent')
    if intent.source_parent_id == intent.destination_parent_id:
        raise MoveBlocked('Same source and destination')
    if intent.intent_id != authorized_id:
        raise PermissionError('Unauthorized intent')
    if (intent.case_id, intent.tax_year, intent.file_id, intent.source_parent_id) != (case_id, tax_year, file_id, parent_id):
        raise MoveBlocked('Stale or cross-case intent')
    return True
