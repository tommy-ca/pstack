---
name: create-verification-skill
description: "Use when a project has no scripted way to prove UI, CLI, or service behavior, or for /create-verification-skill or \"make a control skill for this repo\"."
disable-model-invocation: true
---

# Create a verification skill

Every serious project needs a scripted way to drive the real app and prove behavior: launch it, exercise a feature the way a user would, and capture evidence. This skill generates that as a project-local skill tailored to the repo. You write the generator's output for the next agent, not for a human: it will be read cold, mid-task, by an agent that has never seen the app.

Default path is `.grok/skills/verify-<app>/` for an application repo. If `plugin.json` lists `./skills/`, ship at `skills/verify-<app>/` instead. This pstack plugin is that case (`skills/verify-pstack/`). Do not write `~/.grok/skills`. Do not write `.claude/skills`.

## Why not a wiki

A wiki is for humans. Agents pay for every token they reread. Write a skill plus a feature map. Use one short file per feature, the same four H2s, and a README that is the sweep order. Keep the map next to the skill at `features/`. Do not grow it into a wiki. Do not put it in OpenSpec. `openspec/specs` is capability Gherkin, not a drive recipe. Live OpenSpec must not restate leftover inventory (playbook count, principle count, slash catalog). That would be a third map.

## 1. Interview the repo, not the user

Answer these from the codebase and only ask the user what you cannot observe:

- **Surface:** what does a user actually touch? A web UI, a CLI/TUI, a desktop app, an API, a mobile app, a library? A repo can have several. Pick the primary one and note the rest.
- **Run:** how does the app start locally? Prefer the repo's own documented dev command (package scripts, Makefile, README quickstart). Note ports, env vars, seed data, auth.
- **Drive:** how can an agent interact with it programmatically? Existing harnesses first. Playwright/Cypress specs, expect scripts, PTY helpers, curl-able endpoints, a debug port. Only then pick a generic recipe: browser/CDP for web and Electron, a tmux/PTY harness for CLI/TUI, plain HTTP for services.
- **Observe:** what evidence can be captured? Screenshots, terminal transcripts, response bodies, logs, exit codes, DB state.
- **Isolate:** can two instances run side by side (ports, data dirs, profiles)? The generated skill must refuse to double-drive a shared instance. If isolation is possible, name the handle and require it on every command. If it is not, refuse a second concurrent drive rather than corrupt the user's session. A short-lived CLI isolates with `--run-id` or a fresh PTY, and may share a checkout. Do not emit `--checkout` unless the interview found a long-lived desktop driven over CDP whose port and profile are derived from a git checkout.

If the checkout doesn't build or start as-is, fix that first (or report it precisely) before generating. A skill written against a broken base teaches wrong steps. When an irrelevant missing asset blocks startup (a static dir the API never serves, a sample config), the generated skill may create it, clearly marked as verification scaffolding, and remove it in cleanup.

## 2. Generate the skill

Write `SKILL.md` at the path above with YAML frontmatter:

- `name: verify-<app>`
- `description` that is Use-when triggers only. Name the app, the surface, and when to reach for the skill. Do not dump Launch/Doctor/Drive into the description.
- `disable-model-invocation: true`

Without frontmatter the skill never registers. Then write these sections, each grounded in what the interview actually found (no placeholders left):

- **Launch:** the exact command that starts the app for verification, and how to tell it's ready (a log line, a port answering, a prompt). Include teardown. For a short-lived CLI or TUI there is no server to keep alive. Launch means build the binary (or install deps) once, then start each drive in its own isolated PTY or tmux session. Encode the Isolate answer here. Refuse double-drive of a shared instance.
- **Doctor:** one read-only check that answers whether this instance is worth driving. Process up, right version/build, port owned by us, auth valid. An agent runs this first whenever anything looks off.
- **Drive:** the harness recipe with real selectors/commands from this repo, not examples. Prefer stable handles (ARIA labels, data attributes, prompt strings, route paths) over coordinates and tab order.
- **Proof bar:** do not submit "look, it opens." Proof is the production user path plus an observable result a skeptical reviewer would accept. Exercise every reachable entry point, mode, gated variant, and the success, cancel, error, empty, and persistence paths the change can affect. Show the trigger and the stable end state in the same evidence. Verify side effects, not only the final screen. Run doctor first. A capture against a stale or wrong instance is not evidence. For a broad regression, walk `features/README.md` top to bottom.
- **Evidence:** what to capture for a proof and where it goes. Exercise the real user path, not internal setters or test-only endpoints. Capture the action and the resulting state, not just the final screen. Verify side effects (files written, rows inserted, messages sent) alongside what's visible. Mocks only where a production boundary already isolates the external system. When the safe path is a dry-run or test mode, verify what it actually skips by observing (files, network, git refs) rather than trusting its name: some dry-runs still touch the network or open a browser.
- **Cleanup:** how to tear down instances the run created. Never kill by process name. Kill what you started. Cleanup removes instances and scratch state, never the evidence. Proof artifacts survive the teardown, in a location the skill names.
- **Helpers:** ship the driver. Make it executable. Show the invocation in the skill body. A helper the reader has to reverse-engineer is not a helper. The verification-skill-example omits its driver on purpose (usage-only sample). Generated skills do not copy that omission.

## 3. Seed the feature map

Create `features/README.md` plus one file per user-facing feature you can identify (aim for the top 3-5 to start, from routes, commands, menus, or docs). Put the map at skill-root `features/`, next to `SKILL.md`. Do not nest it under `references/features/` (that layout is the sample app). Do not write it under `openspec/`.

Follow the shape in [`references/feature-map-example/`](references/feature-map-example/), with a README index and one file per feature. The README must include `## Full sweep`. Walk `features/README.md` top to bottom for a broad regression. Driving one convenient feature is not a sweep. Add a journeys closer only when the app has cross-feature paths.

Each file answers, from the user's point of view, what the feature is, how to reach it, how to drive it with the harness, and what observable end state proves it works. The four H2s are `Sub-features`, `How to get to it (user POV)`, `Driving it with <harness>`, and `Gotchas`. The map is the repo's maintained verification source. A proof that drives one convenient entry point is incomplete when the map lists others.

## 4. Prove the generated skill before handing it over

Run its own instructions end to end once: launch, doctor, drive ONE mapped feature (one is enough for this smoke, and the map exists so later runs can cover the rest), capture evidence, clean up. That smoke is not a Full sweep. After cleanup, confirm the evidence still exists at the named location. A cleanup that eats the proof fails this step. Fix what fails, and run the generated cleanup after every failed iteration too, so broken attempts don't strand processes and ports. A generated skill that was never executed is a draft, not a deliverable.

## 5. Offer the maintenance loop

Point the user at `/maintain-verification-skill` for keeping the map honest as the app changes. Suggest a cadence only if they ask.
