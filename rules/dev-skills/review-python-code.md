---
name: review-python-code
description: Review Python code for Arch2Code builder/base internals, with emphasis on finding unnecessary defensive code, fallback paths, compatibility wrappers, and lazy agent-added guards. Use when reviewing Python changes under builder/base.
---

# Review Python Code

Use this skill when reviewing Python changes under `builder/base`. Focus first on whether the change is direct, contract-driven, and aligned with existing builder ownership boundaries.

## Review Priority

Look for unnecessary defensive code before style issues. Agents commonly add guards, fallbacks, compatibility shims, and optional behavior to avoid understanding the real data contract. Treat that as a likely bug unless there is a concrete caller or user-authored input case that requires it.

## Defensive Code Smells

Flag these patterns when they appear in internal Python paths:

- `dict.get()` or `or {}` fallbacks for fields guaranteed by schema, config, or a `projectOpen` view. Ther parser in `projectCreate` adds all fields
- Catch-all `try/except`, broad `except Exception`, or fallback-on-error behavior that hides a violated invariant.
- Optional parameters such as `resolver=None`, `fatal=None`, `strict=False`, or `allow_missing=True` added without an existing caller that needs both paths.
- Parallel APIs such as `foo()` plus `tryFoo()`, `getFoo()` plus `getFooOrDefault()`, or new wrappers that preserve an old internal shape.
- Compatibility code for intermediate dictionaries, generated view rows, or template inputs on the same branch.
- Silent defaults for missing project data, template mappings, schema fields, register fields, interface definitions, or config keys that should have been created earlier.
- Type checks that route around known internal shapes instead of fixing the producer.
- Empty-list, empty-dict, or empty-string substitutes that let generation continue with incomplete required state.
- A failed lookup returned as a plausible value, such as `return x['width'] if x else 0`. Zero is a valid width, count, or address, so the failure is consumed as data rather than reported. Return the failure.

## Contract-Driven Review

For each fallback or guard, identify the contract it is protecting:

1. If the value comes from user-authored YAML, ask whether the YAML form is valid and where validation or migration belongs.
2. If the value comes from schema tables, config, or post-parse state, required fields should be created or validated during `projectCreate`.
3. If the value comes from a generator-facing view, required fields should be produced by the `projectOpen` view helper.
4. If the value is optional by design, the code should branch on that named optional relationship directly, not by using broad defaulting.

Prefer findings that say where the invariant should be enforced rather than only saying that a fallback is suspicious.

## Builder Ownership Boundaries

- Put validation, normalization, migration of accepted YAML, schema population, and durable derived facts in `projectCreate`.
- Put template-facing, language-neutral reshaping in `projectOpen` view helpers.
- Keep templates and template utility modules focused on selecting fields, iterating rows, formatting syntax, and emitting text.
- Do not approve code that reparses YAML, recomputes global derivations, or reconstructs semantic views inside generators or template utilities.

## Review Questions

Ask these questions while reviewing:

- Is this guard handling valid user input, or is it hiding a broken internal producer?
- Can this path actually be reached by a current caller?
- Would failing fast expose the real bug closer to the source?
- Should this be a schema/config/view invariant instead of a consumer fallback?
- Did the change add flexibility that the requested behavior did not need?

## Finding Style

When reporting an issue, be specific and actionable:

- Name the defensive pattern.
- Explain the invariant or ownership boundary it violates.
- Point to the producer that should guarantee the value.
- Suggest removing the fallback when no current valid input requires it.

Do not request abstractions, compatibility layers, or extra configurability as review fixes unless there is an existing tested consumer that needs them.
