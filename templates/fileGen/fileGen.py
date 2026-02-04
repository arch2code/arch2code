
from pysrc.arch2codeHelper import printError, warningAndErrorReport

from jinja2 import Template as J2Template
from string import Template

# Redefine the pattern to follow the format defined by dvt templates (i.e __name__, or __{name}__)
class TemplateCustom(Template):
    delimiter = '__'
    pattern = r'''
    __(?:
    (?P<escaped>__)|
    (?P<named>[a-zA-Z][a-zA-Z0-9]*(_?[a-zA-Z0-9])*)|
    {(?P<braced>[a-zA-Z][a-zA-Z0-9]*(_?[a-zA-Z0-9])*)}|
    (?P<invalid>))__
    '''

# this file is used to create blank files for a new module with sections required
def render(args, prj, data):
    isRegHandler = True if 'block' in data and next(filter(lambda x: x['block'] == data['block'] and x['isRegHandler'] == 1, prj['blocks'].values()), None) else False
    match data['target']:
        case 'blockBase_hdr':
            return(blockBase_hdr(args, prj, data))
        case 'blockBase_src':
            return(blockBase_src(args, prj, data))
        case 'block_hdr':
            if isRegHandler:
                return(blockRegs_hdr(args, prj, data))
            else:
                return(block_hdr(args, prj, data))
        case 'block_src':
            if isRegHandler:
                return(blockRegs_src(args, prj, data))
            else:
                return(block_src(args, prj, data))
            return(block_src(args, prj, data))
        case 'rtlModule_sv':
            if isRegHandler:
                return(rtlModuleRegs(args, prj, data))
            else:
                return(rtlModule(args, prj, data))
        case 'vlSvWrap_sv':
            return(vlSvWrap_sv(args, prj, data))
        case 'vlScWrap_hdr':
            return(vlScWrap_hdr(args, prj, data))
        case 'vlSvWrap_svVariant':
            return(vlSvWrap_sv(args, prj, data))
        case 'tandem_hdr':
            return(tandem_hdr(args, prj, data))
        case 'tandem_src':
            return(tandem_src(args, prj, data))
        case 'tbConfig_src':
            return(tbConfig(args, prj, data))
        case 'testBench_hdr':
            return(testBench_hdr(args, prj, data))
        case 'testBench_src':
            return(testBench_src(args, prj, data))
        case 'tbExternal_hdr':
            return(tbExternal_hdr(args, prj, data))
        case 'tbExternal_src':
            return(tbExternal_src(args, prj, data))
        case 'include_src':
            return(include_src(args, prj, data))
        case 'include_hdr':
            return(include_hdr(args, prj, data))
        case 'includeFW_src':
            return(includeFW_src(args, prj, data))
        case 'includeFW_hdr':
            return(includeFW_hdr(args, prj, data))
        case 'package_sv':
            return(package_sv(args, prj, data))
        case _:
            print(f"Unknown section: {data['target']}")
            exit()

# header file for base class containing common architectureal definitions - such as interfaces to be inherited by implementations
def blockBase_hdr(args, prj, data):
    out = list()
    blockUpper = data["block"].upper()
    out.append(f'#ifndef {blockUpper}_BASE_H\n')
    out.append(f'#define {blockUpper}_BASE_H\n\n')
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append('#include "systemc.h"\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=baseClassDecl\n')
    out.append('\n')
    out.append('// GENERATED_CODE_END\n')
    out.append(f'#endif //{blockUpper}_BASE_H\n')
    return("".join(out))


