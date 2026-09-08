# Per-block trampoline registrar template. The child-named TU aggregates the
# project's SystemC registrations. Each lambda keeps its parent-child factory
# domain, so two parents using one child remain distinct.
#
# Non-templated blocks reach the factory through the self-registering static
# emitted in their own module unit and do not need a trampoline —
# `cond: {hasOwnParams: true}` filters them out at file-generation time, so
# every block reaching this template is a `template<typename Config>` class.
#
# A child whose Config is a function of its CONTAINER's Config is not registered
# here at all: it is a family of C++ types and the factory key has no Config
# dimension to select a member with, so the container names the class at its
# createInstance site instead (instanceFactory::createInstance<Impl>). A child
# every one of whose bindings is container-typed gets no trampoline TU at all -
# the persisted per-parent requirement is what the scaffold and manifest gate on.

import pysrc.intf_gen_utils as intf_gen_utils
from pysrc.arch2codeHelper import printError, warningAndErrorReport

def render(args, prj, data):
    return render_default(args, prj, data)


def render_default(args, prj, data):
    out = list()
    blockName = data['blockName']
    qualBlock = data['qualBlock']
    # Per-variant Config selection resolved against the parent's owning project:
    # the trampoline binds the same Config the parent's own instances bind, so a
    # variant the parent declares as a foreign (assembler-owned) variant of the
    # reused child gets the owner-qualified struct.
    parentBlock = data.get('parent')
    if not parentBlock:
        printError(f"blockRegistrar: block '{blockName}' has no --parent on its "
                   f"GENERATED_CODE_PARAM line; re-run `make newmodule` (registrar "
                   f"mode) to rescaffold the registrar .cppm files.")
        exit(warningAndErrorReport())
    registrarConfig = prj.getRegistrarConfigView(qualBlock, parentBlock)
    # The physical TU is one project-child aggregate, so its C++20 module name
    # has the same stable identity. Pair-qualified factory keys inside it keep
    # parent-specific registrations distinct.
    registrarModule = intf_gen_utils.cpp_child_registrar_module_name(
        registrarConfig['ownerProject'],
        registrarConfig['childModuleIdentity'])

    # #includes are illegal in module purview, so all textual headers live here
    # in the global module fragment.
    out.append('module;')
    out.append('#include "instanceFactory.h"')
    out.append('#include "blockBase.h"')
    out.append('')
    out.append(f'export module {registrarModule};')

    # Block class visibility for the parameterized-block lambda so it can
    # construct `<B><Config>`. A PRIVATE import (plain `import`, not
    # `export import`): the registrar exports nothing, it only runs its static.
    out.append(f'import {intf_gen_utils.cpp_block_module_name(data["blockModuleName"])};')

    for mod in registrarConfig['configModules']:
        out.append(f'import {intf_gen_utils.cpp_config_module_name(mod["project"], mod["block"])};')

    registrations = list()
    for registration in registrarConfig['modelRegistrations']:
        perVariantConfig = intf_gen_utils.cpp_config_expression_name(
            registration['config'])
        registrations.extend(_emit_register_call(
            suffix='model',
            blockName=blockName,
            targetClass=f'{blockName}<{perVariantConfig}>',
            variant=registration['variant'],
            projectName=registration['factoryProject'],
            indent='        ',
        ))

    if not registrations:
        printError(f"blockRegistrar: nothing to register for block '{blockName}' under "
                   f"parent '{parentBlock}'; every binding of it is typed by the "
                   f"parent's Config. Delete this generated file.")
        exit(warningAndErrorReport())
    out.append('')
    out.append(f'namespace {{')
    out.append(f'struct _{blockName}_registrar {{')
    out.append(f'    _{blockName}_registrar() {{')
    out.extend(registrations)
    out.append('    }')
    out.append('};')
    out.append(f'static _{blockName}_registrar _{blockName}_registrar_instance;')
    out.append(f'}} // namespace')
    return '\n'.join(out)


def _emit_register_call(*, suffix, blockName, targetClass, variant, projectName, indent):
    """Emit a single instanceFactory::registerBlock(...) call."""
    return [
        f'{indent}instanceFactory::registerBlock(',
        f'{indent}    "{blockName}_{suffix}",',
        f'{indent}    [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {{',
        f'{indent}        return static_cast<std::shared_ptr<blockBase>>(std::make_shared<{targetClass}>(blockName, variant, bbMode));',
        f'{indent}    }},',
        f'{indent}    "{variant}", "{projectName}");',
    ]
