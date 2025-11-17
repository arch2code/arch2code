# Schema System Specification

## Overview

The schema system defines how YAML files are parsed, validated, and transformed into a relational database structure. It provides a declarative way to specify the structure of configuration data, handling everything from simple key-value pairs to complex nested hierarchies with composite keys.

## Core Concepts

### 1. YAML Anchors vs Database Keys

**Critical Distinction**: The schema system separates two concepts that are often conflated:

- **YAML Anchor**: The key used in the YAML file structure (e.g., `status:` in YAML)
- **Database Key**: The unique identifier used in the database table (may be composite)

For top-level tables, these are usually the same. For nested tables (especially collapsed ones), they may differ:

```yaml
# YAML Structure
modports:
  src:           # <- YAML anchor: "src"
    inputs: [data]
    outputs: []
```

```
# Database Structure (for collapsed nested table)
modportGroupKey = "src/inputs"   # <- Database composite key
modportGroup = "inputs"          # <- YAML anchor from nested structure
modport = "src"                  # <- Parent key
```

### 2. Table Types

#### Top-Level Tables
- Defined at the root level of schema.yaml
- Each entry becomes a row in a database table
- Example: `blocks`, `interfaces`, `constants`

#### Nested Tables (Sub-tables)
- Defined within a parent table using dict-type fields
- Table name is `parentTable + field_name` (e.g., `blocksparams`)
- Inherit parent's key as `outerkey` field
- Can be further nested (e.g., `interface_defsmodportsmodportGroups`)

#### Collapsed Tables
- Marked with `collapsed` attribute
- YAML structure is "flattened" - nested data appears at the same level as parent
- Require special handling for keys (see `anchor` field type)
- Used when YAML readability requires inline nesting but logical structure is flat
- Use `collapsed` when there is only one thing inside the table to reove the need for an additional 
level of hierarchy

### 3. Automated Key Building

The schema system automatically manages keys for nested tables, eliminating the need for manual parent key tracking.

#### Parent Key Chain

When the schema is validated, the system automatically derives a `parent_key_chain` for each nested table. This chain contains the unqualified key field names from all ancestor tables.

**Example**: For the 3-level nesting `interface_defs → modports → modportGroups`:
- `interface_defs`: `parent_key_chain = []` (top-level)
- `modports`: `parent_key_chain = ['interface_type']` (parent is interface_defs)
- `modportGroups`: `parent_key_chain = ['interface_type', 'modport']` (grandparent + parent)

#### Parent Storage Key Field

Each nested table tracks its immediate parent's storage key field via `parent_storage_key_field`. This enables efficient lookups during database loading.

**Example**: For `modportGroups` nested under `modports`:
- `parent_storage_key_field = 'modport'`
- The field `'modportKey'` (parent_storage_key_field + 'Key') contains the parent's storage key value

#### Automatic Field Generation

During schema validation, the system automatically creates necessary fields:

1. **Key Fields**: For simple keys, creates `{field}` (anchor) and `{field}Key` (qualified key)
2. **Outer Fields**: For nested tables, automatically adds parent key fields marked as `outer`
3. **Qualified Keys**: Automatically creates `{field}Key` fields with context appended

**Example**: When defining modports with key `modport`:
- System creates: `modport` (anchor field)
- System creates: `modportKey` (qualified key field with context)
- Child tables automatically inherit: `modport` (as outer field)

#### Key Composition

Keys are built hierarchically, with context appended once at the end (not duplicated at each level):

- **Anchor**: Simple value (e.g., `'inputs'`)
- **Storage Key**: Parent keys + anchor (e.g., `'src/inputs'`)
- **Qualified Key**: Storage key + context (e.g., `'apb/src/inputs/_a2csystem'`)

**Not**: `'apb/_a2csystem/src/_a2csystem/inputs/_a2csystem'` ❌

## Field Types

Field types define how values are processed, validated, and stored.

### Key-Related Types

#### `key`
- **Purpose**: Primary key for this table entry
- **Source**: From YAML anchor 
- **Behavior**: 
  - If anchor is provided, uses it directly
  - If composite key defined via `_key` directive, constructs from multiple fields
  - Automatically creates `{field}Key` field with context: `{key}/{yamlFile}`
