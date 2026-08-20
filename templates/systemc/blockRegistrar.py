# Per-block trampoline registrar template. The trampoline is the single TU per
# (block, project) carrying the SystemC parameterized-block registrations, one
# lambda per (blockType, variant) pair the project's instance tree binds.
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
# getRegistrarConfigView()['hasRegistrations'] is what the scaffold gates on.

import pysrc.intf_gen_utils as intf_gen_utils
from pysrc.arch2codeHelper import printError, warningAndErrorReport

def render(args, prj, data):
    return render_default(args, prj, data)


def render_default(args, prj, data):
    out = list()
    blockName = data['blockName']
    qualBlock = data['qualBlock']
    # A block that declares its own params: is always flagged isParameterizable
    # and therefore always carries a defaultConfig.
    defaultConfig = data['defaultConfig']

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
    variantDescriptors = registrarConfig['variantDescriptors']
    # The variant labels that earn a registration: what this build's design tree
    # binds for the child, plus the labels a container's Config reaches it at,
    # minus the container-sourced ones.
    registeredVariants = registrarConfig['registeredVariants']

    # The registrar is a C++20 module interface unit whose module name is
    # parent-qualified (`<project>.<parent>.<child>.registrar`), so the same
    # child reused under two parents yields two distinct registrar modules that
    # coexist in one binary.
    projectName = prj.config.getConfig('PROJECTNAME')
    registrarModule = intf_gen_utils.cpp_registrar_module_name(projectName, parentBlock, blockName)

    # #includes are illegal in module purview, so all textual headers live here
    # in the global module fragment.
    out.append('module;')
    out.append('#include "instanceFactory.h"')
    out.append('#include "blockBase.h"')

    # Per-context Config-policy headers must be reachable for the
    # parameterized lambda body.
    for context in sorted(data['configIncludeContext']):
        if context in data['includeFiles'].get('config_hdr', {}):
            out.append(f'#include "{data["includeFiles"]["config_hdr"][context]["baseName"]}"')

    out.append('')
    out.append(f'export module {registrarModule};')

    # Block class visibility for the parameterized-block lambda so it can
    # construct `<B><Config>`. A PRIVATE import (plain `import`, not
    # `export import`): the registrar exports nothing, it only runs its static.
    out.append(f'import {intf_gen_utils.cpp_block_module_name(data["blockModuleName"])};')

    # Owner-qualified foreign-Config modules for variants the parent declares as
    # foreign variants of the reused child; the lambda body spells those owner-
    # qualified Config types.
    for mod in registrarConfig['foreignConfigModules']:
        out.append(f'import {intf_gen_utils.cpp_config_module_name(mod["project"], mod["block"])};')

    def _target(desc):
        perVariantConfig = intf_gen_utils.cpp_descriptor_config_name(desc, defaultConfig) if desc else defaultConfig
        return f'{blockName}<{perVariantConfig}>'

    registrations = list()
    for variant in registeredVariants:
        registrations.extend(_emit_register_call(
            suffix='model',
            blockName=blockName,
            targetClass=_target(variantDescriptors[variant]),
            variant=variant,
            projectName=projectName,
            indent='        ',
        ))
    if registrarConfig['defaultRegistration']:
        # The design binds an instance naming no variant, so the block also
        # registers under the empty variant against its default Config.
        registrations.extend(_emit_register_call(
            suffix='model',
            blockName=blockName,
            targetClass=_target(None),
            variant='',
            projectName=projectName,
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
