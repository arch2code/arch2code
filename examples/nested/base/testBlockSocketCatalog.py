# GENERATED_CODE_PARAM --block=testBlock
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'loop1src': {
        "port": 'loop1src',
        "name": 'testBlock.loop1src',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'loop1dst': {
        "port": 'loop1dst',
        "name": 'testBlock.loop1dst',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'loop2src': {
        "port": 'loop2src',
        "name": 'testBlock.loop2src',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'loop2dst': {
        "port": 'loop2dst',
        "name": 'testBlock.loop2dst',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'testBlock.loop1src',
    'testBlock.loop1dst',
    'testBlock.loop2src',
    'testBlock.loop2dst',
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
