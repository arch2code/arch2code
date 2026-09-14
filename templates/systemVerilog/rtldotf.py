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
    for context in data['compileContexts']:
        relDir = contextRtlDir[context]
        incName = '.' if relDir == '.' else './' + relDir
        incdirs[incName] = incName
    for incdir, incdirName in incdirs.items():
        # +incdir+ resolves `include of package and svh bodies; A2C_SV_FILES
        # selects the modules.
        out.append(f'+incdir+{incdirName}')

    for context in data['includeFiles'].get('package_sv', list()):
        # Emit only packages in the compile closure; a referenced child
        # project's standalone harness context sits outside it unless a
        # reachable context includes it. The DB-wide package map keeps order stable.
        if context not in data['compileContexts']:
            continue
        relDir = contextRtlDir[context]
        prefix = '' if relDir == '.' else relDir + '/'
        packageName = data['includeFiles']['package_sv'][context]['baseName']
        out.append(f"{prefix}{packageName}")
    return '\n'.join(out)
