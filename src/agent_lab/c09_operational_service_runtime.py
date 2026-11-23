"""Compose existing SCM roles with their authorities; never install or enroll.

Factories are supplied by the governed deployment composition, not requests or
environment variables. SQLite authorities are opened and used on one worker.
"""
from __future__ import annotations

import threading
from agent_lab.c09_service_host import (
    ROLE_BINDINGS, ServiceRole, ServiceHost, ServiceHostError, current_process_sid,
)
from agent_lab.c09_named_pipe import (
    IDENTITY_PIPE, CUSTODIAN_PIPE, MAX_FRAME_BYTES, create_kernel_only_server,
    authorize_connected_kernel,
)
from agent_lab.c09_pipe_transport import OperationDeadline, PipeDeadlineError, overlapped_io


class AuthorityPipeRuntime:
    """One first-instance endpoint, one existing authority, bounded shutdown."""
    def __init__(self, config, authority_factory, *, allowed_case_ids=frozenset(), mutation_pipeline=False,owner_binding=None):
        if config.role not in {ServiceRole.IDENTITY,ServiceRole.KEY_CUSTODIAN}:
            raise ServiceHostError("authority role required")
        name,sid=ROLE_BINDINGS[config.role]
        if owner_binding is not None:
            from agent_lab.option_b_family_binding import BoundOptionBFamily
            if not isinstance(owner_binding,BoundOptionBFamily) or config.role is not ServiceRole.IDENTITY:
                raise ServiceHostError('accepted Option B Identity binding required')
            owner_binding.constructor_ready()
            sid=owner_binding.binding.payload['owner_sid']
        schema='ai-tax-agent.option-b-identity-host/1' if owner_binding is not None else 'ai-tax-agent.c09-service-config/1.0'
        if (config.schema!=schema or
            config.service_name!=name or config.principal_sid!=sid or config.enabled is not True or
            not isinstance(config.deployment_id,str) or not config.deployment_id):
            raise ServiceHostError("closed deployment binding required")
        if not isinstance(allowed_case_ids,frozenset) or any(not isinstance(v,str) or not v or v=="*" for v in allowed_case_ids):
            raise ServiceHostError("explicit case allowlist required")
        if type(mutation_pipeline) is not bool:
            raise ServiceHostError("explicit mutation routing configuration required")
        self._mutation_pipeline=mutation_pipeline
        self._owner_binding=owner_binding
        self._config=config;self._factory=authority_factory;self._cases=allowed_case_ids
        self._stop=threading.Event();self._ready=threading.Event();self._thread=None
        self._error=None;self._handle=None;self._connection_error=None

    def start(self):
        if self._thread is not None:raise ServiceHostError("runtime already started")
        if current_process_sid()!=self._config.principal_sid:
            raise ServiceHostError("actual authority service token required before opening store")
        if self._owner_binding is not None:
            import win32api,win32process
            from pathlib import Path
            from agent_lab.c09_named_pipe import sha256_file
            image=win32process.GetModuleFileNameEx(win32api.GetCurrentProcess(),0)
            expected=self._owner_binding.binding.payload
            if str(Path(image)).casefold()!=str(Path(expected['identity_image_path'])).casefold() or sha256_file(image)!=expected['identity_image_ref']:
                raise ServiceHostError('actual Option B Identity image mismatch')
        pipe=IDENTITY_PIPE if self._config.role is ServiceRole.IDENTITY else CUSTODIAN_PIPE
        self._handle=(create_kernel_only_server(pipe,overlapped=True,kernel_sid=self._config.principal_sid)
                      if self._owner_binding is not None else create_kernel_only_server(pipe,overlapped=True))
        self._thread=threading.Thread(target=self._serve,name=self._config.service_name,daemon=True)
        self._thread.start()
        if not self._ready.wait(6):
            self._stop.set()
            raise ServiceHostError("authority startup did not complete; reconciliation required")
        if self._error is not None:
            self._thread.join(1)
            raise ServiceHostError("authority startup failed closed") from self._error

    def _serve(self):
        import pywintypes
        import win32file
        import win32pipe
        from agent_lab.identity_persistence import IdentityPersistence
        from agent_lab.c09_custodian_operational import OperationalCustodianRuntime
        from agent_lab.c09_identity_dispatch import dispatch_stateful_identity_read
        from agent_lab.ipc_wire_primitives import decode_frame,encode_frame
        authority=None
        try:
            authority=self._factory(self._config)
            if self._config.role is ServiceRole.IDENTITY:
                if not isinstance(authority,IdentityPersistence):raise ServiceHostError("existing Identity authority required")
                logical=authority._logical_row()
                if logical is None or logical["deployment_id"]!=self._config.deployment_id:
                    raise ServiceHostError("explicit matching enrollment required; never initialize here")
            else:
                if not isinstance(authority,OperationalCustodianRuntime) or authority._deployment!=self._config.deployment_id:
                    raise ServiceHostError("matching existing Custodian authority required")
                authority.start()
            self._ready.set()
            while not self._stop.is_set():
                connected=False
                authenticated=False
                try:
                    try:
                        overlapped_io(self._handle,lambda ov:win32pipe.ConnectNamedPipe(self._handle,ov),OperationDeadline(5,self._stop))
                    except pywintypes.error as exc:
                        if exc.winerror!=535:raise
                    connected=True
                    deadline=OperationDeadline(5,self._stop)
                    def read_message(bound):
                        result,count=overlapped_io(self._handle,lambda ov:win32file.ReadFile(self._handle,bound,ov),deadline)
                        return bytes(result[1][:count])
                    # Impersonation uses the last message read by this pipe.
                    # Buffer bounded opaque bytes first; authenticate actual token
                    # and revert before any decoding, signature or domain work.
                    raw=read_message(MAX_FRAME_BYTES+1)
                    if self._owner_binding is None:authorize_connected_kernel(self._handle)
                    else:authorize_connected_kernel(self._handle,kernel_sid=self._config.principal_sid)
                    authenticated=True
                    try:decode_frame(raw)
                    except ValueError:continue  # Wire syntax only; no authority entered.
                    if self._config.role is ServiceRole.IDENTITY:
                        options=dict(allowed_case_ids=self._cases,mutation_pipeline=self._mutation_pipeline)
                        if self._owner_binding is not None:options['kernel_sid']=self._config.principal_sid
                        reply=dispatch_stateful_identity_read(self._handle,lambda bound:raw,authority,**options)
                    else:
                        reply=encode_frame(authority.handle(decode_frame(raw)))
                    _,count=overlapped_io(self._handle,lambda ov:win32file.WriteFile(self._handle,reply,ov),deadline)
                    if count!=len(reply):raise ServiceHostError("partial authority response")
                    # A write completion can precede peer consumption. Wait for
                    # peer close before DisconnectNamedPipe discards queued bytes.
                    try:
                        extra,received=overlapped_io(self._handle,lambda ov:win32file.ReadFile(self._handle,1,ov),deadline)
                        raise ServiceHostError("one request per connection required")
                    except pywintypes.error as exc:
                        if exc.winerror not in (109,232,233):raise
                except PipeDeadlineError:
                    from agent_lab.c09_pipe_transport import _halted
                    if _halted.is_set():raise ServiceHostError("native cancellation not acknowledged; host halted")
                except Exception as exc:
                    from agent_lab.c09_named_pipe import PipeSecurityError
                    from agent_lab.c09_identity_dispatch import IdentityDispatchError
                    self._connection_error=exc
                    if not authenticated and isinstance(exc,PipeSecurityError):continue
                    if isinstance(exc,PermissionError):continue
                    if isinstance(exc,IdentityDispatchError) and isinstance(exc.__cause__,PermissionError):continue
                    # Integrity/internal faults are sticky: never advertise a
                    # healthy authority or admit another connection afterward.
                    self._stop.set()
                    raise
                finally:
                    if connected:
                        try:win32pipe.DisconnectNamedPipe(self._handle)
                        except pywintypes.error:pass
        except BaseException as exc:self._error=exc
        finally:
            self._ready.set()
            if authority is not None:
                try:authority.close()
                except Exception:self._error=self._error or ServiceHostError("authority close failed")
            if self._handle is not None:
                from agent_lab.c09_pipe_transport import _quarantined
                if not any(entry[0]==self._handle for entry in _quarantined):win32file.CloseHandle(self._handle)
                self._handle=None

    def stop(self):
        self._stop.set()
        if self._thread is None:return
        self._thread.join(7)
        if self._thread.is_alive():raise ServiceHostError("authority shutdown incomplete; host halted")
        if self._error is not None:raise ServiceHostError("authority runtime halted") from self._error

    def check_health(self):
        if self._thread is None or not self._thread.is_alive() or self._error is not None:
            raise ServiceHostError("authority worker is not running")