- **Example**:
```yaml
blocks:
  block: key  # Uses YAML anchor as key
```

#### `anchor`
- **Purpose**: Explicitly captures the YAML anchor value
- **Source**: From YAML structure (the key name in the YAML dict)
- **Behavior**: Stores the raw anchor without modification
- **Use Case**: Collapsed tables where anchor differs from database key
- **Example**:
```yaml
modportGroups:
  _attribs: [collapsed, multiple]
  modportGroup: anchor  # Captures "inputs"/"outputs" from YAML
  modportGroupKey:      # Composite key for database
    _key:
      modport: outerkey
      modportGroup: anchor
```

#### `contextKey`
- **Purpose**: Stores a pre-populated qualified key with context
- **Source**: Automatically populated immediately after processing the corresponding `key`, `anchor`, or `listkey` field
- **Format**: `{key_value}/{yamlFile}` (e.g., `status/_a2csystem`)
- **Processing**:
  - When a `key` field is processed, its corresponding `{field}Key` is immediately populated
  - When an `anchor` field is processed, its corresponding `{field}Key` is immediately populated
  - When a `listkey` field is processed, its corresponding `{field}Key` is immediately populated
  - The `contextKey` handler validates that the field was pre-populated (fail-fast error if missing)
- **Error Handling**: If `contextKey` field is not pre-populated, throws explicit error indicating a bug in processYaml
- **Example**: 
  - Field `block: key` → automatically creates `blockKey` = `{block_value}/{yamlFile}`
  - Field `modport: anchor` → automatically creates `modportKey` = `{modport_value}/{yamlFile}`

#### `outerkey`
- **Purpose**: Reference parent table's key field in nested tables
- **Source**: Copied from parent's corresponding field
- **Behavior**: Maintains hierarchical relationship
- **Example**:
```yaml
modports:
  interface_type: outerkey  # Gets value from parent interface_defs entry
```

#### `listkey`
- **Purpose**: For `singleEntryList` items - the list value becomes the key
- **Source**: The entire item value from the list
- **Example**:
```yaml
# YAML: parameters: [width, height]
# Stored as: {parameter: 'width'}, {parameter: 'height'}
```

### Value Types

#### `required`
- **Purpose**: Field must be present in YAML
- **Validation**: Error if missing
- **Source**: Direct from YAML item data

#### `optional`
- **Purpose**: Field may be omitted in YAML
- **Default**: Empty string "" (unless `optionalDefault` specified in schema)
- **Source**: From YAML item data or default value

#### `const`
- **Purpose**: Numeric constant or reference to named constant/enum
- **Behavior**: 
  - Parses numeric values or constant references
  - Creates `{field}Key` field if reference found
- **Validation**: Error if missing

#### `optionalConst`
- **Purpose**: Optional constant field
- **Behavior**: Like `const` but may be omitted
- **Includes**: Can specify default in parentheses: `optionalConst(0)`

#### `eval`
- **Purpose**: Computed value from expression or direct field
- **Source**: Either named field if present, or 'eval' field with expression
- **Supports**: Variable substitution with $XXX syntax

### Special Types

#### `param`
- **Purpose**: Instance-specific parameter (not constant)
- **Behavior**: Checks if value is a block parameter, otherwise treats as const
- **Use Case**: Values that vary per block instance

#### `subkey`
- **Purpose**: Like `required` but used in specific nested contexts
- **Behavior**: Must be present, no special processing

#### `outer`
- **Purpose**: Reference an outer field (not just key field)
- **Use Case**: When nested table needs parent's data field, not just key

#### `outerkeyKey`
- **Purpose**: Copy the parent's `{field}Key` qualified key field
- **Distinguishes**: Gets the contextualized key, not just the value

#### `combo`
- **Purpose**: Field created by concatenating other fields
- **Defined**: Via `_combo` directive in schema
- **Behavior**: Processed after constituent fields are populated

#### `dataGroup`
- **Purpose**: Creates a 1-to-1 nested table that shares the parent's primary key
- **Behavior**: 
  - Table-level attribute (specified in `_attribs` array)
  - No explicit `key` field needed - automatically inherits parent's storage key
  - Creates separate database table but logically extends parent record
  - Each parent entry has exactly one dataGroup entry (1-to-1 relationship)
