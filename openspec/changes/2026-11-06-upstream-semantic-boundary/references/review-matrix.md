# Review and falsification matrix

Status on authoring: SPECIFIED; live independent review lanes NOT_RUN. Use existing skills; no newly generated verification skill or external executor.

| Review lens | Concrete question / negative control | Required evidence |
| --- | --- | --- |
| Scope / ownership | Do the changed files introduce provider, lifecycle or placement contracts? | diff path/line and exclusion decision |
| Canonical authority | Is each adopted semantic rule present in applied Cursor PStack? | immutable source pin and original path |
| Swarm | Were distinct scope lanes/source scans actually performed? | independent child/model IDs, paths, coverage; else NOT_RUN |
| Arena | Did identical briefs and a predeclared rubric produce independent candidates? | candidates, rubric, real judge ID or explicit skip |
| Interrogate | Does any claimed defect have a reproduced failure on current changed code? | command, output, expected behavior; else unverified |
| Thermo-Nuclear review | Any changed-diff safety, correctness, security or developer-experience regression? | direct diff citations, reproducible impact |
| Thermo-Nuclear code quality | Could removal of a layer or a duplicated spec preserve behavior? | before/after diff and simplified ownership |
| OpenSpec validity | Do only existing capability IDs change; are all scenarios falsifiable? | OpenSpec CLI result or NOT_RUN |
| Verification honesty | Does any static/offline pass imply native or model-checked PASS? | distinct tiered receipts or BLOCKED/NOT_RUN |

## Static negative controls
1. Proposal mentions new Mu/Dogsled worker adapters as proposed PStack deliverables -> FAIL.
2. OpenSpec defines a second execution schema or task-policy owner -> FAIL.
3. Third-party source presented as canonical without upstream path/pin -> FAIL.
4. Missing Swarm/Arena/Interrogate lanes are reported as successfully executed -> FAIL.
5. Verification script, host or formal checker was not run but is described as PASS -> FAIL.
6. Canonical Orchestrate skill is removed because generic orchestration is out-of-scope -> FAIL.

Actual review outputs must attach command, reviewer provenance, revision SHA and target paths. No panel or live proof is implied by this checklist.