def create_identity_service_host(authority_factory,*,allowed_case_ids,mutation_pipeline=False,protected_source=None):
    def bound_factory(config):
        authority=authority_factory(config)
        if protected_source is None:
            return authority
        try:
            from agent_lab.identity_mutation_source import InactiveGoogleDriveMutationSource
            from agent_lab.option_b_family_binding import BoundOptionBFamily
            if not isinstance(protected_source,(InactiveGoogleDriveMutationSource,BoundOptionBFamily)):
                raise ServiceHostError("typed inactive protected source required")
            protected_source.bind_authority(authority,config)
            return authority
        except BaseException:
            authority.close()
            raise
    from agent_lab.option_b_family_binding import BoundOptionBFamily
    owner_binding=protected_source if isinstance(protected_source,BoundOptionBFamily) else None
    return ServiceHost(ServiceRole.IDENTITY,lambda config:AuthorityPipeRuntime(config,bound_factory,allowed_case_ids=allowed_case_ids,mutation_pipeline=mutation_pipeline,owner_binding=owner_binding))


def create_custodian_service_host(authority_factory):
    return ServiceHost(ServiceRole.KEY_CUSTODIAN,lambda config:AuthorityPipeRuntime(config,authority_factory))


class KernelIdentityServiceClient:
    """Existing Kernel coordinates proof, Identity read, Witness, then release.

No UI-provided proof, callback head or authentication boolean is accepted.
Mutation routing is an explicit inactive composition option, with all authority checks preserved.
"""
    def __init__(self,kernel,*,deployment_id,identity_server,custodian,provider,signing_key,key_id,mutation_pipeline=False,owner_binding=None):
        from agent_lab.orchestrator_kernel import OrchestratorKernel
        from agent_lab.c09_named_pipe import PinnedProcess
        from agent_lab.c09_custodian_operational import CustodianServiceClient
        from agent_lab.c09_gcs_witness_adapter import GCSWitnessAdapter
        from cryptography.hazmat.primitives.asymmetric import ec
        if not isinstance(kernel,OrchestratorKernel):raise ServiceHostError("existing Kernel required")
        expected_sid=ROLE_BINDINGS[ServiceRole.IDENTITY][1]
        if owner_binding is not None:
            from agent_lab.option_b_family_binding import BoundOptionBFamily
            if not isinstance(owner_binding,BoundOptionBFamily) or owner_binding.kernel is not kernel:raise ServiceHostError('accepted Option B binding required')
            expected_sid=owner_binding.binding.payload['owner_sid']
        if not isinstance(identity_server,PinnedProcess) or identity_server.sid!=expected_sid:raise ServiceHostError("pinned Identity principal required")
        if not isinstance(custodian,CustodianServiceClient) or custodian.deployment_id!=deployment_id or not isinstance(provider,GCSWitnessAdapter):raise ServiceHostError("concrete deployment ports required")
        if not isinstance(signing_key,ec.EllipticCurvePrivateKey) or not isinstance(signing_key.curve,ec.SECP256R1) or not isinstance(key_id,str) or not key_id:raise ServiceHostError("protected Kernel signer binding required")
        if type(mutation_pipeline) is not bool:
            raise ServiceHostError("explicit mutation routing configuration required")
        if owner_binding is not None:
            if (owner_binding.binding.payload['deployment_id']!=deployment_id or
                owner_binding.binding.payload['witness_bucket']!=provider.bucket or
                owner_binding.binding.payload['custodian_key_id']!=custodian._custodian_key_id):
                raise ServiceHostError('Option B external authority ports mismatch')
            # Cold Kernel has no in-memory verified head. Reconstruct it only
            # from the existing independent Custodian/Witness chain, then
            # enforce the normal Owner/acceptance checks before binding.
            kernel.verify_identity_witness_state(deployment_id,custodian=custodian,provider=provider,
                signing_key=signing_key,kernel_key_id=key_id)
            owner_binding.constructor_ready()
        self._mutation_pipeline=mutation_pipeline
        self._kernel=kernel;self._deployment=deployment_id;self._identity=identity_server
        self._custodian=custodian;self._provider=provider;self._signer=signing_key;self._key_id=key_id
        self._owner_binding=owner_binding
        if owner_binding is not None:kernel._family_runtime_binding=owner_binding

    def read(self,*,manifest_id,task_id,run_id,case_id,tax_year,operation,payload,authorization_references,transaction_id=None,cancellation=None):
        from datetime import datetime,timezone
        from agent_lab.c09_identity_client import exchange_operational_identity_read
        from agent_lab.ipc_wire_primitives import encode_frame
        request=self._kernel.issue_identity_read(deployment_id=self._deployment,manifest_id=manifest_id,task_id=task_id,run_id=run_id,case_id=case_id,tax_year=tax_year,operation=operation,payload=payload,authorization_references=authorization_references,transaction_id=transaction_id,signing_key=self._signer,key_id=self._key_id)
        state=self._kernel._identity_payload("identity_kernel_state","deployment_id",self._deployment)
        scope={name:request[name] for name in "deployment_id case_id tax_year run_id task_id manifest_id actor_instance_id role_id".split()}
        deadline=OperationDeadline(5,cancellation)
        response=exchange_operational_identity_read(encode_frame(request),self._identity,self._signer.public_key(),expected_scope=scope,now=datetime.now(timezone.utc).replace(tzinfo=None),expected_key_id=self._key_id,deadline=deadline,contract_version="oi0002.kernel-identity-c09/1.1",bootstrap_artifact=state["artifact"] if request["message_type"]=="GET_ENROLLMENT_STATUS" else None)
        deadline.milliseconds()
        if response["outcome"] in {"DENIED","CONFLICT"}:return response
        pending=self._kernel.stage_identity_audit_checkpoint(request,response)
        deadline.milliseconds()
        result=self._kernel.witness_identity_checkpoint(pending["receipt"]["checkpoint_id"],custodian=self._custodian,provider=self._provider,signing_key=self._signer,kernel_key_id=self._key_id)
        deadline.milliseconds()  # A cancelled caller cannot publish a held result.
        return result

    def mutation_stage(self,*,manifest_id,task_id,run_id,case_id,tax_year,operation,message_type,
                       payload,authorization_references,transaction_id,cancellation=None):
        """Route one explicit stage through its issuing Kernel and Identity host.

        This opt-in is routing configuration only. Actual source, proof, scope,
        permission, enrollment and finality validation remain in the authorities.
        No automatic retry is permitted after an ambiguous exchange.
        """
        if not self._mutation_pipeline:
            raise ServiceHostError("mutation routing is disabled")
        from datetime import datetime,timezone
        from agent_lab.c09_identity_client import exchange_operational_identity_mutation
        from agent_lab.ipc_wire_primitives import encode_frame
        deadline=OperationDeadline(5,cancellation)
        deadline.milliseconds()
        request=self._kernel.issue_identity_mutation(deployment_id=self._deployment,manifest_id=manifest_id,
            task_id=task_id,run_id=run_id,case_id=case_id,tax_year=tax_year,operation=operation,message_type=message_type,
            payload=payload,authorization_references=authorization_references,transaction_id=transaction_id,
            signing_key=self._signer,key_id=self._key_id)
        scope={name:request[name] for name in "deployment_id case_id tax_year run_id task_id manifest_id actor_instance_id role_id".split()}
        return exchange_operational_identity_mutation(encode_frame(request),self._identity,self._signer.public_key(),
            kernel=self._kernel,expected_scope=scope,now=datetime.now(timezone.utc).replace(tzinfo=None),
            expected_key_id=self._key_id,deadline=deadline)

    def reconcile(self,checkpoint_id):
        """Retry exact held checkpoint; never dispatch Identity a second time."""
        pending=self._kernel._identity_payload("identity_kernel_checkpoint","checkpoint_id",checkpoint_id)
        if self._owner_binding is not None:
            if pending is None:raise ServiceHostError('exact held checkpoint required')
            if pending['receipt']['profile']=='identity-mutation-staged-receipt/1':
                request=pending['request']
                self._owner_binding.authorize_request(message_type='GET_TRANSACTION',transaction_id=request['transaction_id'],case_id=request['case_id'],tax_year=request['tax_year'])
            else:self._owner_binding.ensure_ready()
        if (pending is not None and pending["receipt"]["profile"]=="identity-mutation-staged-receipt/1"
                and not self._mutation_pipeline):
            raise ServiceHostError("mutation routing is disabled")
        return self._kernel.witness_identity_checkpoint(checkpoint_id,custodian=self._custodian,provider=self._provider,signing_key=self._signer,kernel_key_id=self._key_id)

    def recover_read(self, *, transaction_id, manifest_id, task_id, run_id, case_id, tax_year,
                     operation, payload, authorization_references):
        """Explicit recovery of the exact held read, using existing Kernel evidence.

        Never return a caller-supplied result or redispatch a completed mutation.
        A missing checkpoint uses the existing same-transaction read recovery.
        """
        if self._owner_binding is not None:self._owner_binding.ensure_ready()
        from agent_lab.ipc_operational_read import UUID
        if not isinstance(transaction_id,str) or not UUID.fullmatch(transaction_id):
            raise ServiceHostError("canonical read transaction required")
        expected=dict(deployment_id=self._deployment,manifest_id=manifest_id,task_id=task_id,
                      run_id=run_id,case_id=case_id,tax_year=str(tax_year),domain_operation=operation,
                      authorization_references=authorization_references,payload=payload,message_type="READ_IDENTITY_STATE")
        self._kernel._verify_identity_protocol_state()
        rows=self._kernel._connection.execute(
            "SELECT checkpoint_id FROM identity_kernel_checkpoint WHERE json_extract(payload_json,'$.request.transaction_id')=? AND json_extract(payload_json,'$.request.case_id')=?",
            (transaction_id,case_id)).fetchall()
        if len(rows)>1:raise ServiceHostError("ambiguous read checkpoint")
        if rows:
            pending=self._kernel._identity_payload("identity_kernel_checkpoint","checkpoint_id",rows[0][0])
            request=pending["request"]
            if any(request[name]!=value for name,value in expected.items()):
                raise ServiceHostError("read recovery scope substitution")
            self._kernel._current_identity_release_authority(pending)
            self._kernel._assert_identity_witness_idle(self._deployment,read_transaction_id=transaction_id)
            state=self._kernel._identity_payload("identity_kernel_state","deployment_id",self._deployment)
            if (pending["response"]["identity_epoch"],pending["response"]["identity_head"])!=(state["logical_epoch"],state["logical_head"]):
                raise ServiceHostError("read snapshot predates a mutation")
            return self.reconcile(rows[0][0])
        return self.read(transaction_id=transaction_id,manifest_id=manifest_id,task_id=task_id,
                         run_id=run_id,case_id=case_id,tax_year=tax_year,operation=operation,
                         payload=payload,authorization_references=authorization_references)

    def family_workflow(self, **kwargs):
        if self._owner_binding is not None:
            if kwargs.get('workflow') is not None:self._owner_binding.ensure_ready()
            else:self._owner_binding.recovery_ready()
        return self._kernel.family_identity_workflow(deployment_id=self._deployment,**kwargs)

    def complete_mutation(self, intent, *, recovery=False):
        """Complete one exact journaled transaction; no fresh mutation on ambiguity."""
        from agent_lab.ipc_wire_primitives import canonical_sha256 as H
        args={key:value for key,value in intent.items() if key!="payload"}
        self._kernel._verify_identity_protocol_state()
        state=self._kernel._identity_payload("identity_kernel_state","deployment_id",self._deployment)
        tx=state.get("mutations",{}).get(intent["transaction_id"])
        from agent_lab.ipc_operational_read import OPERATION_CAPABILITIES
        self._kernel._identity_continuity_context(manifest_id=intent["manifest_id"],task_id=intent["task_id"],case_id=intent["case_id"],tax_year=intent["tax_year"],run_id=intent["run_id"],operation=intent["operation"])
        if not self._kernel.permission_decision(intent["manifest_id"],OPERATION_CAPABILITIES[intent["operation"]],case_id=intent["case_id"],tax_year=intent["tax_year"],run_id=intent["run_id"]).allowed:
            raise ServiceHostError("mutation recovery authority denied")
        if tx is not None:
            prior=tx["prepare_request"]
            expected={**{key:value for key,value in args.items() if key!="operation"},"tax_year":str(intent["tax_year"]),"domain_operation":intent["operation"],"payload":intent["payload"]}
            if any(prior[name]!=value for name,value in expected.items()):raise ServiceHostError("mutation recovery content substitution")
            if recovery and tx.get("final_response",{}).get("outcome")=="COMMITTED_FINAL":return tx["final_response"]
        if tx is not None and not recovery:
            raise ServiceHostError("explicit original mutation recovery required")
        if tx is None or "prepare_response" not in tx:
            prepared=self.mutation_stage(**args,message_type="PREPARE_MUTATION",payload=intent["payload"])
            if prepared["outcome"]!="PREPARED":raise ServiceHostError("mutation prepare failed")
            state=self._kernel._identity_payload("identity_kernel_state","deployment_id",self._deployment)
            tx=state["mutations"][intent["transaction_id"]]
        if "commit_request" in tx:
            reply=self.mutation_stage(**args,message_type="GET_TRANSACTION",
                payload={"original_request_digest":tx["prepare_request"]["request_digest"]})
            if reply["outcome"]=="COMMITTED_FINAL":return reply
            if reply["outcome"] not in {"PREPARED","IDENTITY_COMMITTED"}:
                raise ServiceHostError("mutation is not resumable")
        else:reply={"outcome":"PREPARED"}
        if reply["outcome"]=="PREPARED":
            reply=self.mutation_stage(**args,message_type="COMMIT_MUTATION",payload=intent["payload"])
            if reply["outcome"]!="IDENTITY_COMMITTED":raise ServiceHostError("mutation commit failed")
        final=self.reconcile("MUTATION:"+intent["transaction_id"])
        receipt=final["receipt"];verification=final["custodian_verification"]["response"]
        payload=dict(staged_receipt_digest=H(receipt),witness_object_key=final["object_key"],witness_generation=final["generation"],
            witness_preimage_digest=receipt["witness_preimage_digest"],signed_record_digest=verification["signed_record_digest"],
            custodian_verification_digest=H(verification),custodian_nonce=verification["nonce"])
        reply=self.mutation_stage(**args,message_type="FINALIZE_MUTATION",payload=payload)
        if reply["outcome"]!="COMMITTED_FINAL":raise ServiceHostError("mutation finalize failed")
        return reply


