"""Closed, content-free failure observations in the existing Kernel audit."""
from __future__ import annotations

from datetime import datetime, timezone


class ProviderConfigurationMissing(RuntimeError):
    pass


MESSAGES = {
    'PROVIDER_CONFIGURATION_MISSING': 'Configure the explicit Gemini credential, then approve one new attempt.',
    'AUTHORIZATION_DENIED': 'Kernel authorization rejected this operation; review the gate or scope.',
    'DOCUMENT_REJECTED': 'The source identity, digest, format or size could not be verified.',
    'PROVIDER_OUTCOME_UNCERTAIN': 'The provider outcome is uncertain. Review before approving a separate attempt.',
    'APPLICATION_ERROR': 'An application error stopped processing. Technical context is retained without document content.',
    'LEGACY_ERROR_CONTEXT_UNAVAILABLE': 'The old failure did not retain its stage or traceback; its cause is not established.',
}


def diagnostic(exc, stage, task, meta):
    from agent_lab.orchestrator_kernel import PermissionDenied
    if isinstance(exc, ProviderConfigurationMissing):
        code = 'PROVIDER_CONFIGURATION_MISSING'
    elif isinstance(exc, PermissionDenied):
        code = 'AUTHORIZATION_DENIED'
    elif stage == 'SOURCE_VERIFICATION':
        code = 'DOCUMENT_REJECTED'
    elif isinstance(exc,(KeyError,TypeError,AttributeError)):
        code = 'APPLICATION_ERROR'
    elif stage == 'PROVIDER_ATTEMPT':
        code = 'PROVIDER_OUTCOME_UNCERTAIN'
    else:
        code = 'APPLICATION_ERROR'
    frames = []
    tb = exc.__traceback__
    while tb is not None and len(frames) < 16:
        # No exception string, source line, locals, provider body or absolute path.
        frames.append({'module': str(tb.tb_frame.f_globals.get('__name__', 'unknown'))[:120],
                       'function': tb.tb_frame.f_code.co_name[:80], 'line': tb.tb_lineno})
        tb = tb.tb_next
    return {
        'document_id': meta['document_id'], 'task_id': task['task_id'],
        'run_id': task['case_context']['run_id'], 'stage': stage, 'error_code': code,
        'safe_message': MESSAGES[code], 'timestamp': datetime.now(timezone.utc).isoformat(),
        'retryable': code == 'PROVIDER_CONFIGURATION_MISSING',
        'recommended_action': 'EXPLICIT_OWNER_SUCCESSOR_APPROVAL',
        'provider_outcome_uncertain': stage == 'PROVIDER_ATTEMPT',
        'exception_type': type(exc).__name__, 'technical_frames': frames,
        'safe_exception_key': (exc.args[0] if isinstance(exc,KeyError) and exc.args and
            exc.args[0] in {'GEMINI_API_KEY','outputs','output_text','steps','fields','id','name','document_id','sha256','model'} else None),
    }


def record(k, task, manifest, value):
    row = k._manifest_row(manifest)
    if row['task_id'] != task['task_id']:
        raise PermissionError('Diagnostic scope mismatch')
    with k._write_scope():
        k._append_event('UI03_DIAGNOSTIC_RECORDED', 'TASK', task['task_id'],
                        task['actor_instance_id'], {'manifest_id': manifest, 'diagnostic': value})


def legacy(document):
    return {'document_id': document['document_id'], 'task_id': document['task_id'],
            'run_id': document['run_id'], 'stage': 'UNKNOWN_LEGACY',
            'error_code': 'LEGACY_ERROR_CONTEXT_UNAVAILABLE',
            'safe_message': MESSAGES['LEGACY_ERROR_CONTEXT_UNAVAILABLE'],
            'timestamp': document.get('finished_at', document['created_at']),
            'retryable': False, 'provider_outcome_uncertain': True,
            'recommended_action': 'REVIEW_OLD_FAILURE_THEN_EXPLICIT_OWNER_SUCCESSOR_APPROVAL'}
