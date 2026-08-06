# Schema-Controlled Flat Data Plan

## Current Status

- **Classification:** historical.
- **Status taxonomy:** historical.
- **Current owner:** this document remains the foundation record for the
  schema-controlled `flatData` mechanism. New or expanded flat-index usage is
  owned by the plan that needs the caller, such as
  `plan-foreign-key-lookup.md`; do not treat this historical plan as permission
  to mark additional sections `flat` preemptively.

## Problem

`projectCreate` stores parsed YAML in context-keyed form:

```python
self.data[section][yamlFile][entryName]
```

That shape is required during parsing because include visibility and scoped lookup
must be preserved. Functions such as `getFromContext()` rely on this shape to
resolve unqualified names through the current YAML file's include hierarchy.

Several create-time post-parse and validation passes also need to iterate across
all rows of a top-level section or dereference rows by their qualified key. Those
passes currently rebuild small flattened dictionaries locally or repeatedly walk
the context-keyed dictionaries.

## Goal

Keep the context-keyed data as the authoritative parse-time representation, and
add a schema-controlled flattened index for top-level sections that need global
iteration or qualified-key lookup.

The flattened form is a derived convenience index, not a replacement for scoped
data.

## Data Contract

`projectCreate.data` remains context-keyed:

```python
self.data[section][yamlFile][entryName] = row
```

Add `projectCreate.flatData` for schema-selected sections:

```python
self.flatData[section][qualifiedKey] = row
```

Examples:

```python
self.flatData['blocks'][blockKey] = blockRow
self.flatData['instances'][instanceKey] = instanceRow
self.flatData['interfaces'][interfaceKey] = interfaceRow
```

Nested rows remain available through their owning top-level row, for example:

```python
blockRow['ports']
blockRow['registerPorts']
connectionRow['ends']
interfaceRow['structures']
```

Do not flatten subtables unless a concrete future caller needs that shape.

`flatData` is maintained incrementally as rows are parsed. A separate full
flattening pass is not part of the normal flow because every row already passes
through the parser once and the flat key is available when the row is inserted
into `self.data`.

## Schema Control

Add a schema attribute named `flat`.

Example:

```yaml
blocks:
  _attribs: [flat, post(validateBlockAddressDecl)]
  block: key
  desc: required
```

For sections with existing attributes, append `flat` to `_attribs`:

```yaml
types:
  _attribs: [flat, post(validateTypeWidth)]
  type: key
```

This keeps the rule abstract: the schema owns which sections expose a flattened
index, and `projectCreate` only follows schema metadata.

## Initial Flat Sections

Mark only top-level sections that have a current consumer requiring global
iteration or qualified-key lookup. Do not mark sections flat preemptively.

Initial required sections:

- `blocks`
- `instances`
- `interfaces`
- `connections`
- `connectionMaps`
- `memoryConnections`
- `registerConnections`
- `memories`
- `registers`

Add `flat` to other sections later only when a concrete create-time caller needs
the flattened index. Candidate future sections include `structures`, `types`,
`constants`, `interface_defs`, `parameters`, `variables`, `encoders`, and
`specialStructures`, but they should remain unmarked until there is an actual
consumer.

## Implementation Steps

1. Add `Node.is_flat = False` in `builder/base/pysrc/schema.py`.

2. Update `Node.set_metadata_field()` so `_attribs: [flat]` sets
   `node.is_flat = True`.

3. Add `flat` to the set of valid schema attributes or attribute handling path
   so schema validation accepts it.

4. Export the policy in `Schema._build_data_dict()` for compatibility with the
   existing dict-based schema access:

   ```python
   data['flat'][full_path] = node.is_flat
   ```

5. Add `self.flatData = dict()` to `projectCreate`.

6. Add a helper on `projectCreate` to insert one parsed top-level row into the
   flat index:

   ```python
   def addFlatRecord(self, section, row):
       ...
   ```

   Behavior:

   - Skip sections not marked `flat`.
   - Use the schema node's qualified storage key field for the flat key.
   - Initialize `self.flatData[section]` on first use.
   - Error on missing key field.
   - Error on duplicate flat key unless the duplicate is the exact same row
     object being re-indexed.

7. Call `addFlatRecord()` when a top-level row is added to `self.data`.

   Primary insertion points:

   - `processSection()` after:

     ```python
     self.data[section][yamlFileOverride][itemkey] = entry
     ```

   - `_process_connections()` after:

     ```python
     self.data['connections'][yamlFile][myKey] = entry
     ```

   - Other custom handlers only if they insert a top-level row directly instead
     of going through `processSection()`.

   Subtable insertions in `processSubTable()` must not call `addFlatRecord()`.

8. Convert local flattening and global-iteration users for sections marked
   `flat`:

   - `validatePorts()` local `_flatten()` helper.
   - `validateDeclaredPorts()` and `validateRtlHierarchy()` callers.
   - `config/postParseRegisterPorts.py::_flattenBlocks()`.
   - Repeated full-section scans in `config/postParseRegister.py`.
   - Repeated full-section scans in `config/postParseRegisterPorts.py` where
     `prj.flatData['instances'].values()` is the intended operation.

## Guardrails

- Do not use `flatData` for scoped name resolution during parse.
- Keep `getFromContext()` backed by context-keyed `self.data`.
- Keep validators for unqualified user references using scoped lookup.
- Treat `flatData` as derived and incrementally maintained. If it is out of
  sync, fix the insertion path rather than rebuilding it later.
- Do not add fallback paths in consumers; if a section is required in flat form,
  mark it `flat` in schema.
- Do not mark a schema section `flat` unless a current caller uses that flattened
  index.
- Do not flatten subtables without a concrete caller.

## Verification

Run database creation for representative projects:

- Workspace project under `arch/yaml/project.yaml`.
- A legacy register-bus example using `postParseRegister.py`.
- A new-schema address-block/register-port example using
  `postParseRegisterPorts.py`.
- Existing unit or example test targets, if available.

Expected results:

- Generated SQLite content is unchanged.
- Post-parse scripts produce the same synthesized rows.
- Scoped lookup failures still report through `getFromContext()` and include
  context diagnostics.
- Local flatten helpers are removed or reduced to direct `flatData` access.
