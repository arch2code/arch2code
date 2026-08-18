# GENERATED_CODE_PARAM --block=blockBRegs
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'apbReg': {
        "port": 'apbReg',
        "name": 'blockBRegs.apbReg',
        "interfaceType": 'apb',
        "direction": 'dst',
        "role": None,
        "observeName": None,
    },
    'rwD': {
        "port": 'rwD',
        "name": 'blockBRegs.rwD',
        "interfaceType": 'status',
        "direction": 'src',
        "role": None,
        "observeName": None,
    },
    'roBsize': {
        "port": 'roBsize',
        "name": 'blockBRegs.roBsize',
        "interfaceType": 'status',
        "direction": 'dst',
        "role": 'observe',
        "observeName": 'blockBRegs.roBsize_obs',
    },
    'blockBTableExt': {
        "port": 'blockBTableExt',
        "name": 'blockBRegs.blockBTableExt',
        "interfaceType": 'memory',
        "direction": 'src',
        "role": None,
        "observeName": None,
    },
    'blockBTable37Bit': {
        "port": 'blockBTable37Bit',
        "name": 'blockBRegs.blockBTable37Bit',
        "interfaceType": 'memory',
        "direction": 'src',
        "role": None,
        "observeName": None,
    },
    'blockBTable1': {
        "port": 'blockBTable1',
        "name": 'blockBRegs.blockBTable1',
        "interfaceType": 'memory',
        "direction": 'src',
        "role": None,
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'blockBRegs.roBsize_obs',
)
SYNC_NAMES = ()

def required_names():
    return list(LISTEN_NAMES) + list(SYNC_NAMES)

def by_port(port):
    return CATALOG[port]

def name_for_port(port):
    return CATALOG[port]["name"]

def observe_name_for_port(port):
    return CATALOG[port]["observeName"]

# GENERATED_CODE_END
