import sqlite3
from threading import RLock
import pytest
from agent_lab.case_document_move import MoveIntent, MoveBlocked, execute_move


class Persistence:
    def __init__(self):
        self._db = sqlite3.connect(':memory:')
        self._db.row_factory = sqlite3.Row
        self._lock = RLock()
        self.owner_id = 'owner'
    def _verify_all(self): pass
    def _verify_anchor(self): pass
    def _authorize(self, owner, case, year):
        if (owner, case, year) != ('owner', 'case', 2025):
            raise PermissionError('scope')


class Files:
    def __init__(self):
        self.parent = 'src'
        self.calls = 0
        self.fail_after_move = False
    def get(self, **kwargs):
        class R:
            def __init__(self, outer): self.outer = outer
            def execute(self): return {'id':'file','parents':[self.outer.parent],'trashed':False}
        return R(self)
    def update(self, **kwargs):
        self.calls += 1
        self.parent = kwargs['addParents']
        if self.fail_after_move: raise RuntimeError('network lost after move')
        class R:
            def execute(self): return {'id':'file'}
        return R()


class Drive:
    def __init__(self): self.f = Files()
    def files(self): return self.f


INTENT = MoveIntent('case',2025,'file','src','dst','intent')
OBS = dict(case_id='case',tax_year=2025,drive_file_id='file',parent_id='src',
           registry_state='PENDING',source_status='ACTIVE',owner_id='owner')


def invoke(p,d,**kw):
    return execute_move(persistence=p,drive=d,intent=INTENT,authorized_id='intent',
                        observed=OBS,verify_folder_scope=kw.get('scope',lambda *a: None),
                        verify_kernel_authority=kw.get('authority',lambda *a: None),
                        reconcile_registry=kw.get('reconcile',lambda *a: None))


def test_move_and_idempotent_retry():
    p=Persistence();d=Drive()
    assert invoke(p,d)['status']=='COMPLETE'
    assert d.f.parent=='dst' and d.f.calls==1
    assert invoke(p,d)['idempotent'] is True and d.f.calls==1


def test_crash_after_drive_move_recovers_without_second_move():
    p=Persistence();d=Drive();d.f.fail_after_move=True
    with pytest.raises(RuntimeError):invoke(p,d)
    assert p._db.execute('SELECT status FROM case_document_move_intent').fetchone()[0]=='PREPARED'
    d.f.fail_after_move=False
    assert invoke(p,d)['status']=='COMPLETE'
    assert d.f.calls==1


def test_wrong_destination_or_authority_never_moves():
    p=Persistence();d=Drive()
    with pytest.raises(PermissionError):
        invoke(p,d,authority=lambda _: (_ for _ in ()).throw(PermissionError('denied')))
    assert d.f.calls==0
    d.f.parent='other'
    with pytest.raises(MoveBlocked):invoke(p,d)
    assert d.f.calls==0


def test_reconciliation_failure_retains_intent():
    p=Persistence();d=Drive()
    with pytest.raises(RuntimeError):
        invoke(p,d,reconcile=lambda _: (_ for _ in ()).throw(RuntimeError('reconcile failed')))
    assert p._db.execute('SELECT status FROM case_document_move_intent').fetchone()[0]=='PREPARED'
    assert invoke(p,d)['status']=='COMPLETE'
    assert d.f.calls==1