class KernelServiceRuntime:
    """SCM lifetime for the existing Kernel and concrete Identity service client."""
    def __init__(self,config,kernel_factory,*,identity_server,custodian,provider,signing_key,key_id,mutation_pipeline=False):
        name,sid=ROLE_BINDINGS[ServiceRole.KERNEL]
        if (config.schema!="ai-tax-agent.c09-service-config/1.0" or config.role is not ServiceRole.KERNEL or
            config.service_name!=name or config.principal_sid!=sid or config.enabled is not True or
            not isinstance(config.deployment_id,str) or not config.deployment_id or len(config.deployment_id.encode())>128):
            raise ServiceHostError("fixed Kernel deployment required")
        self._config=config;self._factory=kernel_factory;self._kernel=None;self.client=None
        self._bindings=dict(identity_server=identity_server,custodian=custodian,provider=provider,signing_key=signing_key,key_id=key_id,mutation_pipeline=mutation_pipeline)

    def start(self):
        if self._kernel is not None or current_process_sid()!=self._config.principal_sid:
            raise ServiceHostError("actual Kernel service token required before store access")
        kernel=self._factory(self._config)
        try:
            client=KernelIdentityServiceClient(kernel,deployment_id=self._config.deployment_id,**self._bindings)
            kernel.verify_audit_chain();kernel._verify_identity_protocol_state()
        except BaseException:kernel.close();raise
        self._kernel=kernel;self.client=client

    def check_health(self):
        if self._kernel is None:raise ServiceHostError("Kernel is stopped")
        self._kernel.verify_audit_chain();self._kernel._verify_identity_protocol_state()

    def stop(self):
        self.client=None
        if self._kernel is not None:self._kernel.close();self._kernel=None


def create_kernel_service_host(kernel_factory,**bindings):
    return ServiceHost(ServiceRole.KERNEL,lambda config:KernelServiceRuntime(config,kernel_factory,**bindings))
