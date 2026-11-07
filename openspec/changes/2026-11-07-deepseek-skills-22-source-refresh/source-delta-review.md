# Source delta: sixteen → twenty-two skills, with behavior-level triage

**Old pin:** `deepseek-ai/deepseek-harness@d743267388641bc76f17c45ce8b4c231aed1d32c` (16 source leaves).  
**New pin:** `deepseek-ai/deepseek-harness@fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159` (22).  
**Evidence:** direct pinned `SKILL.md` read and old/new text comparison; SOURCE_STATIC. This does **not** assert PStack's runtime behavior is missing, that external code paths run, or that Swarm/Arena/Interrogate were invoked.

## New six source skills

| Source | Distinct new subject at new pin | Retain as PStack skill? |
| --- | --- | --- |
| `cordis-styling-nitpicking` | Cordis singleton/effect/disposal-specific review, including last consumer dependency use | **No**. Generic lifecycle invariant only, to existing review/formal skill |
| `dsh-cua-macos-signing` | DSH source-build CUA keychains and authorization | **No**; project/host security configuration |
| `dsh-official-plugin-artwork` | DSH artwork system, SVG shapes and brand approval | **No**; target product visual guidelines |
| `dsh-pr-description` | PR motivation, observable changes, testing evidence, AI Usage rubric | **Yes, only generic PR evidence**, via `make-pr-easy-to-review`, no DSH body template |
| `dsh-responsive-ui` | Viewport, focus, touch/hover, wrapping and accessible action availability | **Conditional**, via `create-verification-skill` + `visual-parity`, no universal viewport values |
| `dsh-session-projection` | DSH session-derived projection replay, checkpoint semantics and service handles | **No generic skill**; only project-local event-sourcing/formal verification |

## Re-reviewed eight earlier directories with changed object IDs

| Source | Old → new behavioral change visible in SKILL.md | General adoption decision |
| --- | --- | --- |
| `dsh-ci-test-reliability` | Document link moved from one defensive-pattern page to `docs/defensive-patterns/general.md`; the 132-line core test-isolation guidance otherwise remains materially the same in this text comparison | Preserve old general test-isolation decision, **no new skill** |
| `dsh-client-ui-ux` | Restructured into a risk-scaled UI inspection workflow with required minimum checks for actual affected page/states, focus, long/wrapped content and shared consumers; adds more process than old style-token guidance | Retain only conditional user-path verification via existing UI playbook, exclude DSH visual foundations |
| `dsh-code-review` | Adds detailed source-of-truth ownership pages, stronger test/contract traceability, Cordis-specific review, and more nuanced scope/consumer/authorization checks | Retain generic exact-head, consumer and lifecycle checks with existing Thermos/Interrogate; exclude the new DSH-only subsystem reading list |
| `dsh-find-simplifications` | Clarifies requirement necessity and consumer-derived distinctions; adds caution that moving an unnecessary concept to a closer owner is not actual simplification | Retain only evidence-backed deletion of maintained obligations in existing quality/refactoring owners |
| `dsh-pre-push-checks` | Adds DSH TypeScript `build:artifacts` then `build:check` and revised UI-review routing | Keep diff-scoped evidence selection; **exclude DSH build commands** |
| `dsh-prose-standard` | Refines language around product text and localized UI strings through DSH's client abstractions | Keep complete-proposition and docs-owner rules; **exclude DSH locale/primitive mandates** |
| `dsh-speed-up-perf` | Main SKILL.md textual change principally updates defensive-patterns reference path | Existing PStack benchmark/perf workflow suffices pending actual negative test |
| `record-browser-gif` | Rewrites publication to `gh --attach`, revises 5 MiB artifact handling and removes old assets-branch fallback | **Conditional visual evidence only**; exclude GH version/media publication mechanics and mandatory model-backed GIF |

The eight directories' change markers originally came from Git tree object IDs. The above table is a **SKILL.md text-level re-review**, not a complete deep diff of every supplementary source reference/script in each directory. For later adoption, inspect the specific referenced scripts/owners before modifying any executable behavior.

## Existing PStack owner evidence inspected

- `create-verification-skill` already documents host-native launch, real user path, readiness/doctor, isolation and captured evidence.
- `fix-ci` already invokes `verify_portable.py select-checks` and checks actual base/head and stale-patch receipts.
- `thermo-nuclear-review` / `thermo-nuclear-code-quality-review` already cover correctness/security, cross-package consumers, behavioral reachability and structural reduction.
- `make-pr-easy-to-review` already covers stale descriptions, missing tests and reviewer guidance.
- `benchmark-checklist` already covers benchmark validity, realistic end-to-end measurement and repeatability.
- `technical-writing`, `unslop` and `principle-guard-the-context-window` already cover prose, reduction and context-efficiency disciplines.

**Static conclusion:** no source-derived standalone PStack leaf, principle or playbook is currently justified. This is not an executed behavioral-equivalence proof; relevant negative-control cases are explicitly left NOT_RUN.

## Scope notes / nonclaims

- **Swarm:** source review was done by single orchestration, not multiple independent workers. No Swarm report.
- **Arena:** architecture alternatives were reasoned about, not executed as competing agent candidates. No Arena winner.
- **Interrogate:** negative test cases were specified, not executed. No independently reproduced failure claim.
- **Thermos:** semantic lenses were referenced by reading their SKILL.md, not executed as independent code-quality/security reviewer subprocesses.
- **PStack runtime:** no source skill or target product code was modified; no PStack tests, native host checks, browser recordings, or credential/signing operations were run.

## Source permissions

The upstream DeepSeek Harness repository declares MIT. This change links the source code and writes independent behavioral summaries, rather than copying proprietary project-specific SKILL.md bodies.