- **Use Case**: Organizing related fields into logical groups without creating multi-entry nested tables
- **Example**: `sc_channel` under `interface_defs` - groups SystemC channel-specific fields
- **Schema Pattern**:
```yaml
interface_defs:
  interface_type: key
  sc_channel:
    _attribs: [dataGroup]    # No 'multiple', no explicit key field
    type: required           # sc_channel fields...
    param_cast: optional
```
- **Database Result**: `interface_defssc_channel` table with `interface_typeKey` as storage key (inherited from parent)

#### `post`
- **Purpose**: Trigger post-processing function after field processing
- **Defined**: Via `_post` directive mapping section to function name

#### `auto`
- **Purpose**: Custom processing via dedicated function
- **Pattern**: Function name from schema's `fnStr` mapping
- **Return**: Can return single value or dict of multiple fields

## Attributes

Attributes modify how tables and fields are processed. Specified in `_attribs` array.

### Table-Level Attributes

#### `multiple`
- **Meaning**: Table can have multiple entries (typical case)
- **Database**: Creates table with multiple rows
- **Absence**: If not specified, only single entry expected

#### `optional`
- **Meaning**: Entire table/field may be omitted
- **Validation**: No error if missing

#### `required`
- **Meaning**: Table/field must be present
- **Validation**: Error if missing

#### `collapsed`
- **Critical**: YAML structure doesn't create a new nesting level
- **Behavior**: 
  - Parser doesn't look for field name as a key in YAML
  - Instead, processes parent's data directly
  - Nested items' anchors become part of composite keys
- **Use Case**: When YAML readability requires inline data but logical structure is nested
- **Example**:
```yaml
# Schema with collapsed
modportGroups:
  _attribs: [collapsed, multiple]
  modportGroup: anchor

# YAML (no "modportGroups:" key needed)
modports:
  src:
    inputs: [...]   # "inputs" becomes modportGroup anchor
    outputs: [...]  # "outputs" becomes modportGroup anchor
```

#### `singleEntryList`
- **Purpose**: YAML list where each item becomes a table entry
- **Key Field**: Must define `listkey` field to capture list value
- **Example**:
```yaml
# Schema
mappedFrom:
  _attribs: [singleEntryList, multiple]
  mapped_type: listkey

# YAML
mappedFrom: ['reg_ro', 'reg_rw']

# Database
{mapped_type: 'reg_ro', interface_type: 'status'}
{mapped_type: 'reg_rw', interface_type: 'status'}
```

#### `dataGroup`
- **Critical**: Creates a 1-to-1 nested table that shares parent's primary key
- **Behavior**:
  - Unlike `multiple` tables, only one dataGroup entry per parent
  - No explicit `key` field specification in schema - automatically inherits parent's key
  - Creates separate database table for organizational purposes
  - Used to group related fields without creating multi-entry nested structure
- **Schema Requirements**:
  - Must be a nested table (not top-level)
  - Do NOT specify a `key` field - schema validation will configure key inheritance
  - Do NOT include `multiple` attribute - enforces 1-to-1 relationship
- **Example**:
```yaml
interface_defs:
  interface_type: key
  sc_channel:
    _attribs: [dataGroup]
    type: required
    param_cast: optional
```
- **Result**: `interface_defssc_channel` table where each entry's storage key matches its parent's `interface_typeKey`

## Directives

Special keys that define schema metadata (prefixed with underscore).

### `_attribs`
- **Purpose**: Array of attributes for this table/field
- **Example**: `_attribs: [required, multiple, collapsed]`

### `_key`
- **Purpose**: Define composite key from multiple fields
- **Behavior**: 
  - Lists fields that form the composite key
  - Each field type (outerkey, anchor, required, etc.) determines source
  - Composite key constructed by concatenating field values
- **Example**:
```yaml
modportGroupKey:
  _key:
    modport: outerkey      # From parent
    modportGroup: anchor   # From YAML structure
# Result: "src/inputs"
```

### `_combo`
- **Purpose**: Define field as concatenation of other fields
- **Format**: Maps field name to array of constituent fields
- **Example**:
```yaml
_combo:
  fullName: [firstName, lastName]
```

