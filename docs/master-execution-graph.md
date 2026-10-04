# Master Execution Graph and hot context

The versioned graph at `contracts/project-execution/v1/master-execution-graph.json` compiles the current supported-product path and separately lists future Master Plan scope. It is a fail-closed planning projection over the existing Deterministic Orchestrator Kernel. It is not another queue, authority source, database, scheduler, or dispatcher.

`project_execution_graph.load_graph()` rejects mixed versions, unknown fields/statuses/cost classes, duplicate IDs, and unknown, forward, or cyclic dependencies. `next_authorized_action()` is a read-only query: it requires a safe repository, exact branch, satisfied dependencies, active node authority, and an accepted capacity decision. Ambiguous ready work fails closed. It cannot grant permissions or perform work.

The hot context is a hash-bound generated projection containing project/repository/branch/HEAD, recovery checkpoint, graph identity, one next-action result, current capacity/reset evidence, and the exact supporting contract. It is rebuilt from canonical evidence; it does not become a competing source of truth.

The current graph distinguishes `CURRENT_SUPPORTED_PRODUCT_COMPLETE` from `MASTER_PLAN_FUTURE_SCOPE_REMAINING`. Additional years, taxpayer categories, legal entities, and generalized production workflows are not claimed as implemented.

The notification contract uses a protected logical destination reference rather than storing the Owner's address in Git. It only evaluates eligibility. It cannot send email. Any real or synthetic external email requires separate ordered Constitution Article 1 Stage One and Stage Two approvals for the exact immutable message and exact destination/channel. Delivery failures never weaken the original gate, and durable event identity prevents unchanged duplicates.

The only continuation automation is `plan-limit-continuation-guard`. During active work, capacity is checked at meaningful package boundaries. On a genuine capacity pause, the durable checkpoint, exact action, closed cost class, and actual service reset timestamps must be written before that same automation is armed once at the reset. Windows Local Sync and Relay tasks are operational workers, not quota schedulers.

R1 found no safe tracked deletion candidate. Historical evidence remains outside normal hot context; disposable ignored logs/caches have no governing value. Protected local artifacts remain untouched.