# constructor etc for base class containing common architectureal definitions
def blockBase_src(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=baseConstructor --section=init\n')
    out.append('// GENERATED_CODE_END\n')
    out.append('// GENERATED_CODE_BEGIN --template=baseConstructor --section=body\n')
    out.append('    // GENERATED_CODE_END\n')
    out.append('};\n\n')
    return("".join(out))

# header file for model implementation
def block_hdr(args, prj, data):
    out = list()
    blockUpper = data["block"].upper()
    out.append(f'#ifndef {blockUpper}_H\n')
    out.append(f'#define {blockUpper}_H\n\n')
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append('#include "systemc.h"\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=classDecl\n')
    out.append('\n')
    out.append('    // GENERATED_CODE_END\n')
    out.append('    // block implementation members\n\n')
    out.append('};\n\n')
    out.append(f'#endif //{blockUpper}_H\n')
    return("".join(out))

# cpp file for model implementation
def block_src(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=constructor --section=init\n')
    out.append('// GENERATED_CODE_END\n')
    out.append('// GENERATED_CODE_BEGIN --template=constructor --section=body\n')
    out.append('    // GENERATED_CODE_END\n')
    out.append('};\n\n')
    return("".join(out))

def blockRegs_hdr(args, prj, data):
    out = list()
    blockUpper = data["block"].upper()
    out.append(f'#ifndef {blockUpper}_H\n')
    out.append(f'#define {blockUpper}_H\n\n')
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append('#include "systemc.h"\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=blockRegs --section=header\n')
    out.append('\n')
    out.append('    // GENERATED_CODE_END\n')
    out.append('    // block implementation members\n\n')
    out.append('};\n\n')
    out.append(f'#endif //{blockUpper}_H\n')
    return("".join(out))

def blockRegs_src(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=blockRegs --section=init\n')
    out.append('// GENERATED_CODE_END\n')
    out.append('// GENERATED_CODE_BEGIN --template=blockRegs --section=body\n')
    out.append('    // GENERATED_CODE_END\n')
    out.append('};\n\n')
    return("".join(out))

# rtl file for implementation
def rtlModule(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances\n')
    out.append('// GENERATED_CODE_END\n')
    out.append(f'\nendmodule: {data["block"]}\n')
    return("".join(out))

def rtlModuleRegs(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=moduleRegs\n')
    out.append('// GENERATED_CODE_END\n')
    return("".join(out))

vlSvWrap_svTemplate = \
"""`ifndef ___MODULENAME___HDL_SV_WRAPPER_SV_GUARD_
`define ___MODULENAME___HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=__modulename__
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper
// GENERATED_CODE_END

`endif // ___MODULENAME___HDL_SV_WRAPPER_SV_GUARD_
"""

vlSvWrap_svVariantTemplate = \
"""`ifndef ___MODULENAME_____VARIANTNAME___HDL_SV_WRAPPER_SV_GUARD_
`define ___MODULENAME_____VARIANTNAME___HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=__modulename__ --variant=__variantname__
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper
// GENERATED_CODE_END

`endif // ___MODULENAME_____VARIANTNAME___HDL_SV_WRAPPER_SV_GUARD_
"""

def vlSvWrap_sv(args, prj, data):
    if data['variant']:
        t = TemplateCustom(vlSvWrap_svVariantTemplate)
        return(t.substitute({'MODULENAME':data["block"].upper(), 'modulename':data["block"], 'VARIANTNAME':data['variant'].upper(), 'variantname':data['variant']}))
    else:
        t = TemplateCustom(vlSvWrap_svTemplate)
        return(t.substitute({'MODULENAME':data["block"].upper(), 'modulename':data["block"]}))

vlScWrap_hdrTemplate = \
"""#ifndef {{MODULENAME}}_HDL_SC_WRAPPER_H_
#define {{MODULENAME}}_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block={{modulename}}

#include "{{modulename}}Base.h"

// Verilated RTL top (SystemC)
{%- if variants %}
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=variant_include_sv_wrapper_header
// GENERATED_CODE_END
{% else %}
#if !defined(VERILATOR) && defined(VCS)
#include "{{modulename}}_hdl_sv_wrapper.h"
#else
#include "V{{modulename}}_hdl_sv_wrapper.h"
#endif
{% endif %}

{%- if variants %}
template <typename DUT_T>
{%- endif %}
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class
// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};
{%- if variants %}

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=variant_class_template_spec
// GENERATED_CODE_END
{%- endif %}

#endif // {{MODULENAME}}_HDL_SC_WRAPPER_H_
"""

def vlScWrap_hdr(args, prj, data):
    t = J2Template(vlScWrap_hdrTemplate)
    return(t.render({'MODULENAME':data["block"].upper(), 'modulename':data["block"], 'variants':data['variants']})+'\n')

tandem_hdrTemplate = \
"""#ifndef __MODULENAME___TANDEM_H
#define __MODULENAME___TANDEM_H
// __copyright__

// GENERATED_CODE_PARAM --block=__modulename__
// GENERATED_CODE_BEGIN --template=tandem --section=tandem
// GENERATED_CODE_END
private:
};

#endif //__MODULENAME___TANDEM_H
"""

def tandem_hdr(args, prj, data):
    t = TemplateCustom(tandem_hdrTemplate)
    return(t.substitute({'MODULENAME':data["block"].upper(),
                         'modulename':data["block"],
                         'copyright':data["fileGeneration"]["fileCopyrightStatement"]}))

tandem_srcTemplate = \
"""// GENERATED_CODE_PARAM --block=__modulename__
// GENERATED_CODE_BEGIN --template=tandemConstructor --section=initTandem

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tandemConstructor --section=bodyTandem
// GENERATED_CODE_END
}
"""

def tandem_src(args, prj, data):
    t = TemplateCustom(tandem_srcTemplate)
    return(t.substitute({'modulename':data["block"]}))

tbConfigTemplate = \
"""// __copyright__

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
#include "endOfTest.h"

// GENERATED_CODE_PARAM --block=__modulename__
// GENERATED_CODE_BEGIN --template=tbConfig
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        //create hierarchy
        std::shared_ptr<blockBase> tb = instanceFactory::createInstance("", "tb", "__modulename__Testbench", "");
        return true;
    }

    void final(void) override
    {
        // Final cleanup if needed
        Q_ASSERT_CTX(endOfTestState::GetInstance().isEndOfTest(), "final", "Premature end of test detected");
        errorCode::pass();
    }

};
__modulename__Config::registerTestBenchConfig __modulename__Config::registerTestBenchConfig_; //register the testBench with the factory
"""

def tbConfig(args, prj, data):
    t = TemplateCustom(tbConfigTemplate)
    return(t.substitute({
        'modulename':data["block"],
        'copyright':data["fileGeneration"]["fileCopyrightStatement"]}))

testBench_hdrTemplate = \
"""#ifndef __MODULENAME___TANDEM_H
#define __MODULENAME___TANDEM_H
// __copyright__

// GENERATED_CODE_PARAM --block=__modulename__
// GENERATED_CODE_BEGIN --template=testbench --section=header
// GENERATED_CODE_END

#endif /* __MODULENAME___TANDEM_H */
"""

def testBench_hdr(args, prj, data):
    t = TemplateCustom(testBench_hdrTemplate)
    return(t.substitute({
        'MODULENAME':data["block"].upper(),
        'modulename':data["block"],
        'copyright':data["fileGeneration"]["fileCopyrightStatement"]}))

testBench_srcTemplate = \
"""// GENERATED_CODE_PARAM --block=__modulename__
// GENERATED_CODE_BEGIN --template=testbench --section=init
// GENERATED_CODE_END
"""

def testBench_src(args, prj, data):
    t = TemplateCustom(testBench_srcTemplate)
    return(t.substitute({'modulename':data["block"]}))


tbExternal_hdrTemplate = \
"""#ifndef __MODULENAME___EXTERNAL_H
#define __MODULENAME___EXTERNAL_H
// __copyright__

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=__modulename__
// GENERATED_CODE_BEGIN --template=tbExternal --section=header
// GENERATED_CODE_END
};

#endif /* __MODULENAME___EXTERNAL_H */
"""

def tbExternal_hdr(args, prj, data):
    t = TemplateCustom(tbExternal_hdrTemplate)
    return(t.substitute({
        'MODULENAME':data["block"].upper(),
        'modulename':data["block"],
        'copyright':data["fileGeneration"]["fileCopyrightStatement"]}))

tbExternal_srcTemplate = \
"""#include "__modulename__External.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=__modulename__

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
// GENERATED_CODE_END
}
"""

def tbExternal_src(args, prj, data):
    t = TemplateCustom(tbExternal_srcTemplate)
    return(t.substitute({'modulename':data["block"]}))

include_hdrTemplate = \
"""
#ifndef __HEADERGUARD___
#define __HEADERGUARD___
// __copyright__

#include "systemc.h"

// GENERATED_CODE_PARAM --context=__context__
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=include_hdr
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// GENERATED_CODE_END
#endif //__HEADERGUARD___
"""
def include_hdr(args, prj, data):
    t = TemplateCustom(include_hdrTemplate)
    return(t.substitute({
        'HEADERGUARD':data["headerName"].replace('.', '_').upper(),
        'context':data["context"],
        'copyright':data["fileGeneration"]["fileCopyrightStatement"]}))

include_srcTemplate = \
"""
// __copyright__
#include "__headerName__"
// GENERATED_CODE_PARAM --context=__context__
// GENERATED_CODE_BEGIN --template=structures --section=cppIncludes
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=cpp
// GENERATED_CODE_END
"""
def include_src(args, prj, data):
    t = TemplateCustom(include_srcTemplate)
    return(t.substitute({
        'headerName':data["headerName"].replace(".cpp", ".h"),
        'context':data["context"],
        'copyright':data["fileGeneration"]["fileCopyrightStatement"]}))

includeFW_hdrTemplate = \
"""
#ifndef __HEADERGUARD___
#define __HEADERGUARD___
// __copyright__

#include <cstdint>
#include <cstring>

// GENERATED_CODE_PARAM --context=__context__ --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes
// GENERATED_CODE_END
namespace fw_ns {
// GENERATED_CODE_BEGIN --template=includes --section=constants
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// GENERATED_CODE_END
} // end of namespace fw_ns
#endif //__HEADERGUARD___
"""
def includeFW_hdr(args, prj, data):
    t = TemplateCustom(includeFW_hdrTemplate)
    return(t.substitute({
        'HEADERGUARD':data["headerName"].replace('.', '_').upper(),
        'context':data["context"],
        'copyright':data["fileGeneration"]["fileCopyrightStatement"]}))

includeFW_srcTemplate = \
"""
// __copyright__
#include "__headerName__"
using namespace fw_ns;
// GENERATED_CODE_PARAM --context=__context__ --mode=fw
// GENERATED_CODE_BEGIN --template=structures --section=cppIncludes
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=cpp --namespace=fw_ns
// GENERATED_CODE_END
"""
def includeFW_src(args, prj, data):
    t = TemplateCustom(includeFW_srcTemplate)
    return(t.substitute({
        'headerName':data["headerName"].replace(".cpp", ".h"),
        'context':data["context"],
        'copyright':data["fileGeneration"]["fileCopyrightStatement"]}))

package_svTemplate = \
"""
// __copyright__
// GENERATED_CODE_PARAM --context=__context__
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
// GENERATED_CODE_END
"""
def package_sv(args, prj, data):
    t = TemplateCustom(package_svTemplate)
    return(t.substitute({
        'context':data["context"],
        'copyright':data["fileGeneration"]["fileCopyrightStatement"]}))
