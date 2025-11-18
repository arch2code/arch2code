"""
Schema module for defining and validating YAML schema structure.

This module provides classes to represent schema definitions with a hierarchical
structure of Nodes and Fields, replacing the monolithic dict-based approach.
"""

import re
from typing import Dict, List, Optional, Any
from pysrc.arch2codeHelper import printError, printWarning, warningAndErrorReport, printIfDebug


class ValidationRule:
    """Represents a validation rule for a field"""
    
    def __init__(self, rule_type: str):
        self.rule_type = rule_type  # 'section', 'values', 'combo'
        self.section = None  # For cross-reference validation
        self.field = None  # Field to reference
        self.scope = None  # 'global' or None for context-based
        self.values = []  # For enumerated value validation
        
    def __repr__(self):
        if self.rule_type == 'section':
            return f"ValidationRule(section={self.section}, field={self.field}, scope={self.scope})"
        elif self.rule_type == 'values':
            return f"ValidationRule(values={self.values})"
        else:
            return f"ValidationRule(type={self.rule_type})"


class Field:
    """Represents a field in a schema node"""
    
    def __init__(self, name: str, field_type: str, line_number: int = 0):
        self.name = name
        self.field_type = field_type  # key, required, optional, auto, const, eval, etc.
        self.line_number = line_number
        self.validator: Optional[ValidationRule] = None
        self.default_value: Any = None
        self.auto_function: Optional[str] = None  # e.g., "_auto_width"
        self.post_function: Optional[str] = None
        self.is_combo = False
        self.combo_sources: List[str] = []  # Unqualified field names used to create this field
        self.combo_sources_qualified: List[str] = []  # Qualified versions (computed during validation)
        # Foreign key metadata - set when field has validator referencing another table
        self.is_foreign_key: bool = False
        
    def __repr__(self):
        return f"Field({self.name}, {self.field_type})"
    
    def set_combo(self, combo_sources: List[str]):
        self.is_combo = True
        self.combo_sources = combo_sources
    def get_value(self, row: dict) -> Any:
        if self.is_combo:
            for source in self.combo_sources:
                if source not in row:
                    raise KeyError(f"Missing combo source '{source}' in row for field '{self.name}'. Row keys: {row.keys()}")
            return ''.join([row[source] for source in self.combo_sources])
        else:
            return row[self.name]


