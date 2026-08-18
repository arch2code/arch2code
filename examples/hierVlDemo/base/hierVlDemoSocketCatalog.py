# GENERATED_CODE_PARAM --block=hierVlDemo
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'axis4_t1': {
        "port": 'axis4_t1',
        "name": 'hierVlDemo.axis4_t1',
        "interfaceType": 'axi4_stream',
        "direction": 'dst',
        "role": None,
        "observeName": None,
    },
    'axis4_t2': {
        "port": 'axis4_t2',
        "name": 'hierVlDemo.axis4_t2',
        "interfaceType": 'axi4_stream',
        "direction": 'src',
        "role": None,
        "observeName": None,
    },
}

LISTEN_NAMES = ()
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
