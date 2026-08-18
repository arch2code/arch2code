# GENERATED_CODE_PARAM --block=blockGLeaf
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'rwG': {
        "port": 'rwG',
        "name": 'blockGLeaf.rwG',
        "interfaceType": 'status',
        "direction": 'dst',
        "role": 'observe',
        "observeName": 'blockGLeaf.rwG_obs',
    },
}

LISTEN_NAMES = (
    'blockGLeaf.rwG_obs',
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
