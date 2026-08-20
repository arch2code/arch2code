# GENERATED_CODE_PARAM --block=bridgeApbDecode
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'apbReg_uBridgeIp0': {
        "port": 'apbReg_uBridgeIp0',
        "name": 'bridgeApbDecode.apbReg_uBridgeIp0',
        "interfaceType": 'apb',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'bridgeApbDecode.apbReg_uBridgeIp0_obs',
    },
    'apbReg_uBridgeIp1': {
        "port": 'apbReg_uBridgeIp1',
        "name": 'bridgeApbDecode.apbReg_uBridgeIp1',
        "interfaceType": 'apb',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'bridgeApbDecode.apbReg_uBridgeIp1_obs',
    },
    'apbReg': {
        "port": 'apbReg',
        "name": 'bridgeApbDecode.apbReg',
        "interfaceType": 'apb',
        "direction": 'dst',
        "role": None,
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'bridgeApbDecode.apbReg_uBridgeIp0',
    'bridgeApbDecode.apbReg_uBridgeIp1',
    'bridgeApbDecode.apbReg_uBridgeIp0_obs',
    'bridgeApbDecode.apbReg_uBridgeIp1_obs',
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