### `_validate`
- **Purpose**: Validation rules for field values
- **Types**:
  - `values`: Array of allowed values
  - `section`: Reference to another table for validation
  - `scope`: Context for validation lookup
- **Example**:
```yaml
blockType:
  _validate:
    section: blocks
    scope: yamlFile  # or specific context
```

### `_post`
- **Purpose**: Name of post-processing function to call after processing section
- **Example**: `_post: _post_process_blocks`

### `_singular`
- **Purpose**: Handle single-value shorthand in YAML
- **Example**: If YAML has `parameter: width` instead of `parameter: {name: width}`
- **Maps**: Single value to specified field name

### `_mapto`
- **Purpose**: Rename field in database (maps YAML field to different DB column)
- **Use Case**: When DB schema differs from YAML structure

## Common Patterns

### Pattern 1: Simple Top-Level Table

```yaml
constants:
  _attribs: [multiple]
  constant: key
  value: required
  description: optional
```

### Pattern 2: Nested Table with Parent Reference

```yaml
blocks:
  block: key
  params:
    _attribs: [optional, multiple]
    block: outerkey        # References parent block
    param: key
    value: required
```

**Database**: `blocksparams` table with `block` as foreign key

### Pattern 3: Single Entry List

```yaml
interface_defs:
  interface_type: key
  parameters:
    _attribs: [optional, singleEntryList, multiple]
    interface_type: outerkey
    parameter: listkey
```

**YAML**:
```yaml
interface_defs:
  axi_read:
    parameters: [addr_t, data_t]
```

**Database**: Two rows in `interface_defsparameters`:
- `{interface_type: 'axi_read', parameter: 'addr_t'}`
- `{interface_type: 'axi_read', parameter: 'data_t'}`

### Pattern 4: Collapsed Nested Table with Anchor

```yaml
modports:
  _attribs: [required, multiple]
  interface_type: outerkey
  modport: key
  modportGroups:
    _attribs: [optional, multiple, collapsed]
    interface_type: outerkey
    modport: outerkey
    modportGroup: anchor        # Captures YAML anchor
    modportGroupKey:            # Composite database key
      _key:
        modport: outerkey
        modportGroup: anchor
```

**YAML**:
```yaml
modports:
  src:
    inputs: [a, b]    # "inputs" is anchor for modportGroup
    outputs: [c]      # "outputs" is anchor for modportGroup
```

**Database** (`interface_defsmodportsmodportGroups`):
- `{interface_type: 'status', modport: 'src', modportGroup: 'inputs', modportGroupKey: 'src/inputs'}`
- `{interface_type: 'status', modport: 'src', modportGroup: 'outputs', modportGroupKey: 'src/outputs'}`

### Pattern 5: Composite Key without Anchor

```yaml
connections:
  connection: key
  ends:
    _attribs: [multiple]
    connection: outerkey
    direction: required
    endKey:
      _key:
        connection: outerkey
        direction: required
```

**Database**: Key is `{connection}/{direction}` (e.g., `conn1/src`, `conn1/dst`)

### Pattern 6: Context-Aware Validation

```yaml
blocks:
  block: key
  parentBlock: optional
  parentBlockKey:
    _validate:
      section: blocks
      scope: yamlFile  # Look in same context as current file
```

**Behavior**: Validates `parentBlock` exists in the blocks table within the appropriate context

### Pattern 7: DataGroup Table (1-to-1 Nested)

```yaml
interface_defs:
  interface_type: key
  # ... other fields ...
  sc_channel:
    _attribs: [dataGroup]     # Note: No 'multiple', no explicit key field
    type: required
    param_cast: optional
    multicycle_types:
      _attribs: [optional, singleEntryList, multiple]
      multicycle_type: listkey
```

**Key Characteristics**:
- No explicit `key` field in `sc_channel` - automatically inherits parent's key
- `_attribs: [dataGroup]` creates 1-to-1 relationship with parent
- Cannot have multiple `sc_channel` entries per `interface_defs` entry
- Creates separate table `interface_defssc_channel` for organizational purposes

**Database Result**:
```python
# interface_defs table
{interface_type: 'apb', interface_typeKey: 'apb/_a2csystem', ...}

# interface_defssc_channel table (inherits key)
{interface_typeKey: 'apb/_a2csystem', type: 'sc_fifo', param_cast: 'data_t', ...}
```

