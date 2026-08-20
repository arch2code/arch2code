# GENERATED_CODE_PARAM --block=ipStdDecode
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'ipReg': {
        "port": 'ipReg',
        "name": 'ipStdDecode.ipReg',
        "interfaceType": 'apb',
        "direction": 'dst',
        "role": None,
        "observeName": None,
    },
    'ipReg_uIp': {
        "port": 'ipReg_uIp',
        "name": 'ipStdDecode.ipReg_uIp',
        "interfaceType": 'apb',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'ipStdDecode.ipReg_uIp_obs',
    },
}

LISTEN_NAMES = (
    'ipStdDecode.ipReg_uIp',
    'ipStdDecode.ipReg_uIp_obs',
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
