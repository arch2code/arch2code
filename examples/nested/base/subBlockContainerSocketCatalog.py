# GENERATED_CODE_PARAM --block=subBlockContainer
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'in': {
        "port": 'in',
        "name": 'subBlockContainer.in',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'out': {
        "port": 'out',
        "name": 'subBlockContainer.out',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'subBlockContainer.in',
    'subBlockContainer.out',
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
