# Adapter version identity is grokbuild, not plugin name

- Status: accepted
- Date: 2026-08-31

## Context

pstack is one plugin in one git repo. ADR 0009 locks `MAJOR.MINOR.PATCH-grokbuild.N` as SemVer plus adapter counter. Catalog siblings use `MAJOR.MINOR.PATCH-<plugin-name>.N` because they share one tag namespace (ADR 0003). Specs named each grammar in isolation. A later agent could copy catalog name-in-version onto pstack (`0.14.5-pstack.N`) and drop the grokbuild adapter identity.

## Decision

pstack versions MUST remain `MAJOR.MINOR.PATCH-grokbuild.N`. They MUST NOT use `-pstack.N` or other catalog sibling name-in-version. Unifying with grok-build-plugins is forbidden. Existing tags MUST NOT be moved.

## Consequences

Cursor overlay MAJOR.MINOR.PATCH stays the foreign key. Adapter counter stays grokbuild. Catalog uniqueness stays a catalog problem.
