from pysrc.intf_gen_utils import module_name_from_include

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    match args.section:
        case 'moduleHeader':
            return moduleHeader(args, prj, data)
        case _:
            print("error missing section, valid values are moduleHeader")
            exit()


def moduleHeader(args, prj, data):
    out = [
        'module;',
        '#include "systemc.h"',
        '#include "logging.h"',
        '#include "bitTwiddling.h"',
        '#include "q_assert.h"',
        '#include <algorithm>',
        '',
        f'export module {module_name_from_include(data["fileNameBase"])};',
    ]
    return "\n".join(out)
