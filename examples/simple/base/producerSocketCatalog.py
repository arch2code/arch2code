# GENERATED_CODE_PARAM --block=producer
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'tag0': {
        "port": 'tag0',
        "name": 'producer.tag0',
        "interfaceType": 'push_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'tag1': {
        "port": 'tag1',
        "name": 'producer.tag1',
        "interfaceType": 'push_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'producer.tag0',
    'producer.tag1',
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
