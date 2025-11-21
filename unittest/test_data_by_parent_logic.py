#!/usr/bin/env python3
"""
Test the data_by_parent indexing logic using real schema and database.

This test validates that parent-child relationships work correctly by:
1. Building a real database from test YAML files
2. Loading it with projectOpen (which uses the real schema)
3. Verifying the loaded data structures are correct

This approach tests the BEHAVIOR, not the implementation details.
"""

import sys
import os
import subprocess
import tempfile

# Add builder to path
test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen


def build_test_database():
    """Build a test database to get real schema and data."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db', prefix='test_data_by_parent_')
    os.close(db_fd)
    
    mixed_dir = os.path.join(test_dir, 'mixed_test_arch')
    yaml_path = os.path.join(mixed_dir, 'mixedProject.yaml')
    
    arch2code_path = os.path.join(base_dir, 'arch2code.py')
    cmd = [sys.executable, arch2code_path, '--yaml', yaml_path, '--db', db_path]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=mixed_dir)
    
    if result.returncode != 0:
        os.unlink(db_path)
        raise RuntimeError(f"Failed to build database:\n{result.stderr}")
    
    return db_path


def test_interfaces_with_structures_separated():
    """Test that interface structures are properly separated by qualified keys."""
    print("\n=== Test 1: Interface Structures Separation ===")
    
    db_path = build_test_database()
    try:
        proj = projectOpen(db_path)
        
        # Check that duplicate interfaces have separate structure lists
        if 'interfaces' not in proj.data:
            print("✗ No interfaces in proj.data")
            return False
        
        # Find dupIf interfaces
        dupif_interfaces = {k: v for k, v in proj.data['interfaces'].items() if 'dupIf' in k}
        
        if len(dupif_interfaces) != 2:
            print(f"✗ Expected 2 dupIf interfaces, found {len(dupif_interfaces)}")
            return False
        
        print(f"✓ Found {len(dupif_interfaces)} dupIf interfaces")
        
        # Verify each has exactly 1 structure from its own context
        for key, intf_data in dupif_interfaces.items():
            structures = intf_data.get('structures', [])
            context = intf_data.get('_context')
            
            if len(structures) != 1:
                print(f"✗ Interface {key} has {len(structures)} structures (expected 1)")
                return False
            
            struct_context = structures[0].get('_context')
            if struct_context != context:
                print(f"✗ Interface {key} (context={context}) has structure from {struct_context}")
                return False
            
            print(f"✓ Interface {key}: 1 structure from correct context ({context})")
        
        return True
        
    finally:
        os.unlink(db_path)


def test_schema_node_configuration():
    """Test that schema nodes are properly configured (using API, not internals)."""
    print("\n=== Test 2: Schema Node Configuration ===")
    
    db_path = build_test_database()
    try:
        proj = projectOpen(db_path)
        
        # Test that we can get schema nodes via API
        interfaces_node = proj.getSchemaNode('interfaces')
        if not interfaces_node:
            print("✗ Could not get interfaces node")
            return False
        print(f"✓ Got interfaces node: {interfaces_node.name}")
        
        # Test that nested table node exists
        structures_node = proj.getSchemaNode('interfacesstructures')
        if not structures_node:
            print("✗ Could not get interfacesstructures node")
            return False
        print(f"✓ Got interfacesstructures node: {structures_node.name}")
        
        # Use public API methods to check configuration
        interfaces_key = interfaces_node.get_storage_key_field_name_qualified()
        print(f"✓ interfaces storage key field (qualified): {interfaces_key}")
        
        structures_parent = structures_node.get_parent_storage_key_field_name()
        print(f"✓ interfacesstructures parent key field: {structures_parent}")
        
        return True
        
    finally:
        os.unlink(db_path)


def test_nested_data_correctly_attached():
    """Test that nested tables are correctly attached to their parents."""
    print("\n=== Test 3: Nested Data Attachment ===")
    
    db_path = build_test_database()
    try:
        proj = projectOpen(db_path)
        
        # Check that interfaces have their structures properly attached
        if 'interfaces' not in proj.data:
            print("✗ No interfaces in proj.data")
            return False
        
        interfaces_with_structures = 0
        for key, intf_data in proj.data['interfaces'].items():
            structures = intf_data.get('structures')
            if structures:
                interfaces_with_structures += 1
                
                # Verify structures is a list
                if not isinstance(structures, list):
                    print(f"✗ Interface {key} structures is not a list: {type(structures)}")
                    return False
                
                # Verify each structure has proper fields
                for struct in structures:
                    if not isinstance(struct, dict):
                        print(f"✗ Structure is not a dict: {type(struct)}")
                        return False
                    
                    required_fields = ['structure', 'structureType', '_context']
                    missing = [f for f in required_fields if f not in struct]
                    if missing:
                        print(f"✗ Structure missing fields: {missing}")
                        return False
        
        print(f"✓ Found {interfaces_with_structures} interfaces with properly attached structures")
        return True
        
    finally:
        os.unlink(db_path)


def test_context_isolation():
    """Test that data from different contexts doesn't mix."""
    print("\n=== Test 4: Context Isolation ===")
    
    db_path = build_test_database()
    try:
        proj = projectOpen(db_path)
        
        # Get all interfaces and group by context
        contexts = {}
        for key, intf_data in proj.data.get('interfaces', {}).items():
            context = intf_data.get('_context')
            if context not in contexts:
                contexts[context] = []
            contexts[context].append(key)
        
        print(f"✓ Found {len(contexts)} contexts: {list(contexts.keys())}")
        
        # For each interface, verify structures match its context
        for key, intf_data in proj.data.get('interfaces', {}).items():
            intf_context = intf_data.get('_context')
            structures = intf_data.get('structures')
            
            # Skip interfaces without structures
            if not structures:
                continue
            
            for struct in structures:
                struct_context = struct.get('_context')
                if struct_context != intf_context:
                    print(f"✗ Context mismatch: interface {key} ({intf_context}) has structure from {struct_context}")
                    return False
        
        print(f"✓ All structures match their parent interface context")
        return True
        
    finally:
        os.unlink(db_path)


if __name__ == '__main__':
    print("="*70)
    print("TESTING DATA_BY_PARENT LOGIC WITH REAL SCHEMA")
    print("="*70)
    
    tests = [
        ("Interface Structures Separation", test_interfaces_with_structures_separated),
        ("Schema Node Configuration", test_schema_node_configuration),
        ("Nested Data Attachment", test_nested_data_correctly_attached),
        ("Context Isolation", test_context_isolation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n✅ ALL TESTS PASSED!")
        sys.exit(0)

