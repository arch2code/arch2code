# GENERATED_CODE_PARAM --block=apbDecode
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'apbReg_uBridge': {
        "port": 'apbReg_uBridge',
        "name": 'apbDecode.apbReg_uBridge',
        "interfaceType": 'apb',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'apbDecode.apbReg_uBridge_obs',
    },
    'apbReg_uIp0': {
        "port": 'apbReg_uIp0',
        "name": 'apbDecode.apbReg_uIp0',
        "interfaceType": 'apb',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'apbDecode.apbReg_uIp0_obs',
    },
    'apbReg_uIp1': {
        "port": 'apbReg_uIp1',
        "name": 'apbDecode.apbReg_uIp1',
        "interfaceType": 'apb',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'apbDecode.apbReg_uIp1_obs',
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
    'apbDecode.apbReg_uBridge',
    'apbDecode.apbReg_uIp0',
    'apbDecode.apbReg_uIp1',
    'apbDecode.apbReg_uBridge_obs',
    'apbDecode.apbReg_uIp0_obs',
    'apbDecode.apbReg_uIp1_obs',
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
