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

# Test 10b: Own-surface parameterizable structure without own params
echo ""
echo "Test Suite 10b: Block Own-Surface Parameterizable Without Params"
echo "------------------------------------------------------------------------"
if ! python3 test_block_own_surface_param_no_params.py; then
    FAILED=1
    echo "Note: Own-surface parameterizable validator test failed"
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

echo ""
echo "Test Suite 19c: Eval Expression Parser"
echo "------------------------------------------------------------------------"
python3 test_eval_expr_parser.py || FAILED=1

echo ""
echo "Test Suite 19d: Eval Expression Evaluator"
echo "------------------------------------------------------------------------"
python3 test_eval_expr_evaluator.py || FAILED=1

echo ""
echo "Test Suite 19e: Eval Canonical View Exposure"
echo "------------------------------------------------------------------------"
python3 test_eval_canonical_view.py || FAILED=1

echo ""
echo "Test Suite 19f: Eval SV localparam Emission"
echo "------------------------------------------------------------------------"
python3 test_eval_sv_emit.py || FAILED=1

echo ""
echo "Test Suite 19g: Eval C++/SystemC Config Emission"
echo "------------------------------------------------------------------------"
python3 test_eval_cpp_emit.py || FAILED=1

echo ""
echo "Test Suite 19h: Python->SV Eval Converter"
echo "------------------------------------------------------------------------"
python3 test_eval_py_to_sv.py || FAILED=1

echo ""
echo "Test Suite 19m: Parent->child parameter symbol forwarding"
echo "------------------------------------------------------------------------"
python3 test_param_symbol_forwarding.py || FAILED=1

echo ""
echo "Test Suite 19n: Implied register connection stays in-container scope"
echo "------------------------------------------------------------------------"
python3 test_implied_register_in_container_scope.py || FAILED=1

echo ""
echo "Test Suite 19i: yamlFormat sentinel gate (projectCreate)"
echo "------------------------------------------------------------------------"
python3 test_gate_yaml_format.py || FAILED=1

echo ""
echo "Test Suite 19j: addressControl -> addressBlock Converter"
echo "------------------------------------------------------------------------"
python3 test_migrate_address_control.py || FAILED=1

echo ""
echo "Test Suite 19k: Unified YAML Migration Orchestrator (migrateYaml.py)"
echo "------------------------------------------------------------------------"
python3 test_migrate_yaml.py || FAILED=1

echo ""
echo "Test Suite 19l: Includes header -> cppm module migration (migrateIncludes.py)"
echo "------------------------------------------------------------------------"
python3 test_migrate_includes.py || FAILED=1

# Address-control decode: register/memory decode topology, port-name
# resolution, parameterized routers/leaves, the diagnostic error cases,
# and the migrated ip_test view assertions. The synthetic-topology tests
# build fixtures in-process; the ip_test view test opens the migrated
# example database.
ADDRCTL_TESTS=(
    "single-router one-register view"           "test_addrctl_single_router_one_reg.py"
    "single-router multi-register leaf"         "test_addrctl_single_router_multi_reg.py"
    "single-router two-leaves"                  "test_addrctl_single_router_two_leaves.py"
    "single-router mixed leaves"                "test_addrctl_mixed_leaves.py"
    "primary plus nested router"                "test_addrctl_two_router_simple.py"
    "primary with no direct leaves"             "test_addrctl_primary_no_direct_leaves.py"
    "parameterized nested router"               "test_addrctl_parameterized_router.py"
    "three-level chain"                         "test_addrctl_three_level_chain.py"
    "three-level fanout"                        "test_addrctl_three_level_fanout.py"
    "register-bearing block reuse"              "test_addrctl_block_reuse_across_levels.py"
    "sibling leaf and nested router"            "test_addrctl_sibling_leaf_and_router.py"
    "single-router no-IP simple"                "test_addrctl_no_ip_simple.py"
    "two-level no-IP hierarchy"                 "test_addrctl_no_ip_two_level.py"
    "mixed IP / no-IP under one router"         "test_addrctl_no_ip_mixed.py"
    "router with no leaves"                     "test_addrctl_router_no_leaves.py"
    "leaf with registerPorts only"              "test_addrctl_leaf_register_port_only.py"
    "default upstream / decoder ports"          "test_addrctl_default_port_names.py"
    "explicit non-default ports"                "test_addrctl_explicit_port_names.py"
    "top-down leaf infers register bus"         "test_addrctl_top_down_leaf_infers.py"
    "parameterized register interface"          "test_addrctl_parameterized_reg_iface.py"
    "parameterized router upstream"             "test_addrctl_parameterized_router_upstream.py"
    "parent router variant interface"           "test_addrctl_parent_router_variant_interface.py"
    "addressBlock and registerPorts both"       "test_error_addr_and_register_ports.py"
    "multi registerPorts rows"                  "test_error_multi_register_ports.py"
    "registerPort interface not addressBus"     "test_error_register_port_not_addressbus.py"
    "duplicate addressGroup"                    "test_error_duplicate_address_group.py"
    "registerPort out-of-scope interface"       "test_error_register_port_out_of_scope.py"
    "router has no instance"                    "test_error_router_no_instance.py"
    "multi-instance router"                     "test_error_multi_instance_router.py"
    "no primary router candidate"               "test_error_no_primary_router.py"
    "multiple primary router candidates"        "test_error_multi_primary_router.py"
    "routed leaf in unserved container"         "test_error_leaf_unserved.py"
    "no serving router for reg leaf"            "test_error_leaf_no_serving_router.py"
    "register interfaceType mismatch"           "test_error_register_interface_type_mismatch.py"
    "register packed-form mismatch"             "test_error_register_packed_form.py"
    "registerPorts independent of ports"        "test_register_ports_independent_of_ports.py"
    "migrated ip_test view"                     "test_addrctl_ip_test_view.py"
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
echo "Test Suite ${idx}: project layout mode — selector validation"
echo "------------------------------------------------------------------------"
python3 test_layout_selector.py || FAILED=1
idx=$((idx+1))

echo ""
echo "Test Suite ${idx}: project layout mode — hierarchical structural golden"
echo "------------------------------------------------------------------------"
python3 test_layout_hierarchical.py || FAILED=1
idx=$((idx+1))

echo ""
echo "Test Suite ${idx}: project layout mode — nested sign-off structural golden"
echo "------------------------------------------------------------------------"
python3 test_layout_nested.py || FAILED=1
idx=$((idx+1))

echo ""
echo "Test Suite ${idx}: project layout mode — build manifest reproduces glob set"
echo "------------------------------------------------------------------------"
python3 test_build_manifest.py || FAILED=1
idx=$((idx+1))

echo ""
echo "Test Suite ${idx}: project layout mode — hierarchical migration trigger"
echo "------------------------------------------------------------------------"
python3 test_migrate_layout.py || FAILED=1
idx=$((idx+1))

echo ""
echo "Test Suite ${idx}: nested project ownership — non-uniform context owners"
echo "------------------------------------------------------------------------"
python3 test_nested_ownership.py || FAILED=1

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
