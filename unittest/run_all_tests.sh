#!/bin/bash
# Run all unit tests

FAILED=0

echo "========================================================================"
echo "Running All Unit Tests"
echo "========================================================================"

# Test 1: Nested loading
echo ""
echo "Test Suite 1: Nested Table Loading"
echo "------------------------------------------------------------------------"
python3 test_nested_loading.py || FAILED=1

# Test 2: APB validation  
echo ""
echo "Test Suite 2: APB Interface Validation"
echo "------------------------------------------------------------------------"
python3 test_apb_validation.py || FAILED=1

# Test 3: Interface loading
echo ""
echo "Test Suite 3: Interface Loading"
echo "------------------------------------------------------------------------"
python3 test_interface_loading.py || FAILED=1

# Test 4: Data by parent logic
echo ""
echo "Test Suite 4: Data by Parent Logic"
echo "------------------------------------------------------------------------"
python3 test_data_by_parent_logic.py || FAILED=1

# Test 5: Mixed project
echo ""
echo "Test Suite 5: Mixed Project Build"
echo "------------------------------------------------------------------------"
python3 test_mixed_project.py || FAILED=1

# Test 6: Error handling - missing fields
echo ""
echo "Test Suite 6: Error Handling (Missing Fields)"
echo "------------------------------------------------------------------------"
if ! python3 test_error_missing_fields.py; then
    FAILED=1
    echo "⚠️  Note: Some error tests failed"
    echo "    This indicates bugs in error handling that need fixing."
fi

# Test 7: Error handling - auto functions
echo ""
echo "Test Suite 7: Error Handling (Auto Functions)"
echo "------------------------------------------------------------------------"
if ! python3 test_error_auto_functions.py; then
    FAILED=1
    echo "⚠️  Note: Some error tests failed"
    echo "    This indicates bugs in auto function error handling."
fi

# Test 8: Duplicate interface handling
echo ""
echo "Test Suite 8: Duplicate Interface Handling"
echo "------------------------------------------------------------------------"
python3 test_duplicate_interface.py || FAILED=1

# Test 9: ContextKey schema validation
echo ""
echo "Test Suite 9: ContextKey Validation"
echo "------------------------------------------------------------------------"
python3 test_contextkey_validation.py || FAILED=1

# Test 10: Error handling - parameterizable constants (F2/F3)
echo ""
echo "Test Suite 10: Error Handling (Parameterizable Constants)"
echo "------------------------------------------------------------------------"
if ! python3 test_error_parameterizable.py; then
    FAILED=1
    echo "Note: Some parameterizable-constant error tests failed"
fi

# Test 11: Config template generation
echo ""
echo "Test Suite 11: Config Template Generation"
echo "------------------------------------------------------------------------"
python3 test_config_template.py || FAILED=1

# Test 12: Error handling - declared ports
echo ""
echo "Test Suite 12: Error Handling (Declared Ports)"
echo "------------------------------------------------------------------------"
if ! python3 test_error_declared_ports.py; then
    FAILED=1
    echo "Note: Some declared-port error tests failed"
fi

# Test 13: Thunker view derivation
echo ""
echo "Test Suite 13: Thunker View Derivation"
echo "------------------------------------------------------------------------"
python3 test_thunker_view.py || FAILED=1

# Test 14: Declared port resolved interface context
echo ""
echo "Test Suite 14: Declared Port Resolved Interface Context"
echo "------------------------------------------------------------------------"
python3 test_declared_port_resolved_interface_key.py || FAILED=1

# Test 15: ValueResolver qualified override scope
echo ""
echo "Test Suite 15: ValueResolver Qualified Override Scope"
echo "------------------------------------------------------------------------"
python3 test_value_resolver_qualified_override.py || FAILED=1

# Test 16: Error handling - RTL hierarchy implementation
echo ""
echo "Test Suite 16: Error Handling (RTL Hierarchy)"
echo "------------------------------------------------------------------------"
if ! python3 test_error_rtl_hierarchy.py; then
    FAILED=1
    echo "Note: Some RTL hierarchy error tests failed"
fi

# Test 17: Foreign-key lookup primitives
echo ""
echo "Test Suite 17: Foreign-Key Lookup Primitives"
echo "------------------------------------------------------------------------"
python3 test_foreign_key_lookup.py || FAILED=1

# Test 18: Block-param / ipParameters-constant linkage and declaration set
echo ""
echo "Test Suite 18: Parameter/Constant Linkage and Declaration Set"
echo "------------------------------------------------------------------------"
if ! python3 test_param_const_linkage.py; then
    FAILED=1
    echo "Note: Some parameter/constant linkage tests failed"
fi

# Test 19: Block config parameterization
echo ""
echo "Test Suite 19: Block Config Parameterization"
echo "------------------------------------------------------------------------"
python3 test_block_config_parameterization.py || FAILED=1

