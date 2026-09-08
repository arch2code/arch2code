# Plan: YAML diagnostics that show the offending source

- **Status:** DEFERRED — captured for a future date, confirmed by user decision
  on 2026-09-08. The enabling work is done; this records what is left, what it
  costs, and the one hazard that must be settled first. Nothing here is
  scheduled.
- **Source:** review during the multi-clock work (issue #129), after the
  diagnostic-location consolidation.
- **Goal:** a YAML diagnostic prints the statement it is complaining about, with
  the specific token indicated, instead of only naming `file:line`.

## 1. What is already in place

Two pieces of groundwork make this affordable; before them it would have meant
auditing 84 independently formatted messages.

1. **One location constructor.** `projectCreate.diagnosticLocation(yamlFile, lc)`
   is the sole producer of location text for YAML diagnostics; 84 call sites route
   through it and none formats its own `path:line`. A source-excerpt renderer is a
   sibling of that function, not a sweep of the call sites.
2. **Diagnostics name the section key's own line.** `_sectionKeyLc` recovers a
   section key's position from the parent mapping, because a section's own `lc` is
   the `lc` of its *body*, which sits a line lower in block style. Covered by
   `unittest/test_error_missing_fields.py::test_diagnostic_reports_1_based_yaml_line`,
   which fails if the position is taken from the body or if the 0-based ruamel
   line is not converted.

## 2. The position data ruamel already carries

Probed rather than assumed. For

```yaml
clocks:
  clk:   { period: 1, desc: fast }
  clkSlow: { period: 3, bogusField: 7 }
```

```
body per-key data: {'clk': [1, 2, 1, 9], 'clkSlow': [2, 2, 2, 11]}
row per-field:     {'period': [2, 13, 2, 21], 'bogusField': [2, 24, 2, 36]}
```

Each entry is `[key_line, key_col, value_line, value_col]`, 0-based. So the
column of the offending **field** is a dictionary lookup away, and most
field-level diagnostics already know the field name. A caret under the exact
token is available without new plumbing.

## 3. Design constraints

- **`printError` needs no signature change.** It takes one string and prints it
  verbatim (`arch2codeHelper.py:157`), so a multi-line excerpt can simply be
  appended to the message. The colour wrapper covers the whole block.
- **The excerpt cannot come from `diagnosticLocation`.** Its return value is
  spliced mid-sentence, and an excerpt has to trail the message. It therefore
  needs a sibling function called at the end of each adopting message — so
  adoption is per-site, and should be selective rather than universal.
- **Do not extend the YAML byte cache to serve diagnostics.**
  `yamlReadCache` holds every parsed file's raw bytes, but is deliberately
  cleared at `processYaml.py:4426` so the whole closure does not stay resident;
  the `_post_*` validators run after that point. Re-read the single file on the
  error path instead. One read in a process that is about to exit is the same
  trade already made for location strings: the work happens only once something
  has gone wrong.

## 4. The hazard to settle first

**Some rows carry a borrowed `lc`.** `_encoders` and `postParseRegisterPorts`
synthesise rows and copy a `LineCol` from a different parsed row. Today that
yields a quietly wrong line number. An excerpt would print source text that is
not the fault, with a caret under an unrelated token — confidently wrong instead
of quietly wrong.

So an excerpt must either be shown only where the `lc` provably belongs to the
row, or be suppressed where provenance is unknown. Establishing that provenance
is the bulk of the work, not the rendering.

## 5. Scope when picked up

- Adopt at the field-level sites in `processSimple` and `_constants`, where the
  field name is known and the `lc` provably belongs to the row.
- Do not adopt at synthesised-row sites until §4 is settled.
- Smaller decisions, none blocking: tab handling for caret alignment, truncation
  of long or flow-style lines, and whether the caret marks the key or the value.
- Test churn is mostly additive, since existing assertions match substrings; any
  harness comparing whole output will need updating.
