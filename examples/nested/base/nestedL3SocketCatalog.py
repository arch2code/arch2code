# GENERATED_CODE_PARAM --block=nestedL3
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'nested3': {
        "port": 'nested3',
        "name": 'nestedL3.nested3',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'nestedL3.nested3',
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