# Test 19b: HDL wrapper boundary width spelling
echo ""
echo "Test Suite 19b: HDL Wrapper Boundary Width Spelling"
echo "------------------------------------------------------------------------"
python3 test_boundary_signals.py || FAILED=1

# Test 20-: address-control refactor — Stage 7 Batches A and B.
# Per plan-address-control-test-coverage.md "Implementation Phasing":
#   Batch A — single-router positives, the lowest-cost two-level
#             positives, port-name boundary cases, and the Stage 1.5 /
#             Stage 4 diagnostic skeleton.
#   Batch B — three-level and thunker cases, including the block-reuse
#             and mixed-sibling cases that exercise the multi-hop walk.
# See plan-address-control-refactor.md Stage 7.
ADDRCTL_TESTS=(
    "T1.1 single-router one-register view"      "test_addrctl_single_router_one_reg.py"
    "T1.2 single-router multi-register leaf"    "test_addrctl_single_router_multi_reg.py"
    "T1.3 single-router two-leaves"             "test_addrctl_single_router_two_leaves.py"
    "T1.5 single-router mixed leaves"           "test_addrctl_mixed_leaves.py"
    "T2.1 primary plus nested router"           "test_addrctl_two_router_simple.py"
    "T2.2 primary with no direct leaves"        "test_addrctl_primary_no_direct_leaves.py"
    "T2.6 parameterized nested router"          "test_addrctl_parameterized_router.py"
    "T3.1 three-level chain"                    "test_addrctl_three_level_chain.py"
    "T3.2 three-level fanout"                   "test_addrctl_three_level_fanout.py"
    "T3.4 register-bearing block reuse"         "test_addrctl_block_reuse_across_levels.py"
    "T3.5 sibling leaf and nested router"       "test_addrctl_sibling_leaf_and_router.py"
    "T4.1 single-router no-IP simple"           "test_addrctl_no_ip_simple.py"
    "T4.2 two-level no-IP hierarchy"            "test_addrctl_no_ip_two_level.py"
    "T4.3 mixed IP / no-IP under one router"    "test_addrctl_no_ip_mixed.py"
    "T5.1 router with no leaves"                "test_addrctl_router_no_leaves.py"
    "T5.2 leaf with registerPorts only"         "test_addrctl_leaf_register_port_only.py"
    "T5.3 default upstream / decoder ports"     "test_addrctl_default_port_names.py"
    "T5.4 explicit non-default ports"           "test_addrctl_explicit_port_names.py"
    "TT.3 parameterized register interface"     "test_addrctl_parameterized_reg_iface.py"
    "TT.4 parameterized router upstream"        "test_addrctl_parameterized_router_upstream.py"
    "TT.5 parent router variant interface"      "test_addrctl_parent_router_variant_interface.py"
    "E1.1 addressBlock and registerPorts both"  "test_error_addr_and_register_ports.py"
    "E1.2 multi registerPorts rows"             "test_error_multi_register_ports.py"
    "E1.3 registerPort interface not addressBus" "test_error_register_port_not_addressbus.py"
    "E1.4 duplicate addressGroup"               "test_error_duplicate_address_group.py"
    "E1.5 registerPort out-of-scope interface"  "test_error_register_port_out_of_scope.py"
    "E2.1 router has no instance"               "test_error_router_no_instance.py"
    "E2.2 multi-instance router"                "test_error_multi_instance_router.py"
    "E2.3 no primary router candidate"          "test_error_no_primary_router.py"
    "E2.4 multiple primary router candidates"   "test_error_multi_primary_router.py"
    "E2.5 routed leaf in unserved container"    "test_error_leaf_unserved.py"
    "E2.6 leaf with regs but no registerPorts"  "test_error_leaf_no_register_port.py"
    "E3.1 register interfaceType mismatch"      "test_error_register_interface_type_mismatch.py"
    "E3.2 register packed-form mismatch"        "test_error_register_packed_form.py"
)

idx=20
for ((i = 0; i < ${#ADDRCTL_TESTS[@]}; i+=2)); do
    label=${ADDRCTL_TESTS[i]}
    script=${ADDRCTL_TESTS[i+1]}
    echo ""
    echo "Test Suite ${idx}: addressControl refactor — ${label}"
    echo "------------------------------------------------------------------------"
    if ! python3 "${script}"; then
        FAILED=1
        echo "Note: ${label} failed"
    fi
    idx=$((idx+1))
done

echo ""
echo "========================================================================"
if [ $FAILED -eq 0 ]; then
    echo "✅ ALL TEST SUITES PASSED!"
    echo "========================================================================"
    exit 0
else
    echo "❌ SOME TEST SUITES FAILED!"
    echo "========================================================================"
    exit 1
fi
