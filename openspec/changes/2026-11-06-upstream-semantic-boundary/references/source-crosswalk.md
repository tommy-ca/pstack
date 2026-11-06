# Semantic source crosswalk — upstream first

| Source (commit-pinned) | Observation | Existing PStack owner | Decision |
| --- | --- | --- | --- |
| [Cursor poteto-mode](https://github.com/cursor/plugins/tree/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/poteto-mode) | source principles and playbook dispatch | pstack-reference-port, pstack-playbooks | preserve/adapt per applied pin |
| [Cursor orchestrate](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/poteto-mode/playbooks/orchestrate.md) | brief, ownership, evidence, per-host gap | existing orchestrate playbook | preserve/adapt, not a new runtime |
| [Cursor swarm](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/swarm/SKILL.md) | independent slices/races; aggregate gaps | existing swarm | preserve |
| [Cursor arena](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/arena/SKILL.md) | frozen brief, rubric, isolated output, synthesis | existing arena | preserve |
| [Cursor interrogate](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/interrogate/SKILL.md) | reproduce findings; discard speculation | existing interrogate | preserve |
| [Mu DAG](https://github.com/mu-crew/mu/blob/73fb53d4e38c9717be5642460b2344c76cfe6349/docs/architecture/dag.md) | task dependency representation | no PStack runtime adoption | reference-only |
| [Mu operation log](https://github.com/mu-crew/mu/blob/73fb53d4e38c9717be5642460b2344c76cfe6349/docs/architecture/ops-log.md) | durable event/rebuild storage | no PStack runtime adoption | reference-only |
| [Dogsled unit requests](https://github.com/oisin-ee/dogsled/blob/5e28a8c72272f8d8a91f86c4691a43f4bca6d551/docs/unit-requests.md) | executor-side prepare/commit/observe | no PStack runtime adoption | reference-only |
| [Dogsled lifecycle](https://github.com/oisin-ee/dogsled/blob/5e28a8c72272f8d8a91f86c4691a43f4bca6d551/docs/lifecycle.md) | custody/cleanup/terminal state implementation | existing generic safety principles where canonical | reference-only for executor details |

| [Cursor Thermos review](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/thermos/skills/thermo-nuclear-review/SKILL.md) | changed-diff security/correctness | external reusable review skill | apply review lens only; no owned execution |
| [Cursor Thermos quality](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/thermos/skills/thermo-nuclear-code-quality-review/SKILL.md) | simplification and boundary quality | external reusable review skill | apply review lens only |
| [QStack AGENTS](https://github.com/tommy-ca/qstack/blob/918b3c57c75e1caae3f44a686bed6e8c3619ee0c/AGENTS.md) | software-dev vs quant research state ownership, one-way skill use | downstream quant overlay | reference-only; no reverse dependency |
| [QStack taskgraph-runner](https://github.com/tommy-ca/qstack/blob/918b3c57c75e1caae3f44a686bed6e8c3619ee0c/skills/taskgraph-runner/SKILL.md) | checks qorch research DAG, explicitly not a generic orchestrator | downstream quant verification | reference-only; not ported to PStack |
| [QStack declare-your-falsifier](https://github.com/tommy-ca/qstack/blob/918b3c57c75e1caae3f44a686bed6e8c3619ee0c/skills/qstack-principle-declare-your-falsifier/SKILL.md) | empirically falsifiable quant research hypotheses | downstream quant principle | reference-only; no duplicate PStack principle |

This is a **classification**, not a code import or claim of tested external integration. The reference commits are observed snapshots, not a substitute for the applied UPSTREAM pin. Reclassify only when a change is independently evidenced by canonical Cursor PStack and reviewed as an upstream semantic delta.

Downstream mapping: qstack-mode -> pstack-mode for generic engineering method reuse; qorch and quant-specific scheduling belong solely to QStack or another external orchestration owner. Do not add reverse imports, duplicate playbooks, or compiled wiki runtime dependencies.
