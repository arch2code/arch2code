# GENERATED_CODE_PARAM --block=sink
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'in': {
        "port": 'in',
        "name": 'sink.in',
        "interfaceType": 'push_ack',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'sink.in',
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
