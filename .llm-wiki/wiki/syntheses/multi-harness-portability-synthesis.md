# Synthesis: Canonical Intent vs Multi-Harness Portability

## Strategic Division
The PStack multi-harness port resolves the tension between rapidly evolving canonical Cursor features and broad, truthful host portability:

1. **Canonical Intent Authority:**
   - Canonical Cursor PStack owns workflow patterns, prompt structures, review principles, and developer experience.
   - Updates from upstream (0.15.29 -> 0.15.36) are systematically audited and adopted where they enhance agent reasoning and verification rigor.
2. **Port Host Boundary Authority:**
   - The multi-harness port owns host-neutral execution adapters, capability profiles, package generators, and evidence ledgers.
   - Cursor-specific assumptions (native background Task agents, IDE-private APIs, cloud-only VM executors) are cleanly abstracted through portable capability bindings.
   - Where a host cannot support a capability natively (e.g. nested subagents), PStack records an honest GAP or adapted pattern rather than simulating a brittle parallel runtime.
3. **Downstream Ecosystem Preservation:**
   - Downstream projects like QStack rely on PStack for general-purpose orchestration and core software engineering principles while maintaining domain-specific authorities (such as `qorch`) independently.