class Node:
    """Represents a section or subtable in the schema"""
    
    def __init__(self, name: str, context: str = ''):
        self.name = name
        self.context = context  # e.g., "structures" for nested vars
        self.full_path = context + name
        self.fields: Dict[str, Field] = {}  # name -> Field
        self.fields_lower: Dict[str, str] = {}  # lowercase name -> actual name (for case-insensitive collision detection)
        self.sub_nodes: Dict[str, Node] = {}  # name -> Node
        self._item_order: List[tuple] = []  # [(name, 'field'|'subnode')] - tracks insertion order
        
        # Key composition tracking
        # 
        # Three different key concepts:
        # 1. anchor_field: The YAML anchor - what user types as dict key (e.g., 'port1' in `ports: {port1: {...}}`)
        #                  Used for hierarchical YAML structure navigation
        # 2. storage_key_field: The composite key field name for DB storage (e.g., 'memoryBlockPort' = memoryBlock + port)
        #                       For simple keys, same as anchor_field. For combo keys, the concatenated field name.
        # 3. item_key_name: Base key field tracked during validation (local variable, not stored here)
        self.anchor_field: Optional[str] = None  # Field name from YAML anchor (what user types as dict key)
        self.storage_key_field: Optional[str] = None  # Field name for storage/DB (combo key field name or same as anchor)
        self.storage_key_field_qualified: Optional[str] = None  # Qualified version: storage_key_field + 'Key'
        self.parent_storage_key_field: Optional[str] = None  # Unqualified field name for storage/DB (parent's combo key field name or same as anchor)
        self.key_fields: List[str] = []  # All fields that compose the database key
        self.outer_key_fields: List[str] = []  # Fields marked as 'outerkey' (reference parent)
        self.is_combo_key = False  # True if key uses _key: directive
        self.combo_key_sources: List[str] = []  # Unqualified fields used for combo key
        self.combo_key_sources_qualified: List[str] = []  # Qualified versions (computed during validation)
        self.parent_key_chain: List[str] = []  # Auto-derived parent unqualified keys (e.g., ['interface_type', 'modport'])
        
        # Content structure
        self.content_type = 'dict'  # 'dict', 'list', or 'value'
        self.attributes: List[str] = []  # [multiple, optional, required, list, etc.]
        self.is_multi_entry = False  # Can have multiple records
        self.is_collapsed = False  # Nested content merged with parent level
        self.is_list = False  # User provides list, not dict
        self.is_single_entry_list = False  # List converted to dict
        self.is_data_group = False  # Subtable shares parent's key
        
        # Special behaviors
        self.is_singular = False  # Single value converted to dict
        self.singular_field: Optional[str] = None  # Field name for singular conversion
        self.mapto: Optional[str] = None  # Maps to another section
        self.data_schema: Optional['Node'] = None  # Alternative Node for parsing (when YAML != DB)
        self.post_function: Optional[str] = None  # Post-processing function
        
        # Database metadata
        self.indexes: List[str] = []  # Fields to index
        self.outerkey_key_field: Optional[str] = None  # Field name with "Key" suffix for subtables
        
    def get_field(self, name: str) -> Optional[Field]:
        """Get field by name"""
        return self.fields.get(name)
        
    def get_sub_node(self, name: str) -> Optional['Node']:
        """Get sub-node by name"""
        return self.sub_nodes.get(name)
        
    def get_anchor_field_name(self) -> Optional[str]:
        """Get the name of the field from YAML anchor (what user types as dict key)"""
        return self.anchor_field
    
    def get_storage_key_field_name(self) -> Optional[str]:
        """Get the name of the field used for storage/DB (combo key field name)"""
        return self.storage_key_field
    
    def compute_qualified_combo_sources(self, combo_sources: List[str]) -> List[str]:
        """
        Compute the qualified versions of combo source fields based on metadata.
        For foreign key fields (those with validators), return the qualified version (field + 'Key').
        For local fields, return unqualified version.
        
        This should be called during schema validation to precompute the qualified sources.
        
        Args:
            combo_sources: List of unqualified field names used in combo key
            
        Returns:
            List of field names, with foreign keys qualified
        """
        qualified = []
        for source in combo_sources:
            field = self.get_field(source)
            if field and field.is_foreign_key:
                # Foreign key - use qualified version
                qualified.append(source + 'Key')
            else:
                # Local field - use unqualified version
                qualified.append(source)
        return qualified
        
    def get_key_field_names(self) -> List[str]:
        """Get list of all fields that compose the database key"""
        return self.key_fields
        
    def get_outer_key_fields(self) -> List[str]:
        """Get fields that reference parent node's key"""
        return self.outer_key_fields
    
    def set_parent_key_chain(self, parent_keys: List[str], parent_storage_key: Optional[str] = None, parent_node: Optional['Node'] = None) -> None:
        """
        Set the parent key chain for this node and automatically add the necessary outer fields.
        
        This is used during database loading to construct composite keys that include qualified parent keys.
        For each parent key in the chain, this automatically creates:
        - Unqualified field (e.g., 'interface_type') marked as 'outer'
        - Qualified field (e.g., 'interface_typeKey') marked as 'outerKey' (only if it exists in parent)
        
        For nested tables with simple keys, this also updates the storage_key_field to be the composite
        of all parent keys + own anchor field (e.g., 'interface_typemodport').
        
        Args:
            parent_keys: List of parent key field names (e.g., ['interface_type', 'modport'])
            parent_storage_key: Optional parent storage key field name (e.g., 'memoryBlockPortKey')
            parent_node: Optional parent Node to check if qualified versions exist
        """
        
        # Automatically add outer fields for each parent key
        for parent_key in parent_keys:
            outer_field = Field(parent_key, 'outer', 0) # add the parent key as an automatic outer field
            self.add_field(outer_field)
            self.parent_key_chain.append(parent_key)
            qualified_key = parent_key + 'Key'
            
            # Only add qualified version if parent node has it (i.e., field has validator/reference)
            if parent_node and parent_node.has_field(qualified_key):
                if not self.has_field(qualified_key):
                    # Qualified key fields from parent should be copied (outerkeyKey), not recomputed
                    outer_key_field = Field(qualified_key, 'outerkeyKey', 0)
                    self.add_field(outer_key_field)
        
        self.parent_storage_key_field = parent_storage_key
        if parent_storage_key:
            parent_storage_field = Field(parent_storage_key, 'outer', 0)
            self.add_field(parent_storage_field)
            qualified_key = parent_storage_key + 'Key'
            # Only add qualified version if parent node has it
            if parent_node and parent_node.has_field(qualified_key):
                # Qualified key field from parent should be copied (outerkeyKey), not recomputed
                outer_key_field = Field(qualified_key, 'outerkeyKey', 0)
                self.add_field(outer_key_field)
    
    def set_key(self, field_name: Optional[str] = None, is_combo: bool = False, combo_sources: Optional[List[str]] = None):
        """
        Set the key field for this node.
        
        This API manages the internal details of key handling:
        - Sets anchor_field
        - Sets storage_key_field
        - Sets combo_sources if applicable
        
        Note: parent_key_chain is NOT automatically cleared for combo keys.
        The decision of whether to include parent context is made separately
        based on the schema structure and nesting relationships.
        
        Args:
            field_name: Name of the field that serves as the key (None for dataGroup - uses parent's key)
            is_combo: True if this is a composite key created via _key directive
            combo_sources: List of field names that compose the combo key
        """
        if self.is_data_group:
            # dataGroup tables share parent's key (1-to-1 relationship)
            # Use parent's storage_key_field directly (already set by set_parent_key_chain)
            self.storage_key_field = self.parent_storage_key_field
            self.storage_key_field_qualified = self.storage_key_field + 'Key' if self.storage_key_field else None
            # Don't set anchor_field - dataGroup doesn't have its own anchor
        elif is_combo:
            # For combo keys, use add_combo to create all necessary fields
            self.storage_key_field = field_name
            self.storage_key_field_qualified = field_name + 'Key'
            self.is_combo_key = True
            self.add_combo(field_name, combo_sources, field_type='key')
        else:
            # For simple keys
            self.anchor_field = field_name
            if self.parent_storage_key_field:
                # nested case - create composite storage key from parent + anchor
                self.storage_key_field = self.parent_storage_key_field + field_name
                self.storage_key_field_qualified = self.storage_key_field + 'Key'
                # Storage key is a combo field that will be computed from parent + anchor
                self.add_combo(self.storage_key_field, [self.parent_storage_key_field, field_name], field_type='key')
            else:
                # default simple case
                self.storage_key_field = field_name
                self.storage_key_field_qualified = field_name + 'Key'
                storage_field = Field(self.storage_key_field, 'key', 0)
                qualified_storage_field = Field(self.storage_key_field_qualified, 'contextKey', 0)
                self.add_field(storage_field)
                self.add_field(qualified_storage_field)
        
    def get_parent_key_chain(self) -> List[str]:
        """Get the list of qualified parent keys for composite key construction"""
        return self.parent_key_chain
    
    def build_storage_key(self, row: dict) -> str:
        """
        Build the composite key for storing this row in self.data[tableName].
        
        Strategy is determined during schema creation (is_multi_entry, parent_key_chain, storage_key_field)
        and pickled with the Node, so it's efficiently available during loading.
        
        For multi-entry tables: Returns parent_key_chain values joined
        For single-entry tables: Returns parent_key_chain + own qualified key joined
        
        Args:
            row: Database row dict with all key values
        
        Returns:
            Composite key string (e.g., 'apb/src/_a2csystem')
        
        Examples:
            # Single-entry table (interface_defs)
            node.build_storage_key({'interface_type': 'apb', '_context': '_a2csystem'})
            # Returns: 'apb/_a2csystem'
            
            # Single-entry nested (modports under interface_defs)
            node.build_storage_key({
                'interface_type': 'apb',
                'modport': 'src',
                '_context': '_a2csystem'} )
            # Returns: 'apb/src/_a2csystem'
            
            # Multi-entry nested (modportGroups - multiple per modport)
            node.build_storage_key({
                'interface_type': 'apb',
                'modport': 'src',
                'modportGroup': 'inputs',
                '_context': '_a2csystem'})
            # Returns: 'apb/src/inputs/_a2csystem' 
        """
        # For single-entry tables (including dataGroup), return the qualified storage key
        if not self.is_multi_entry and self.storage_key_field_qualified:
            try:
                return str(row[self.storage_key_field_qualified])
            except (KeyError, IndexError):
                row_keys = list(row.keys()) if hasattr(row, 'keys') else list(row.keys())
                raise KeyError(f"Missing qualified key '{self.storage_key_field_qualified}' in row for table '{self.full_path}'. Row keys: {row_keys}")
        
        # For multi-entry tables, return the parent storage key for grouping
        # (used to detect when we've finished reading all children for a parent)
        if self.is_multi_entry and self.parent_storage_key_field:
            try:
                return str(row[self.parent_storage_key_field])
            except (KeyError, IndexError):
                row_keys = list(row.keys()) if hasattr(row, 'keys') else list(row.keys())
                raise KeyError(f"Missing parent key '{self.parent_storage_key_field}' in row for table '{self.full_path}'. Row keys: {row_keys}")
        
        # If we reach here, the node is misconfigured
        raise ValueError(
            f"Cannot build storage key for table '{self.full_path}': "
            f"is_multi_entry={self.is_multi_entry}, "
            f"storage_key_field_qualified={self.storage_key_field_qualified}, "
            f"parent_storage_key_field={self.parent_storage_key_field}. "
            f"Node must have either storage_key_field_qualified (for single-entry) "
            f"or parent_storage_key_field (for multi-entry)."
        )
    
    def get_yaml_storage_key(self, row_dict: dict) -> str:
        """
        Extract the storage key from a row dict during YAML processing.
        
        During YAML processing (projectCreate), processSimple creates the composite key field
        (e.g., 'memoryBlockPort') which contains the storage key value for this table.
        
        Args:
            row_dict: The processed row dict returned from processSimple
            
        Returns:
            Storage key string (e.g., 'blockBTable1port1' for a combo key)
            
        Examples:
            # For memoryBlockPort table with combo key (memoryBlock + port):
            node.get_yaml_storage_key({
                'port': 'port1',
                'memoryBlock': 'blockBTable1',
                'memoryBlockPort': 'blockBTable1port1',  # The composite key value
                'memoryBlockPortKey': 'blockBTable1port1/mixed.yaml'  # Qualified version
            })
            # Returns: 'blockBTable1port1'
        """
        # The storage key field contains the actual composite value (without /context)
        return str(row_dict[self.storage_key_field])
    
    def get_parent_storage_key_field_name(self) -> Optional[str]:
        """
        Get the field name containing parent's storage key.
        
        For nested tables, this returns the parent's storage_key_field + 'Key' suffix.
        Returns None for top-level tables (those without a parent).
        
        Returns:
            Field name containing parent's storage key, or None for top-level tables
        
        Examples:
            # For modportGroups nested under modports
            node = schema.get_node('interface_defsmodportsmodportGroups')
            node.get_parent_storage_key_field_name()
            # Returns: 'modportKey'
            
            # For top-level table
            node = schema.get_node('interface_defs')
            node.get_parent_storage_key_field_name()
            # Returns: None
        """
        if self.parent_storage_key_field:
            return self.parent_storage_key_field + 'Key'
        return None
        
    def has_field(self, field_name: str) -> bool:
        """Check if a field exists (case-insensitive)"""
        return field_name.lower() in self.fields_lower
    
    def get_field(self, field_name: str) -> Optional[Field]:
        """Get a field by name (case-insensitive)"""
        if field_name.lower() in self.fields_lower:
            actual_name = self.fields_lower[field_name.lower()]
            return self.fields[actual_name]
        return None
    
    def add_field(self, field: Field):
        """Add a field to this node (with case-insensitive duplicate detection)"""
        if not self.has_field(field.name):
            self.fields[field.name] = field
            self.fields_lower[field.name.lower()] = field.name
            self._item_order.append((field.name, 'field'))
        
    def add_sub_node(self, node: 'Node'):
        """Add a sub-node to this node"""
        self.sub_nodes[node.name] = node
        self._item_order.append((node.name, 'subnode'))
    
    def add_combo(self, field_name: str, combo_sources: List[str], field_type: str = 'key') -> Field:
        """Add a combo field with qualified source computation.
        
        This method encapsulates all the logic for creating a combo field:
        - Ensures all combo source fields exist (adds them if missing)
        - Creates the combo field with the specified sources
        - Computes and stores the qualified versions of combo sources
        - Creates the qualified key field (fieldNameKey) only for 'key' type combo fields
        - For 'key' type combos, also sets node.combo_key_sources_qualified for easy access
        - Adds the field(s) to the node
        
        Args:
            field_name: Name of the combo field (e.g., 'memoryBlockPort')
            combo_sources: List of unqualified field names to combine (e.g., ['memoryBlock', 'port'])
            field_type: Type for the combo field ('key' for storage keys, 'combo' for other combo fields)
            
        Returns:
            The created combo Field object for further manipulation if needed
        """
        # Ensure all combo source fields exist
        for source in combo_sources:
            if not self.has_field(source):
                source_field = Field(source, 'required', 0)
                self.add_field(source_field)
        
        # Create the combo field if it doesn't exist
        if not self.has_field(field_name):
            combo_field = Field(field_name, field_type, 0)
            combo_field.set_combo(combo_sources)
            # Compute and store qualified combo sources
            combo_field.combo_sources_qualified = self.compute_qualified_combo_sources(combo_sources)
            self.add_field(combo_field)
            
            # For key-type combo fields:
            if field_type == 'key':
                # Create the qualified key field (contextKey type)
                qualified_key = field_name + 'Key'
                qualified_key_field = Field(qualified_key, 'contextKey', 0)
                self.add_field(qualified_key_field)
                
                # Store qualified combo sources at node level for easy access
                self.combo_key_sources_qualified = combo_field.combo_sources_qualified
            
            return combo_field
        else:
            return self.get_field(field_name)
        
    def set_metadata_field(self, field_name: str, value: Any, section_fields: dict, all_sections: dict) -> dict:
        """Handle special metadata fields (_attribs, _singular, _mapto).
        
        Args:
            field_name: The metadata field name (_attribs, _singular, _mapto)
            value: The value from the schema YAML
            section_fields: Dict of all fields in this section (for _singular validation)
            all_sections: Dict of all sections (for _mapto validation)
            
        Returns:
            Dict with:
                - 'error': str or None - Error message if validation failed
                - 'post_functions': list - List of post function strings to validate
        """
        result = {
            'error': None,
            'post_functions': []
        }
        
        if field_name == '_attribs':
            attrib_list = value if isinstance(value, list) else [value]
            self.attributes = attrib_list
            
            # Set flags based on attributes
            if 'multiple' in attrib_list:
                self.is_multi_entry = True
                
            if 'list' in attrib_list:
                self.is_list = True
                self.is_multi_entry = True
                
            if 'singleEntryList' in attrib_list:
                self.is_single_entry_list = True
                self.is_multi_entry = True
                
            if 'dataGroup' in attrib_list:
                self.is_data_group = True
                
            if 'collapsed' in attrib_list:
                self.is_collapsed = True
                
            # Collect post functions for validation by caller
            for attrib in attrib_list:
                if attrib.startswith('post('):
                    result['post_functions'].append(attrib)
                    
        elif field_name == '_singular':
            self.is_singular = True
            self.singular_field = value
            if value not in section_fields:
                result['error'] = f"Specified a singular field: {value} that is not a field in this section"
                
        elif field_name == '_mapto':
            self.mapto = value
            if value not in all_sections:
                result['error'] = f"_mapto is specifying an invalid section {value}"
        
        return result
        
    def get_fields_dict(self) -> Dict[str, Any]:
        """Get fields as a dict of {field_name: field_type} for backward compatibility
        
        For subtables, returns the nested schema dict instead of field_type.
        Maintains the original schema order (fields and sub-nodes interleaved).
        Excludes metadata like _dataSchema.
        """
        result = {}
        # Use the tracked order to maintain field/subnode interleaving
        for name, item_type in self._item_order:
            if item_type == 'field':
                result[name] = self.fields[name].field_type
            else:  # 'subnode'
                # Skip _dataSchema as it's pure metadata, not an actual field
                if name != '_dataSchema':
                    result[name] = self.sub_nodes[name].get_fields_dict()
        return result
    def finalize(self):
        """Finalize the node after all fields and sub-nodes have been added.
        
        calculate storage key
        """
        printIfDebug(f"Node:{self.name}, storage_key: {self.storage_key_field} parent_keys: {self.parent_key_chain}, parent_storage_key: {self.parent_storage_key_field}")        

    def __repr__(self):
        return f"Node({self.name}, context={self.context}, fields={len(self.fields)}, sub_nodes={len(self.sub_nodes)})"