**In-Memory Access** (after loading):
```python
prj.data['interface_defs']['apb/_a2csystem']['sc_channel'] = {
    'type': 'sc_fifo',
    'param_cast': 'data_t',
    'multicycle_types': {...}
}
```

**Use Case**: When you need to organize related fields into a logical group but don't want the complexity of multi-entry nested tables. Common for optional field groups or fields specific to certain subtypes.

## Processing Flow

### 1. Schema Validation (`schema.py`)
- Parse schema.yaml
- Validate field types are in `valid_field_types`
- Build node/field hierarchy
- Check for reserved key usage
- Validate `_key` and `_combo` references

### 2. YAML Processing (`processYaml.py`)

#### For Each YAML File:
1. **Load YAML** with line number tracking (lc)
2. **Identify Section** (blocks, interfaces, etc.)
3. **For Each Entry**:
   - Call `processSimple(section, anchor, item, yamlFile, ...)`
   - `anchor` = YAML key for this entry
   - `item` = YAML value (dict or scalar)

#### `processSimple` Flow:
1. **Schema Lookup**: Get field definitions for this section
2. **Singular Conversion**: If single value, wrap in dict
3. **Field Validation**: Check for unknown fields (warn if not in schema)
4. **Field Processing**: For each field in schema:
   - **Dict Type** → Nested table → Call `processSubTable`
   - **Key Type** → Handle composite keys, assign anchor
   - **Anchor Type** → Store YAML anchor directly
   - **Required/Optional** → Get from item or use default
   - **Const** → Parse numeric/constant reference
   - **Outer Types** → Copy from parent entry
   - **Auto** → Call custom handler function
5. **Validation**: Check values against `_validate` rules
6. **Post-Processing**: Call `_post` function if defined
7. **Return**: Processed entry dict

#### `processSubTable` Flow:
1. **Schema Lookup**: Get nested schema definition
2. **Attribute Check**: Check for `collapsed`, `singleEntryList`, `multiple`
3. **Key Construction**:
   - Normal: Use YAML anchor as-is
   - Collapsed + Anchor: Build composite key (`parent/anchor`)
4. **Iterate Items**: Call `processSimple` for each nested entry
5. **Store**: Add to both local return and global `self.data`

### 3. Database Creation (`projectCreate`)
- Iterate through `self.data` structure
- Create tables from section names
- Insert rows with all fields (including qualified keys)
- Nested tables automatically linked via `outerkey` fields

### 4. Database Loading (`projectOpen`)

Database loading happens in depth-first order (children before parents) to enable efficient nested structure assembly.

#### Critical Distinction: SQL vs In-Memory Access

**Database Table Names** (flat, for SQL queries):
- Nested tables have concatenated names: `parametersvariants`, `interface_defsmodports`, `connectionsends`
- Used in SQL queries: `SELECT * FROM parametersvariants WHERE block = ?`
- Example from `postParseChecks.py`:
```python
sql = "select variant from parametersvariants where block = instances.instanceType"
```

**In-Memory Data Access** (hierarchical, after loading):
- Nested tables are reconstructed under their parent in the dict structure
- Access via parent key, then nested field name
- Example: `self.data['parameters'][qualBlock]['variants']` (NOT `self.data['parametersvariants'][qualBlock]`)
- Example from `processYaml.py`:
```python
def getQualBlockVariants(self, qualBlock):
    variants = []
    variantData = self.data['parameters'].get(qualBlock, {}).get('variants', {})
    for _, data in variantData.items():
        if data['variant'] not in variants:
            variants.append(data['variant'])
    return variants
```

This dual nature exists because:
- **Database**: Flat relational tables for efficient queries
- **In-Memory**: Hierarchical structure matching YAML for code convenience

#### Two-Index System

The loading system maintains two data structures:

1. **`self.data[tableName]`**: Primary index by each table's own storage key
   - Used for top-level table lookups
   - Format: `{storage_key: entry_dict}`
   - Example: `self.data['interface_defs']['apb/_a2csystem'] = {...}`
   - For multi-entry tables: Also stores individual entries by their qualified storage keys
   - Example: `self.data['parametersvariants']['blockF/v1/width/mixed.yaml'] = {...}`

