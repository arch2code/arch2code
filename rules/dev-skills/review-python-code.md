---
name: review-python-code
description: Review Python code for Arch2Code builder/base internals, with emphasis on finding unnecessary defensive code, fallback paths, compatibility wrappers, and lazy agent-added guards. Use when reviewing Python changes under builder/base.
---

# Review Python code

Load `builder-base-development` with this skill. It owns the rules a reviewer checks against: where a change belongs, the internal data contracts, comments, declaration order, no string splitting for lookups, and no SQL over data already in dicts. This skill adds what to look for and how to report it.

## Review priority

Look for unnecessary defensive code before style. Agents add guards, fallbacks, compatibility shims and optional behavior to avoid learning the real data contract. Treat each one as a likely bug unless a current caller or a valid user-authored input needs it.

## Defensive code smells

Flag these in internal Python paths:

- `dict.get()` or `or {}` on a field the schema, config or a `projectOpen` view guarantees. Scalar schema fields always exist on a row. An optional sub-table is absent in `projectCreate` and `None` in `projectOpen`, and a block with no rows in a derived table has no key there. Branching on those is correct, for example `self.data['containerLocalNets'].get(blockKey, [])` or `intfDef['parameters'] or {}`. Do not flag those.
- Catch-all `try/except`, broad `except Exception`, or fallback-on-error behavior that hides a violated invariant.
- Optional parameters such as `resolver=None`, `fatal=None`, `strict=False` or `allow_missing=True` without an existing caller that needs both paths.
- Parallel APIs such as `foo()` plus `tryFoo()`, or `getFoo()` plus `getFooOrDefault()`.
- Compatibility code for old shapes of intermediate dictionaries, view rows or template inputs. The only compatibility boundary is user-authored YAML accepted by `projectCreate`.
- Silent defaults for missing project data, template mappings, schema fields, register fields, interface definitions or config keys that an earlier step should have created.
- Type checks that route around a known internal shape instead of fixing its producer.
- Empty-list, empty-dict or empty-string substitutes that let generation continue with incomplete required state.
- A failed lookup returned as a plausible value, such as `return x['width'] if x else 0`. Zero is a valid width, count or address, so the caller treats the failure as data.

## How a failure should be reported

The codebase reports a failure in one of three ways. Ask for the one that fits:

- **Bad user YAML.** `projectCreate` calls `self.logError()` with a message that names the YAML file and the offending item.
- **A broken internal invariant.** Raise, or print an `Internal error:` message and exit, as `splitQualifiedKey()` does.
- **A lookup whose caller writes the message.** Return `None` only there, as `qualifyKey(..., fatal=False)` in `pysrc/valueResolver.py` does.

## Tracing the contract

For each fallback or guard, find who creates the value:

1. User-authored YAML. Is the YAML form valid? `projectCreate` validates it. `projectCreate` accepts only the current format. `make migrate` rewrites any other.
2. Schema tables, config or post-parse state. `projectCreate` creates or validates required fields.
3. A generator-facing view. The `projectOpen` view helper produces required fields.
4. An optional relationship. The code branches on that relationship by name, not by broad defaulting.

## Ranking findings

- **Defect.** The guard hides a broken invariant, turns a failure into data, or lets generation continue with missing required state.
- **Convention.** The guard is unreachable on a guaranteed path and only adds noise, or the code breaks a `builder-base-development` rule without changing output.

## Finding style

- Name the defensive pattern.
- Name the invariant or ownership boundary it breaks.
- Point to the producer that should guarantee the value.
- Suggest removing the fallback when no current valid input needs it.

Do not ask for abstractions, compatibility layers or extra configurability as fixes unless an existing tested consumer needs them.
