"""Environment for a make the unit tests start as if from a shell."""

import os

# An outer make running the suite would otherwise pass its jobserver, flags
# and command-line variables down to the test's own make.
SUBMAKE_VARS = ('MAKELEVEL', 'MAKEFLAGS', 'MFLAGS', 'MAKEOVERRIDES')


def shell_make_env():
    env = {k: v for k, v in os.environ.items() if k not in SUBMAKE_VARS}
    env['NO_COLOR'] = '1'
    return env
