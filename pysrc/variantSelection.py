"""The declarations the bare `<block>_<label>` artefacts are built at. One
descriptor per label, all the block owner's own."""


def standaloneVariantDescriptors(config, qualBlock):
    # A container-sourced label's values come from the pair contract.
    descriptorsByBlock = config.getConfig('VARIANTCONFIGDESCRIPTORS')
    selected = dict()
    for sourceBlock in config.getConfig('VARIANTSOURCEBLOCKS')[qualBlock]:
        for descriptor in descriptorsByBlock[sourceBlock]:
            if not descriptor['isForeign'] and not descriptor['containerSourced']:
                selected[descriptor['variant']] = descriptor
    return selected
