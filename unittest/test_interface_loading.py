#!/usr/bin/env python3
"""Test that interface_defs nested tables load correctly with cumulative parent chains."""

import sys
import os
import subprocess
import tempfile

# Add builder to path
test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen
import pysrc.arch2codeGlobals as g


def build_test_database():
    """Build a test database from mixed test project."""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='.db', prefix='test_interface_')
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


print("=" * 80)
print("TESTING INTERFACE_DEFS LOADING")
print("=" * 80)

# Build test database
print("\n[Setup] Building test database...")
db_path = build_test_database()
print("  ✓ Test database created")

try:
    # Open the project
    proj = projectOpen(db_path)
    
    print("\n" + "=" * 80)
    print("INTERFACE_DEFS DATA")
    print("=" * 80)
    
    # Check if we have interface_defs
    if 'interface_defs' not in proj.data:
        print("ERROR: No interface_defs found in database!")
        sys.exit(1)
    
    print(f"\nFound {len(proj.data['interface_defs'])} interface_defs entries")
    
    # Check apb interface
    apb_key = 'apb/_a2csystem'
    if apb_key in proj.data['interface_defs']:
        apb = proj.data['interface_defs'][apb_key]
        print(f"\nAPB Interface (key: {apb_key}):")
        print(f"  interface_type: {apb.get('interface_type')}")
        print(f"  Has modports: {' modports' in apb}")
        
        if 'modports' in apb:
            print(f"  Modports: {list(apb['modports'].keys())}")
            
            # Check src modport
            if 'src' in apb['modports']:
                src = apb['modports']['src']
                print(f"\n  SRC Modport:")
                print(f"    modport: {src.get('modport')}")
                print(f"    Has modportGroups: {'modportGroups' in src}")
                
                if 'modportGroups' in src:
                    print(f"    modportGroups: {list(src['modportGroups'].keys())}")
                    
                    # Check inputs group
                    if 'inputs' in src['modportGroups']:
                        inputs_group = src['modportGroups']['inputs']
                        print(f"\n    INPUTS ModportGroup:")
                        print(f"      modportGroup: {inputs_group.get('modportGroup')}")
                        print(f"      Has groups: {'groups' in inputs_group}")
                        
                        if 'groups' in inputs_group:
                            print(f"      Signals in inputs: {list(inputs_group['groups'].keys())}")
                            
                            # Show first signal details
                            if inputs_group['groups']:
                                first_signal = list(inputs_group['groups'].values())[0]
                                print(f"\n      First signal details:")
                                for k, v in first_signal.items():
                                    print(f"        {k}: {v}")
    else:
        print(f"ERROR: APB interface not found with key {apb_key}")
        print(f"Available keys: {list(proj.data['interface_defs'].keys())[:5]}")
    
    # Check axi_read interface
    axi_key = 'axi_read/_a2csystem'
    if axi_key in proj.data['interface_defs']:
        axi = proj.data['interface_defs'][axi_key]
        print(f"\n\nAXI_READ Interface (key: {axi_key}):")
        print(f"  interface_type: {axi.get('interface_type')}")
        
        if 'modports' in axi and 'src' in axi['modports']:
            src = axi['modports']['src']
            if 'modportGroups' in src:
                print(f"  SRC modportGroups: {list(src['modportGroups'].keys())}")
    
    print("\n" + "=" * 80)
    print("CHECKING FOR COLLISIONS")
    print("=" * 80)
    
    # Verify that apb and axi_read have DIFFERENT modportGroups (no collision)
    if apb_key in proj.data['interface_defs'] and axi_key in proj.data['interface_defs']:
        apb_modports = proj.data['interface_defs'][apb_key].get('modports', {})
        axi_modports = proj.data['interface_defs'][axi_key].get('modports', {})
        
        if 'src' in apb_modports and 'src' in axi_modports:
            apb_groups = apb_modports['src'].get('modportGroups', {})
            axi_groups = axi_modports['src'].get('modportGroups', {})
            
            print(f"\nAPB src modportGroups count: {len(apb_groups)}")
            print(f"AXI_READ src modportGroups count: {len(axi_groups)}")
            
            # They should be different!
            if apb_groups and axi_groups:
                apb_first = list(apb_groups.values())[0] if apb_groups else None
                axi_first = list(axi_groups.values())[0] if axi_groups else None
                
                if apb_first and axi_first:
                    # Check interface_type to ensure they're distinct
                    apb_intf = apb_first.get('interface_type')
                    axi_intf = axi_first.get('interface_type')
                    
                    print(f"\nAPB modportGroup interface_type: {apb_intf}")
                    print(f"AXI modportGroup interface_type: {axi_intf}")
                    
                    if apb_intf == axi_intf:
                        print("\n❌ ERROR: APB and AXI modportGroups have same interface_type - COLLISION!")
                    else:
                        print("\n✓ SUCCESS: APB and AXI modportGroups are distinct - no collision!")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

finally:
    # Cleanup
    print("\n[Teardown] Cleaning up test database...")
    if os.path.exists(db_path):
        os.unlink(db_path)
        print("  ✓ Removed temporary database")
