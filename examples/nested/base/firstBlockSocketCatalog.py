# GENERATED_CODE_PARAM --block=firstBlock
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'primary': {
        "port": 'primary',
        "name": 'firstBlock.primary',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'response': {
        "port": 'response',
        "name": 'firstBlock.response',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'firstBlock.primary',
    'firstBlock.response',
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
