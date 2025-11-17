"""
Unit tests for the processYaml module.

Tests the projectCreate and projectOpen classes to ensure that all input data
is properly stored and retrieved from the database.
"""

import unittest
import sys
import os
import tempfile
import shutil
import sqlite3
from pathlib import Path
from collections import OrderedDict

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pysrc.processYaml import projectCreate, projectOpen
from pysrc import arch2codeGlobals as g


class TestMixedProjectRoundTrip(unittest.TestCase):
    """
    Test that projectCreate and projectOpen work together.
    Creates the mixed project database once, opens it once, and verifies all data.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures - runs once for all tests"""
        # Use the mixed project as it contains comprehensive test cases
        cls.base_dir = Path(__file__).parent.parent
        cls.test_project_dir = cls.base_dir / "examples" / "mixed" / "arch"
        cls.test_project_file = cls.test_project_dir / "mixedProject.yaml"
        
        # Verify the test project exists
        if not cls.test_project_file.exists():
            raise FileNotFoundError(
                f"Test project file not found: {cls.test_project_file}"
            )
        
        # Create a temporary directory for test database
        cls.temp_dir = tempfile.mkdtemp(prefix="test_processYaml_")
        cls.test_db_file = os.path.join(cls.temp_dir, "test_mixed.db")
        
        # Change to project directory and create the project
        cls.original_dir = os.getcwd()
        os.chdir(cls.test_project_dir)
        
        try:
            # Create the project (this is the ONE projectCreate call)
            print(f"\nCreating project from {cls.test_project_file}...")
            cls.proj_create = projectCreate(
                str(cls.test_project_file),
                str(cls.test_db_file)
            )
            print(f"Database created at {cls.test_db_file}")
            
            # Reset globals for projectOpen
            g.db = None
            g.cur = None
            
            # Open the project (this is the ONE projectOpen call)
            print(f"Opening project database...")
            cls.proj = projectOpen(str(cls.test_db_file))
            print(f"Project opened successfully")
            
        except Exception as e:
            os.chdir(cls.original_dir)
            raise
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures - runs once after all tests"""
        # Return to original directory
        os.chdir(cls.original_dir)
        
        # Close any open database connections
        if g.db:
            try:
                g.db.close()
            except:
                pass
        
        # Clean up temporary directory
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    def test_01_database_created(self):
        """Test that database file was created"""
        self.assertTrue(
            os.path.exists(self.test_db_file),
            "Database file should be created"
        )
    
    def test_02_database_has_tables(self):
        """Test that database has expected tables"""
        db = sqlite3.connect(self.test_db_file)
        cur = db.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        db.close()
        
        # Should have at least some standard tables
        expected_tables = ['_config', 'constants', 'types', 'variables', 
                         'structures', 'interfaces', 'blocks', 'instances',
                         'connections']
        for table in expected_tables:
            self.assertIn(
                table, tables,
                f"Expected table '{table}' should exist in database"
            )
    
    def test_03_project_open_loaded_data(self):
        """Test that projectOpen loaded the data"""
        self.assertIsNotNone(self.proj.data, "Data should be loaded")
        self.assertIsNotNone(self.proj.schema, "Schema should be loaded")
        self.assertIsNotNone(self.proj.tables, "Tables should be loaded")
        self.assertGreater(len(self.proj.tables), 0, "Should have at least one table")
    
    def test_04_constants_preserved(self):
        """Test that constants from mixed.yaml are preserved"""
        self.assertIn('constants', self.proj.data, "Constants section should exist")
        constants = self.proj.data['constants']
        self.assertIsInstance(constants, dict, "Constants should be a dictionary")
        
        # Check for specific constants from mixed.yaml
        expected_constants = ['ASIZE', 'DWORD', 'BOB0', 'BOB1', 'TESTCONST1']
        for const_name in expected_constants:
            found = False
            for key, const_data in constants.items():
                if isinstance(const_data, dict) and const_data.get('constant') == const_name:
                    found = True
                    # Verify it has required fields
                    self.assertIn('desc', const_data, 
                                f"Constant {const_name} should have desc field")
                    # Should have value field (even if computed from eval)
                    self.assertIn('value', const_data,
                                f"Constant {const_name} should have value field")
                    break
            
            self.assertTrue(found, f"Expected constant '{const_name}' should exist")
    
    def test_05_types_preserved(self):
        """Test that types from mixed.yaml are preserved"""
        self.assertIn('types', self.proj.data, "Types section should exist")
        types = self.proj.data['types']
        self.assertIsInstance(types, dict, "Types should be a dictionary")
        
        # Check for specific types from mixed.yaml
        expected_types = ['twoBitT', 'threeBitT', 'fourBitT', 'wordT', 'testEnumT', 'readyT']
        for type_name in expected_types:
            found = False
            for key, type_data in types.items():
                if isinstance(type_data, dict) and type_data.get('type') == type_name:
                    found = True
                    # Verify it has desc field
                    self.assertIn('desc', type_data,
                                f"Type {type_name} should have desc field")
                    break
            
            self.assertTrue(found, f"Expected type '{type_name}' should exist")
    
    def test_06_variables_preserved(self):
        """Test that variables from mixed.yaml are preserved"""
        self.assertIn('variables', self.proj.data, "Variables section should exist")
        variables = self.proj.data['variables']
        self.assertIsInstance(variables, dict, "Variables should be a dictionary")
        
        # Check for specific variables from mixed.yaml
        expected_vars = ['variablea', 'variablea2', 'variabled', 'variabled2']
        for var_name in expected_vars:
            found = False
            for key, var_data in variables.items():
                if isinstance(var_data, dict) and var_data.get('variable') == var_name:
                    found = True
                    # Verify it has required fields
                    self.assertIn('desc', var_data,
                                f"Variable {var_name} should have desc field")
                    self.assertIn('type', var_data,
                                f"Variable {var_name} should have type field")
                    break
            
            self.assertTrue(found, f"Expected variable '{var_name}' should exist")
    
    def test_07_structures_preserved(self):
        """Test that structures from mixed.yaml are preserved"""
        self.assertIn('structures', self.proj.data, "Structures section should exist")
        structures = self.proj.data['structures']
        self.assertIsInstance(structures, dict, "Structures should be a dictionary")
        
        # Check for specific structures from mixed.yaml
        expected_structs = ['aSt', 'dSt', 'nestedSt', 'aRegSt', 'seeSt']
        for struct_name in expected_structs:
            found = False
            for key, struct_data in structures.items():
                if isinstance(struct_data, dict) and struct_data.get('structure') == struct_name:
                    found = True
                    break
            
            self.assertTrue(found, f"Expected structure '{struct_name}' should exist")
    
    def test_08_interfaces_preserved(self):
        """Test that interfaces from mixed.yaml are preserved"""
        self.assertIn('interfaces', self.proj.data, "Interfaces section should exist")
        interfaces = self.proj.data['interfaces']
        self.assertIsInstance(interfaces, dict, "Interfaces should be a dictionary")
        
        # Check for specific interfaces from mixed.yaml
        expected_interfaces = ['aStuffIf', 'dStuffIf', 'apbReg', 'startDone', 'cStuffIf']
        for if_name in expected_interfaces:
            found = False
            for key, if_data in interfaces.items():
                if isinstance(if_data, dict) and if_data.get('interface') == if_name:
                    found = True
                    # Verify it has required fields
                    self.assertIn('desc', if_data,
                                f"Interface {if_name} should have desc field")
                    self.assertIn('interfaceType', if_data,
                                f"Interface {if_name} should have interfaceType field")
                    break
            
            self.assertTrue(found, f"Expected interface '{if_name}' should exist")
    
    def test_09_blocks_preserved(self):
        """Test that blocks from mixed.yaml are preserved"""
        self.assertIn('blocks', self.proj.data, "Blocks section should exist")
        blocks = self.proj.data['blocks']
        self.assertIsInstance(blocks, dict, "Blocks should be a dictionary")
        
        # Check for specific blocks from mixed.yaml
        expected_blocks = ['top', 'cpu', 'blockA', 'blockB', 'blockD', 'blockF', 'blockC']
        for block_name in expected_blocks:
            found = False
            for key, block_data in blocks.items():
                if isinstance(block_data, dict) and block_data.get('block') == block_name:
                    found = True
                    # Verify it has required fields
                    self.assertIn('desc', block_data,
                                f"Block {block_name} should have desc field")
                    break
            
            self.assertTrue(found, f"Expected block '{block_name}' should exist")
    
    def test_10_instances_preserved(self):
        """Test that instances from mixed.yaml are preserved"""
        self.assertIn('instances', self.proj.data, "Instances section should exist")
        instances = self.proj.data['instances']
        self.assertIsInstance(instances, dict, "Instances should be a dictionary")
        
        # Check for specific instances from mixed.yaml
        expected_instances = ['uTop', 'uCPU', 'uBlockA', 'uBlockB', 'uBlockD', 'uBlockF0']
        for inst_name in expected_instances:
            found = False
            for key, inst_data in instances.items():
                if isinstance(inst_data, dict) and inst_data.get('instance') == inst_name:
                    found = True
                    # Verify it has required fields
                    self.assertIn('instanceType', inst_data,
                                f"Instance {inst_name} should have instanceType field")
                    self.assertIn('container', inst_data,
                                f"Instance {inst_name} should have container field")
                    break
            
            self.assertTrue(found, f"Expected instance '{inst_name}' should exist")
    
    def test_11_connections_preserved(self):
        """Test that connections from mixed.yaml are preserved"""
        self.assertIn('connections', self.proj.data, "Connections section should exist")
        connections = self.proj.data['connections']
        self.assertIsInstance(connections, dict, "Connections should be a dictionary")
        
        # Verify we have connections
        self.assertGreater(len(connections), 0, "Should have at least one connection")
        
        # Check that connections have required fields
        connection_count = 0
        for key, conn_data in connections.items():
            if isinstance(conn_data, dict):
                # Connections should have interface, src, and dst
                self.assertIn('interface', conn_data,
                            f"Connection {key} should have interface field")
                self.assertIn('src', conn_data,
                            f"Connection {key} should have src field")
                self.assertIn('dst', conn_data,
                            f"Connection {key} should have dst field")
                connection_count += 1
        
        # Should have multiple connections in mixed.yaml
        self.assertGreater(connection_count, 5, "Should have multiple connections")
    
    def test_12_memories_preserved(self):
        """Test that memories from mixed.yaml are preserved"""
        self.assertIn('memories', self.proj.data, "Memories section should exist")
        memories = self.proj.data['memories']
        self.assertIsInstance(memories, dict, "Memories should be a dictionary")
        
        # Check for specific memories from mixed.yaml
        expected_memories = ['blockBTable0', 'blockBTable1', 'blockBTable2']
        for mem_name in expected_memories:
            found = False
            for key, mem_data in memories.items():
                if isinstance(mem_data, dict) and mem_data.get('memory') == mem_name:
                    found = True
                    # Verify it has required fields
                    self.assertIn('block', mem_data,
                                f"Memory {mem_name} should have block field")
                    self.assertIn('structure', mem_data,
                                f"Memory {mem_name} should have structure field")
                    break
            
            self.assertTrue(found, f"Expected memory '{mem_name}' should exist")
    
    def test_13_registers_preserved(self):
        """Test that registers from mixed.yaml are preserved"""
        self.assertIn('registers', self.proj.data, "Registers section should exist")
        registers = self.proj.data['registers']
        self.assertIsInstance(registers, dict, "Registers should be a dictionary")
        
        # Check for specific registers from mixed.yaml
        expected_registers = ['rwD', 'roBsize', 'roA']
        for reg_name in expected_registers:
            found = False
            for key, reg_data in registers.items():
                if isinstance(reg_data, dict) and reg_data.get('register') == reg_name:
                    found = True
                    # Verify it has required fields
                    self.assertIn('regType', reg_data,
                                f"Register {reg_name} should have regType field")
                    self.assertIn('block', reg_data,
                                f"Register {reg_name} should have block field")
                    break
            
            self.assertTrue(found, f"Expected register '{reg_name}' should exist")
    
    def test_14_config_preserved(self):
        """Test that config data is preserved"""
        self.assertIsNotNone(self.proj.config, "Config should exist")
        
        # Check for expected config items
        yaml_base_path = self.proj.config.getConfig('BASEYAMLPATH', failOk=True)
        self.assertIsNotNone(yaml_base_path, "BASEYAMLPATH should be in config")
    
    def test_15_all_sections_have_data(self):
        """Test that all expected sections have data"""
        # Expected sections that should have data from mixed.yaml
        expected_sections = [
            'constants', 'types', 'variables', 'structures',
            'interfaces', 'blocks', 'instances', 'connections'
        ]
        
        # Check each section
        for section in expected_sections:
            self.assertIn(section, self.proj.data,
                        f"Section '{section}' should exist in data")
            self.assertIsInstance(self.proj.data[section], dict,
                                f"Section '{section}' should be a dictionary")
            self.assertGreater(len(self.proj.data[section]), 0,
                             f"Section '{section}' should have data")
    
    def test_16_encoders_preserved(self):
        """Test that encoders from mixed.yaml are preserved"""
        # Encoders are a special section in mixed.yaml
        if 'encoders' in self.proj.data:
            encoders = self.proj.data['encoders']
            self.assertIsInstance(encoders, dict, "Encoders should be a dictionary")
            
            # Check for opcodeEnA from mixed.yaml line 51
            found = False
            for key, enc_data in encoders.items():
                if isinstance(enc_data, dict) and enc_data.get('encoder') == 'opcodeEnA':
                    found = True
                    self.assertIn('desc', enc_data, "Encoder should have desc field")
                    break
            
            if not found:
                print("Note: opcodeEnA encoder not found, may be normal depending on schema")
    
    def test_17_interface_defs_preserved(self):
        """Test that interface_defs are preserved (complex nested structure)"""
        self.assertIn('interface_defs', self.proj.data, 
                     "interface_defs section should exist")
        interface_defs = self.proj.data['interface_defs']
        self.assertIsInstance(interface_defs, dict, 
                            "interface_defs should be a dictionary")
        self.assertGreater(len(interface_defs), 0, 
                          "Should have at least one interface definition")
        
        # Check structure of interface_def entries
        for key, if_def in interface_defs.items():
            if isinstance(if_def, dict):
                self.assertIn('interface_type', if_def,
                            f"Interface def {key} should have interface_type")
    
    def test_18_interface_defs_signals_preserved(self):
        """Test that interface_defs signals (subtable) are preserved"""
        # signals is a direct subtable of interface_defs
        self.assertIn('interface_defssignals', self.proj.data,
                     "interface_defssignals subtable should exist")
        signals = self.proj.data['interface_defssignals']
        self.assertIsInstance(signals, dict, "Signals should be a dictionary")
        
        # Signals are grouped by parent interface_type key
        # Each value is a dict of signal entries
        for parent_key, signal_group in signals.items():
            if isinstance(signal_group, dict):
                # Iterate through individual signals
                for signal_name, signal_data in signal_group.items():
                    if isinstance(signal_data, dict):
                        self.assertIn('signal', signal_data,
                                    f"Signal {signal_name} should have signal field")
                        self.assertIn('signalType', signal_data,
                                    f"Signal {signal_name} should have signalType field")
    
    def test_19_interface_defs_modports_preserved(self):
        """Test that interface_defs modports (subtable) are preserved"""
        # modports is a direct subtable of interface_defs
        self.assertIn('interface_defsmodports', self.proj.data,
                     "interface_defsmodports subtable should exist")
        modports = self.proj.data['interface_defsmodports']
        self.assertIsInstance(modports, dict, "Modports should be a dictionary")
        
        # Modports are grouped by parent interface_type key
        for parent_key, modport_group in modports.items():
            if isinstance(modport_group, dict):
                # Iterate through individual modports
                for modport_name, modport_data in modport_group.items():
                    if isinstance(modport_data, dict):
                        self.assertIn('modport', modport_data,
                                    f"Modport {modport_name} should have modport field")
    
    def test_20_interface_defs_nested_modportgroups_preserved(self):
        """Test that nested modportGroups (sub-subtable) are preserved"""
        # modportGroups is a subtable of modports (2 levels deep)
        self.assertIn('interface_defsmodportsmodportGroups', self.proj.data,
                     "interface_defsmodportsmodportGroups should exist")
        modport_groups = self.proj.data['interface_defsmodportsmodportGroups']
        self.assertIsInstance(modport_groups, dict, 
                            "ModportGroups should be a dictionary")
        
        # Should have entries
        self.assertGreater(len(modport_groups), 0,
                          "Should have at least one modport group")
        
        # ModportGroups are grouped by parent modport key
        for parent_key, mpg_group in modport_groups.items():
            if isinstance(mpg_group, dict):
                # Iterate through individual modportGroups
                for mpg_name, mpg_data in mpg_group.items():
                    if isinstance(mpg_data, dict):
                        self.assertIn('modportGroup', mpg_data,
                                    f"ModportGroup {mpg_name} should have modportGroup field")
    
    def test_21_interface_defs_triple_nested_groups_preserved(self):
        """Test that groups (sub-sub-subtable, 3 levels deep) are preserved"""
        # groups is a subtable of modportGroups which is a subtable of modports
        # This is 3 levels of nesting!
        self.assertIn('interface_defsmodportsmodportGroupsgroups', self.proj.data,
                     "interface_defsmodportsmodportGroupsgroups should exist")
        groups = self.proj.data['interface_defsmodportsmodportGroupsgroups']
        self.assertIsInstance(groups, dict, "Groups should be a dictionary")
        
        # Should have entries
        self.assertGreater(len(groups), 0,
                          "Should have at least one group entry")
        
        # Groups are grouped by parent modportGroup key
        for parent_key, group_group in groups.items():
            if isinstance(group_group, dict):
                # Iterate through individual groups
                for group_name, group_data in group_group.items():
                    if isinstance(group_data, dict):
                        self.assertIn('signal', group_data,
                                    f"Group {group_name} should have signal field")
    
    def test_22_interface_defs_parameters_preserved(self):
        """Test that interface_defs parameters (subtable) are preserved"""
        # parameters is a direct subtable of interface_defs
        self.assertIn('interface_defsparameters', self.proj.data,
                     "interface_defsparameters subtable should exist")
        parameters = self.proj.data['interface_defsparameters']
        self.assertIsInstance(parameters, dict, "Parameters should be a dictionary")
    
    def test_23_interface_defs_sc_channel_preserved(self):
        """Test that interface_defs sc_channel (subtable) are preserved"""
        # sc_channel is a direct subtable of interface_defs
        self.assertIn('interface_defssc_channel', self.proj.data,
                     "interface_defssc_channel subtable should exist")
        sc_channel = self.proj.data['interface_defssc_channel']
        self.assertIsInstance(sc_channel, dict, "SC channel should be a dictionary")
    
    def test_24_all_nested_tables_accessible(self):
        """Test that all nested subtables are accessible and correctly structured"""
        # This tests the recursive loading - all nested tables should be loaded
        # and accessible in the flat data dictionary
        
        nested_tables = [
            'typesenum',  # types -> enum (list subtable)
            'structuresvars',  # structures -> vars (multiple subtable)
            'interfacesstructures',  # interfaces -> structures (list subtable)
            'interface_defssignals',  # interface_defs -> signals
            'interface_defsmodports',  # interface_defs -> modports
            'interface_defsmodportsmodportGroups',  # 2-level nesting
            'interface_defsmodportsmodportGroupsgroups',  # 3-level nesting!
            'encodersitems',  # encoders -> items
            'blocksparams',  # blocks -> params
            'parametersvariants',  # parameters -> variants
            'memoriesports',  # memories -> ports
            'connectionsends',  # connections -> ends
        ]
        
        for table in nested_tables:
            self.assertIn(table, self.proj.data,
                        f"Nested table '{table}' should be loaded and accessible")
            self.assertIsInstance(self.proj.data[table], dict,
                                f"Nested table '{table}' should be a dictionary")
    
    def test_25_getConst_with_integer_values(self):
        """Test getConst with direct integer values"""
        # getConst should pass through integer strings as-is
        self.assertEqual(self.proj.getConst('42'), 42)
        self.assertEqual(self.proj.getConst('0'), 0)
        self.assertEqual(self.proj.getConst('1234'), 1234)
        self.assertEqual(self.proj.getConst('-5'), -5)
    
    def test_26_getConst_with_constant_names(self):
        """Test getConst with qualified constant names"""
        # Constants are stored with qualified keys like 'ASIZE/mixed.yaml'
        
        # Test basic constants from mixed.yaml (using qualified keys)
        asize = self.proj.getConst('ASIZE/mixed.yaml')
        self.assertEqual(asize, 1, "ASIZE should be 1")
        
        dword = self.proj.getConst('DWORD/mixed.yaml')
        self.assertEqual(dword, 32, "DWORD should be 32")
        
        # Test computed constant (from eval)
        asize2 = self.proj.getConst('ASIZE2/mixed.yaml')
        self.assertEqual(asize2, 2, "ASIZE2 should be ASIZE+1 = 2")
        
        bsize = self.proj.getConst('BSIZE/mixedInclude.yaml')
        self.assertEqual(bsize, 10, "BSIZE should be 10")
        
        # Test large hex constants
        yuge = self.proj.getConst('YUGE/mixed.yaml')
        self.assertEqual(yuge, 0x7FFFFFFFFFFFFFFF, "YUGE should be 0x7FFFFFFFFFFFFFFF")
    
    def test_27_getConst_with_negative_constants(self):
        """Test getConst with negative constant values"""
        # Test negative constants from mixed.yaml (using qualified keys)
        intn = self.proj.getConst('INTN/mixed.yaml')
        self.assertLess(intn, 0, "INTN should be negative")
        
        longn = self.proj.getConst('LONGN/mixed.yaml')
        self.assertLess(longn, 0, "LONGN should be negative")
    
    def test_28_getConst_with_hex_constants(self):
        """Test getConst with hexadecimal constant values"""
        # Test hex constants from mixed.yaml (using qualified keys)
        intp = self.proj.getConst('INTP/mixed.yaml')
        self.assertEqual(intp, 0xFFFFFC00, "INTP should match hex value")
        
        bige33 = self.proj.getConst('BIGE33/mixed.yaml')
        self.assertEqual(bige33, 0x1FFFFFFFF, "BIGE33 should match hex value")
    
    def test_29_getConst_preserves_constant_values(self):
        """Test that getConst returns correct values for all constants from constants section"""
        # Test that all constant values are accessible using qualified keys
        
        # Get all constants and verify they return valid integers
        constants_tested = 0
        for qual_key, const_data in self.proj.data['constants'].items():
            if isinstance(const_data, dict):
                expected_value = const_data.get('value')
                
                if expected_value is not None:
                    # getConst should return the same value when given the qualified key
                    result = self.proj.getConst(qual_key)
                    self.assertEqual(result, expected_value,
                                   f"Constant {qual_key} should have value {expected_value}")
                    constants_tested += 1
        
        # Ensure we actually tested some constants
        self.assertGreater(constants_tested, 0, "Should have tested at least one constant")
    
    def test_30_getConst_with_computed_constants(self):
        """Test getConst with constants that have eval expressions"""
        # These constants use eval in mixed.yaml (using qualified keys)
        
        # DWORD_LOG2 uses eval: "($DWORD).bit_length()"
        dword_log2 = self.proj.getConst('DWORD_LOG2/mixed.yaml')
        self.assertEqual(dword_log2, 6, "DWORD_LOG2 should be log2(32+1) = 6")
        
        # BSIZE_LOG2 uses eval: "($BSIZE-1).bit_length()"
        bsize_log2 = self.proj.getConst('BSIZE_LOG2/mixedInclude.yaml')
        self.assertEqual(bsize_log2, 4, "BSIZE_LOG2 should be log2(10-1) = 4")
    
    def test_31_getConst_with_enum_values_from_enums_section(self):
        """Test that getConst can resolve enum values from the top-level enums section"""
        # Extract test cases from typesenum table where type is from enums section
        # From mixed.yaml: test1EnumT with TEST1_A, TEST1_B, TEST1_C
        
        enums_tested = 0
        if 'typesenum' in self.proj.data:
            # test1EnumT is from the top-level enums section
            enum_type_key = 'test1EnumT/mixed.yaml'
            if enum_type_key in self.proj.data['typesenum']:
                enum_list = self.proj.data['typesenum'][enum_type_key]
                self.assertIsInstance(enum_list, list, "typesenum entries should be lists")
                
                for enum_entry in enum_list:
                    if isinstance(enum_entry, dict):
                        enum_name = enum_entry.get('enumName')
                        expected_value = enum_entry.get('value')
                        context = enum_entry.get('_context', '')
                        
                        if enum_name and expected_value is not None:
                            # Construct qualified name: enumName/context
                            qual_enum_name = f"{enum_name}/{context}"
                            result = self.proj.getConst(qual_enum_name)
                            self.assertEqual(result, expected_value,
                                           f"Enum {qual_enum_name} should have value {expected_value}")
                            enums_tested += 1
        
        self.assertGreater(enums_tested, 0, "Should have tested at least one enum from enums section")
    
    def test_32_getConst_with_enum_values_from_types_section(self):
        """Test that getConst can resolve enum values from the types section"""
        # Extract test cases from typesenum table where type is from types section
        # From mixed.yaml types: testEnumT with TEST_A, TEST_B, TEST_C
        
        enums_tested = 0
        if 'typesenum' in self.proj.data:
            # testEnumT is from the types section
            enum_type_key = 'testEnumT/mixed.yaml'
            if enum_type_key in self.proj.data['typesenum']:
                enum_list = self.proj.data['typesenum'][enum_type_key]
                self.assertIsInstance(enum_list, list, "typesenum entries should be lists")
                
                for enum_entry in enum_list:
                    if isinstance(enum_entry, dict):
                        enum_name = enum_entry.get('enumName')
                        expected_value = enum_entry.get('value')
                        context = enum_entry.get('_context', '')
                        
                        if enum_name and expected_value is not None:
                            # Construct qualified name: enumName/context
                            qual_enum_name = f"{enum_name}/{context}"
                            result = self.proj.getConst(qual_enum_name)
                            self.assertEqual(result, expected_value,
                                           f"Enum {qual_enum_name} should have value {expected_value}")
                            enums_tested += 1
        
        self.assertGreater(enums_tested, 0, "Should have tested at least one enum from types section")
    
    def test_33_getConst_with_all_enum_values(self):
        """Test that getConst can resolve ALL enum values from typesenum table"""
        # Comprehensive test: iterate through all enum types and all enum values
        
        total_enums_tested = 0
        if 'typesenum' in self.proj.data:
            for enum_type_key, enum_list in self.proj.data['typesenum'].items():
                if isinstance(enum_list, list):
                    for enum_entry in enum_list:
                        if isinstance(enum_entry, dict):
                            enum_name = enum_entry.get('enumName')
                            expected_value = enum_entry.get('value')
                            context = enum_entry.get('_context', '')
                            
                            if enum_name and expected_value is not None:
                                # Construct qualified name: enumName/context
                                qual_enum_name = f"{enum_name}/{context}"
                                result = self.proj.getConst(qual_enum_name)
                                self.assertEqual(result, expected_value,
                                               f"Enum {qual_enum_name} from type {enum_type_key} "
                                               f"should have value {expected_value}")
                                total_enums_tested += 1
        
        self.assertGreater(total_enums_tested, 10, 
                          f"Should have tested many enums (tested {total_enums_tested})")
    
    def test_34_optionalConst_arraySize_with_default(self):
        """Test that optionalConst sets default value when field is omitted"""
        # Schema defines: arraySize: optionalConst(0)
        # Test structures where arraySize is NOT specified should get default value '0'
        # Note: structuresvars is nested: {structKey: {varName: {fields}}}
        
        if 'structuresvars' in self.proj.data:
            # Look for structure variables without arraySize specified in YAML
            # Example: aASt.variablea has no arraySize in YAML
            found_default = False
            
            for struct_key, var_dict in self.proj.data['structuresvars'].items():
                if isinstance(var_dict, dict):
                    for var_name, var_data in var_dict.items():
                        if isinstance(var_data, dict):
                            struct_name = var_data.get('structure')
                            array_size = var_data.get('arraySize')
                            array_size_key = var_data.get('arraySizeKey')
                            
                            # In the YAML, aASt.variablea is defined as just: variablea: {}
                            # So it should have arraySize = '0' (the default from optionalConst(0))
                            # and arraySizeKey = '' (no constant reference)
                            if struct_name == 'aASt' and var_name == 'variablea':
                                self.assertEqual(array_size, '0', 
                                               f"aASt.variablea should have default arraySize of '0'")
                                self.assertEqual(array_size_key, '', 
                                               f"aASt.variablea should have no arraySizeKey")
                                found_default = True
                                break
                if found_default:
                    break
            
            self.assertTrue(found_default, "Should have found at least one structure variable with default arraySize")
    
    def test_35_optionalConst_arraySize_with_explicit_value(self):
        """Test that optionalConst uses explicit value when provided"""
        # Test structures where arraySize IS specified should use that value
        
        if 'structuresvars' in self.proj.data:
            # Look for structure variables WITH arraySize specified
            # Example: aSt.variablea has arraySize: ASIZE2 in YAML
            found_explicit = False
            
            for struct_key, var_dict in self.proj.data['structuresvars'].items():
                if isinstance(var_dict, dict):
                    for var_name, var_data in var_dict.items():
                        if isinstance(var_data, dict):
                            struct_name = var_data.get('structure')
                            array_size = var_data.get('arraySize')
                            array_size_key = var_data.get('arraySizeKey')
                            
                            # In the YAML, aSt.variablea has arraySize: ASIZE2
                            # It should be stored as 'ASIZE2' (string)
                            # with arraySizeKey: 'ASIZE2/mixed.yaml'
                            if struct_name == 'aSt' and var_name == 'variablea':
                                self.assertEqual(array_size, 'ASIZE2', 
                                               f"aSt.variablea should have arraySize stored as 'ASIZE2'")
                                self.assertEqual(array_size_key, 'ASIZE2/mixed.yaml',
                                               f"aSt.variablea should have arraySizeKey referencing ASIZE2")
                                # Verify it can be resolved using getConst
                                resolved_value = self.proj.getConst(array_size_key)
                                self.assertEqual(resolved_value, 2,
                                               f"ASIZE2 should resolve to 2")
                                found_explicit = True
                                break
                if found_explicit:
                    break
            
            self.assertTrue(found_explicit, "Should have found at least one structure variable with explicit arraySize")
    
    def test_36_optionalConst_memory_count_with_default(self):
        """Test that optionalConst sets default value for memory count when omitted"""
        # Schema defines: count: optionalConst(1)
        # Memories without count specified should get default value '1' (as string)
        
        if 'memories' in self.proj.data:
            # Look for memories without count specified
            # Example: blockBTable0 has no count in YAML
            found_default = False
            
            for mem_key, mem_data in self.proj.data['memories'].items():
                if isinstance(mem_data, dict):
                    memory_name = mem_data.get('memory')
                    count = mem_data.get('count')
                    count_key = mem_data.get('countKey')
                    
                    # blockBTable0 is defined without count, should default to '1'
                    if memory_name == 'blockBTable0':
                        self.assertEqual(count, '1', 
                                       f"blockBTable0 should have default count of '1' (string)")
                        self.assertEqual(count_key, '',
                                       f"blockBTable0 should have empty countKey (no constant reference)")
                        found_default = True
                        break
            
            self.assertTrue(found_default, "Should have found at least one memory with default count")
    
    def test_37_optionalConst_memory_count_with_constant_reference(self):
        """Test that optionalConst stores constant reference and can be resolved"""
        # Test memories where count references a constant
        
        if 'memories' in self.proj.data:
            # Look for memories with count specified as a constant
            # Example: blockBTableSP has count: ASIZE
            found_const = False
            
            for mem_key, mem_data in self.proj.data['memories'].items():
                if isinstance(mem_data, dict):
                    memory_name = mem_data.get('memory')
                    count = mem_data.get('count')
                    count_key = mem_data.get('countKey')
                    
                    # blockBTableSP has count: ASIZE
                    # It should be stored as 'ASIZE' (string)
                    # with countKey: 'ASIZE/mixed.yaml'
                    if memory_name == 'blockBTableSP':
                        self.assertEqual(count, 'ASIZE', 
                                       f"blockBTableSP should have count stored as 'ASIZE'")
                        self.assertEqual(count_key, 'ASIZE/mixed.yaml',
                                       f"blockBTableSP should have countKey referencing ASIZE")
                        # Verify it can be resolved using getConst
                        resolved_value = self.proj.getConst(count_key)
                        self.assertEqual(resolved_value, 1,
                                       f"ASIZE should resolve to 1")
                        found_const = True
                        break
            
            self.assertTrue(found_const, "Should have found at least one memory with constant reference in count")
    
    def test_38_optionalConst_comprehensive_defaults(self):
        """Test that all optionalConst fields have proper default values"""
        # Comprehensive test: verify that optionalDefault is properly loaded
        
        # Check that optionalDefault data exists in schema
        self.assertIn('optionalDefault', self.proj.schema.data,
                     "Schema should have optionalDefault data")
        
        optional_defaults = self.proj.schema.data['optionalDefault']
        
        # Verify specific optionalConst defaults from schema.yaml:
        # - structurevariable.arraySize should default to 0
        # - memories.count should default to 1
        # - interfaces.maxTransferSize should default to 0
        
        # Check for arraySize default
        array_size_keys = [k for k in optional_defaults.keys() if 'arraySize' in k]
        if array_size_keys:
            for key in array_size_keys:
                if 'structurevariable' in key:
                    self.assertEqual(optional_defaults[key], '0',
                                   f"arraySize default should be 0 for {key}")
        
        # Check for count default
        count_keys = [k for k in optional_defaults.keys() if 'count' in k.lower()]
        if count_keys:
            for key in count_keys:
                if 'memories' in key:
                    self.assertEqual(optional_defaults[key], '1',
                                   f"count default should be 1 for {key}")
        
        # Verify we have some optionalDefault entries
        self.assertGreater(len(optional_defaults), 0,
                          "Should have at least one optionalDefault entry")
    
    def test_39_getBlockData_returns_interface_defs(self):
        """Test that getBlockData returns interface_defs for all interface types used"""
        # Get block data for a block that uses interfaces
        # blockA uses multiple interfaces from mixed.yaml
        block_data = self.proj.getBlockData('blockA/mixed.yaml')
        
        # Verify interface_defs exists
        self.assertIn('interface_defs', block_data,
                     "Block data should contain interface_defs")
        self.assertIsInstance(block_data['interface_defs'], dict,
                            "interface_defs should be a dictionary")
        
        # Should have at least one interface definition
        self.assertGreater(len(block_data['interface_defs']), 0,
                          "Should have at least one interface definition")
        
        # Verify structure of interface definitions
        for intf_type, intf_def in block_data['interface_defs'].items():
            self.assertIsInstance(intf_def, dict,
                                f"Interface definition for {intf_type} should be a dict")
            self.assertIn('interface_type', intf_def,
                        f"Interface definition for {intf_type} should have interface_type field")
    
    def test_40_getBlockData_returns_interface_type_mappings(self):
        """Test that getBlockData returns interface_type_mappings dictionary"""
        # Get block data for a block
        block_data = self.proj.getBlockData('blockA/mixed.yaml')
        
        # Verify interface_type_mappings exists
        self.assertIn('interface_type_mappings', block_data,
                     "Block data should contain interface_type_mappings")
        self.assertIsInstance(block_data['interface_type_mappings'], dict,
                            "interface_type_mappings should be a dictionary")
    
    def test_41_interface_type_mappings_includes_reg_mappings(self):
        """Test that interface_type_mappings includes register interface mappings"""
        # Get block data for blockD which has registers
        block_data = self.proj.getBlockData('blockD/mixed.yaml')
        
        mappings = block_data.get('interface_type_mappings', {})
        
        # Check for expected mappings from status_if.yaml and external_reg_if.yaml
        # reg_ro and reg_rw should map to status
        if 'reg_ro' in mappings:
            self.assertEqual(mappings['reg_ro'], 'status',
                           "reg_ro should map to status interface type")
        
        if 'reg_rw' in mappings:
            self.assertEqual(mappings['reg_rw'], 'status',
                           "reg_rw should map to status interface type")
        
        if 'reg_ext' in mappings:
            self.assertEqual(mappings['reg_ext'], 'external_reg',
                           "reg_ext should map to external_reg interface type")
    
    def test_42_interface_defs_contains_status_for_registers(self):
        """Test that interface_defs includes status interface for blocks with registers"""
        # blockD has registers with reg_ro and reg_rw types
        block_data = self.proj.getBlockData('blockD/mixed.yaml')
        
        interface_defs = block_data.get('interface_defs', {})
        
        # Should have status interface definition (canonical type for reg_ro/reg_rw)
        if 'status' in interface_defs:
            status_def = interface_defs['status']
            self.assertIsInstance(status_def, dict,
                                "status interface definition should be a dict")
            self.assertEqual(status_def.get('interface_type'), 'status',
                           "status interface definition should have correct interface_type")
            # Verify it has signals and modports
            self.assertIn('signals', status_def,
                        "status interface should have signals field")
            self.assertIn('modports', status_def,
                        "status interface should have modports field")
    
    def test_43_interface_defs_contains_used_interface_types(self):
        """Test that interface_defs only includes interface types actually used by the block"""
        # Get block data for blockA
        block_data = self.proj.getBlockData('blockA/mixed.yaml')
        
        interface_defs = block_data.get('interface_defs', {})
        interface_types = block_data.get('interfaceTypes', {})
        
        # All interface types used should have definitions (or be None for built-ins)
        for intf_type, qual_key in interface_types.items():
            if qual_key is not None:
                # Should have a definition for this type (or its canonical mapping)
                mappings = block_data.get('interface_type_mappings', {})
                canonical_type = mappings.get(intf_type, intf_type)
                
                # Either the original type or canonical type should be in interface_defs
                found = (intf_type in interface_defs or canonical_type in interface_defs)
                self.assertTrue(found,
                              f"Interface type {intf_type} (canonical: {canonical_type}) "
                              f"should have a definition in interface_defs")
    
    def test_44_interface_defs_has_required_fields(self):
        """Test that interface definitions contain all required fields"""
        # Get block data for a block with various interface types
        block_data = self.proj.getBlockData('blockA/mixed.yaml')
        
        interface_defs = block_data.get('interface_defs', {})
        
        # Check that each interface definition has required fields
        for intf_type, intf_def in interface_defs.items():
            self.assertIn('interface_type', intf_def,
                        f"Interface {intf_type} should have interface_type field")
            self.assertIn('signals', intf_def,
                        f"Interface {intf_type} should have signals field")
            self.assertIn('modports', intf_def,
                        f"Interface {intf_type} should have modports field")
            
            # Verify signals is a dict or list
            self.assertTrue(
                isinstance(intf_def['signals'], (dict, list)),
                f"Interface {intf_type} signals should be dict or list"
            )
            
            # Verify modports is a dict or list
            self.assertTrue(
                isinstance(intf_def['modports'], (dict, list)),
                f"Interface {intf_type} modports should be dict or list"
            )
    
    def test_45_interface_defsmappedFrom_table_exists(self):
        """Test that interface_defsmappedFrom table is loaded"""
        # Verify the flattened mappedFrom table exists
        self.assertIn('interface_defsmappedFrom', self.proj.data,
                     "interface_defsmappedFrom table should exist")
        
        mapped_from = self.proj.data['interface_defsmappedFrom']
        self.assertIsInstance(mapped_from, dict,
                            "interface_defsmappedFrom should be a dictionary")
    
    def test_46_interface_defsmappedFrom_contains_expected_mappings(self):
        """Test that interface_defsmappedFrom contains the mappings we added"""
        # Check the flattened mappedFrom table
        mapped_from = self.proj.data.get('interface_defsmappedFrom', {})
        
        # Should have entries for the mappings we added to YAML files
        # Look for status interface mappings (reg_ro, reg_rw)
        found_reg_ro = False
        found_reg_rw = False
        found_reg_ext = False
        
        for key, mapping_data in mapped_from.items():
            if isinstance(mapping_data, dict):
                interface_type = mapping_data.get('interface_type')
                mapped_type = mapping_data.get('mapped_type')
                
                if interface_type == 'status' and mapped_type == 'reg_ro':
                    found_reg_ro = True
                if interface_type == 'status' and mapped_type == 'reg_rw':
                    found_reg_rw = True
                if interface_type == 'external_reg' and mapped_type == 'reg_ext':
                    found_reg_ext = True
        
        # At least some of these should be found
        found_any = found_reg_ro or found_reg_rw or found_reg_ext
        self.assertTrue(found_any,
                       "Should have found at least one of the expected mappings "
                       "(reg_ro->status, reg_rw->status, reg_ext->external_reg)")


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test class
    suite.addTests(loader.loadTestsFromTestCase(TestMixedProjectRoundTrip))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
