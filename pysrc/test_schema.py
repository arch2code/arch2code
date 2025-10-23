"""
Unit tests for the schema module.

Tests the Field, Node, and Schema classes with various configurations.
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pysrc.schema import Field, Node, Schema, ValidationRule


class TestField(unittest.TestCase):
    """Test the Field class"""
    
    def test_field_creation(self):
        """Test basic field creation"""
        field = Field("test_field", "required")
        self.assertEqual(field.name, "test_field")
        self.assertEqual(field.field_type, "required")
        self.assertIsNone(field.validator)
        self.assertIsNone(field.default_value)
        
    def test_field_with_line_number(self):
        """Test field with line number"""
        field = Field("test_field", "required", 42)
        self.assertEqual(field.line_number, 42)
        
    def test_field_types(self):
        """Test various field types"""
        types = ['key', 'required', 'optional', 'eval', 'const', 'auto', 'outerkey']
        for ftype in types:
            field = Field(f"field_{ftype}", ftype)
            self.assertEqual(field.field_type, ftype)
            
    def test_field_with_validator(self):
        """Test field with validator"""
        field = Field("test_field", "required")
        validator = ValidationRule('section')
        validator.section = 'types'
        validator.field = 'type'
        field.validator = validator
        self.assertIsNotNone(field.validator)
        self.assertEqual(field.validator.section, 'types')
        
    def test_field_with_default_value(self):
        """Test field with default value"""
        field = Field("test_field", "optional")
        field.default_value = "default"
        self.assertEqual(field.default_value, "default")
        
    def test_field_with_auto_function(self):
        """Test field with auto function"""
        field = Field("test_field", "auto")
        field.auto_function = "_auto_width"
        self.assertEqual(field.auto_function, "_auto_width")
        
    def test_field_combo(self):
        """Test combo field"""
        field = Field("test_field", "combo")
        field.is_combo = True
        field.combo_sources = ['field1', 'field2']
        self.assertTrue(field.is_combo)
        self.assertEqual(len(field.combo_sources), 2)
        

class TestNode(unittest.TestCase):
    """Test the Node class"""
    
    def test_node_creation(self):
        """Test basic node creation"""
        node = Node("test_node")
        self.assertEqual(node.name, "test_node")
        self.assertEqual(node.context, "")
        self.assertEqual(node.full_path, "test_node")
        self.assertEqual(len(node.fields), 0)
        self.assertEqual(len(node.sub_nodes), 0)
        
    def test_node_with_context(self):
        """Test node with context"""
        node = Node("vars", "structures")
        self.assertEqual(node.name, "vars")
        self.assertEqual(node.context, "structures")
        self.assertEqual(node.full_path, "structuresvars")
        
    def test_add_field(self):
        """Test adding fields to a node"""
        node = Node("test_node")
        field1 = Field("field1", "required")
        field2 = Field("field2", "optional")
        node.add_field(field1)
        node.add_field(field2)
        self.assertEqual(len(node.fields), 2)
        self.assertIn("field1", node.fields)
        self.assertIn("field2", node.fields)
        
    def test_get_field(self):
        """Test getting a field by name"""
        node = Node("test_node")
        field = Field("test_field", "required")
        node.add_field(field)
        retrieved = node.get_field("test_field")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "test_field")
        self.assertIsNone(node.get_field("nonexistent"))
        
    def test_add_sub_node(self):
        """Test adding sub-nodes"""
        parent = Node("parent")
        child = Node("child", "parent")
        parent.add_sub_node(child)
        self.assertEqual(len(parent.sub_nodes), 1)
        self.assertIn("child", parent.sub_nodes)
        
    def test_get_sub_node(self):
        """Test getting a sub-node by name"""
        parent = Node("parent")
        child = Node("child", "parent")
        parent.add_sub_node(child)
        retrieved = parent.get_sub_node("child")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "child")
        
    def test_simple_key(self):
        """Test simple key field"""
        node = Node("constants")
        node.anchor_field = "constant"
        node.key_fields = ["constant"]
        self.assertEqual(node.get_anchor_field_name(), "constant")
        self.assertEqual(node.get_key_field_names(), ["constant"])
        
    def test_composite_key(self):
        """Test composite key"""
        node = Node("connections")
        node.is_combo_key = True
        node.combo_key_sources = ["interface", "src", "dst"]
        self.assertTrue(node.is_combo_key)
        self.assertEqual(len(node.combo_key_sources), 3)
        
    def test_outer_key(self):
        """Test outer key fields"""
        node = Node("vars", "structures")
        node.outer_key_fields = ["structure"]
        self.assertEqual(node.get_outer_key_fields(), ["structure"])
        
    def test_multi_entry_node(self):
        """Test multi-entry node"""
        node = Node("types")
        node.is_multi_entry = True
        node.attributes = ['multiple']
        self.assertTrue(node.is_multi_entry)
        self.assertIn('multiple', node.attributes)
        
    def test_collapsed_node(self):
        """Test collapsed node"""
        node = Node("vars", "structures")
        node.is_collapsed = True
        node.attributes = ['collapsed', 'required', 'multiple']
        self.assertTrue(node.is_collapsed)
        
    def test_singular_field(self):
        """Test singular field conversion"""
        node = Node("signals")
        node.is_singular = True
        node.singular_field = "signalType"
        self.assertTrue(node.is_singular)
        self.assertEqual(node.singular_field, "signalType")
        
    def test_mapto(self):
        """Test section mapping"""
        node = Node("enums")
        node.mapto = "types"
        self.assertEqual(node.mapto, "types")
        
    def test_set_metadata_field_attribs(self):
        """Test set_metadata_field with _attribs"""
        node = Node("test_node")
        section_fields = {"field1": "required", "field2": "optional"}
        all_sections = {"section1": {}, "section2": {}}
        
        result = node.set_metadata_field("_attribs", ["multiple", "collapsed"], section_fields, all_sections)
        
        self.assertIsNone(result['error'])
        self.assertFalse(result['needs_listindex'])
        self.assertEqual(len(result['post_functions']), 0)
        self.assertTrue(node.is_multi_entry)
        self.assertTrue(node.is_collapsed)
        self.assertEqual(node.attributes, ["multiple", "collapsed"])
        
    def test_set_metadata_field_attribs_list(self):
        """Test set_metadata_field with _attribs containing list"""
        node = Node("test_node")
        section_fields = {}
        all_sections = {}
        
        result = node.set_metadata_field("_attribs", ["list", "multiple"], section_fields, all_sections)
        
        self.assertIsNone(result['error'])
        self.assertTrue(result['needs_listindex'])
        self.assertTrue(node.is_list)
        self.assertTrue(node.is_multi_entry)
        
    def test_set_metadata_field_attribs_single_entry_list(self):
        """Test set_metadata_field with singleEntryList"""
        node = Node("test_node")
        section_fields = {}
        all_sections = {}
        
        result = node.set_metadata_field("_attribs", "singleEntryList", section_fields, all_sections)
        
        self.assertIsNone(result['error'])
        self.assertTrue(node.is_single_entry_list)
        self.assertTrue(node.is_multi_entry)
        
    def test_set_metadata_field_attribs_with_post(self):
        """Test set_metadata_field with post function in attributes"""
        node = Node("test_node")
        section_fields = {}
        all_sections = {}
        
        result = node.set_metadata_field("_attribs", ["multiple", "post(myFunction)"], section_fields, all_sections)
        
        self.assertIsNone(result['error'])
        self.assertEqual(len(result['post_functions']), 1)
        self.assertIn("post(myFunction)", result['post_functions'])
        
    def test_set_metadata_field_singular_valid(self):
        """Test set_metadata_field with valid _singular"""
        node = Node("test_node")
        section_fields = {"field1": "required", "signalType": "required"}
        all_sections = {}
        
        result = node.set_metadata_field("_singular", "signalType", section_fields, all_sections)
        
        self.assertIsNone(result['error'])
        self.assertTrue(node.is_singular)
        self.assertEqual(node.singular_field, "signalType")
        
    def test_set_metadata_field_singular_invalid(self):
        """Test set_metadata_field with invalid _singular"""
        node = Node("test_node")
        section_fields = {"field1": "required"}
        all_sections = {}
        
        result = node.set_metadata_field("_singular", "nonexistent", section_fields, all_sections)
        
        self.assertIsNotNone(result['error'])
        self.assertIn("nonexistent", result['error'])
        self.assertIn("not a field", result['error'])
        
    def test_set_metadata_field_mapto_valid(self):
        """Test set_metadata_field with valid _mapto"""
        node = Node("enums")
        section_fields = {}
        all_sections = {"types": {}, "constants": {}}
        
        result = node.set_metadata_field("_mapto", "types", section_fields, all_sections)
        
        self.assertIsNone(result['error'])
        self.assertEqual(node.mapto, "types")
        
    def test_set_metadata_field_mapto_invalid(self):
        """Test set_metadata_field with invalid _mapto"""
        node = Node("enums")
        section_fields = {}
        all_sections = {"types": {}, "constants": {}}
        
        result = node.set_metadata_field("_mapto", "nonexistent", section_fields, all_sections)
        
        self.assertIsNotNone(result['error'])
        self.assertIn("nonexistent", result['error'])
        self.assertIn("invalid section", result['error'])
        
    def test_field_ordering_preserved(self):
        """Test that field and subnode ordering is preserved"""
        node = Node("test_node")
        
        # Add fields and subnodes in specific order
        field1 = Field("alpha", "required")
        node.add_field(field1)
        
        subnode1 = Node("beta", "test_node")
        node.add_sub_node(subnode1)
        
        field2 = Field("gamma", "optional")
        node.add_field(field2)
        
        subnode2 = Node("delta", "test_node")
        node.add_sub_node(subnode2)
        
        field3 = Field("epsilon", "key")
        node.add_field(field3)
        
        # Check that _item_order preserves the insertion order
        self.assertEqual(len(node._item_order), 5)
        self.assertEqual(node._item_order[0], ("alpha", "field"))
        self.assertEqual(node._item_order[1], ("beta", "subnode"))
        self.assertEqual(node._item_order[2], ("gamma", "field"))
        self.assertEqual(node._item_order[3], ("delta", "subnode"))
        self.assertEqual(node._item_order[4], ("epsilon", "field"))
        
    def test_get_fields_dict_ordering(self):
        """Test that get_fields_dict maintains order"""
        node = Node("test_node")
        
        # Add in specific order: field, subnode, field
        node.add_field(Field("field1", "required"))
        
        subnode = Node("subnode1", "test_node")
        subnode.add_field(Field("nested1", "optional"))
        node.add_sub_node(subnode)
        
        node.add_field(Field("field2", "key"))
        
        result = node.get_fields_dict()
        
        # Verify order is maintained
        keys = list(result.keys())
        self.assertEqual(keys, ["field1", "subnode1", "field2"])
        self.assertEqual(result["field1"], "required")
        self.assertEqual(result["field2"], "key")
        self.assertIsInstance(result["subnode1"], dict)
        self.assertEqual(result["subnode1"]["nested1"], "optional")
        

class TestSchema(unittest.TestCase):
    """Test the Schema class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the config class to avoid database dependencies
        import pysrc.processYaml as py
        self.original_config = py.config
        
    def test_schema_creation(self):
        """Test basic schema creation"""
        # This will test without YAML (read-only mode)
        # We'll skip this for now since it requires database
        pass
        
    def test_simple_schema_validation(self):
        """Test validation of a simple schema"""
        simple_schema = {
            'constants': {
                'constant': 'key',
                'value': 'eval',
                'desc': 'required'
            }
        }
        
        schema = Schema(skip_config=True)
        schema.validate(simple_schema, 'test_schema.yaml')
        
        self.assertIn('constants', schema.sections)
        node = schema.get_section('constants')
        self.assertIsNotNone(node)
        self.assertEqual(node.anchor_field, 'constant')
        self.assertIn('constant', node.fields)
        self.assertIn('value', node.fields)
        self.assertIn('desc', node.fields)
        
    def test_nested_schema_validation(self):
        """Test validation of schema with nested tables"""
        nested_schema = {
            'types': {
                'type': 'key',
                'desc': 'required',
                'enum': {
                    '_attribs': ['optional', 'list'],
                    'enumName': 'required',
                    'type': 'outerkey'
                }
            }
        }
        
        schema = Schema(skip_config=True)
        schema.validate(nested_schema, 'test_schema.yaml')
        
        self.assertIn('types', schema.sections)
        types_node = schema.get_section('types')
        self.assertIsNotNone(types_node)
        self.assertIn('enum', types_node.sub_nodes)
        
        enum_node = types_node.get_sub_node('enum')
        self.assertIsNotNone(enum_node)
        self.assertTrue(enum_node.is_list)
        self.assertTrue(enum_node.is_multi_entry)
        
    def test_collapsed_nested_schema(self):
        """Test validation of collapsed nested schema"""
        collapsed_schema = {
            'structures': {
                'structure': 'key',
                'vars': {
                    '_attribs': ['required', 'multiple', 'collapsed'],
                    'structure': 'outerkey',
                    'variable': 'key',
                    'varType': {
                        '_type': 'optional'
                    }
                }
            }
        }
        
        schema = Schema(skip_config=True)
        schema.validate(collapsed_schema, 'test_schema.yaml')
        
        structures_node = schema.get_section('structures')
        self.assertIsNotNone(structures_node)
        self.assertIn('vars', structures_node.sub_nodes)
        
        vars_node = structures_node.get_sub_node('vars')
        self.assertIsNotNone(vars_node)
        self.assertTrue(vars_node.is_collapsed)
        self.assertTrue(vars_node.is_multi_entry)
        
    def test_field_with_validator(self):
        """Test field with cross-reference validator"""
        schema_with_validator = {
            'variables': {
                'variable': 'key',
                'type': {
                    '_type': 'required',
                    '_validate': {
                        'section': 'types',
                        'field': 'type'
                    }
                }
            }
        }
        
        schema = Schema(skip_config=True)
        schema.validate(schema_with_validator, 'test_schema.yaml')
        
        variables_node = schema.get_section('variables')
        type_field = variables_node.get_field('type')
        self.assertIsNotNone(type_field)
        self.assertIsNotNone(type_field.validator)
        self.assertEqual(type_field.validator.section, 'types')
        self.assertEqual(type_field.validator.field, 'type')
        
    def test_field_with_values_validator(self):
        """Test field with enumerated values validator"""
        schema_with_values = {
            'interfaces': {
                'interface': 'key',
                'interfaceType': {
                    '_type': 'required',
                    '_validate': {
                        'values': ['rdy_vld', 'push_ack', 'pop_ack']
                    }
                }
            }
        }
        
        schema = Schema(skip_config=True)
        schema.validate(schema_with_values, 'test_schema.yaml')
        
        interfaces_node = schema.get_section('interfaces')
        type_field = interfaces_node.get_field('interfaceType')
        self.assertIsNotNone(type_field)
        self.assertIsNotNone(type_field.validator)
        self.assertEqual(type_field.validator.values, ['rdy_vld', 'push_ack', 'pop_ack'])
        
    def test_optional_field_with_default(self):
        """Test optional field with default value"""
        schema_with_optional = {
            'blocks': {
                'block': 'key',
                'hasVl': 'optional(false)'
            }
        }
        
        schema = Schema(skip_config=True)
        schema.validate(schema_with_optional, 'test_schema.yaml')
        
        blocks_node = schema.get_section('blocks')
        has_vl_field = blocks_node.get_field('hasVl')
        self.assertIsNotNone(has_vl_field)
        self.assertEqual(has_vl_field.field_type, 'optional')
        self.assertEqual(has_vl_field.default_value, False)
        
    def test_composite_key_schema(self):
        """Test schema with composite key"""
        composite_key_schema = {
            'connections': {
                'interface': 'required',
                'src': 'required',
                'dst': 'required',
                'connection': {
                    '_key': {
                        'interface': 'required',
                        'src': 'required',
                        'dst': 'required'
                    }
                }
            }
        }
        
        schema = Schema(skip_config=True)
        schema.validate(composite_key_schema, 'test_schema.yaml')
        
        connections_node = schema.get_section('connections')
        self.assertIsNotNone(connections_node)
        self.assertTrue(connections_node.is_combo_key)
        self.assertGreater(len(connections_node.combo_key_sources), 0)
        
    def test_singular_field_schema(self):
        """Test schema with singular field"""
        singular_schema = {
            'signals': {
                '_attribs': ['required', 'multiple'],
                'signal': 'key',
                'signalType': 'required',
                '_singular': 'signalType'
            }
        }
        
        schema = Schema(skip_config=True)
        schema.validate(singular_schema, 'test_schema.yaml')
        
        signals_node = schema.get_section('signals')
        self.assertIsNotNone(signals_node)
        self.assertTrue(signals_node.is_singular)
        self.assertEqual(signals_node.singular_field, 'signalType')
        
    def test_mapto_schema(self):
        """Test schema with section mapping"""
        mapto_schema = {
            'types': {
                'type': 'key',
                'desc': 'required'
            },
            'enums': {
                '_mapto': 'types'
            }
        }
        
        schema = Schema(skip_config=True)
        schema.validate(mapto_schema, 'test_schema.yaml')
        
        # enums should be removed from sections after validation
        self.assertNotIn('enums', schema.sections)
        self.assertIn('types', schema.sections)
        
    def test_get_section(self):
        """Test get_section method"""
        simple_schema = {
            'constants': {
                'constant': 'key',
                'value': 'required'
            }
        }
        
        schema = Schema(skip_config=True)
        schema.validate(simple_schema, 'test_schema.yaml')
        
        node = schema.get_section('constants')
        self.assertIsNotNone(node)
        self.assertEqual(node.name, 'constants')
        self.assertIsNone(schema.get_section('nonexistent'))
        
    def test_get_node(self):
        """Test get_node method with full path"""
        nested_schema = {
            'structures': {
                'structure': 'key',
                'vars': {
                    '_attribs': ['required', 'multiple'],
                    'variable': 'key'
                }
            }
        }
        
        schema = Schema(skip_config=True)
        schema.validate(nested_schema, 'test_schema.yaml')
        
        # Get parent node
        structures_node = schema.get_node('structures')
        self.assertIsNotNone(structures_node)
        
        # Get nested node by full path
        vars_node = schema.get_node('structuresvars')
        self.assertIsNotNone(vars_node)
        self.assertEqual(vars_node.name, 'vars')
        self.assertEqual(vars_node.context, 'structures')
        
    def test_get_table_names(self):
        """Test get_table_names method"""
        multi_table_schema = {
            'constants': {'constant': 'key'},
            'types': {'type': 'key'},
            'variables': {'variable': 'key'}
        }
        
        schema = Schema(skip_config=True)
        schema.validate(multi_table_schema, 'test_schema.yaml')
        
        tables = schema.get_table_names()
        self.assertEqual(len(tables), 3)
        self.assertIn('constants', tables)
        self.assertIn('types', tables)
        self.assertIn('variables', tables)
        
    def test_tables_prefiltered(self):
        """Test that schema.tables is pre-filtered to exclude mapto sections"""
        schema_with_mapto = {
            'types': {
                'type': 'key',
                'desc': 'optional'
            },
            'enums': {
                '_mapto': 'types'
            },
            'constants': {
                'constant': 'key',
                'value': 'required'
            }
        }
        
        schema = Schema(skip_config=True)
        schema.validate(schema_with_mapto, 'test_schema.yaml')
        
        # schema.tables should already be filtered
        self.assertEqual(len(schema.tables), 2)
        self.assertIn('types', schema.tables)
        self.assertIn('constants', schema.tables)
        self.assertNotIn('enums', schema.tables)
        
        # data['schema'] should also be filtered
        self.assertEqual(len(schema.data['schema']), 2)
        self.assertIn('types', schema.data['schema'])
        self.assertIn('constants', schema.data['schema'])
        self.assertNotIn('enums', schema.data['schema'])
        
        # mapto info should be in data['mapto']
        self.assertIn('enums', schema.data['mapto'])
        self.assertEqual(schema.data['mapto']['enums'], 'types')


