# GENERATED_CODE_PARAM --block=apbDecode
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'apbReg_uBlockA': {
        "port": 'apbReg_uBlockA',
        "name": 'apbDecode.apbReg_uBlockA',
        "interfaceType": 'apb',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'apbDecode.apbReg_uBlockA_obs',
    },
    'apbReg_uBlockB': {
        "port": 'apbReg_uBlockB',
        "name": 'apbDecode.apbReg_uBlockB',
        "interfaceType": 'apb',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'apbDecode.apbReg_uBlockB_obs',
    },
    'apbReg_uBlockG': {
        "port": 'apbReg_uBlockG',
        "name": 'apbDecode.apbReg_uBlockG',
        "interfaceType": 'apb',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'apbDecode.apbReg_uBlockG_obs',
    },
    'cpu_main': {
        "port": 'cpu_main',
        "name": 'apbDecode.cpu_main',
        "interfaceType": 'apb',
        "direction": 'dst',
        "role": None,
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'apbDecode.apbReg_uBlockA',
    'apbDecode.apbReg_uBlockB',
    'apbDecode.apbReg_uBlockG',
    'apbDecode.apbReg_uBlockA_obs',
    'apbDecode.apbReg_uBlockB_obs',
    'apbDecode.apbReg_uBlockG_obs',
)
SYNC_NAMES = (
    'pysocket_sync',
)

def required_names():
    return list(LISTEN_NAMES) + list(SYNC_NAMES)

def by_port(port):
    return CATALOG[port]

def name_for_port(port):
    return CATALOG[port]["name"]

def observe_name_for_port(port):
    return CATALOG[port]["observeName"]

# GENERATED_CODE_END
