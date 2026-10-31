# CandidateEnvelope.v1 schema — design contract, not deployed admission

`candidate-envelope.v1.schema.json` is JSON Schema Draft 2020-12. Valid fixtures are synthetic and contain placeholder hex digests; the test suite checks **syntax, fields and rejection cases only**. Never claim these digests were computed from real source files. The schema does not establish reviewer identity, legal usage rights, source byte equality, citation truth or QStack write permission.

Runtime PStack `scripts/llm_wiki.py check` remains a structural validator. Promotion would need a separate trusted publisher to check real file digests, target preconditions, review authentication, rights and schema; this PR does **not** implement a candidate publisher.

Source mapping: Atomicstrata 1.5.0 compilation/review/state/citations; Geronimo type schema/epistemic/read-model separation; QStack nine-role governance. See [design.md](../design.md).