2. **`self.data_by_parent[tableName]`**: Secondary index by parent's storage key (nested tables only)
   - Used for efficient child lookups when loading parent tables
   - Format: `{parent_storage_key: {unqualified_anchor: entry_dict}}`
   - Children indexed by unqualified anchor (just the anchor, e.g., `'inputs'`) for easier access
   - Example: `self.data_by_parent['modportGroups']['apb/src/_a2csystem'] = {'inputs': {...}, 'outputs': {...}}`
   - For multi-entry tables: Both indexes maintained simultaneously during loading

#### Multi-Entry Table Dual Storage

Multi-entry nested tables (marked with `multiple` attribute) maintain **two simultaneous storage locations** during loading:

**1. Flat Top-Level Storage** (`self.data[tableName]`):
- Each individual entry stored with its own qualified storage key
- Enables direct table-wide lookups and queries
- Example for `parametersvariants`:
```python
self.data['parametersvariants'] = {
    'blockF/v1/width/mixed.yaml': {block: 'blockF', variant: 'v1', param: 'width', ...},
    'blockF/v1/height/mixed.yaml': {block: 'blockF', variant: 'v1', param: 'height', ...},
    'blockF/v2/width/mixed.yaml': {block: 'blockF', variant: 'v2', param: 'width', ...},
    ...
}
```

**2. Grouped Parent-Indexed Storage** (`self.data_by_parent[tableName]`):
- Entries grouped by parent's storage key, indexed by anchor within each group
- Enables efficient nested structure reconstruction
- Example for same `parametersvariants` data:
```python
self.data_by_parent['parametersvariants'] = {
    'blockF/mixed.yaml': {  # Parent's storage key
        'v1/width': {block: 'blockF', variant: 'v1', param: 'width', ...},
        'v1/height': {block: 'blockF', variant: 'v1', param: 'height', ...},
        'v2/width': {block: 'blockF', variant: 'v2', param: 'width', ...},
        ...
    }
}
```

**Why Both?**
- Flat storage: For table-wide operations, SQL-like access patterns
- Grouped storage: For reconstructing hierarchical in-memory structure that matches YAML
- Both populated simultaneously during `loadTable()` for efficiency

#### Loading Process

1. **Load Subtables First**: Depth-first traversal ensures all children loaded before parents
2. **Build Both Indexes**: For multi-entry nested tables, populate both `data` and `data_by_parent` simultaneously
3. **Attach Children**: When loading parent table, lookup children using `data_by_parent[childTable][parent_storage_key]`
4. **Key Strategy**: 
   - Top-level storage: Always uses qualified keys (storage_key_field_qualified)
   - Nested dict reconstruction: Uses anchor field for user-friendly structure
   - DataGroup tables: Share parent's storage key (1-to-1 relationship)

#### Example: Loading interface_defs → modports → modportGroups

```python
# Step 1: Load modportGroups (deepest first)
# Creates:
self.data['modportGroups']['apb/src/inputs/_a2csystem'] = {
    'modportGroup': 'inputs',
    'modportKey': 'src/_a2csystem',  # Parent storage key
    ...
}

# Also creates:
self.data_by_parent['modportGroups']['apb/src/_a2csystem'] = {
    'inputs': {...},   # Indexed by unqualified anchor (easier access)
    'outputs': {...}
}

# Step 2: Load modports (parents of modportGroups)
# When processing a modport row, looks up its children:
parent_storage_key = 'apb/src/_a2csystem'  # From modportKey field
children = self.data_by_parent['modportGroups'][parent_storage_key]
modport_row['modportGroups'] = children  # Attach with anchor-based keys

# Step 3: Load interface_defs (top level)
# Similar process for attaching modports to interface_defs
```

## Node API Reference

The `Node` class (in `schema.py`) provides methods for automated key building:

### Key Attributes

#### `storage_key_field: Optional[str]`
The unqualified field name used as the primary key for this table's database storage.
- For simple keys: Same as the key field name (e.g., `'block'`)
- For combo keys: The concatenated field name (e.g., `'memoryBlockPort'` = memoryBlock + port)
- For dataGroup tables: Inherited from parent (e.g., `'interface_type'`)

