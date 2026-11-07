"""Unstarted task disposition regression tests on isolated database copies."""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from agent_lab.orchestrator_kernel import OrchestratorKernel, PermissionDenied, StateTransitionError

ROOT=Path(__file__).resolve().parents[2]
DB=Path(os.environ["LOCALAPPDATA"])/"AI-Tax-Agent"/"Cases"/"orchestrator-kernel.sqlite"
CONTRACT=ROOT/"contracts"/"orchestrator"/"v1"

class TestUnstartedTaskClosure(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"test.sqlite"
        src=sqlite3.connect(DB)
        dst=sqlite3.connect(self.path)
        try:
            src.backup(dst)
        finally:
            src.close()
            dst.close()
        self.k=OrchestratorKernel(self.path,CONTRACT)
        self.ids=[r[0] for r in self.k._connection.execute("SELECT task_id FROM tasks WHERE status='REGISTERED' ORDER BY created_at")]
        self.assertGreaterEqual(len(self.ids),3)
    def tearDown(self):
        self.k.close()
        self.tmp.cleanup()
    def test_expired_and_audit(self):
        self.k.close_unstarted_task(self.ids[0],actor_id="HUMAN_PROJECT_OWNER",authority_reference="owner://test",reason="expired registered intent")
        self.assertEqual(self.k._connection.execute("SELECT status FROM tasks WHERE task_id=?",(self.ids[0],)).fetchone()[0],"EXPIRED")
        self.k.verify_audit_chain()
        with self.assertRaises(StateTransitionError):
            self.k.close_unstarted_task(self.ids[0],actor_id="HUMAN_PROJECT_OWNER",authority_reference="owner://test",reason="replay")
    def test_future_expiry_denied(self):
        with self.assertRaises(StateTransitionError):
            self.k.close_unstarted_task(self.ids[-1],actor_id="HUMAN_PROJECT_OWNER",authority_reference="owner://test",reason="not yet expired")
    def test_nonowner_denied(self):
        with self.assertRaises(PermissionDenied):
            self.k.close_unstarted_task(self.ids[-1],actor_id="AGENT",authority_reference="owner://test",reason="unauthorized",outcome="CANCELLED")
    def test_owner_cancel_audited(self):
        self.k.close_unstarted_task(self.ids[-1],actor_id="HUMAN_PROJECT_OWNER",authority_reference="owner://test",reason="test cancellation",outcome="CANCELLED")
        self.k.verify_audit_chain()
        self.assertEqual(self.k._connection.execute("SELECT status FROM tasks WHERE task_id=?",(self.ids[-1],)).fetchone()[0],"CANCELLED")

if __name__=="__main__":
    unittest.main()
