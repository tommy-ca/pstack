# Detail Report 04: Architectural Containment & Zero Bloat to QStack

- **Subsystem**: Architectural Boundaries, Dependency Hygiene & Standard Library Confinement
- **Base Revision**: `5f649c6`
- **Head Revision**: `20164ba`
- **Reviewed Epic**: Issue [#685](https://github.com/tommy-ca/pstack/issues/685) (PR [#686](https://github.com/tommy-ca/pstack/pull/686), commit `7d0dbd2`)

---

## 1. Context & Standard

Standard 6 of the Thermo-Nuclear Code Quality Review mandates:
> Keep logic in the canonical layer and reuse existing helpers. Call out feature logic leaking into shared paths or implementation details leaking through APIs.

Furthermore, user-defined guidelines dictate:
> Keep JEV integration lean and clean, do not bloat to QStack, keep it at PStack.

---

## 2. Dependency Audit

PR [#686](https://github.com/tommy-ca/pstack/pull/686) introduced origin validation and IP classification across provider profiles. A frequent engineering risk during SSRF validation is importing heavy third-party networking or URL parsing libraries (such as `validators`, `tldextract`, `netaddr`, `urllib3`, or `requests`).

### 2.1 Standard Library Confinement
An audit of imports in [`scripts/decision_adapter.py`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py) reveals:
```python
import ipaddress
import json
import math
import os
import threading
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
```
- **Zero Third-Party Dependencies**: All URL parsing is handled via `urllib.parse.urlparse`.
- **Zero Network Egress for Validation**: IP classification is performed entirely in-memory using `ipaddress.ip_address` predicates (`is_loopback`, `is_private`, `is_link_local`, `is_unspecified`, `is_multicast`, `is_reserved`). No DNS resolution or network sockets are invoked during validation, preventing DNS rebinding risks and ensuring validation runs hermetically offline.
- **Zero Heavyweight Concurrency Frameworks**: `SpendLedger` relies exclusively on Python standard library `threading.Lock`. No external Redis instances, distributed locks, database connections, or background daemon processes were introduced.

---

## 3. Boundary Containment: PStack vs. QStack

QStack represents multi-node orchestration, distributed tracing, and heavyweight consensus protocols. PStack represents portable, local, file-based, lightweight developer harness tooling.

The implementation of Epic [#685](https://github.com/tommy-ca/pstack/issues/685) strictly protects this boundary:
1. **Local Process Scope**: `SpendLedger` operates as a thread-safe in-process admission controller. It does not attempt to solve distributed multi-machine quota synchronization, which would require QStack infrastructure.
2. **Explicit Semantic Contracts**: Instead of bloating PStack with distributed consensus, the architecture explicitly documents the distinction between process-local admission and account-wide provider ceilings. If an account requires distributed multi-process budget coordination, that belongs to the upstream provider's account quota controls or an external gateway, not PStack.
3. **Hermetic Testability**: The entire test suite in [`tests/test_paid_budget_concurrency.py`](file:///home/tommyk/projects/pstack/tests/test_paid_budget_concurrency.py) and [`tests/test_jev_transport_and_profiles.py`](file:///home/tommyk/projects/pstack/tests/test_jev_transport_and_profiles.py) runs completely offline without internet connectivity, external services, or API tokens.

---

## 4. Verdict
Zero bloat. Absolute adherence to PStack architectural containment and zero-dependency discipline.