class Schema:
    """Main schema class managing all sections"""
    
    fn_finders = {
        'auto': re.compile(r"auto\(([^\)]*)\)"),
        'post': re.compile(r"post\(([^\)]*)\)")
    }
    # match optional*() and get the bracket contents
    optional_find = re.compile(r"optional.*\(([^\)]*)\)")
    
    def __init__(self, schema_yaml=None, schema_file='', skip_config=False):
        self.sections: Dict[str, Node] = {}  # section_name -> Node (top-level only)
        self.nodes: Dict[str, Node] = {}  # full_path -> Node (all nodes, for direct access)
        self.tables: List[str] = []  # List of table names
        self.config = None
        self.col_sql: Dict[str, str] = {}  # table -> SQL column string
        self.counter_reverse_field: Dict[str, str] = {}  # Back-references for calculators
        self._data = None  # Backward compatibility - lazy loaded
        
        if schema_yaml:
            if not skip_config:
                from pysrc.processYaml import config
                self.config = config(RO=False)
            self.validate(schema_yaml, schema_file)
            # Build data dict immediately after validation so it's available
            self._data = self._build_data_dict()
        elif not skip_config:
            from pysrc.processYaml import config
            self.config = config(RO=True)
            self._load_from_config()
        
        if not skip_config:
            printIfDebug("Schema loaded")
    
    @property
    def data(self) -> dict:
        """Backward compatibility property - provides old dict-based interface"""
        return self._data
        
    def get_section(self, name: str) -> Optional[Node]:
        """Get a top-level section node"""
        return self.sections.get(name)
        
    def get_node(self, full_path: str) -> Optional[Node]:
        """Get any node by full path (e.g., 'structuresvars')"""
        return self.nodes.get(full_path)
        
    def get_table_names(self) -> List[str]:
        """Get list of all table names (already filtered to exclude mapto aliases)"""
        return self.tables
    
    def get_node(self, table_name: str) -> Optional[Node]:
        """
        Get the Node object for a given table name.
        
        Args:
            table_name: Full table name (e.g., 'interface_defs', 'interface_defsmodports')
        
        Returns:
            Node object if found, None otherwise
        """
        return self.nodes.get(table_name)
        
    def _function_find(self, fn_type: str, data: str) -> str:
        """Find auto or post function in a field type string"""
        if data[:len(fn_type)] == fn_type and len(data) > len(fn_type):
            # Import here to avoid circular dependency
            from pysrc.processYaml import projectCreate
            
            f = self.fn_finders[fn_type].search(data)
            if not f:
                return ""
            brace_contents = f.group(1).strip()
            fn = f"_{fn_type}_" + brace_contents
            # search the projectCreate class to see if it contains an appropriate fn
            if hasattr(projectCreate, fn):
                # valid function
                return fn
            else:
                return "__bad_function"
        return ""
        
    def validate(self, schema_yaml: dict, schema_file: str):
        """Parse and validate schema YAML, building Node/Field hierarchy"""
        valid_field_types = {
            'key', 'required', 'eval', 'const', 'optional', 'optionalConst', 'auto', 'post', 'dataGroup',
            'list', 'outerkey', 'outer', 'multiple', '_ignore', 'collapsed', 'combo', 'param', 
            'singleEntryList', 'listkey', 'subkey', 'context', 'contextKey', 'ignore', 'outerkeyKey', 'anchor'
        }
        reserved_keys = {'_validate', '_type', '_key', '_combo', '_attribs', '_singular', '_mapto'}
        custom_checker = {'_singular', '_mapto'}
        
        # Process all sections recursively, starting with no parent keys
        self._validate_sections(schema_yaml, schema_file, '', valid_field_types, reserved_keys, custom_checker)
                
    def _validate_sections(self, schema: dict, schema_file: str, context: str,
                          valid_field_types: set, reserved_keys: set, custom_checker: set, 
                          parent_keys: Optional[List[str]] = None, parent_storage_key: Optional[str] = None,
                          parent_node: Optional['Node'] = None):
        """Validate and build nodes for all sections in the schema
        
        Args:
            parent_keys: List of ancestor key field names (e.g., ['interface_typeKey', 'modportKey'])
                        that should be added to this node if it's a collapsed table
        """
        parent_keys = parent_keys or [] # handle default case. if none provided, use empty list

        for section in schema:
            is_combo_override = False  # Reset for each section
            current_keys = parent_keys  # Reset for each section - can be overridden by combo keys
            if section == 'memories':
                pass
            node = Node(section, context)
            
            # Set parent_key_chain from the parent_keys passed down
            # parent_node is passed from the recursive call and contains the parent's field information
            node.set_parent_key_chain(parent_keys, parent_storage_key, parent_node)
            # For collapsed tables, add all ancestor key fields first
            # This will be set later when we process _attribs, but we'll add the fields at the end
            ancestor_keys_to_add = []
                
            item_key_name = None
            indexes = []
            optional_defaults = {}
            
            # Process all fields in this section
            for field_name, ftype in schema[section].items():
                # Get line number if available
                if hasattr(ftype, 'lc'):
                    line_number = ftype.lc.line + 1
                elif hasattr(schema[section], 'lc'):
                    line_number = schema[section].lc.line + 1
                else:
                    line_number = 0
                    printWarning(f"Warning: {schema_file} {section} {field_name} does not have a line number")
                
                # Handle metadata fields early (before creating Field objects)
                if field_name in ('_attribs', '_singular', '_mapto'):
                    result = node.set_metadata_field(field_name, ftype, schema[section], schema)
                    
                    # Check for validation errors
                    if result['error']:
                        printError(f"Bad schema detected in {schema_file}:{line_number}, section {section} context {context}. {result['error']}")
                        exit(warningAndErrorReport())
                    
                    # Validate and set post functions
                    for post_func_str in result['post_functions']:
                        fn = self._function_find('post', post_func_str)
                        if fn:
                            if fn == "__bad_function":
                                printError(f"Bad schema detected in {schema_file}:{line_number}. Field {field_name} post, is referencing an invalid function '{post_func_str}'")
                                exit(warningAndErrorReport())
                            else:
                                node.post_function = fn
                    
                    # For dataGroup nodes, configure storage_key_field early (before processing subtables)
                    # so that child tables can inherit it correctly
                    if field_name == '_attribs' and node.is_data_group:
                        if not node.parent_storage_key_field:
                            printError(f"Bad schema detected in {schema_file}, section {section}. dataGroup table must be nested under a parent table with a key")
                            exit(warningAndErrorReport())
                        # Configure key using existing API - it handles dataGroup logic
                        node.set_key()
                    
                    continue  # Don't process metadata fields as regular fields
                
                # Handle dict-based field definitions (nested or with _type)
                if isinstance(ftype, dict):
                    my_type = ftype.get('_type', None)
                    my_validate = ftype.get('_validate', None)
                    my_combo_key = ftype.get('_key', None)
                    my_combo_field = ftype.get('_combo', None)
                    
                    if my_combo_key:
                        my_type = 'key'
                        # Note: We'll call set_key() later after fields are created and validated
                        # Just mark that we have a combo key for now
                    if my_combo_field:
                        my_type = 'combo'
                        
                    # Check if this is a sub-table or just a field with metadata
                    is_sub_table = False
                    if field_name == '_dataSchema':
                        # Special case: data schema is a nested definition but not a subtable
                        # Process it separately but don't add it as a field or subnode
                        sub_schema_dict = {field_name: ftype}
                        self._validate_sections(sub_schema_dict, schema_file, context + section,
                                              valid_field_types, reserved_keys, custom_checker, parent_keys, node.get_storage_key_field_name(), node)
                        # Store reference to dataschema node (will be linked later)
                        continue  # Don't add _dataSchema as a regular field
                    else:
                        for k in ftype:
                            # Any non-reserved field implies subtable
                            if k not in reserved_keys:
                                is_sub_table = True
                                break
                                
                        if is_sub_table:
                            # Build parent keys for the child - inherit our parent_keys plus our own key (if we have one)
                            child_parent_keys = list(current_keys)  # Copy parent's keys
                            if item_key_name and item_key_name not in child_parent_keys:  # If this node has a key, add it to child's parent keys
                                child_parent_keys.append(item_key_name)
                            
                            # This is a subtable - recursively validate it with updated parent keys
                            sub_schema = {field_name: ftype}
                            self._validate_sections(sub_schema, schema_file, context + section,
                                                  valid_field_types, reserved_keys, custom_checker, child_parent_keys, node.get_storage_key_field_name(), node)
                            
                            # Add the sub-node to this node
                            sub_node = self.nodes.get(context + section + field_name)
                            if sub_node:
                                node.add_sub_node(sub_node)
                            
                            # Even though it's a subtable, it could still be the key in collapsed case
                            if my_type == 'key':
                                item_key_name = field_name
                                # Add contextKey field
                                context_key_field = Field(field_name + 'Key', 'contextKey', line_number)
                                node.add_field(context_key_field)
                            continue
                        else:
                            if my_type is None:
                                printError(f"Bad schema detected in {schema_file}:{line_number}. Section {context}, {section}, Field {field_name}, is missing a _type definition")
                                exit(warningAndErrorReport())
                                
                    # Create field with the determined type
                    field = Field(field_name, my_type, line_number)
                    
                    # Check for naming conflicts with auto-generated qualified key fields
                    # The system auto-generates fields like 'interface_typeKey' for key/outerkey fields
                    # Users should not manually declare fields ending with 'Key'
                    if field_name.endswith('Key') and my_type not in ['contextKey', 'outerkeyKey', 'ignore']:
                        # Check if this looks like it might be an auto-generated field name
                        base_name = field_name[:-3]  # Remove 'Key' suffix
                        if base_name in schema[section]:
                            printError(
                                f"Bad schema detected in {schema_file}:{line_number}. "
                                f"Field '{field_name}' appears to be a manually declared qualified key field. "
                                f"The system auto-generates '{field_name}' from '{base_name}'. "
                                f"Please remove '{field_name}' from the schema - it will be created automatically."
                            )
                            exit(warningAndErrorReport())
                    
                    # Handle validator
                    if my_validate is not None:
                        validator = ValidationRule('section' if 'section' in my_validate else 'values')
                        if 'section' in my_validate:
                            validator.section = my_validate['section']
                            validator.field = my_validate.get('field')
                            validator.scope = my_validate.get('scope')
                            # Mark field as foreign key (references another table)
                            field.is_foreign_key = True
                            # Add fieldKey for lookup validators (but not for combo fields or combo keys)
                            # Combo keys will have their qualified key created by set_key()
                            # Regular combo fields don't need qualified keys
                            if not my_combo_field and not my_combo_key:
                                field_key = Field(field_name + 'Key', 'ignore', line_number)
                                node.add_field(field_key)
                        elif 'values' in my_validate:
                            validator.values = my_validate['values']
                        field.validator = validator
                    
                    # Handle combo key
                    if my_combo_key:
                        combo_sources = list(my_combo_key.keys()) if isinstance(my_combo_key, dict) else []
                        
                        # Verify referenced fields exist
                        for k in combo_sources:
                            if k not in node.fields:
                                printError(f"Bad schema detected in {schema_file}:{line_number}. Field {field_name} combo key, is referencing an invalid field '{k}'. Fields must be declared before use")
                                exit(warningAndErrorReport())
                        
                        # Use the set_key API which internally uses add_combo for all setup
                        current_keys = combo_sources  # override any inheritance from parent keys
                        is_combo_override = True
                        node.set_key(field_name, is_combo=True, combo_sources=combo_sources)
                        my_type = 'key'
                        item_key_name = field_name
                        
                    # Handle combo field
                    if my_combo_field:
                        combo_sources = list(my_combo_field.keys()) if isinstance(my_combo_field, dict) else []
                        
                        # Verify referenced fields exist
                        for k in combo_sources:
                            if k not in node.fields:
                                printError(f"Bad schema detected in {schema_file}:{line_number}. Field {field_name} combo field, is referencing an invalid field '{k}'. Fields must be declared before use")
                                exit(warningAndErrorReport())
                        
                        # Use add_combo which handles all setup including qualified sources
                        # Update field reference to the one created by add_combo
                        field = node.add_combo(field_name, combo_sources, field_type='combo')
                        
                    node.add_field(field)
                else:
                    # Simple field (string type)
                    my_type = ftype
                    field = Field(field_name, my_type, 0)
                    node.add_field(field)
                    
                # Process field type attributes
                fn = self._function_find('auto', my_type)
                if fn:
                    if fn == "__bad_function":
                        printError(f"Bad schema detected in {schema_file}:{line_number}. Field {field_name} auto, is referencing an invalid function '{my_type}' ")
                        exit(warningAndErrorReport())
                    else:
                        field.auto_function = fn
                        # counterReverseField allows back reference - keyed by context+section+functionname
                        self.counter_reverse_field[context + section + fn[len('_auto_'):]] = field_name
                    my_type = 'auto'
                    field.field_type = my_type
                    
                if my_type == 'const' or my_type[:13] == 'optionalConst' or my_type == 'param':
                    # Add fieldKey for const/param fields
                    field_key = Field(field_name + 'Key', "ignore", line_number)
                    node.add_field(field_key)
                    
                if my_type[:8] == 'optional' and len(my_type) > 8:
                    brace_contents = self.optional_find.search(my_type)
                    if brace_contents:
                        if my_type[:13] == 'optionalConst':
                            optional_type = 'optionalConst'
                        else:
                            optional_type = 'optional'
                        default = brace_contents.group(1).strip()
                        if str(default).lower() in {"true", "false"}:
                            default = str(default).lower() == "true"
                        field.field_type = optional_type
                        field.default_value = default
                        optional_defaults[field_name] = default
                        my_type = optional_type  # Update my_type for validation
                        
                # Validate field type
                check_fields = [my_type] if not isinstance(my_type, list) else my_type
                for check in check_fields:
                    if check[:4] == 'post':
                        continue
                    if check not in valid_field_types and field_name not in custom_checker:
                        printError(f"Bad schema detected in {schema_file}:{line_number}. Field {field_name} is using unknown value '{check}' ")
                        exit(warningAndErrorReport())
                        
                # Handle key field
                if my_type == 'key' and not is_combo_override:
                    item_key_name = field_name
                    
                    # For nested tables, treat 'key' as 'anchor' since the actual storage key
                    # will be a composite field created by set_key()
                    if node.parent_storage_key_field:
                        # Change field type to 'anchor' for nested tables
                        field.field_type = 'anchor'
                        my_type = 'anchor'
                    
                    # Add the key field itself first (needed by set_key for composite key creation)
                    node.add_field(field)
                    
                    # Add contextKey field
                    context_key_field = Field(field_name + 'Key', 'contextKey', line_number)
                    node.add_field(context_key_field)
                    node.set_key(field_name, is_combo=False)
                    
                    # Key field is fully processed, skip normal field addition
                    continue
                
                # Handle anchor field (used with _key directive for composite keys, or in nested tables)
                if my_type == 'anchor':
                    # Anchor fields are valid in two cases:
                    # 1. With _key directive (explicit combo key)
                    # 2. In nested tables (where 'key' was converted to 'anchor')
                    if not node.is_combo_key and not node.parent_storage_key_field:
                        printError(
                            f"Bad schema detected in {schema_file}:{line_number}. "
                            f"Field '{field_name}' is declared as 'anchor' but no _key directive is present and this is not a nested table. "
                            f"Anchor fields are only valid when defining composite keys with _key or in nested tables. "
                            f"Either add a _key directive or change '{field_name}' to 'key'."
                        )
                        exit(warningAndErrorReport())
                    item_key_name = field_name
                    node.anchor_field = field_name
                    # Note: storage_key_field is already set by the combo key processing (combo keys)
                    # or by set_key() (nested tables)
                    # Add contextKey field if not already present
                    if not node.has_field(field_name + 'Key'):
                        context_key_field = Field(field_name + 'Key', 'contextKey', line_number)
                        node.add_field(context_key_field)
                
                # Handle listkey field (for singleEntryList)
                # Only set as key if no key has been set yet (combo keys take precedence)
                if my_type == 'listkey':
                    if not item_key_name:  # Only set if not already set by a combo key
                        item_key_name = field_name
                        node.set_key(field_name, is_combo=False)
                    # Add contextKey field regardless
                    context_key_field = Field(field_name + 'Key', 'contextKey', line_number)
                    node.add_field(context_key_field)
                    
                # Handle outerkey field
                if my_type == 'outerkey':
                    # For outerkey case we also need the key with context added
                    outer_key_field = Field(field_name + 'Key', 'outerkeyKey', line_number)
                    node.add_field(outer_key_field)
                    node.outerkey_key_field = field_name + 'Key'
                    node.outer_key_fields.append(field_name)
                    indexes.append(field_name + 'Key')
            
            # Verify that list tables have an explicit key defined
            if node.is_list and item_key_name is None:
                printError(f"Bad schema detected in {schema_file}. Section {context}{section} is a list table but has no key field defined. All list tables must have an explicit key field (e.g., 'fieldName: key').")
                exit(warningAndErrorReport())
            
            node.finalize()
            
            # Verify key field exists (skip for mapto sections since they're just aliases)
            if node.mapto is not None:
                # Store mapto node in nodes dict for lookups, but not in sections
                # (mapto sections are aliases, not real tables)
                self.nodes[node.full_path] = node
                continue
            
            # Handle dataGroup tables - they inherit parent's key (1-to-1 relationship)
            # Note: storage_key_field was already set early when processing _attribs
            if node.is_data_group and item_key_name is None:
                # Verify storage_key_field was set correctly
                if not node.storage_key_field:
                    printError(f"Bad schema detected in {schema_file}, section {section}. dataGroup table storage_key_field not configured")
                    exit(warningAndErrorReport())
            elif item_key_name is None:
                printError(f"Bad schema detected in {schema_file}, section {section}. There is no field defined as key")
                exit(warningAndErrorReport())
                
            # Verify single entry list has required fields
            if node.is_single_entry_list:
                found_listkey = False
                for field_name, field in node.fields.items():
                    if field.field_type == 'listkey':
                        found_listkey = True
                    elif field.field_type not in ['key', 'outerkey', 'outer', 'outerkeyKey', 'context', 'contextKey']:
                        printError(f"Bad schema detected in {schema_file}, section {section} context {context}. singleEntryList is specified but field {field_name} is defined as {field.field_type}. Only listkey, key, outerkey and outer are allowed")
                        exit(warningAndErrorReport())
                if not found_listkey:
                    printError(f"Bad schema detected in {schema_file}, section {section} context {context}. singleEntryList is specified but no field is defined as listkey")
                    exit(warningAndErrorReport())
                    
            # Add _context field
            context_field = Field('_context', 'context', 0)
            node.add_field(context_field)
            
            # Set up indexes
            # For dataGroup tables, use the parent's storage key field for indexing
            if node.is_data_group and item_key_name is None:
                # dataGroup uses parent's storage key
                if node.storage_key_field:
                    indexes.append(node.storage_key_field + 'Key')
            elif item_key_name:
                indexes.append(item_key_name + 'Key')
            node.indexes = indexes
            
            # Store the node
            if context == "":
                self.sections[section] = node
                # Only add to tables list if it's a real table (not a mapto alias)
                if not node.mapto:
                    self.tables.append(section)
            self.nodes[node.full_path] = node
            
            # Handle _dataSchema
            if '_dataSchema' in schema[section]:
                data_schema_node = self.nodes.get(context + section + '_dataSchema')
                if data_schema_node:
                    node.data_schema = data_schema_node
                    
    def _load_from_config(self):
        """Load schema from config database (for read-only access)"""
        # Load the entire pickled Schema object
        schema_obj = self.config.getConfig('SCHEMA')
        if not schema_obj:
            return
        
        # Restore all attributes from the pickled Schema object
        self.sections = schema_obj.sections
        self.nodes = schema_obj.nodes
        self.tables = schema_obj.tables
        self.col_sql = schema_obj.col_sql
        self.counter_reverse_field = schema_obj.counter_reverse_field
        self._data = schema_obj._data
        
    def _build_data_dict(self) -> dict:
        """Build data dictionary from Node/Field structure for backward compatibility"""
        data = {
            'schema': {},
            'key': {},
            'attrib': {},
            'dataSchema': {},
            'colsSQL': self.col_sql,
            'multiEntry': {},
            'fnStr': {},
            'post': {},
            'optionalDefault': {},
            'mapto': {},
            'validator': {},
            'counterReverseField': self.counter_reverse_field,
            'subTable': {},
            'outerkeyKey': {},
            'parentKeyChain': {},  # Export parent key chains for nested reconstruction
            'indexes': {},
            'tables': {t: t for t in self.tables},
            'comboKey': {},
            'comboField': {},
            'singular': {}
        }
        
        # Convert nodes back to dict structure
        for full_path, node in self.nodes.items():
            # Skip mapto nodes - they're aliases, not real tables
            if node.mapto is not None:
                # Store mapto reference
                data['mapto'][full_path] = node.mapto
                continue
                
            # Build field dict (including nested subnodes)
            field_dict = node.get_fields_dict()
                
            # Store in schema dict
            if node.context == "":
                data['schema'][node.name] = field_dict
            
            # Store key field
            if node.storage_key_field:
                data['key'][full_path] = node.storage_key_field
            elif node.anchor_field:
                data['key'][full_path] = node.anchor_field
                
            # Store attributes
            if node.attributes:
                data['attrib'][full_path] = node.attributes
                
            # Store multi-entry flag
            data['multiEntry'][full_path] = node.is_multi_entry
            
            # Store indexes
            data['indexes'][full_path] = node.indexes
            
                
            # Store singular
            if node.is_singular:
                data['singular'][full_path] = node.singular_field
                
            # Store mapto
            if node.mapto:
                data['mapto'][full_path] = node.mapto
                
            # Store post function
            if node.post_function:
                data['post'][full_path] = node.post_function
                
            # Store outer key key field
            if node.outerkey_key_field:
                data['outerkeyKey'][full_path] = node.outerkey_key_field
            
            # Store parent key chain (for nested reconstruction)
            if node.parent_key_chain:
                data['parentKeyChain'][full_path] = node.parent_key_chain
                
            # Store field-level data
            for field_name, field in node.fields.items():
                field_path = full_path + field_name
                
                # Store auto function
                if field.auto_function:
                    data['fnStr'][field_path] = field.auto_function
                    
                # Store default value
                if field.default_value is not None:
                    data['optionalDefault'][field_path] = field.default_value
                    
                # Store validator
                if field.validator:
                    if field.validator.rule_type == 'section':
                        validator_dict = {
                            'section': field.validator.section,
                            'field': field.validator.field
                        }
                        # Only include scope if it's not None
                        if field.validator.scope is not None:
                            validator_dict['scope'] = field.validator.scope
                        data['validator'][field_path] = validator_dict
                    else:
                        data['validator'][field_path] = {
                            'values': field.validator.values
                        }
                    
                # Store combo field
                if field.is_combo:
                    data['comboKey'][full_path] = {src: 'required' for src in field.combo_sources}
                    if full_path not in data['comboField']:
                        data['comboField'][full_path] = {}
                    data['comboField'][full_path][field_name] = {src: 'required' for src in field.combo_sources}
                    
            # Store sub-tables
            if node.sub_nodes:
                if node.full_path not in data['subTable']:
                    data['subTable'][node.full_path] = {}
                for sub_name, sub_node in node.sub_nodes.items():
                    data['subTable'][node.full_path][sub_node.full_path] = sub_name
                    
            # Store data schema reference
            if node.data_schema:
                data['dataSchema'][full_path] = self._node_to_dict(node.data_schema)
        
        return data
    
    def save(self):
        """Serialize schema to database"""
        # Build data dict and store in self._data before pickling
        self._data = self._build_data_dict()
        
        # Pickle the entire Schema object (includes nodes, sections, tables, etc.)
        self.config.setConfig('SCHEMA', self, bin=True)
        
    def _node_to_dict(self, node: Node) -> dict:
        """Convert a node to a dict representation for storage"""
        result = {}
        for field_name, field in node.fields.items():
            result[field_name] = field.field_type
        return result

