# GENERATED_CODE_PARAM --block=secondSubB
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'test': {
        "port": 'test',
        "name": 'secondSubB.test',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'beta': {
        "port": 'beta',
        "name": 'secondSubB.beta',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'secondSubB.test',
    'secondSubB.beta',
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
