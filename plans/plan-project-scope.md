# Plan: Project-scoped declarations (`scope: project`)

- **Status:** IMPLEMENTED and **verified** — Phase 1 may build on it. Three
  remediation rounds and two independent adversarial reviews; §12 records the
  findings, §13 the outcome and the residual pre-existing items left unfixed. The
  final review found no live defect. Unit suite 92 suites 0 failures, example
  suite regenerates byte-identical, `make two-clk` green.
  The history is worth keeping in view: the first review reproduced **eight
  confirmed defects** in an implementation whose suite was already passing, and
  the decisive one was that the suite passed with a load-bearing line of the
  implementation deleted. Passing was never the evidence; mutation was. Changes
  are unstaged in `builder/base`.
- **Source:** design session on issue #129 multi-clock support, split out so the
  scope mechanism is designed on its own.
- **Components touched:** `pysrc/processYaml.py` (`createProjectConfig`, a parse
  pre-pass, the FK scope branch), `pysrc/schema.py` (scope value validation),
  `config/SCHEMA_SPECIFICATION.md`.
- **First consumer:** [`plan-multi-clock-reset.md`](./plan-multi-clock-reset.md)
  §2.0.3. This plan is the prerequisite and lands first.
- **Shared fixture:** the multi-clock example serves both plans. Phase 0 lands
  the `clocks:` / `resets:` **sections** (that plan's §2.1, §2.2) and the example
  that declares them, with no derivation and no emission. The sections exercise
  project scope end to end as real schema content, and the clock feature then
  builds on a fixture that already exists. See §8.
- **Anchors** were verified against current source during the design session;
  line numbers drift, so confirm before editing.

---

## 1. What this delivers

A way to declare a schema-backed object **once per project** and reference it
from any of that project's contexts, without include-chain plumbing and without
`scope: global`. The declaration is authored in the project file; resolution is a
new `_validate` option, `scope: project`.

The toolchain has no such mechanism today. The two existing scopes are the
include-chain walk (too narrow: every referring file must include the declaring
file) and `scope: global` (wrong: see §3).

---

## 2. Problem

Some design facts are properties of a whole project rather than of one context.
Clocks and resets are the motivating case: a design has a small set of them, any
block may reference any of them, and threading a declaration file into the
include chain of every context that mentions one is pure ceremony.

Expressing that today forces a bad choice:

- **Include-chain scope.** Correct and composable, but every design file naming
  the object must include the declaring file. The plumbing burden scales with
  the design, and it invites a single "include everything" file that destroys
  context isolation.
- **`scope: global`.** Discouraged by contract and wrong for composition (§3).

---

## 3. Why `scope: global` is not the answer

- `config/SCHEMA_SPECIFICATION.md` states that global lookup "discards
  include-chain isolation and is therefore undesired", and that adding or
  retaining `scope: global` "requires explicit architect signoff".
- It breaks multi-project composition outright. `_lookupInGlobal`
  (`pysrc/processYaml.py:7775`) raises `Duplicate key ... found in global
  context` when two contexts declare the same name. Two composed projects that
  each declare a clock named `clk` would be a hard error rather than two
  correctly separate declarations.

Project scope is the missing middle: wider than an include chain, narrower than
the database.

---

## 4. Ground truth

Verified during design. These facts are what make the change small.

- **Child project files are parse contexts; the root project file is not.** This
  asymmetry drives the whole of §5.2 and is easy to miss.
  - A **child** project file, reached through a `projectFiles:` slot, is read by
    `readRaw` into `yamlAllFiles`, `yamlRaw`, and `yamlDependancies`
    (`pysrc/processYaml.py:4291-4313`), is assigned an `includeName`
    (`:4303-4306`), and is given its own context entry by `processYamls`
    (`:6066`). It already flows through `processSingleFile`, with its
    project-level keys skipped by `ignoreSections` — which is exactly what the
    comment at `:3963` refers to.
  - The **root** project file does not. It is loaded into `self.proj` at
    startup, and the file-read BFS is seeded from the *results* of its
    `getFileList` — its `projectFiles:` and `include:` entries — not from the
    file itself (`:3592-3610`). It therefore never enters `yamlAllFiles` or
    `yamlRaw`, is never handed to `processSingleFile`, and has no `yamlContext`
    or `contextOwningProject` entry.
  - Consequence: a section authored in the root project file is not merely
    parsed late, it is never parsed at all. A monolithic project has exactly one
    project file and it is the root, so this is the common case, not an edge
    case.
- **`ignoreSections` is consulted in exactly one place**, the section dispatch at
  `pysrc/processYaml.py:6161`. Its base value is small (`:3448`); the bulk is
  added by `createProjectConfig` (`:3958-3970`), which adds **every** project-file
  key so that nested project files parsed as ordinary YAML skip their
  project-level keys.
- **Ownership is available at parse time.** `_deriveOwnershipFromScan()` runs
  before `processYamls()` (`pysrc/processYaml.py:3627-3632`), populating
  `self.contextOwningProject` (context to owning `projectName`), and a child
  project file's members are reattributed to the copy's declaring `projectName`
  (`pysrc/projectScan.py::_assignOwnership`).
- **The FK scope hook already exists.** `pysrc/processYaml.py:6496` computes
  `scope = validator.get('scope', yamlFile)` and passes it to
  `validateForeignKey` and thence to `lookupInScope`. `pysrc/schema.py:938`
  already carries an arbitrary scope string onto the validator.
- **Programmatic section injection is an established pattern.**
  `processSingleFile(context, sections=...)` is used at
  `pysrc/processYaml.py:4027` and `:5266`, and throughout
  `config/postParseRegisterPorts.py`. The reserved-context variant
  (`contextOverride`) is used for `systemFiles` at `:6060-6064`.
- **Dependency edges come only from `include:`.** `readRaw` records
  `yamlDependancies[f] = include` (`:4310-4313`); `projectFiles:` entries are
  queued for reading but are **not** dependency edges. A design file therefore
  has no ordering relationship with the project file, which is why §5.2 needs an
  explicit pre-pass rather than relying on the main loop's order.
- **A context only grows generated includes if it declares an `includeSections`
  member.** `includeValid[file]['valid']` is set at
  `pysrc/processYaml.py:6173-6174`, and `saveIncludeFiles` skips
  `smartInclude` file types for contexts that are not valid. A project file
  carrying only project-scoped rows stays `valid: False` and generates nothing,
  provided the new sections are not added to `includeSections` (§6.1).

---

## 5. Design

### 5.1 Declaration

A project-scoped object is authored as an ordinary schema section in the project
file:

```yaml
projectName: myIp

clocks:
  clk: {desc: "main design clock", period: 1, timeUnit: ns, default: true}
```

The section is defined in `config/schema.yaml` like any other, and is parsed by
the ordinary machinery. It is **not** saved into the DB-backed config, and it is
**not** merged through the base/pro/user project merge (§6.2).

### 5.2 Parsing

Parsing is driven by an explicit pre-pass. The main `processYamls` loop is not
used for these sections at all.

**Why a pre-pass, and not the ordinary loop.** Two independent reasons, either of
which alone would require it:

1. **The root project file is never parsed** (§4). A section authored there
   would be silently ignored by the ordinary loop, because the loop never sees
   the file. This is the common case, so it is not a corner to be tidied later.
2. **Parse order is not guaranteed for child project files.** Dependency edges
   come only from `include:` (`:4310-4313`); `projectFiles:` entries are not
   edges, so no design file is recorded as depending on its project file. Since
   foreign keys are validated at parse time (`:6496`), a reference parsed before
   the declaring rows exist fails outright. Relying on the insertion order of
   `yamlDependancies` would make correctness incidental.

**What the pre-pass does.** It runs once, after `_deriveOwnershipFromScan()` and
before `processYamls()` (`:3627-3632`), and for each project file in the build —
the root and every child — parses that file's project-scoped sections into a
bucket keyed by the declaring **`projectName`**.

**The bucket is keyed by `projectName`, not by the project file path.** The rows
land in the ordinary schema tables, in their own per-project bucket:
`self.data['clocks']['myIp']`. Keying by `projectName` rather than by the project
file is what makes the container searchable by the identity callers actually
have, and it deletes machinery rather than adding it — see §5.3, where the
`projectName -> projectFileContext` map this plan previously required disappears
entirely.

The alternative, keying by the project file path and resolving
`projectYaml -> projectName` at lookup time, is equivalent in behaviour and left
to the implementer if it turns out to fit the parse-time code better. The
project file path is available either way, since the pre-pass is iterating it.

A child IP's rows therefore land in the **child's** bucket, under the child's
`projectName`. That is what makes the mechanism composable.

**The bucket is deliberately not a context.** The pre-pass registers **no**
`yamlContext`, `includeValid`, or `includeName` entry, and contributes nothing to
the persisted `YAMLCONTEXT` blob. Project-scoped data is a separate container
that the ordinary context machinery never sees, which is what keeps this change
from rippling outward (§6.3). The one registry entry worth adding is
`contextOwningProject[<projectName>] = <projectName>`, which is trivially true
and makes any generic owner lookup that does encounter a project bucket safe
rather than a `KeyError`.

**Invariant: every project in the build contributes its rows to the database.**
A composed build has one database spanning every project in the graph, and
downstream projects' project-scoped rows belong in it exactly like their blocks,
interfaces, and connections. Two consequences that must not be conflated:

- **Ownership gates generation, never data.** The composition work gates which
  project *emits* which artifact; it does not remove a child's data from the
  database. A downstream project's project-scoped rows are required in the
  database whether or not that project emits anything in this build, because its
  own design YAML resolves against them and because an assembler must be able to
  see them.
- **Not a context does not mean not in the database.** The rows are ordinary
  schema rows in ordinary schema tables; only the *context registries* are left
  untouched. `_a2csystem` is the precedent for the distinction: it is in
  `specialContexts` and excluded from include generation, yet its
  `interface_defs` rows are plainly in the database and resolve normally.

Per §9, a project file produces a bucket when it declares a project-scoped
section or receives an injected one, so under the shipped schema every project
owns one. A project file that declares a section is always parsed, root or
downstream, so no rows are dropped either way.

**Section dispatch.** Project-scoped sections **remain** in `ignoreSections`.
That is what stops a child project file's sections being parsed a second time
when the main loop later reaches it as an ordinary file. Because the gate at
`:6161` is inside the section loop, the pre-pass drives `processSection()`
(`:6176`) per section rather than `processSingleFile()`, replicating the small
setup the latter performs — binding `self._parserResolver` to the bucket key.
This is preferred over adding a bypass parameter to `processSingleFile`, which
would create a parallel API for one caller. Driving `processSection()` directly
is also what keeps the pre-pass clear of `processSingleFile`'s context-registry
side effects, which populate `includeValid` and `yamlDir` (`:6146-6155`).

**The `createProjectConfig` change** (`pysrc/processYaml.py:3958`) therefore
reduces to one thing: project-scoped sections join the `notConfig` set so they
are not also saved into the DB-backed config as `CLOCKS`, `RESETS`, and so on.
They continue to be added to `ignoreSections` as today.

The set of project-scoped section names is derived from the schema, not
hand-listed: a section is project-scoped when its schema entry declares it so
(§5.4). That keeps one source of truth and prevents drift from
`config/schema.yaml`.

### 5.3 Resolution — `scope: project`

```yaml
connections:
  clock:
    _type: optional()
    _validate:
      section: clocks
      field: clock
      scope: project
```

Resolution is a **direct bucket hit, not an include-chain walk**. For a referring
row in `yamlFile`:

```
owner  = self.contextOwningProject[yamlFile]     # already populated pre-parse
row    = self.data[<section>].get(owner, {}).get(<name>)
```

`contextOwningProject` is exactly the map needed, and it is already built before
`processYamls()` (§4). Because the bucket is keyed by `projectName`, no
`projectName -> projectFileContext` map is required — the piece of machinery an
earlier draft of this plan called for is deleted by keying on the identity the
caller already holds.

The change lands in two places:

- `pysrc/processYaml.py:6496`, where `scope = validator.get('scope', yamlFile)`
  is computed, gains a `'project'` branch that performs the direct hit above
  instead of falling through to the include-chain walk.
- `lookupInScope` is left alone. It is the include-chain resolver; project scope
  is a different resolution strategy and should not be threaded through it as a
  special case. This mirrors how `_lookupInGlobal` (`:7775`) is a separate
  branch rather than a mode of the walk.

A miss returns nothing and produces the §7 diagnostic. There is no fallback to
the include chain and none to `_a2csystem`: a `scope: project` reference resolves
in the owning project or not at all, which is what makes two composed projects
declaring the same name unambiguous.

### 5.4 Declaring a section project-scoped

A section is marked in `config/schema.yaml` via a new table-level attribute,
`projectScope`:

```yaml
clocks:
  _attribs: [flat, projectScope]
  clock: key
  ...
```

The attribute is the single source of truth for three things: which project-file
keys the pre-pass parses (§5.2), which keys join the `notConfig` set so they are
not also saved into the DB-backed config (§5.2), and the authoring-location check
(§7).

An alternative is to infer project scope from the presence of a `scope: project`
validator pointing at the section. That is rejected: it makes a section's
authoring location depend on whether some other section happens to reference it,
which is action at a distance and breaks the moment the last reference is
removed.

---

## 6. Constraints and hazards

### 6.1 Do not add project-scoped sections to `includeSections`

A project file carrying project-scoped rows must stay `valid: False` in
`includeValid` so `saveIncludeFiles` emits no context header for it (§4). If a
future project-scoped section genuinely needs generated artifacts, that is a
separate design question and must not be solved by quietly adding it to
`includeSections`.

### 6.2 The base/pro/user merge is bypassed

Routing these sections through the parser rather than `createProjectConfig`
means they do not inherit through `merge_with_spec`. This is deliberate: a
declaration shipped in `$a2c/config/project.yaml` must not silently appear in
every project. It is also protective, because the merge default is
`dict_shallow` (`pysrc/merge_utils.py:44`), which would merge base rows into every
project per key, with no removal sentinel — see
[`plan-multi-clock-reset.md`](./plan-multi-clock-reset.md) §2.5 for the concrete
defects that causes.

The consequence to document: a project-scoped section behaves differently from
every other project-file section. A consumer needing a shipped default should
inject it in `projectCreate` through the same `processSingleFile` call, so the
injected rows are indistinguishable from authored ones downstream.

### 6.3 Project buckets must not leak into the context registries

The separate-container design of §5.2 exists to keep this change from rippling
outward. An earlier draft registered the project file as a real parse context,
which would have added an entry to every context-iterating structure in every
project — including monolithic ones — and required auditing each consumer for the
assumption that a context corresponds to a design YAML file. Keying a separate
bucket by `projectName` and registering no context removes that work rather than
managing it.

The obligation this creates is a negative one, and it must be tested rather than
assumed. After the pre-pass, none of the following may contain a project bucket
key: `yamlContext`, `includeValid`, `includeName`, the persisted `YAMLCONTEXT`
blob (`:3673`), or `CONTEXTNODEDIR`. The single deliberate exception is
`contextOwningProject`, which gains the identity entry described in §5.2.

Two supporting points:

- **Key collision.** A `projectName` and a context file key share the
  `self.data[section]` keyspace. Collision is implausible in practice, since
  context keys are relative paths ending in `.yaml`, but it should be a validated
  error rather than an assumption, and the check is one comparison.
- **The bucket key is a parse-time shape, not a `projectOpen` shape.** During
  parsing, rows are held per context as `self.data[<section>][<projectName>]`.
  After `projectOpen` the ordinary loading contract applies and a `flat` section
  is keyed by **qualified storage key** — `clk/assembler`, `clk/childIp` — in
  exactly the way `data['blocks']` is keyed by `qualBlock`. A view selects a
  project's rows by the row's `_context`, which carries the `projectName`. An
  earlier draft of this plan stated that views read
  `prj.data[<section>][<projectName>]`; that was wrong and would have misled the
  first view written against it.

### 6.4 One-way door on the section name

A section name used in the project file cannot also be a design-YAML section,
and the reverse. The two locations are mutually exclusive by construction, so
each new project-scoped section is a decision that cannot later be hedged.

---

## 7. Validation and errors

Implemented:

- **Scope values are validated in the schema.**
  `schema.py::_validate_foreign_key_lookups` previously checked the target
  section, the target field, and combo agreement, but not the `scope` value, so
  a typo reached `lookupInScope` and failed on a missing `yamlContext` key rather
  than at schema-validation time. It now rejects any scope outside
  (unset, `global`, `project`). A small pre-existing gap that the new value made
  worth closing.
- **`scope: project` and a `projectScope` target imply each other**, in both
  directions. A project-scoped section lives in a bucket, not a file context, so
  an include-chain or global lookup could never find it; requiring the pairing
  keeps every reference to such a section on the one resolution path that works.
  This also makes unreachable a failure discovered during implementation: an
  unscoped foreign key against a project-scoped section would default its scope
  to the referring file and then index `yamlContext` with a key that does not
  exist.
- **Per-project single default.** `_validateProjectScopeDefaults`, driven from the
  pre-pass once per project per contributed section, rejects both zero and more
  than one `default: true` within one project. Neither half can be a row hook: a
  row cannot see that no *other* row claimed the default, and the count is final
  only once the section is parsed. The rule belongs to
  [`plan-multi-clock-reset.md`](./plan-multi-clock-reset.md) §7 rather than to
  this plan. It applies to any project-scoped section declaring a `default:`
  field, and never to a section a project does not contribute. An earlier
  implementation put the at-most-one half in hand-written `_post_validateClocks` /
  `_post_validateResets` row hooks, which left the rule generic in its diagnostic
  but not in its enforcement; both hooks are removed.
- **Unresolved reference diagnostics** name the owning project and its project
  file rather than talking about include chains, so the author is pointed at the
  file they must edit.

**Not implemented — authoring location is not enforced.** A project-scoped
section appearing in a design YAML file, or a design section appearing in a
project file, is not rejected. Two complications for whoever takes it:

- A **child** project file is walked by `processSingleFile` as an ordinary file
  and legitimately carries `clocks:`, so a "project-scoped section in a design
  YAML" check must exempt project-file contexts.
- The reverse direction is fuzzier, because project files legitimately carry
  many non-schema keys.

Impact is mitigated rather than absent: a misplaced declaration now fails with
the diagnostic above, which names the project file the author must edit.

---

## 8. Test plan

The consumer is the **multi-clock example**, shared with
[`plan-multi-clock-reset.md`](./plan-multi-clock-reset.md). Phase 0 creates the
`clocks:` and `resets:` sections and the example that declares them, but
implements none of the clock feature: no per-block derivation, no port emission,
no wrapper changes. The sections are real schema content whose only job in this
phase is to be declared in a project file and referenced from design YAML, which
is exactly what project scope must support. The clock work then starts from a
fixture that already exists rather than inventing a throwaway one.

The example must be a **composed** fixture — a child IP project plus an
assembling project, each declaring clocks — because the composition case in the
list below is the acceptance gate for this plan and cannot be shown any other
way.

Following the convention that library content is validated in `unittest/` rather
than on every generator run:

- **Schema validation.** `scope: project` accepted; an unknown scope value
  rejected; `scope: project` against a non-project-scoped section rejected.
- **Resolution.** A design-YAML row referencing a project-file-declared object
  resolves. The same reference from a second, unrelated context also resolves,
  proving no include-chain edge is required.
- **Negative.** A reference to an undeclared name fails with a message naming the
  owning project's project file.
- **Authoring location.** A project-scoped section placed in a design YAML file
  is rejected, and vice versa.
- **Composition.** A fixture with a child IP project and an assembling project,
  each declaring the **same name** with different attributes. Both must resolve,
  each within its own project, with no duplicate-key error. This is the test that
  `scope: global` cannot pass, and it is the reason the mechanism exists.
- **Downstream rows reach the database.** In that same composed fixture, assert
  the child project's project-scoped rows are present in the database with the
  child's context and owning `projectName`, independently of whether the child
  emits any artifact in that build (§5.2 invariant). A reference from the child's
  own design YAML must resolve in the composed build exactly as it does when the
  child is built standalone.
- **No artifact leakage.** A project declaring project-scoped rows generates no
  context header for them (§6.1).
- **No context-registry leakage.** Assert directly that no project bucket key
  appears in `yamlContext`, `includeValid`, `includeName`, the persisted
  `YAMLCONTEXT` blob, or `CONTEXTNODEDIR`, and that `contextOwningProject`
  contains the identity entry and nothing more (§6.3). This is the negative
  obligation the separate-container design rests on, so it is asserted rather
  than inferred from the absence of symptoms.
- **Key collision.** A project whose `projectName` collides with a context file
  key is rejected with a clear error (§6.3).
- **Backward compatibility.** Full example suite regenerated with no YAML change,
  byte-identical output.

---

## 9. Settled decisions

1. The attribute is `projectScope` (§5.4).
2. The pre-pass creates a bucket for a project file that declares a
   project-scoped section **or receives an injected one**. This drops no rows: a
   project file that declares a section is always parsed, root or downstream
   (§5.2). As first written the condition was declaration-only, on the reasoning
   that a project declaring nothing gains nothing; that was superseded by the
   built-in clock and reset of
   [`plan-multi-clock-reset.md`](./plan-multi-clock-reset.md) §2.5, which every
   project receives, so under the shipped schema every project now owns a bucket.
   The declaration-only skip survives for a custom `dbSchema:` that declares
   neither section.
3. The bucket is keyed by `projectName`, and is not a context (§5.2, §6.3).
   Keying by the project file path with a `projectYaml -> projectName` lookup at
   resolution time is behaviourally equivalent and left to the implementer.

No open decisions remain in this plan.

---

## 10. Verification items — both HELD

1. **Child project ownership — held.** In a composed fixture (assembling project
   `assembler` plus child `childIp`), `contextOwningProject` attributes the
   child's design YAML to `childIp`. Both projects declare a clock named `clk`
   with different attributes; the child's reference resolves to `clk/childIp` and
   the parent's to `clk/assembler`, both present in the one database with no
   duplicate-key error. This is the acceptance gate of §8 and the case
   `scope: global` cannot pass.
2. **Root project `projectName` availability — held.** `PROJECTNAME` is
   populated by `createProjectConfig` well before the pre-pass and is the only
   root input required; children get theirs from `contextOwningProject`.

## 11. Implementation notes worth carrying forward

- **`post(...)` hooks must live on `projectCreate`.** `schema.py::_function_find`
  resolves `post(X)` only as `projectCreate._post_X`. `config/postParseChecks.py`
  hosts whole-project scripts invoked by `postYamlExternalScript()`, not row
  hooks, so a row hook cannot be placed there.
- **Phase 0 ships no real design-YAML consumer of `scope: project`.** The only
  reference in the shipped schema, `resets.clock`, is itself inside a
  project-scoped section. The design-YAML resolution path is therefore covered by
  a test-only schema section rather than by shipped content, and gets real
  coverage when the connection `clock:` field of
  [`plan-multi-clock-reset.md`](./plan-multi-clock-reset.md) §2.3 lands.

---

## 12. Adversarial review findings — remediation required

An independent review attacked the seven claims this plan makes. Claims 2
(ordering), 3 (composition), 6 (single default) and 7 (backwards compatibility)
were attacked and **held**, each by construction or execution rather than by
inspection. The rest produced the following. Every item below was reproduced by
the reviewer, not merely inspected, except where marked PLAUSIBLE.

### Must fix before Phase 1 builds on this

1. **Unguarded `contextOwningProject[yamlFile]` for special contexts**
   (`pysrc/processYaml.py:6589`, `:6601`). `_deriveOwnershipFromScan` keys that
   dict by real file paths, so a special context such as `_a2csystem` is absent.
   `processSingleFile:6229` already guards with
   `if contextFile not in self.specialContexts:`; the new foreign-key branch does
   not. Reproduced as a bare `KeyError: '_a2csystem'` with no diagnostic. Not
   reachable through the shipped schema today, because the only `scope: project`
   reference is `resets.clock` and `resets` is in `ignoreSections` — but the first
   such field placed on any section appearing in `$a2c/interfaces/*.yaml` crashes.
   `self.projectFileByName[owningProject]` at `:6601` has the same exposure.
2. **The symmetric schema check closes only one direction**
   (`pysrc/schema.py:720-735`). The two checks cover *references to* a
   `projectScope` section. Nothing rejects an ordinary include-chain foreign key
   on a *field of* a `projectScope` section, which can never resolve: the pre-pass
   parses with `yamlFile = <projectName>`, so `lookupInScope:7935` indexes
   `yamlContext[<projectName>]` and raises. Reproduced as `KeyError: 'assembler'`.
   This is the same failure mode §7 claimed to have made unreachable. Rule to
   add: a field of a `projectScope` node may not carry a `section:` validator with
   `scope:` omitted.
3. *(CLOSED — the pre-pass orders by schema declaration order, and the fix is
   mutation-covered by `test_project_scope.py::run_authored_order_build`.)*
   **Resolution depends on the author's key order in the project file**
   (`pysrc/processYaml.py:4007`). `sections = [s for s in raw if s in
   projectScopeSections]` walks the mapping in authored order and foreign keys
   resolve at parse time, so authoring `resets:` *above* `clocks:` fails with
   "value clk is not declared in the clocks: section" while `clk` is declared
   three lines below. This is the shipped schema's only `scope: project`
   reference, so it is the first thing a real user hits. Order the pre-pass by
   schema declaration order rather than authored order.
4. **The test cannot fail on the line it claims to cover**
   (`unittest/test_project_scope.py:222-244`). Deleting
   `self.ignoreSections.update(projectScopeSections)` (`processYaml.py:4053`)
   leaves all 17 assertions passing, because the assertion is satisfied by the
   pre-existing `ignoreSections.add` loop over `self.proj` — the fixture's *root*
   project declares both sections. The uncovered case is root-declares-nothing
   with child-declares-`clocks:`, which without line 4053 silently produces a
   duplicate row (`clk/childIp` from the bucket **and** `clk/ip/ipProject.yaml`
   from the child project file re-parsed as a design context) and exits 0. Needs a
   `_make_fixture("", CHILD_CLOCKS)` case plus an assertion that no `clocks` row
   carries a `.yaml` `_context`. Two further assertions in the same function are
   tautologies: `sections & includeSections` can never be non-empty, and the
   plan's no-artifact-leakage obligation is asserted only through that tautology.
5. **Duplicate `projectName` silently merges two projects' rows**
   (`pysrc/processYaml.py:4014`). The guard rejects `projectName in
   yamlAllFiles`, but not two project files declaring the same `projectName` —
   which lands both projects' rows in one bucket and clobbers
   `projectFileByName`. The underlying acceptance of a duplicate `projectName` is
   pre-existing and behaved non-deterministically between in-process and
   subprocess runs, which deserves its own investigation; the pre-pass adds a new
   silent-merge surface regardless.
6. **A `projectScope` section authored in a design YAML is silently swallowed.**
   `ignoreSections` is consulted at `:6244`, before the unknown-section check at
   `:6254`, so `clocks:` in a design file produces zero diagnostics where it
   previously produced `Unknown section: clocks found in top.yaml`. §7 records
   the missing enforcement, but `config/SCHEMA_SPECIFICATION.md` asserts a
   stronger and **false** invariant — that the two locations are "mutually
   exclusive by construction". The doc must be corrected even if enforcement
   stays deferred.
7. **Every project-file diagnostic names a non-file** (`:6602`). Messages read
   `In file assembler:9, ...`; `assembler` is a project name. The real path is in
   `projectFileByName` and is already interpolated later in the same string.
8. **Three in-code invariants are now false and were not updated.** The
   `contextOwningProject` identity entry at `:4022` contradicts the comments at
   `:3459`, `:1044-1046` and `:3684`, which still state the dict is keyed
   identically to `includeName`. Nothing iterates the dict today, so nothing
   breaks, but `projectOpen.getOwningProject(<projectName>)` now silently succeeds
   where it used to raise. `SCHEMA_SPECIFICATION.md` discloses the exception; the
   source comments do not.

### Lower priority

9. *(PLAUSIBLE)* `scope` is unvalidated on non-section validators
   (`pysrc/schema.py:682` returns early), so `_validate: {values: [...], scope:
   nonsense}` is accepted. Harmless at parse time, but `SCHEMA_SPECIFICATION.md`
   rule 5 states the constraint unconditionally.
10. *(PLAUSIBLE)* A combo foreign key may declare `scope: project`; the scope
    checks precede the combo branch and do not exclude it, and the new resolution
    path does a flat `.get` without calling `validateForeignKey`, so combo
    component matching is bypassed. Related: `projectScope` without `flat` is not
    rejected, yet composition depends on the qualified storage key only `flat`
    produces.
11. Minor, but named by `CLAUDE.md`: `:7871` uses a fallback default
    (`item.get('lc') is not None else '?'`) for a field `processSimple` always
    sets — note `:7782` sets the precedent, so fixing one means deciding about
    both; `:6601` recomputes `owningProject` and `varContext` at `:6591` is dead
    on the miss path; `_validateSingleProjectDefault`'s parameter is named
    `projectName` while both callers pass `yamlFile` (moot — the function is gone,
    consolidated into `_validateProjectScopeDefaults`); `projectFileByName` mixes
    two path bases across one family of diagnostics when `_rootProjFileAbs`
    exists; and `test_project_scope.py::_run` silently depends on
    `run_composed_build()` running before `run_schema_cases()`, which leaves five
    errors in the global counter.

### Supervisory note on verification

Finding 4 is the important one, beyond its own severity. A passing suite was
treated as evidence the mechanism was correct. It was evidence the mechanism was
not obviously broken. Mutation — deliberately breaking the implementation and
checking the test notices — is what distinguished the two, and it should be the
standard applied to the Phase 1 derivation tests as well, not only to this
remediation.

## 13. Remediation outcome and residual items

Three remediation rounds and two independent adversarial reviews. Round 3 closed
the one NOT CLOSED item, both material PARTIALs, and the two lesser items; the
final review found no live defect in the code. What follows is what remains
known and unfixed, so nobody rediscovers it as new.

### Accepted

- The project-file shape guard is a single check in `processSection`, the funnel
  used by design YAML, the project-scope pre-pass, and `ipParameters`
  sub-sections. Verified against a census of 4,816 `processSection` calls across
  16 example projects and the unit suite: bodies are only `CommentedMap`,
  `CommentedSeq`, plain `dict`/`list` (Python-synthesized rows), or
  `OrderedDict`. Every shape the guard rejects crashed or hard-errored before it
  existed, so there is no false rejection.
- No top-level section carries `singular`, `singleEntryList`, `list`,
  `dataGroup`, `multiple`, or `collapsed` — all are nested-sub-table-only, and
  `_coerceSingular` runs strictly after `processSection`. A scalar top-level body
  is therefore structurally impossible, not merely unobserved.

### Residual, unfixed

1. `customSections` (`connections`, `ipParameters`) dispatch to
   `_process_<section>` before the `processSection` branch, so their own bodies
   reach no shape check: a null `connections:` body still raises
   `TypeError: 'NoneType' object is not iterable`, and `ipParameters: <scalar>`
   raises `AttributeError`. Pre-existing, unchanged by this work, and the same
   defect class the guard closed elsewhere.
2. A user field literally named `lc` (`clocks:\n  clkA: { lc: 5 }`) raises
   `AttributeError: 'int' object has no attribute 'line'` in `processSimple`.
   Pre-existing in `HEAD`; crashes during the row parse, before any section-level
   check runs.
3. `logWarning` sets `self.errorState = False`, so a warning after an error
   erases the error state. Latent only because `continueOnError` is a module
   constant `False` and `logError` exits first — but the `errorState`
   placement inside the per-project loop is justified by that same constant, so
   both become live together if it is ever flipped.
4. A project named literally `_global` would give a bucket key colliding with
   `specialContexts`; the `projectName` collision checks screen against
   `yamlAllFiles`, not `specialContexts`. PLAUSIBLE, not reproduced.
5. `test_eval_sv_emit.py` builds its db outside the `try` whose `finally`
   removes the temp tree (three sites), so a failing run leaks
   `unittest/eval_sv_emit_*` directories into the repo.

### Correction to record

An earlier round removed the `item.get('lc')` fallback in the second-default
diagnostic on the grounds that `processSimple` always sets `ret['lc']`. It does
**not** — it has a live `else: myLineNumber = None` branch, and `processSubTable`
passes `{}` deliberately. The claim held only because every row then came from a
round-trip-parsed project file: `createProjectConfig` adds every project-scoped
section to `ignoreSections` before parsing, and `processSingleFile` hard-errors
such a section from a non-project-file context. That premise is now gone —
[`plan-multi-clock-reset.md`](./plan-multi-clock-reset.md) §2.5 injects rows from
a Python dict, which carry no line — so the consolidated check reads `lc`
through `.get`, as every other diagnostic in `processSimple` does, and
`diagnosticLocation` reports the file alone when there is no line.