class TestSchemaIntegration(unittest.TestCase):
    """Integration tests with more complex schema definitions"""
    
    def test_full_types_schema(self):
        """Test a full types schema with enum"""
        types_schema = {
            'types': {
                'type': 'key',
                'desc': 'required',
                'enum': {
                    '_attribs': ['optional', 'list', 'post(add_enum)'],
                    'enumName': 'required',
                    'type': 'outerkey',
                    'desc': 'optional',
                    'value': 'eval'
                },
                'width': 'auto(width)'
            }
        }
        
        schema = Schema(skip_config=True)
        schema.validate(types_schema, 'test_schema.yaml')
        
        types_node = schema.get_section('types')
        self.assertIsNotNone(types_node)
        
        # Check auto field
        width_field = types_node.get_field('width')
        self.assertIsNotNone(width_field)
        self.assertEqual(width_field.field_type, 'auto')
        
        # Check nested enum
        enum_node = types_node.get_sub_node('enum')
        self.assertIsNotNone(enum_node)
        self.assertTrue(enum_node.is_list)
        
    def test_interface_defs_multi_level(self):
        """Test interface_defs with multiple nesting levels"""
        interface_defs_schema = {
            'interface_defs': {
                'interface_type': 'key',
                'signals': {
                    '_attribs': ['required', 'multiple'],
                    'interface_type': 'outerkey',
                    'signal': 'key',
                    'signalType': 'required',
                    '_singular': 'signalType'
                },
                'modports': {
                    '_attribs': ['required', 'multiple'],
                    'interface_type': 'outerkey',
                    'modport': 'key',
                    'modportGroups': {
                        '_attribs': ['optional', 'multiple', 'collapsed'],
                        'modportGroup': 'key'
                    }
                }
            }
        }
        
        schema = Schema(skip_config=True)
        schema.validate(interface_defs_schema, 'test_schema.yaml')
        
        interface_defs_node = schema.get_section('interface_defs')
        self.assertIsNotNone(interface_defs_node)
        
        # Check signals
        signals_node = interface_defs_node.get_sub_node('signals')
        self.assertIsNotNone(signals_node)
        self.assertTrue(signals_node.is_singular)
        
        # Check modports
        modports_node = interface_defs_node.get_sub_node('modports')
        self.assertIsNotNone(modports_node)
        
        # Check nested modportGroups
        modport_groups_node = modports_node.get_sub_node('modportGroups')
        self.assertIsNotNone(modport_groups_node)
        self.assertTrue(modport_groups_node.is_collapsed)


class TestSchemaSerialization(unittest.TestCase):
    """Test schema serialization and deserialization"""
    
    def test_save_method_structure(self):
        """Test that save method can be called and produces expected structure"""
        simple_schema = {
            'constants': {
                'constant': 'key',
                'value': 'eval',
                'desc': 'required'
            }
        }
        
        schema = Schema(skip_config=True)
        schema.validate(simple_schema, 'test_schema.yaml')
        
        # We can't actually test save() without a real database
        # but we can verify the structure is there
        self.assertTrue(hasattr(schema, 'save'))
        self.assertIn('constants', schema.sections)
        # Verify the schema has the expected attributes for serialization
        self.assertIsNotNone(schema.col_sql)
        self.assertIsNotNone(schema.counter_reverse_field)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestField))
    suite.addTests(loader.loadTestsFromTestCase(TestNode))
    suite.addTests(loader.loadTestsFromTestCase(TestSchema))
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaSerialization))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

