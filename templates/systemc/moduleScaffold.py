from pysrc.intf_gen_utils import cpp_module_name

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    match args.section:
        case 'moduleHeader':
            return moduleHeader(args, prj, data)
        case _:
            raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are moduleHeader")


def moduleHeader(args, prj, data):
    out = [
        'module;',
        '#include "systemc.h"',
        '#include "logging.h"',
        '#include "bitTwiddling.h"',
        '#include "q_assert.h"',
        '#include <algorithm>',
        '',
        f'export module {cpp_module_name(data["contextIncludeName"])};',
    ]
    return "\n".join(out)
