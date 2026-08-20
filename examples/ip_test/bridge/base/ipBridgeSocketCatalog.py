# GENERATED_CODE_PARAM --block=ipBridge
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'data8In': {
        "port": 'data8In',
        "name": 'ipBridge.data8In',
        "interfaceType": 'push_ack',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'data70In': {
        "port": 'data70In',
        "name": 'ipBridge.data70In',
        "interfaceType": 'push_ack',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'apbReg': {
        "port": 'apbReg',
        "name": 'ipBridge.apbReg',
        "interfaceType": 'apb',
        "direction": 'dst',
        "role": None,
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'ipBridge.data8In',
    'ipBridge.data70In',
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
