# CLI 1.5.16 Models, Effort, ACP, and Plugin Validation

## Sub-features

- Live `agy models` slugs (`gemini-4-hydrogen-*`, `gemini-3.8-flash-*`, `claude-opus-4-6-thinking`, `claude-sonnet-4-6`) plus documented Neon and Orchestrator entries
- November 30, 2026 deprecation tracking and strict exclusion of `gpt-oss-*` prefixes
- Startup `--effort` / `/effort` levels (`low`, `medium`, `high`, `xhigh`, `max`) vs fixed-budget `Orchestrator`
- Strict native packaging proof (`agy plugin validate --strict --json`, `agy agents`, `agy acp`, plugin-root `hooks.json`)

## How to get to it (user POV)

Run `uv run python scripts/prove_antigravity_native_package.py --json` and inspect `agy_validation.findings` and discovered component counts.

## Driving it with Antigravity

Execute `bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh all` and optionally run `PSTACK_RUN_HOST_DEPENDENT_TESTS=1 uv run pytest -q tests/test_harness_drivers.py -k antigravity`.

## Gotchas

- `~/.gemini/config/plugins/pstack` must keep root `plugin.json` canonical with no stale `.antigravity-plugin/plugin.json` or repo cache directories inside it.
- Hook matchers in `hooks.json` must reference headless tool IDs (`view_file`, `replace_file_content`, `write_to_file`) rather than interactive aliases.
- `"gpt-oss"` must not appear anywhere inside projected `.antigravity-plugin/models.json`.
