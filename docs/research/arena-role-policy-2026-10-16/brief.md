# Architecture question (identical for every candidate)

What is the minimal seam that lets pstack resolve canonical role -> model/effort per harness without importing another port's policy forks?

Constraints: canonical role IDs stay in pstack.package.json#/roles; host model facts stay host-owned (profiles/<host>.json + projected manifests); no new workflow runtime, scheduler, gateway, or durable store; unsupported host primitive is an explicit GAP; every claim needs evidence.

Deliverable: a one-page architecture brief in your output dir with (a) the data shape, (b) the boundary/ownership table, (c) why it is minimal, (d) what it rejects and why.
