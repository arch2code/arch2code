#!/usr/bin/env python3
"""
Test suite to verify duplicate interface definition handling.
This tests that when an interface is defined in multiple files (mixed.yaml and mixedBlockC.yaml),
the parsing and loading process correctly separates the data.
"""

import sys
import os
import subprocess
import tempfile
import sqlite3

# Add builder to path
test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen
import pysrc.arch2codeGlobals as g


def build_test_database():
    """Build the mixed test database."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db', prefix='test_dup_interface_')
    os.close(db_fd)
    
    # Use unittest mixed test project which has duplicate interfaces
    mixed_dir = os.path.join(test_dir, 'mixed_test_arch')
    yaml_path = os.path.join(mixed_dir, 'mixedProject.yaml')
    
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Mixed project YAML not found at {yaml_path}")
    
    # Build database
    arch2code_path = os.path.join(base_dir, 'arch2code.py')
    cmd = [sys.executable, arch2code_path, '--yaml', yaml_path, '--db', db_path]
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=mixed_dir
    )
    
    if result.returncode != 0:
        os.unlink(db_path)
        raise RuntimeError(
            f"Failed to build test database:\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )
    
    return db_path


def check_sql_data(db_path):
    """Check the raw SQL data to verify duplicate interface entries."""
    print("\n" + "=" * 80)
    print("CHECKING SQL DATA")
    print("=" * 80)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Query interfaces table
    cursor.execute("SELECT interface, interfaceKey, _context, interfaceType, desc FROM interfaces WHERE interface = 'dupIf' ORDER BY _context")
    rows = cursor.fetchall()
    
    print(f"\nFound {len(rows)} interface entries with name 'dupIf':")
    print("-" * 80)
    
    for i, row in enumerate(rows, 1):
        print(f"\nEntry {i}:")
        print(f"  interface:     {row['interface']}")
        print(f"  interfaceKey:  {row['interfaceKey']}")
        print(f"  _context:      {row['_context']}")
        print(f"  interfaceType: {row['interfaceType']}")
        print(f"  desc:          {row['desc']}")
    
    # Query interfacesstructures table to see structures
    print("\n" + "-" * 80)
    cursor.execute("""
        SELECT interface, interfaceKey, structure, structureType, _context 
        FROM interfacesstructures 
        WHERE interface = 'dupIf' 
        ORDER BY _context
    """)
    struct_rows = cursor.fetchall()
    
    print(f"\nFound {len(struct_rows)} structure entries for 'dupIf':")
    print("-" * 80)
    
    for i, row in enumerate(struct_rows, 1):
        print(f"\nStructure Entry {i}:")
        print(f"  interface:     {row['interface']}")
        print(f"  interfaceKey:  {row['interfaceKey']}")
        print(f"  structure:     {row['structure']}")
        print(f"  structureType: {row['structureType']}")
        print(f"  _context:      {row['_context']}")
    
    conn.close()
    
    # Verify we have exactly 2 entries
    if len(rows) != 2:
        print(f"\n❌ ERROR: Expected 2 interface entries, found {len(rows)}")
        return False
    
    # Verify they have different contexts
    contexts = [row['_context'] for row in rows]
    if len(set(contexts)) != 2:
        print(f"\n❌ ERROR: Expected 2 different contexts, got: {contexts}")
        return False
    
    print("\n✓ SQL data correctly stores 2 separate interface definitions")
    return True


def check_in_memory_data(proj):
    """Check the in-memory data structure after loading."""
    print("\n" + "=" * 80)
    print("CHECKING IN-MEMORY DATA (proj.data)")
    print("=" * 80)
    
    if 'interfaces' not in proj.data:
        print("❌ ERROR: No 'interfaces' table in proj.data")
        return False
    
    interfaces = proj.data['interfaces']
    
    # Find all dupIf entries
    dup_entries = {k: v for k, v in interfaces.items() if 'dupIf' in k}
    
    print(f"\nFound {len(dup_entries)} dupIf entries in proj.data['interfaces']:")
    print("-" * 80)
    
    for key, interface_data in dup_entries.items():
        print(f"\nKey: {key}")
        print(f"  interface:     {interface_data.get('interface')}")
        print(f"  interfaceKey:  {interface_data.get('interfaceKey')}")
        print(f"  _context:      {interface_data.get('_context')}")
        print(f"  interfaceType: {interface_data.get('interfaceType')}")
        print(f"  desc:          {interface_data.get('desc')}")
        
        # Check structures
        if 'structures' in interface_data:
            structures = interface_data['structures']
            print(f"  structures:    {len(structures)} defined")
            if isinstance(structures, dict):
                for struct_key, struct_data in structures.items():
                    print(f"    - {struct_key}: {struct_data.get('structure')} ({struct_data.get('structureType')})")
            elif isinstance(structures, list):
                for i, struct_data in enumerate(structures):
                    print(f"    [{i}] structure: {struct_data.get('structure')}, structureType: {struct_data.get('structureType')}, _context: {struct_data.get('_context')}")
    
    # Verify separation
    if len(dup_entries) != 2:
        print(f"\n❌ ERROR: Expected 2 separate dupIf entries, found {len(dup_entries)}")
        return False
    
    # Verify keys are different
    keys = list(dup_entries.keys())
    if keys[0] == keys[1]:
        print(f"\n❌ ERROR: Duplicate entries have the same key: {keys[0]}")
        return False
    
    # Verify structure counts are correct (each should have exactly 1 structure)
    print("\n" + "-" * 80)
    print("VERIFYING STRUCTURE COUNTS:")
    print("-" * 80)
    
    all_correct = True
    for key, interface_data in dup_entries.items():
        structures = interface_data.get('structures', [])
        if structures is None:
            structures = []
        
        expected_count = 1  # Each dupIf should have exactly 1 structure
        actual_count = len(structures) if structures else 0
        
        print(f"\nKey: {key}")
        print(f"  Expected structures: {expected_count}")
        print(f"  Actual structures:   {actual_count}")
        
        if actual_count != expected_count:
            print(f"  ❌ ERROR: Structure count mismatch!")
            all_correct = False
            
            # Show details of the structures to help debug
            if isinstance(structures, list):
                print(f"  Structure details:")
                for i, struct_data in enumerate(structures):
                    print(f"    [{i}] {struct_data}")
        else:
            print(f"  ✓ Correct structure count")
    
    if not all_correct:
        print("\n❌ ERROR: Structure counts are incorrect - data not properly separated!")
        return False
    
    print("\n✓ In-memory data correctly separates 2 interface definitions")
    print("✓ Each interface has correct number of structures")
    return True


def check_connection_usage(proj):
    """Check that the duplicate interface is used in a connection correctly."""
    print("\n" + "=" * 80)
    print("CHECKING CONNECTION USAGE OF DUPLICATE INTERFACE")
    print("=" * 80)
    
    if 'connections' not in proj.data:
        print("❌ ERROR: No connections table in proj.data")
        return False
    
    # Find the dupIf connection
    dupif_connections = []
    for conn_key, conn_data in proj.data['connections'].items():
        if conn_data.get('interface') == 'dupIf':
            dupif_connections.append((conn_key, conn_data))
    
    print(f"\nFound {len(dupif_connections)} connection(s) using 'dupIf' interface:")
    print("-" * 80)
    
    if len(dupif_connections) == 0:
        print("❌ ERROR: No connections found using dupIf interface")
        return False
    
    for conn_key, conn_data in dupif_connections:
        print(f"\nConnection Key: {conn_key}")
        print(f"  interface:     {conn_data.get('interface')}")
        print(f"  interfaceKey:  {conn_data.get('interfaceKey')}")
        print(f"  src:           {conn_data.get('src')}")
        print(f"  dst:           {conn_data.get('dst')}")
        print(f"  _context:      {conn_data.get('_context')}")
    
    # Verify the connection uses the correct context
    expected_src = 'uBlockA'
    expected_dst = 'uBlockB'
    
    found_correct = False
    for conn_key, conn_data in dupif_connections:
        if conn_data.get('src') == expected_src and conn_data.get('dst') == expected_dst:
            found_correct = True
            print(f"\n✓ Found expected connection: {expected_src} → {expected_dst}")
            break
    
    if not found_correct:
        print(f"\n❌ ERROR: Expected connection from {expected_src} to {expected_dst} not found")
        return False
    
    print("\n✓ Connection correctly uses the duplicate interface")
    return True


def check_getBlockData_output(proj):
    """Check that getBlockData correctly handles the interfaces."""
    print("\n" + "=" * 80)
    print("CHECKING getBlockData OUTPUT")
    print("=" * 80)
    
    # Get blockC data (which is defined in mixedBlockC.yaml)
    try:
        # Find the qualified block name for blockC
        blockC_qual = None
        for qual_name, block_info in proj.data['blocks'].items():
            if block_info['block'] == 'blockC':
                blockC_qual = qual_name
                break
        
        if not blockC_qual:
            print("❌ ERROR: Could not find blockC in blocks")
            return False
        
        print(f"\nFound blockC with qualified name: {blockC_qual}")
        
        # Call getBlockData for blockC
        block_data = proj.getBlockData(blockC_qual)
        
        print("\ngetBlockData returned successfully")
        print(f"  qualBlock: {block_data.get('qualBlock')}")
        print(f"  blockInfo: {block_data.get('blockInfo', {}).get('block')}")
        
        # Check interfaces available in block context
        if 'temp' in block_data:
            print(f"\n  temp data keys: {list(block_data['temp'].keys())}")
        
        # Check includeContext
        if 'includeContext' in block_data:
            print(f"\n  includeContext: {list(block_data['includeContext'].keys())}")
        
        print("\n✓ getBlockData executed successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: getBlockData failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("TESTING DUPLICATE INTERFACE DEFINITION HANDLING")
    print("=" * 80)
    print("\nThis test verifies that duplicate interface definitions in")
    print("mixed.yaml and mixedBlockC.yaml are correctly separated during")
    print("parsing and loading.")
    
    # Build database
    print("\n[Setup] Building test database...")
    db_path = build_test_database()
    print("  ✓ Test database created")
    
    all_passed = True
    
    try:
        # Test 1: Check SQL data
        if not check_sql_data(db_path):
            all_passed = False
        
        # Test 2: Check in-memory data
        print("\n[Loading] Opening project database...")
        proj = projectOpen(db_path)
        print("  ✓ Project loaded")
        
        if not check_in_memory_data(proj):
            all_passed = False
        
        # Test 3: Check connection usage
        if not check_connection_usage(proj):
            all_passed = False
        
        # Test 4: Check getBlockData
        if not check_getBlockData_output(proj):
            all_passed = False
        
        # Summary
        print("\n" + "=" * 80)
        if all_passed:
            print("✅ ALL TESTS PASSED!")
            print("\nSummary:")
            print("  • SQL tables correctly store separate interface definitions")
            print("  • In-memory data structure correctly loads separate definitions")
            print("  • Duplicate interface can be used in connections")
            print("  • getBlockData correctly processes block context")
        else:
            print("❌ SOME TESTS FAILED")
        print("=" * 80)
        
    finally:
        # Cleanup
        print("\n[Teardown] Cleaning up test database...")
        if os.path.exists(db_path):
            os.unlink(db_path)
            print("  ✓ Removed temporary database")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())

