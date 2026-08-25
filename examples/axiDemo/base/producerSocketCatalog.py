# GENERATED_CODE_PARAM --block=producer
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'axiRd0': {
        "port": 'axiRd0',
        "name": 'producer.axiRd0',
        "interfaceType": 'axi_read',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'producer.axiRd0_obs',
    },
    'axiRd1': {
        "port": 'axiRd1',
        "name": 'producer.axiRd1',
        "interfaceType": 'axi_read',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'producer.axiRd1_obs',
    },
    'axiRd2': {
        "port": 'axiRd2',
        "name": 'producer.axiRd2',
        "interfaceType": 'axi_read',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'producer.axiRd2_obs',
    },
    'axiRd3': {
        "port": 'axiRd3',
        "name": 'producer.axiRd3',
        "interfaceType": 'axi_read',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'producer.axiRd3_obs',
    },
    'axiWr0': {
        "port": 'axiWr0',
        "name": 'producer.axiWr0',
        "interfaceType": 'axi_write',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'producer.axiWr0_obs',
    },
    'axiWr1': {
        "port": 'axiWr1',
        "name": 'producer.axiWr1',
        "interfaceType": 'axi_write',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'producer.axiWr1_obs',
    },
    'axiWr2': {
        "port": 'axiWr2',
        "name": 'producer.axiWr2',
        "interfaceType": 'axi_write',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'producer.axiWr2_obs',
    },
    'axiWr3': {
        "port": 'axiWr3',
        "name": 'producer.axiWr3',
        "interfaceType": 'axi_write',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'producer.axiWr3_obs',
    },
    'axiStr0': {
        "port": 'axiStr0',
        "name": 'producer.axiStr0',
        "interfaceType": 'axi4_stream',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'axiStr1': {
        "port": 'axiStr1',
        "name": 'producer.axiStr1',
        "interfaceType": 'axi4_stream',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'producer.axiRd0',
    'producer.axiRd1',
    'producer.axiRd2',
    'producer.axiRd3',
    'producer.axiWr0',
    'producer.axiWr1',
    'producer.axiWr2',
    'producer.axiWr3',
    'producer.axiStr0',
    'producer.axiStr1',
    'producer.axiRd0_obs',
    'producer.axiRd1_obs',
    'producer.axiRd2_obs',
    'producer.axiRd3_obs',
    'producer.axiWr0_obs',
    'producer.axiWr1_obs',
    'producer.axiWr2_obs',
    'producer.axiWr3_obs',
)
SYNC_NAMES = (
    'pysocket_sync',
)

def required_names():
    return list(LISTEN_NAMES) + list(SYNC_NAMES)

def by_port(port):
    return CATALOG[port]

def name_for_port(port):
    return CATALOG[port]["name"]

def observe_name_for_port(port):
    return CATALOG[port]["observeName"]

# GENERATED_CODE_END
