# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    out = []
    # Per-context RTL output directory (relative to the rtl.f location) is
    # precomputed by the projectOpen view (getContextData/_contextRtlDirs) so
    # that cross-project contexts resolve to the owning child's rtl/ output
    # rather than its yaml source tree. The template only formats these dirs.
    contextRtlDir = data['contextRtlDir']
    incdirs = dict()
    for context in data['includeContext']:
        relDir = contextRtlDir[context]
        incName = '.' if relDir == '.' else './' + relDir
        incdirs[incName] = incName
    for incdir, incdirName in incdirs.items():
        out.append(f'+incdir+{incdirName}')
        out.append(f'-y {incdirName}')

    for context in data['includeFiles'].get('package_sv', list()):
        # Emit only packages in this build's include-chain scope. A referenced
        # child project's standalone harness context is parsed into the same
        # database but is not on the build context's include chain, so it is not
        # part of the compiled design. Iterating the (DB-wide) package map in its
        # own order keeps the emitted order stable.
        if context not in data['includeContext']:
            continue
        relDir = contextRtlDir[context]
        prefix = '' if relDir == '.' else relDir + '/'
        packageName = data['includeFiles']['package_sv'][context]['baseName']
        out.append(f"{prefix}{packageName}")
    return '\n'.join(out)
