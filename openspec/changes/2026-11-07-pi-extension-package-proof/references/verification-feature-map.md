# Verification feature map, risk matrix, test tiers and independent review plan

Status: source-reviewed; **native extension/child/security tests NOT_RUN**. Existing bounded contract tests are useful, but a source/CLI preflight cannot prove the Pi runtime.

| Feature ID | Required observable | Current evidence | Negative control | Owning verifier |
| --- | --- | --- | --- | --- |
| PI-01 | native skills selected under project trust | .pi/settings.json static | disable trust or shadow skill; no false discovery | verify-pi-pstack doctor + future package smoke |
| PI-02 | Pi git package exports skills AND canonical agents via pi.subagents.agents | source-documented v0.86 API, no native install | missing 22nd role / duplicate legacy skill / package loads executable extension | #975 package test |
| PI-03 | pi-subagents single delegate engine | extension pin static-only | second engine/tool-owner collision | existing candidate contract |
| PI-04 | model/provider identity exact | v0.87 source change, uninstalled | provider/id fallback to other account/model | native v0.87 candidate test |
| PI-05 | child launch only after authorization | unobserved | denied subagent_launch still starts child | future native actor driver |
| PI-06 | join/cancel/drain terminal state | unobserved | stop drain starts new child or counts cancelled PASS | actor driver/formal property |
| PI-07 | worktree policy and cleanup | unobserved | symlink/outside write or orphaned worktree | OS sandbox native test |
| PI-08 | pi-verdict deterministic deny floor | source template + mutants | model allow overrides deny path | native hook test |
| PI-09 | headless ask never authorizes effect | source template + mutants | no operator yet privileged action executes | native denial test |
| PI-10 | sandbox actually ON for main/child/detached | static source policy only | installed but off / trusted tool bypass | enabled backend test |
| PI-11 | pi-ask-user human.ask not human.gate | profile static | structured response becomes hard approval | source + native auth test |
| PI-12 | native web/MCP only authorized | source mapping | child silently inherits privileged network tool | native tool admission |
| PI-13 | 53 source mutants rejected | existing bounded suite | false host promotion, ignored launch, duplicate binding | verify-pi-pstack-formal model |
| PI-14 | healthy preflight remains BLOCKED | before fix: false PASS | fake live data with all preflight booleans true | test_pi_authorization_contracts |
| PI-15 | cleanup cannot claim unobserved absence | before fix: unconditional PASS | call cleanup with zero child tracking | shell wrapper regression |
| PI-16 | offline results never become observed_live | existing receipt shapes | fake child ID or absent source SHA | four-plane Receipt validation |
| PI-17 | independent Swarm/Arena/Interrogate/Thermos | NOT_RUN | same model/context falsely called independent | reviewer receipts + #978 |

## Role-semantic negative tests to add before Pi package promotion

| ID | Assumption to falsify | Required native observation |
| --- | --- | --- |
| PI-18 | Zero-extension Pi single-agent cannot load canonical PStack skills | Native PStack skill discovery, no bundled executable extensions |
| PI-19 | pi-subagents cannot consume `pi.subagents.agents` (v0.86) | Disposable package install + listing/resolution of all 22 role identities |
| PI-20 | PStack frontmatter `effort` becomes Pi `thinking` automatically | Resolved child thinking level and explicit mapping when needed; no guessed equivalence |
| PI-21 | Prompt-only independent-verifier no-edit creates hard read-only | Denied native `edit`, `write`, `bash` and nested delegate spawn, plus actual OS effect |
| PI-22 | Fresh Pi children inherit project skills and context automatically | Child can resolve the exact `poteto-mode` skill/principles under declared `inheritSkills` or explicit `skills`; otherwise GAP |
| PI-23 | Guarded profile optional packages imply hard human.gate | Separate enabled hooks and OS policy denial, but hard human.gate remains GAP without independent enforcement |

All PI-18..PI-23 are **SOURCE-DESIGNED / NOT_RUN**. Existing 53 mutants test only the previous source manifest and profile contract; do not imply new role-effect coverage was executed. A real Pi package and role runner must prove these controls before #975/#978 can close.

## Exact tests to run at PR HEAD
~~~sh
python3 scripts/verify_pi_candidate.py check
python3 scripts/verify_pi_candidate.py model
python3 -m pytest -q tests/test_pi_candidate_profile.py tests/test_pi_authorization_contracts.py
bash .pi/skills/verify-pi-pstack/scripts/driver.sh doctor
bash .pi/skills/verify-pi-pstack/scripts/driver.sh drive    # BLOCKED / exit 2 until live actor driver
bash .pi/skills/verify-pi-pstack/scripts/driver.sh cleanup  # BLOCKED / exit 2, no false PASS
python3 scripts/prove_pi_vertical_slice.py --json            # runtime BLOCKED without native actor
openspec validate 2026-11-07-pi-extension-package-proof --type change --strict
~~~

## Review composition
- **Swarm**: independent source/manifest trace, child permission/confinement, package resource-discovery and evidence accounting, each with real agent/model ID or NOT_RUN.
- **Arena**: freeze two alternatives: thin skills-only native package versus an executable Pi adapter package, grade by true Pi discovery, trust surface, maintenance size, 17-contract fidelity and negative proof.
- **Interrogate**: reproduce a false preflight PASS / cleanup PASS mutant and provider-qualified fallback/cross-session failures. No invented effect or independent review.
- **Thermo Nuclear Review**: changed-code auth/fake proof, path misuse, user config side effects, package install surprises.
- **Thermo Nuclear Code Quality Review**: remove redundant adapter/registry/sdk, keep one source for roles and 17 capability mapping, no complexity balloon.

## Completion
An offline PStack CI PASS is not installed Pi/package proof or native sandbox PASS. Only actually run commands, source/version/SHA, outputs and exit codes support claims. OpenSpec CLI unavailable => UNTESTED; absent independent reviewer => NOT_RUN; native Pi binaries missing => BLOCKED; no effective hard human.gate => GAP.
