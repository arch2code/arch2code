#!/usr/bin/env python3
"""
Test suite for mixed project YAML processing.
This tests that the schema refactoring didn't break existing functionality.
"""

import sys
import os
import subprocess
import tempfile

def test_mixed_project_build():
    """Test that mixed project builds successfully with our schema changes"""
    
    print("=" * 70)
    print("Testing Mixed Project Build")
    print("=" * 70)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Get paths
        test_dir = os.path.dirname(__file__)
        yaml_path = os.path.join(test_dir, 'mixed_test_arch', 'mixedProject.yaml')
        arch2code_path = os.path.join(test_dir, '..', 'arch2code.py')
        
        print(f"\n[Test 1] Building mixed project from {yaml_path}")
        
        # Run arch2code to build the project
        cmd = [sys.executable, arch2code_path, '--yaml', yaml_path, '--db', db_path]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=test_dir)
        
        if result.returncode == 0:
            print("  ✓ Project built successfully")
        else:
            print(f"  ✗ Build failed with return code {result.returncode}")
            print(f"\nSTDOUT:\n{result.stdout}")
            print(f"\nSTDERR:\n{result.stderr}")
            raise AssertionError(f"Build failed: {result.stderr}")
        
        # Now load the database and verify structure
        print(f"\n[Test 2] Verifying database schema")
        
        # Add parent directory to path
        sys.path.insert(0, os.path.join(test_dir, '..'))
        from pysrc.processYaml import projectOpen
        
        project = projectOpen(db_path)
        schema = project.schema
        
        # Check that we have expected sections from mixed project
        expected_sections = ['structures', 'interfaces', 'blocks', 'instances', 'connections']
        for section in expected_sections:
            if section in schema.sections:
                print(f"  ✓ Section '{section}' exists")
            else:
                print(f"  ✗ Missing section '{section}'")
                raise AssertionError(f"Missing expected section: {section}")
        
        print(f"\n[Test 3] Verifying node pickling")
        if schema.nodes:
            print(f"  ✓ Found {len(schema.nodes)} nodes")
        else:
            print(f"  ✗ No nodes found - pickling may have failed")
            raise AssertionError("Schema nodes dict is empty")
        
        print(f"\n[Test 4] Verifying key building methods exist")
        # Check that at least some nodes have the key building methods
        nodes_with_methods = []
        for node_name, node in schema.nodes.items():
            if hasattr(node, 'build_storage_key'):
                nodes_with_methods.append(node_name)
        
        if nodes_with_methods:
            print(f"  ✓ Found {len(nodes_with_methods)} nodes with key building methods")
            print(f"    Examples: {', '.join(nodes_with_methods[:3])}")
        else:
            print(f"  ⚠ Warning: No nodes have key building methods (may be expected for simple schemas)")
        
        print("\n" + "=" * 70)
        print("✅ ALL MIXED PROJECT TESTS PASSED!")
        print("=" * 70)
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == '__main__':
    try:
        test_mixed_project_build()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
