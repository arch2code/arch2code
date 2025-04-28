import colorama
import os
import re

# Basic color string function using ansi color
RED, MAGENTA, GREEN, RESET = colorama.Fore.RED, colorama.Fore.MAGENTA, colorama.Fore.GREEN, colorama.Fore.RESET
cstr = lambda s,c : str(c+s+RESET)

# Join string if list, else return unchanged
_str_join = lambda s, c=' ' : c.join(s) if isinstance(s, list) else s

# wrapper function around os.environ to set environment variables
def setenv(key, value):
    os.environ[key] = str(value)

# Replace placeholders with environ variables in string
def subst_env(string):
    return re.sub(r'\${?(\w+)}?', lambda match: os.environ.get(match.group(1), ''), string)

# Get trully random number of <size> bytes from os random device, and convert to "0x" hexadecimal string format
def getrandom_hex(size=4):
    return ''.join(['0x', os.getrandom(size).hex()])

'''
convert an input value in heterogenous type/format to the most appropriate output type
if no conversion possible, raise ValueError
'''
def convert_value(value):
    if isinstance(value, int):
        return int(value)
    elif isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return hex(int(value, 16))
        except ValueError:
            pass
        if value == 'null':
            return None
        else:
            return value
    raise ValueError
