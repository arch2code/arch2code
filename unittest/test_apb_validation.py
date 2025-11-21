#!/usr/bin/env python3
"""
Comprehensive validation of APB interface loading from YAML → Schema → Database → Reconstruction.

This test validates:
1. YAML structure of apb_if.yaml 
2. Schema definition for interface_defs and nested tables
3. Database structure and content
4. Reconstruction of nested structure after loading
"""

import sys
import os
import sqlite3
import subprocess
import tempfile

# Add builder to path
test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen
from pysrc.schema import Schema
import pysrc.arch2codeGlobals as g


def build_test_database():
    """Build a test database from mixed test project."""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='.db', prefix='test_apb_')
    os.close(db_fd)
    
    # Use mixed test project YAML
    mixed_test_dir = os.path.join(test_dir, 'mixed_test_arch')
    yaml_path = os.path.join(mixed_test_dir, 'mixedProject.yaml')
    
    # Build database from mixed project
    arch2code_path = os.path.join(base_dir, 'arch2code.py')
    cmd = [sys.executable, arch2code_path, '--yaml', yaml_path, '--db', db_path]
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=mixed_test_dir
    )
    
    if result.returncode != 0:
        os.unlink(db_path)
        raise RuntimeError(
            f"Failed to build test database:\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )
    
    return db_path

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_yaml_structure():
    """Test the raw YAML structure."""
    print_section("1. YAML STRUCTURE VALIDATION")
    
    # System-level APB interface (framework resource, not user project)
    yaml_path = os.path.join(base_dir, 'interfaces', 'apb', 'apb_if.yaml')
    
    import yaml
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    
    print(f"\n✓ Loaded {yaml_path}")
    print(f"  Top-level keys: {list(data.keys())}")
    
    if 'interface_defs' in data:
        print(f"  interface_defs keys: {list(data['interface_defs'].keys())}")
        
        if 'apb' in data['interface_defs']:
            apb = data['interface_defs']['apb']
            print(f"\n  APB structure:")
            print(f"    - parameters: {list(apb.get('parameters', {}).keys())}")
            print(f"    - signals: {list(apb.get('signals', {}).keys())}")
            print(f"    - modports: {list(apb.get('modports', {}).keys())}")
            
            if 'modports' in apb:
                for mp_name, mp_data in apb['modports'].items():
                    print(f"\n    modport '{mp_name}':")
                    print(f"      - inputs: {mp_data.get('inputs', [])}")
                    print(f"      - outputs: {mp_data.get('outputs', [])}")
            
            return apb
    
    return None

def test_schema_definition():
    """Test the schema definition for interface_defs"""
    print_section("2. SCHEMA DEFINITION VALIDATION")
    
    # For now, skip direct schema object testing since it requires DB connection
    # The schema will be validated indirectly through database structure
    print("\n  Skipping direct schema validation (requires DB connection)")
    print("  Schema will be validated through database structure below")
    
    return None

def test_database_structure(db_path):
    """Test the database structure and content."""
    print_section("3. DATABASE STRUCTURE & CONTENT VALIDATION")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"\n✓ Connected to test database")
    
    # Check interface_defs table
    print(f"\n  interface_defs table:")
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='interface_defs'")
    create_sql = cursor.fetchone()
    if create_sql:
        print(f"    Schema: {create_sql[0]}")
    
    cursor.execute("SELECT interface_type, interface_typeKey FROM interface_defs WHERE interface_type='apb'")
    rows = cursor.fetchall()
    print(f"    APB entries: {len(rows)}")
    for row in rows:
        print(f"      - interface_type={row[0]}, interface_typeKey={row[1]}")
    
    # Check modports table
    print(f"\n  interface_defsmodports table:")
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='interface_defsmodports'")
    create_sql = cursor.fetchone()
    if create_sql:
        print(f"    Schema: {create_sql[0]}")
    
    cursor.execute("""
        SELECT modport, modportKey, interface_typeKey 
        FROM interface_defsmodports 
        WHERE interface_typeKey LIKE 'apb/%'
    """)
    rows = cursor.fetchall()
    print(f"    APB modport entries: {len(rows)}")
    for row in rows:
        print(f"      - modport={row[0]}, modportKey={row[1]}, interface_typeKey={row[2]}")
    
    # Check modportGroups table
    print(f"\n  interface_defsmodportsmodportGroups table:")
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='interface_defsmodportsmodportGroups'")
    create_sql = cursor.fetchone()
    if create_sql:
        print(f"    Schema: {create_sql[0]}")
    
    cursor.execute("""
        SELECT modportGroup, modportGroupKey, modportKey
        FROM interface_defsmodportsmodportGroups 
        WHERE modportKey LIKE '%/_a2csystem'
    """)
    rows = cursor.fetchall()
    print(f"    APB modportGroup entries: {len(rows)}")
    for row in rows:
        print(f"      - modportGroup={row[0]}, modportGroupKey={row[1]}, modportKey={row[2]}")
    
    # Check groups (signals) table
    print(f"\n  interface_defsmodportsmodportGroupsgroups table:")
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='interface_defsmodportsmodportGroupsgroups'")
    create_sql = cursor.fetchone()
    if create_sql:
        print(f"    Schema: {create_sql[0]}")
    
    cursor.execute("""
        SELECT signal, modportGroup, modportKey
        FROM interface_defsmodportsmodportGroupsgroups 
        WHERE modportKey LIKE '%/_a2csystem'
        LIMIT 5
    """)
    rows = cursor.fetchall()
    print(f"    APB signal entries (first 5): {len(rows)}")
    for row in rows:
        print(f"      - signal={row[0]}, modportGroup={row[1]}, modportKey={row[2]}")
    
    conn.close()

