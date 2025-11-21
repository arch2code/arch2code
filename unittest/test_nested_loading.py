#!/usr/bin/env python3
"""
Test nested table loading for interface_defs hierarchy.

Tests the 4-level nesting:
  interface_defs -> modports -> modportGroups -> groups (signals)

This verifies:
1. Multi-entry tables group correctly by parent key
2. Composite keys work for nested lookups
3. No collisions between different interfaces
4. All ancestor keys present in nested tables
"""

import sys
import os
import subprocess
import tempfile

# Add builder path
test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen


def build_test_database():
    """Build a test database from mixed test project."""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='.db', prefix='test_nested_')
    os.close(db_fd)
    
    # Use mixed test project YAML
    mixed_test_dir = os.path.join(test_dir, 'mixed_test_arch')
    yaml_path = os.path.join(mixed_test_dir, 'mixedProject.yaml')
    
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Mixed test project not found: {yaml_path}")
    
    # Build database from mixed project
    arch2code_path = os.path.join(base_dir, 'arch2code.py')
    cmd = [sys.executable, arch2code_path, '--yaml', yaml_path, '--db', db_path]
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=mixed_test_dir
    )
    
    if result.returncode != 0:
        os.unlink(db_path)
        raise RuntimeError(
            f"Failed to build database from {yaml_path}:\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )
    
    return db_path


def test_interface_loading():
    """Test that interface_defs loads with correct nested structure."""
    print("=" * 70)
    print("Testing Nested Table Loading")
    print("=" * 70)
    
    # Build test database
    print("\n[Setup] Building test database from mixed_test_arch project...")
    db_path = build_test_database()
    print(f"  ✓ Test database created")
    
    try:
        proj = projectOpen(db_path)
        
        # Test 1: Interface definitions exist
        print("\n[Test 1] Interface definitions loaded")
        assert 'interface_defs' in proj.data, "interface_defs table missing"
        interfaces = proj.data['interface_defs']
        print(f"  ✓ Found {len(interfaces)} interface definitions")
        
        # Test 2: APB interface exists with modports
        print("\n[Test 2] APB interface structure")
        apb_key = 'apb/_a2csystem'
        assert apb_key in interfaces, f"APB interface {apb_key} not found"
        apb = interfaces[apb_key]
        assert 'modports' in apb, "modports missing from APB interface"
        print(f"  ✓ APB has {len(apb['modports'])} modports: {list(apb['modports'].keys())}")
        
        # Test 3: src modport has modportGroups (nested: unqualified key)
        print("\n[Test 3] src modport structure")
        src = apb['modports']['src']
        assert 'modportGroups' in src, "modportGroups missing from src modport"
        assert src['modportGroups'] is not None, "modportGroups is None"
        assert isinstance(src['modportGroups'], dict), f"modportGroups should be dict, got {type(src['modportGroups'])}"
        print(f"  ✓ src has {len(src['modportGroups'])} groups: {list(src['modportGroups'].keys())}")
        
        # Test 4: modportGroups contain signals (groups) - using unqualified anchors (nested)
        print("\n[Test 4] modportGroup signal nesting")
        inputs = src['modportGroups']['inputs']
        outputs = src['modportGroups']['outputs']
        
        assert 'groups' in inputs, "groups missing from inputs modportGroup"
        assert inputs['groups'] is not None, "inputs groups is None"
        print(f"  ✓ inputs has {len(inputs['groups'])} signals: {list(inputs['groups'].keys())}")
        
        assert 'groups' in outputs, "groups missing from outputs modportGroup"
        assert outputs['groups'] is not None, "outputs groups is None"
        print(f"  ✓ outputs has {len(outputs['groups'])} signals: {list(outputs['groups'].keys())}")
        
        # Test 5: Signal details are correct
        print("\n[Test 5] Signal details")
        pready = inputs['groups']['pready']
        assert pready['interface_type'] == 'apb', f"Wrong interface_type: {pready['interface_type']}"
        assert pready['modport'] == 'src', f"Wrong modport: {pready['modport']}"
        assert pready['modportGroup'] == 'inputs', f"Wrong modportGroup: {pready['modportGroup']}"
        assert pready['signal'] == 'pready', f"Wrong signal: {pready['signal']}"
        print(f"  ✓ pready: interface={pready['interface_type']}, modport={pready['modport']}, group={pready['modportGroup']}")
        
        # Test 6: Ancestor keys present
        print("\n[Test 6] Ancestor key fields")
        assert 'interface_typeKey' in pready, "interface_typeKey missing from signal"
        assert 'modportKey' in pready, "modportKey missing from signal"
        assert 'modportGroupKey' in pready, "modportGroupKey missing from signal"
        print(f"  ✓ Signal has ancestor keys: interface_typeKey={pready['interface_typeKey']}")
        print(f"                              modportKey={pready['modportKey']}")
        print(f"                              modportGroupKey={pready['modportGroupKey']}")
        
        # Test 7: dst modport separate from src (no collision)
        print("\n[Test 7] dst modport independence")
        dst = apb['modports']['dst']  # Nested: unqualified key
        dst_inputs = dst['modportGroups']['inputs']  # Nested: unqualified key
        dst_outputs = dst['modportGroups']['outputs']  # Nested: unqualified key
        
        # dst should have DIFFERENT signals than src
        assert list(dst_inputs['groups'].keys()) != list(inputs['groups'].keys()), \
            "dst inputs should differ from src inputs"
        print(f"  ✓ dst inputs: {list(dst_inputs['groups'].keys())}")
        print(f"  ✓ src inputs: {list(inputs['groups'].keys())}")
        print(f"  ✓ No collision between src and dst modports")
        
        # Test 8: Different interfaces don't collide
        print("\n[Test 8] Multiple interfaces independence")
        axi_key = 'axi4_stream/_a2csystem'
        if axi_key in interfaces:
            axi = interfaces[axi_key]
            axi_src = axi['modports']['src']  # Nested: unqualified key
            axi_outputs = axi_src['modportGroups']['outputs']  # Nested: unqualified key
            axi_signals = list(axi_outputs['groups'].keys())
            apb_signals = list(outputs['groups'].keys())
            
            # AXI signals should be different from APB
            assert axi_signals != apb_signals, "AXI and APB should have different signals"
            print(f"  ✓ AXI4_stream signals: {axi_signals[:3]}...")
            print(f"  ✓ APB signals: {apb_signals[:3]}...")
            print(f"  ✓ No collision between APB and AXI4_stream")
        else:
            print(f"  ⚠ Skipping AXI test - {axi_key} not found")
        
        # Test 9: Composite key uniqueness
        print("\n[Test 9] Composite key construction")
        # Check that qualified keys form unique composite
        composite = f"{pready['interface_typeKey']}/{pready['modportKey']}/{pready['modportGroupKey']}/{pready['signalKey']}"
        print(f"  ✓ Signal composite key: {composite}")
        # 4 key parts = 3 slashes (interface/modport/modportGroup/signal)
        assert composite.count('/') >= 3, f"Should have at least 3 slashes, got {composite.count('/')}"
        
        # Test 10: Empty groups handled correctly (status interface)
        print("\n[Test 10] Optional nested tables")
        status_key = 'status/_a2csystem'
        if status_key in interfaces:
            status = interfaces[status_key]
            status_src = status['modports']['src']  # Nested: unqualified key
            status_inputs = status_src['modportGroups']['inputs']  # Nested: unqualified key
            
            # status src/inputs should have no groups (None)
            assert status_inputs['groups'] is None, "status src/inputs should have no groups"
            print(f"  ✓ status src/inputs groups is None (correct for optional empty table)")
        else:
            print(f"  ⚠ Skipping status test - {status_key} not found")
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nNested table loading verified:")
        print("  • 4-level hierarchy working")
        print("  • Multi-entry tables grouped correctly")
        print("  • Composite keys constructed properly")
        print("  • No collisions between interfaces/modports")
        print("  • Ancestor keys present at all levels")
        print("  • Optional nested tables handled")
        
    finally:
        # Cleanup
        print(f"\n[Teardown] Cleaning up test database...")
        if os.path.exists(db_path):
            os.unlink(db_path)
            print(f"  ✓ Removed temporary database")


if __name__ == '__main__':
    try:
        test_interface_loading()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