#### `storage_key_field_qualified: Optional[str]`
The qualified field name (storage_key_field + 'Key') that stores the contextualized key value.
- Precomputed during schema validation to avoid string manipulation at runtime
- Used for efficient lookups during database loading
- Contains the full qualified key: `{storage_key_value}/{context}` (e.g., `'apb/_a2csystem'`)
- Example: If `storage_key_field = 'modport'`, then `storage_key_field_qualified = 'modportKey'`

#### `parent_storage_key_field: Optional[str]`
The parent table's unqualified storage key field name.
- Used by nested tables to reference parent's key
- Enables efficient parent-child lookups during loading
- Example: For `modportGroups` nested under `modports`, value is `'modport'`

#### `anchor_field: Optional[str]`
The field name that captures the YAML anchor (the dict key the user types).
- For simple keys: Same as storage_key_field
- For collapsed tables with anchor type: Stores the YAML structure key
- Used for reconstructing user-friendly nested dict structure
- Example: In `modports: {src: {...}}`, anchor_field `'modport'` captures `'src'`

### `set_parent_key_chain(parent_keys: List[str], parent_storage_key: Optional[str])`

Called during schema validation to set up parent context.

**Arguments**:
- `parent_keys`: List of unqualified parent key field names (e.g., `['interface_type', 'modport']`)
- `parent_storage_key`: Parent's storage key field name (e.g., `'modport'`)

**Effect**: Automatically creates `outer` fields for each parent key and sets up parent tracking.

### `set_key(field_name: str, is_combo: bool, combo_sources: List[str])`

Sets up the key field(s) for this node.

**Arguments**:
- `field_name`: Name of the key field
- `is_combo`: True if composite key defined via `_key` directive
- `combo_sources`: List of fields that compose the combo key (if applicable)

**Effect**: Creates key field, qualified key field, and handles combo key logic.

### `build_storage_key(row: dict, inner_key: Optional[str]) -> str`

Builds the composite storage key for a database row.

**Arguments**:
- `row`: Database row dict with all key field values
- `inner_key`: For multi-entry tables, the anchor field name (used for context)

**Returns**: Composite key string (e.g., `'apb/src/inputs/_a2csystem'`)

**Used During**: Database loading (`projectOpen.loadTable()`)

**Example**:
```python
# For modportGroups row
row = {
    'interface_type': 'apb',
    'modport': 'src',
    'modportGroup': 'inputs',
    '_context': '_a2csystem'
}
node.build_storage_key(row, 'modportGroup')
# Returns: 'apb/src/inputs/_a2csystem'
```

### `get_parent_storage_key_field_name() -> Optional[str]`

Returns the field name containing the parent's storage key.

**Returns**: Parent storage key field name with 'Key' suffix (e.g., `'modportKey'`), or `None` for top-level tables

**Used During**: Database loading to build `data_by_parent` index

**Example**:
```python
node = schema.get_node('modportGroups')
node.get_parent_storage_key_field_name()
# Returns: 'modportKey'
```

### `get_yaml_storage_key(row_dict: dict) -> str`

Extracts the storage key from a processed YAML row.

**Arguments**:
- `row_dict`: Processed row dict from `processSimple()`

**Returns**: Storage key value (e.g., `'blockBTable1port1'` for combo key)

**Used During**: YAML processing (`projectCreate`)

## Best Practices

### 1. Naming Conventions
- **Tables**: Lowercase, descriptive (e.g., `blocks`, `connections`)
- **Keys**: Singular form of table name (e.g., `block`, `connection`)
- **Nested Tables**: Concatenate parent + field (e.g., `blocksparams`)

### 2. Key Design
- **Simple Keys**: Use when YAML anchor = database key
- **Composite Keys**: Use for many-to-many or when context needed
- **Anchor Fields**: Use for collapsed tables to preserve YAML structure

### 3. When to Use `collapsed`
- YAML readability requires inline data
- Logical structure is still hierarchical
- Need to preserve YAML anchor in separate field
- **Always pair with `anchor` field type** for proper key handling

