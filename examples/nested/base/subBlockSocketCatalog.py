# GENERATED_CODE_PARAM --block=subBlock
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'src': {
        "port": 'src',
        "name": 'subBlock.src',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'dst': {
        "port": 'dst',
        "name": 'subBlock.dst',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'subBlock.src',
    'subBlock.dst',
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
