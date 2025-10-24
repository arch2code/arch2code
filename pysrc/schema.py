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
        self.combo_sources: List[str] = []  # Fields used to create this field
        
    def __repr__(self):
        return f"Field({self.name}, {self.field_type})"


class Node:
    """Represents a section or subtable in the schema"""
    
    def __init__(self, name: str, context: str = ''):
        self.name = name
        self.context = context  # e.g., "structures" for nested vars
        self.full_path = context + name
        self.fields: Dict[str, Field] = {}  # name -> Field
        self.sub_nodes: Dict[str, Node] = {}  # name -> Node
        self._item_order: List[tuple] = []  # [(name, 'field'|'subnode')] - tracks insertion order
        
        # Key composition tracking
        self.anchor_field: Optional[str] = None  # Field name that captures YAML anchor (marked as 'key')
        self.key_fields: List[str] = []  # All fields that compose the database key
        self.outer_key_fields: List[str] = []  # Fields marked as 'outerkey' (reference parent)
        self.is_combo_key = False  # True if key uses _key: directive
        self.combo_key_sources: List[str] = []  # Fields used for combo key
        
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
        """Get the name of the field that captures the YAML anchor"""
        return self.anchor_field
        
    def get_key_field_names(self) -> List[str]:
        """Get list of all fields that compose the database key"""
        return self.key_fields
        
    def get_outer_key_fields(self) -> List[str]:
        """Get fields that reference parent node's key"""
        return self.outer_key_fields
        
    def add_field(self, field: Field):
        """Add a field to this node"""
        self.fields[field.name] = field
        self._item_order.append((field.name, 'field'))
        
    def add_sub_node(self, node: 'Node'):
        """Add a sub-node to this node"""
        self.sub_nodes[node.name] = node
        self._item_order.append((node.name, 'subnode'))
        
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
                - 'needs_listindex': bool - True if _listIndex field should be added
                - 'post_functions': list - List of post function strings to validate
        """
        result = {
            'error': None,
            'needs_listindex': False,
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
                result['needs_listindex'] = True
                
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
        elif not skip_config:
            from pysrc.processYaml import config
            self.config = config(RO=True)
            self._load_from_config()
        
        if not skip_config:
            printIfDebug("Schema loaded")
    
    @property
    def data(self) -> dict:
        """Backward compatibility property - provides old dict-based interface"""
        if self._data is None:
            self._data = self._build_data_dict()
        return self._data
    
    def _build_data_dict(self) -> dict:
        """Build old-style data dictionary from Node/Field structure for backward compatibility"""
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
            'indexes': {},
            'tables': {t: t for t in self.tables},
            'comboKey': {},
            'comboField': {},
            'singular': {}
        }
        
        # Convert nodes to dict structure
        for full_path, node in self.nodes.items():
            # Handle mapto nodes (they're aliases to other sections)
            if node.mapto:
                data['mapto'][full_path] = node.mapto
                # Don't process the rest for mapto sections
                continue
            
            # Build field dict
            field_dict = node.get_fields_dict()
            
            # Store in schema dict (only top-level sections, excluding mapto)
            if node.context == "":
                data['schema'][node.name] = field_dict
            
            # Store key field
            if node.anchor_field:
                data['key'][full_path] = node.anchor_field
                
            # Store attributes
            if node.attributes:
                data['attrib'][full_path] = node.attributes
                
            # Store multi-entry flag
            data['multiEntry'][full_path] = node.is_multi_entry
            
            # Store indexes
            data['indexes'][full_path] = node.indexes
            
            # Store combo key
            if node.is_combo_key:
                data['comboKey'][full_path] = {src: 'required' for src in node.combo_key_sources}
                
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
                data['dataSchema'][full_path] = node.data_schema.get_fields_dict()
                
        return data
        
    def get_section(self, name: str) -> Optional[Node]:
        """Get a top-level section node"""
        return self.sections.get(name)
        
    def get_node(self, full_path: str) -> Optional[Node]:
        """Get any node by full path (e.g., 'structuresvars')"""
        return self.nodes.get(full_path)
        
    def get_table_names(self) -> List[str]:
        """Get list of all table names (already filtered to exclude mapto aliases)"""
        return self.tables
        
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
            'singleEntryList', 'listkey', 'subkey', 'context', 'contextKey', 'ignore', 'outerkeyKey'
        }
        reserved_keys = {'_validate', '_type', '_key', '_combo', '_attribs', '_singular', '_mapto'}
        custom_checker = {'_singular', '_mapto'}
        
        # Process all sections recursively
        self._validate_sections(schema_yaml, schema_file, '', valid_field_types, reserved_keys, custom_checker)
                
    def _validate_sections(self, schema: dict, schema_file: str, context: str,
                          valid_field_types: set, reserved_keys: set, custom_checker: set):
        """Validate and build nodes for all sections in the schema"""
        for section in schema:
            node = Node(section, context)
                
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
                    
                    # Add _listIndex field if needed
                    if result['needs_listindex']:
                        item_key_name = '_listIndex'
                        list_index_field = Field('_listIndex', 'key', line_number)
                        node.add_field(list_index_field)
                    
                    # Validate and set post functions
                    for post_func_str in result['post_functions']:
                        fn = self._function_find('post', post_func_str)
                        if fn:
                            if fn == "__bad_function":
                                printError(f"Bad schema detected in {schema_file}:{line_number}. Field {field_name} post, is referencing an invalid function '{post_func_str}'")
                                exit(warningAndErrorReport())
                            else:
                                node.post_function = fn
                    
                    continue  # Don't process metadata fields as regular fields
                
                # Handle dict-based field definitions (nested or with _type)
                if isinstance(ftype, dict):
                    my_type = ftype.get('_type', None)
                    my_validate = ftype.get('_validate', None)
                    my_combo_key = ftype.get('_key', None)
                    my_combo_field = ftype.get('_combo', None)
                    
                    if my_combo_key:
                        my_type = 'key'
                        node.is_combo_key = True
                        node.combo_key_sources = list(my_combo_key.keys()) if isinstance(my_combo_key, dict) else []
                    if my_combo_field:
                        my_type = 'combo'
                        
                    # Check if this is a sub-table or just a field with metadata
                    is_sub_table = False
                    if field_name == '_dataSchema':
                        # Special case: data schema is a nested definition but not a subtable
                        # Process it separately but don't add it as a field or subnode
                        sub_schema_dict = {field_name: ftype}
                        self._validate_sections(sub_schema_dict, schema_file, context + section,
                                              valid_field_types, reserved_keys, custom_checker)
                        # Store reference to dataschema node (will be linked later)
                        continue  # Don't add _dataSchema as a regular field
                    else:
                        for k in ftype:
                            # Any non-reserved field implies subtable
                            if k not in reserved_keys:
                                is_sub_table = True
                                break
                                
                        if is_sub_table:
                            # This is a subtable - recursively validate it
                            sub_schema = {field_name: ftype}
                            self._validate_sections(sub_schema, schema_file, context + section,
                                                  valid_field_types, reserved_keys, custom_checker)
                            
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
                    
                    # Handle validator
                    if my_validate is not None:
                        validator = ValidationRule('section' if 'section' in my_validate else 'values')
                        if 'section' in my_validate:
                            validator.section = my_validate['section']
                            validator.field = my_validate.get('field')
                            validator.scope = my_validate.get('scope')
                            # Add fieldKey for lookup validators
                            field_key = Field(field_name + 'Key', 'ignore', line_number)
                            node.add_field(field_key)
                        elif 'values' in my_validate:
                            validator.values = my_validate['values']
                        field.validator = validator
                    
                    # Handle combo key
                    if my_combo_key:
                        # Verify referenced fields exist
                        for k in my_combo_key:
                            if k not in node.fields:
                                printError(f"Bad schema detected in {schema_file}:{line_number}. Field {field_name} combo key, is referencing an invalid field '{k}'. Fields must be declared before use")
                                exit(warningAndErrorReport())
                        node.combo_key_sources = list(my_combo_key.keys()) if isinstance(my_combo_key, dict) else []
                        my_type = 'key'
                        
                    # Handle combo field
                    if my_combo_field:
                        for k in my_combo_field:
                            if k not in node.fields:
                                printError(f"Bad schema detected in {schema_file}:{line_number}. Field {field_name} combo field, is referencing an invalid field '{k}'. Fields must be declared before use")
                                exit(warningAndErrorReport())
                        field.is_combo = True
                        field.combo_sources = list(my_combo_field.keys()) if isinstance(my_combo_field, dict) else []
                        
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
                if my_type == 'key':
                    item_key_name = field_name
                    node.anchor_field = field_name
                    # Add contextKey field
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
                        
            # Verify key field exists (skip for mapto sections since they're just aliases)
            if node.mapto is not None:
                # Store mapto node in nodes dict for lookups, but not in sections
                # (mapto sections are aliases, not real tables)
                self.nodes[node.full_path] = node
                continue
            if item_key_name is None:
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
        # Load the schema data dictionary from config
        data = self.config.getConfig('SCHEMA')
        if not data:
            return
            
        # For backward compatibility, store the data dict directly
        self._data = data
        
        # Extract tables list
        if 'tables' in data:
            # Convert from dict format {table_name: table_name} to list
            self.tables = list(data['tables'].keys())
        
        # Extract counter reverse field
        if 'counterReverseField' in data:
            self.counter_reverse_field = data['counterReverseField']
            
        # Extract colsSQL
        if 'colsSQL' in data:
            self.col_sql = data['colsSQL']
        
    def save(self):
        """Serialize schema to database"""
        # Convert Node/Field structure back to dict format for storage
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
            'indexes': {},
            'tables': {t: t for t in self.tables},
            'comboKey': {},
            'comboField': {},
            'singular': {}
        }
        
        # Convert nodes back to dict structure
        for full_path, node in self.nodes.items():
            # Build field dict (including nested subnodes)
            field_dict = node.get_fields_dict()
                
            # Store in schema dict
            if node.context == "":
                data['schema'][node.name] = field_dict
            
            # Store key field
            if node.anchor_field:
                data['key'][full_path] = node.anchor_field
            elif node.is_list:
                # Lists use _listIndex as the key
                data['key'][full_path] = '_listIndex'
                
            # Store attributes
            if node.attributes:
                data['attrib'][full_path] = node.attributes
                
            # Store multi-entry flag
            data['multiEntry'][full_path] = node.is_multi_entry
            
            # Store indexes
            data['indexes'][full_path] = node.indexes
            
            # Store combo key
            if node.is_combo_key:
                data['comboKey'][full_path] = {src: 'required' for src in node.combo_key_sources}
                
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
                
        self.config.setConfig('SCHEMA', data, bin=True)
        
    def _node_to_dict(self, node: Node) -> dict:
        """Convert a node to a dict representation for storage"""
        result = {}
        for field_name, field in node.fields.items():
            result[field_name] = field.field_type
        return result

