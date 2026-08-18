# GENERATED_CODE_PARAM --block=apbDecode
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'apbReg_uIp': {
        "port": 'apbReg_uIp',
        "name": 'apbDecode.apbReg_uIp',
        "interfaceType": 'apb',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'apbDecode.apbReg_uIp_obs',
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
    'apbDecode.apbReg_uIp',
    'apbDecode.apbReg_uIp_obs',
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