### 4. Context Management
- Use `_a2csystem` for system-wide definitions
- Use `yamlFile` for project-specific definitions
- `getFromContext` automatically searches `_a2csystem` as fallback
- Validators should use appropriate scope (usually `yamlFile`)

### 5. Validation Strategy
- Use `_validate` with `values` for enums
- Use `_validate` with `section` for referential integrity
- Specify `scope` to control lookup context
- Use `NotFoundFatal=False` for optional references

### 6. Avoiding Common Pitfalls
- **Don't** use `itemkey` in new code (use `anchor` parameter name)
- **Don't** conflate YAML anchor with database key in collapsed tables
- **Don't** forget to mark nested tables with `multiple` attribute (unless it's a dataGroup)
- **Don't** add explicit `key` field to dataGroup tables - they inherit from parent automatically
- **Don't** use `_key` directive in non-collapsed tables (unnecessary complexity)
- **Don't** access nested tables using flat table names in code (use hierarchical access: `data['parent'][key]['child']` not `data['parentchild'][key]`)
- **Don't** manually populate `contextKey` fields - they're auto-populated when base field is processed
- **Do** use qualified keys for database lookups (`type/context`)
- **Do** include `outerkey` fields in nested tables (automatic for parent keys via `set_parent_key_chain`)
- **Do** use dataGroup for 1-to-1 nested relationships to organize fields
- **Do** test schema changes with database rebuild

## Debugging Schema Issues

### Symptom: "Field not found in schema"
- **Cause**: Field in YAML not defined in schema
- **Fix**: Add field to schema or remove from YAML

### Symptom: "Required field missing"
- **Cause**: YAML missing a `required` field
- **Fix**: Add field to YAML or change schema to `optional`

### Symptom: Data not in database
- **Cause**: Usually `collapsed` attribute without proper key handling
- **Fix**: Add `anchor` field type and composite key with `_key`

### Symptom: KeyError on qualified key lookup
- **Cause**: Looking for `type/context` but data stored with different context
- **Fix**: Check `_context` field in database, verify context handling

### Symptom: Nested data appearing at wrong level
- **Cause**: Missing or incorrect `collapsed` attribute
- **Fix**: Review YAML structure vs. desired database schema

### Symptom: Composite key malformed
- **Cause**: `_key` fields not properly ordered or typed
- **Fix**: Ensure `_key` references existing fields with correct types

## Extension Points

### Adding New Field Types
1. Add to `valid_field_types` in `schema.py`
2. Add handling in `processSimple` in `processYaml.py`
3. Document behavior and use cases
4. Add tests for new type

### Adding New Attributes
1. Update attribute checking in `processSubTable`
2. Implement behavior in processing logic
3. Document interaction with existing attributes
4. Add tests for edge cases

### Adding New Validators
1. Define in schema using `_validate`
2. Implement custom validation logic if needed
3. Set appropriate scope for context
4. Handle `NotFoundFatal` appropriately

## Future Enhancements

Potential improvements to the schema system:

1. **Schema Versioning**: Support multiple schema versions for backward compatibility
2. **Type System**: Strong typing beyond const/optional/required
3. **Constraints**: Min/max values, string patterns, etc.
4. **Computed Fields**: More sophisticated expressions
5. **Migrations**: Automatic database schema updates
6. **Introspection**: Runtime query of schema structure
7. **Documentation Generation**: Auto-generate docs from schema
8. **IDE Support**: JSON Schema export for YAML validation

## Conclusion

The schema system provides a powerful, declarative way to define configuration structure. Key principles:

- **Separation of concerns**: YAML structure vs. database structure (flat tables for SQL, hierarchical dicts for code)
- **Explicit is better than implicit**: Use `anchor` field type for clarity in collapsed tables
- **Context awareness**: Qualified keys enable proper scoping and multi-context data
- **Automatic key management**: `storage_key_field_qualified` precomputed, contextKey fields pre-populated
- **Dual storage for efficiency**: Multi-entry tables maintain both flat and grouped indexes
- **Flexible nesting**: DataGroup for 1-to-1, multiple for 1-to-many relationships
- **Extensibility**: Auto functions and post-processing for custom logic
- **Validation**: Built-in checks for data integrity with fail-fast error handling

By following these specifications and best practices, you can effectively define, validate, and process complex hierarchical configuration data.

