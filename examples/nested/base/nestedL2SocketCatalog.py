# GENERATED_CODE_PARAM --block=nestedL2
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'nested2': {
        "port": 'nested2',
        "name": 'nestedL2.nested2',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'nestedL2.nested2',
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
