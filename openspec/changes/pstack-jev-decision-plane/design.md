# Design

## Goal

Define a removable semantic decision contract without changing runtime behavior. The existing pstack route remains the acting route and the comparison baseline.

## Ownership

```text
deterministic facts / explicit command / hard policy
                     |
                     v
          precomputed baseline route
                     |
                     +-------------------------+
                     |                         |
                     v                         v
              acting route              optional shadow request
                                               |
                                               v
                                SemanticDecisionProvider.decide
                                               |
                                               v
                                      outcome + receipt
```

The caller owns authority, mode, eligibility, baseline routing, fallback, and evidence persistence. The provider owns one bounded judgment. An adapter may later own transport, authentication, serialization, model selection, and bounded retry behavior. No provider adapter or runtime call is part of this change.

## Provider-neutral shapes

The sketches below define the linked shapes used by the requirements. They are design constraints rather than a runtime schema.

```ts
type ChoiceOption = { id: string; label: string };
type NonEmptyChoices = readonly [ChoiceOption, ...ChoiceOption[]];
type ScoreRange = { minimum: number; maximum: number };

type DecisionRequest =
	| { kind: "choice"; questionId: string; context: SafeContext; choices: NonEmptyChoices }
	| { kind: "score"; questionId: string; context: SafeContext; range: ScoreRange }
	| { kind: "boolean"; questionId: string; context: SafeContext };

type DecisionOutcome =
	| { status: "decided"; kind: "choice"; value: string }
	| { status: "decided"; kind: "score"; value: number }
	| { status: "decided"; kind: "boolean"; value: boolean }
	| { status: "abstain" }
	| { status: "unavailable" }
	| { status: "invalid" };

type ProviderObservation = {
	outcome: DecisionOutcome;
	confidence?: number;
	probabilities?: Readonly<Record<string, number>>;
	providerIdentity: string;
	modelIdentity: string;
};

interface SemanticDecisionProvider {
	decide(request: DecisionRequest): Promise<ProviderObservation>;
}
```

The union correlates each decided value with its question kind. Non-decided variants cannot carry a decided value. Provider identity and model identity belong in integration metadata because the provider must not decide routing authority.

## Egress policy

Every candidate input receives exactly one class before request construction.

```ts
type EgressClass =
	| "local_only"
	| "safe_to_send"
	| "derived_sanitized"
	| "prohibited";

declare const safeContextBrand: unique symbol;
type SafeContext = string & { readonly [safeContextBrand]: true };
```

Only the egress boundary may construct `SafeContext`. It may do so from a public sanitized fixture or an explicitly selected public current-task summary with closed labels. The current prompt is not public by default. Secret detection cannot promote input to a sendable class.

Raw transcripts, diffs, repository dumps, logs, tool output, files, authentication material, configuration, and secrets are `local_only` or `prohibited`. Lossy redaction or truncation cannot turn rejected input into sendable input. Rejection returns the precomputed baseline route without calling the provider.

The conservative policy ceilings are 2,048 UTF-8 bytes for context, 32 choices, 64 UTF-8 bytes per identifier, 128 UTF-8 bytes per label, and 8,192 UTF-8 bytes for the complete request. These are policy limits. They are not measured provider, latency, cost, or quality facts.

Evidence stores a fixture identifier, fixture digest, closed labels, and revision identities. It never stores raw context. A digest is correlatable evidence for a sanitized fixture. It is not anonymous.

## Canonical mapping

The canonical registry lives at `references/decision-routing.json`. Each row identifies one canonical playbook, its source blob, and one selection: `direct`, `semantic_candidate`, or `system_two`. A semantic candidate also carries one unique class label. Direct routes bypass semantic classification. Human and safety gates remain policy in the formal contract, not mutable registry flags. The registry contains no provider names, model names, confidence thresholds, or execution authority.

Explicit or directly inspectable routes bypass the semantic provider. High-risk, generative, arithmetic, tool-execution, shipping, and preference decisions have no semantic authority. An eligibility result is a classification hint only. It cannot authorize execution. An unknown or `other` class returns the baseline route. Skill suggestion remains unavailable until a separate grounded taxonomy and caller exist.

## Receipt and fallback

```ts
type DecisionReceipt = {
	source: "deterministic" | "semantic_provider" | "system_two" | "human" | "observation";
	observation: ProviderObservation;
	mode: "shadow" | "advisory" | "controlling";
	implementationRevision: string;
	canonicalMappingRevision: string;
	providerIdentity: string;
	modelIdentity: string;
	policyQuestionSetRevision: string;
	fixtureRevision: string;
};
```

Provider and model identities must be available at runtime before a receipt can support control. `unknown` cannot authorize a controlling result. A missing field, stale revision, provider failure, invalid result, or receipt persistence failure returns the already computed baseline route. Evidence contains no hidden reasoning or raw input.

## Gates

#197 must accept and merge the reconciled specification. #209 must complete the refreshed baseline before runtime implementation starts. Later work must produce blinded Eval evidence under #198 and prove evidence freshness under #199. Exact-head Swarm and Interrogate review plus rollback proof under #200 must pass before promotion.

No-change remains the acting baseline and is a valid final outcome. This contract makes no claim about an unrun Jev evaluation, provider quality, latency, or cost.

## Non-goals

- No provider runtime or adapter.
- No runtime schema. The canonical mapping is a source registry, not a runtime schema.
- No shared decision service or generic provider gateway.
- No skill-suggestion caller.
- No workflow runtime, durable decision store, or new agent role.
