# GENERATED_CODE_PARAM --block=axiSocket
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'axiRd0': {
        "port": 'axiRd0',
        "name": 'axiSocket.axiRd0',
        "interfaceType": 'axi_read',
        "direction": 'dst',
        "role": 'drive',
        "observeName": 'axiSocket.axiRd0_obs',
    },
    'axiWr0': {
        "port": 'axiWr0',
        "name": 'axiSocket.axiWr0',
        "interfaceType": 'axi_write',
        "direction": 'dst',
        "role": 'drive',
        "observeName": 'axiSocket.axiWr0_obs',
    },
}

LISTEN_NAMES = (
    'axiSocket.axiRd0',
    'axiSocket.axiWr0',
    'axiSocket.axiRd0_obs',
    'axiSocket.axiWr0_obs',
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