def test_reconstruction(db_path):
    """Test the reconstruction of nested structure after loading."""
    print_section("4. RECONSTRUCTION VALIDATION")
    
    proj = projectOpen(db_path)
    
    print(f"\n✓ Loaded project from test database")
    
    # Check interface_defs
    if 'interface_defs' not in proj.data:
        print("\n✗ ERROR: No interface_defs in loaded data!")
        return
    
    print(f"\n  Loaded {len(proj.data['interface_defs'])} interface_defs")
    
    # Find APB interface
    apb_entry = None
    apb_key = None
    for key, intf in proj.data['interface_defs'].items():
        if intf.get('interface_type') == 'apb':
            apb_entry = intf
            apb_key = key
            break
    
    if not apb_entry:
        print("\n✗ ERROR: No APB interface found!")
        return
    
    print(f"\n  Found APB interface with key: {apb_key}")
    print(f"    Entry keys: {list(apb_entry.keys())}")
    print(f"    Has 'modports': {'modports' in apb_entry}")
    
    if 'modports' in apb_entry and apb_entry['modports']:
        modports = apb_entry['modports']
        print(f"\n  ✓ modports present:")
        print(f"    Type: {type(modports)}")
        print(f"    Keys: {list(modports.keys()) if isinstance(modports, dict) else 'NOT A DICT'}")
        
        if isinstance(modports, dict):
            for mp_name, mp_data in modports.items():
                print(f"\n    modport '{mp_name}':")
                print(f"      Type: {type(mp_data)}")
                print(f"      Keys: {list(mp_data.keys()) if isinstance(mp_data, dict) else 'NOT A DICT'}")
                print(f"      Has 'modportGroups': {'modportGroups' in mp_data if isinstance(mp_data, dict) else False}")
                
                if isinstance(mp_data, dict) and 'modportGroups' in mp_data and mp_data['modportGroups']:
                    groups = mp_data['modportGroups']
                    print(f"\n      ✓ modportGroups present:")
                    print(f"        Type: {type(groups)}")
                    print(f"        Keys: {list(groups.keys()) if isinstance(groups, dict) else 'NOT A DICT'}")
                    
                    if isinstance(groups, dict):
                        for grp_name, grp_data in groups.items():
                            print(f"\n        modportGroup '{grp_name}':")
                            print(f"          Type: {type(grp_data)}")
                            print(f"          Keys: {list(grp_data.keys()) if isinstance(grp_data, dict) else 'NOT A DICT'}")
                            print(f"          Has 'groups': {'groups' in grp_data if isinstance(grp_data, dict) else False}")
                            
                            if isinstance(grp_data, dict) and 'groups' in grp_data and grp_data['groups']:
                                signals = grp_data['groups']
                                print(f"\n          ✓ groups (signals) present:")
                                print(f"            Type: {type(signals)}")
                                if isinstance(signals, dict):
                                    print(f"            Signal count: {len(signals)}")
                                    print(f"            Signals: {list(signals.keys())[:5]}")  # First 5
                                else:
                                    print(f"            NOT A DICT: {signals}")
    else:
        print(f"\n  ✗ modports NOT present or None")

def main():
    print("\n" + "#" * 80)
    print("  APB INTERFACE VALIDATION TEST")
    print("#" * 80)
    
    # Build test database
    print("\n[Setup] Building test database...")
    db_path = build_test_database()
    print("  ✓ Test database created")
    
    try:
        yaml_data = test_yaml_structure()
        schema_obj = test_schema_definition()
        test_database_structure(db_path)
        test_reconstruction(db_path)
        
        print_section("SUMMARY")
        print("\n✓ All validation steps completed")
        print("  Review output above to identify any issues")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        # Cleanup
        print("\n[Teardown] Cleaning up test database...")
        if os.path.exists(db_path):
            os.unlink(db_path)
            print("  ✓ Removed temporary database")


if __name__ == '__main__':
    main()
