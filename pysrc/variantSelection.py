"""Single owner for standalone-variant selection: which descriptor a build
resolves a block's own parameters at for each declared variant label."""


def standaloneVariantDescriptors(config, qualBlock):
    # {variant: descriptor} this build resolves a block's own parameters at.
    # The build's own descriptor of a label wins; container-sourced labels
    # take their values from the parent-child pair contract, not from here.
    consumerProject = config.getConfig('PROJECTNAME')
    descriptorsByBlock = config.getConfig('VARIANTCONFIGDESCRIPTORS')
    selected = dict()
    for sourceBlock in config.getConfig('VARIANTSOURCEBLOCKS')[qualBlock]:
        grouped = dict()
        for descriptor in descriptorsByBlock[sourceBlock]:
            grouped.setdefault(descriptor['variant'], []).append(descriptor)
        for variant, descriptors in grouped.items():
            own = [d for d in descriptors if d['declaringProject'] == consumerProject]
            (descriptor,) = own or descriptors
            if not descriptor['containerSourced']:
                selected[variant] = descriptor
    return selected
