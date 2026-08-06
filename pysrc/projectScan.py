"""Scan-all / reconcile engine for projectOverride multi-copy ownership.

A standalone discovery scanner that reads the FULL projectFiles:/include:
reference closure of a root project - INCLUDING the own closures of every
override-redirected child-project copy (which readRaw() aliases and skips) AND
the closure of each projectOverride target the walk would not otherwise reach
(the master copy, named only by the override) - and reconciles the copies of one
logical IP that projectOverride unifies. Nested overrides are honored with
highest-ancestor-wins, so every level (a subproject standalone and the composed
parent) reconciles onto the same masters the live parse selects.

Unlike readRaw() this scanner:
  * uses the fast PyYAML CSafeLoader (never the heavy ruamel round-trip loader),
    reading only the structural top keys the scan needs (projectName,
    projectFiles, include, dirs, projectOverrides);
  * never collapses a redirected copy onto its master and never raises the
    duplicate-provider error - every physically distinct copy of one
    projectName stays a provider so its members can be enumerated with
    copy-local paths and reattributed to the copy's declaring projectName.

It is NOT wired into projectCreate/readRaw and does not mutate the database; it
returns a ScanResult. Path identity is the whole root-relative context key (no
basename, no dir-nesting, no realpath): distinct physical copies keep distinct
physical keys while sharing one logical key.
"""

import os
from dataclasses import dataclass

import pysrc.arch2codeGlobals as g
from pysrc.arch2codeHelper import printIfDebug, printWarning
from pysrc.processYaml import projectCreate, _expand_with_macros

# PyYAML fast loader - the deliberate NOT-ruamel path for the discovery scan.
import yaml as _pyyaml

import pysrc.yamlReadCache as yamlReadCache


@dataclass
class ScanResult:
    """Reconcile result of a scan-all. Every path is the whole
    root-relative context key (relative to the root project file's directory),
    the same identity used by processYaml's context/ownership maps.

    Fields:
      logicalKey:          physicalPath -> (declaringProjectName, copyRelPath).
                           copyRelPath is the file relative to ITS OWN copy's
                           $root; two physical copies of one logical file share
                           one logical key.
      copyRoots:           providerFileKey -> that copy's absolute $root, one
                           entry per discovered child-project copy.
      logicalGroups:       logicalKey -> [physicalPaths]; a >1-member group is
                           the multi-copy signal.
      masterByProject:     projectName -> master copy's absolute $root, chosen by
                           the projectOverride selection (else the sole copy).
      ownership:           physicalPath -> declaringProjectName (reattributed: a
                           redirected copy's members are owned by the copy's
                           declaring projectName, not the including project).
      aliasMemberToMaster: nonMasterMemberPath -> masterMemberPath, member-level
                           (generalizes readRaw's provider-file-only aliasing).
    """
    logicalKey: dict
    copyRoots: dict
    logicalGroups: dict
    masterByProject: dict
    ownership: dict
    aliasMemberToMaster: dict


class ProjectScanner:
    # Reuse projectCreate's path-normalization, override-merge, and
    # child-project classifier verbatim so the scan derives override precedence
    # and boundaries identically to the live parse. All three are shared with
    # the live parse and pure with respect to projectCreate instance state (they
    # touch only module globals and free functions), so binding them as scanner
    # methods keeps one implementation with no live-path edit.
    getFileList = projectCreate.getFileList
    _mergeOverrides = projectCreate._mergeOverrides
    _isChildProjectFile = projectCreate._isChildProjectFile

    def __init__(self, projFile):
        self.projFile = os.path.abspath(projFile)
        # Shared a2c root, only used to expand a leading $a2c in a dirs: root
        # entry (parity with projectCreate._resolveDirMacros). pysrc parent.
        self.a2cRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Per read file, its projectFiles:+include: reference edges - the
        # ownership graph _referenceClosure walks (systemFiles excluded).
        self.yamlReferences = {}
        # Every discovered child-project copy aliases to ITSELF: the scanner
        # never redirects a copy onto its master, so all copies of one
        # projectName remain distinct providers/boundaries.
        self.providerFileAliases = {}
        # Provider file key -> declaring projectName. Distinct from
        # projectCreate.projectProviders (name -> file, one per name): this is
        # file-keyed so multiple copies of one projectName coexist.
        self.providerName = {}
        # Provider file key -> that copy's absolute $root.
        self.copyRoots = {}
        # Per read file, its include: dependency list, accumulated during the
        # walk and fed into getFileList exactly as readRaw feeds its own
        # yamlDependancies, so a bare-basename include: entry that is a known
        # dependency keys identically to the live parse.
        self.yamlDependancies = {}
        # Root project's own projectFiles:+include: closure (seeds the ownership
        # root walk); the root project file is not itself a graph node.
        self.rootReferences = set()
        self._seen = set()
        # projectName -> BFS depth at which its winning override was folded
        # (root project = 0). Lets _foldEffective tell a legitimate
        # shallower-ancestor shadow from a same-depth sibling contradiction.
        self.overrideDepth = {}
        # Deepest BFS level reached; the post-drain master-discovery pass folds
        # override targets strictly below it so they never masquerade as
        # same-depth conflicts with the declared tree.
        self._maxDepth = 0

    def _fastLoad(self, path):
        # Read through the shared byte cache so readRaw's proper parse reuses
        # these bytes instead of re-reading each closure file from disk.
        return _pyyaml.load(yamlReadCache.read(path),
                            Loader=_pyyaml.CSafeLoader)

    def _resolveRoot(self, projectFileDirKey, dirsBlock):
        # A project's $root: dirs['root'] resolved relative to its project file's
        # directory, mirroring _resolveDirMacros' root anchor. projectFileDirKey
        # is '' for the root project or a root-relative dir for a child copy.
        if 'root' not in dirsBlock:
            raise ValueError(
                "Definition for project root directory missing in project "
                "file. This should reflect the root of all generated files "
                "and is relative to the project file.")
        rootRel = _expand_with_macros(dirsBlock['root'], {'a2c': self.a2cRoot})
        return os.path.abspath(
            os.path.join(g.yamlBasePath, projectFileDirKey, rootRel))

    def scan(self):
        prevCwd = os.getcwd()
        prevBase = g.yamlBasePath
        g.yamlBasePath = os.path.dirname(self.projFile)
        os.chdir(g.yamlBasePath)
        try:
            rootRaw = self._fastLoad(self.projFile)
            self.rootName = rootRaw['projectName']
            self.rootRoot = self._resolveRoot('', rootRaw['dirs'])
            # Root project's projectOverrides seed the inherited-override map
            # (highest ancestor wins as the closure is walked).
            self.rootOverrides = self._mergeOverrides(rootRaw, '.', {})
            # Reconciled highest-ancestor-wins override map across the whole walk:
            # every project's own projectOverrides are folded in via
            # _foldEffective in shallow-to-deep (BFS) order, so the shallowest
            # declarer of each projectName wins. _selectMasters consults this so a
            # nested override (declared by a child project) is honored when no
            # shallower ancestor overrides that projectName.
            self.effectiveOverrides = dict(self.rootOverrides)
            # Root project overrides are folded at depth 0 (the shallowest
            # possible declarer); child copies fold at their BFS level.
            self.overrideDepth = {name: 0 for name in self.rootOverrides}
            (userTodo, userInclude, userProjectSlot) = self.getFileList(
                rootRaw, g.yamlBasePath)
            self.rootReferences = set(userProjectSlot) | set(userInclude)
            # Walk references in declaration order (todoNorm: projectFiles then
            # include, systemFiles excluded from the scan), mirroring the live
            # readRaw walk order, so the include-dependency map accumulates in the
            # same order and getFileList's bare-basename retention keys a
            # subdirectory bare include identically to the live parse. Set-based
            # rootReferences / yamlReferences still drive the order-independent
            # ownership closure.
            queue = [(f, f in userProjectSlot, self.rootOverrides, 1)
                     for f in userTodo if f in self.rootReferences]
            self._drainQueue(queue)
            # Guarantee every projectOverride master selected via the GLOBAL
            # effective map is recorded as a provider, not only the branch-local
            # targets the main BFS reaches (_selectMasters picks the master from
            # self.effectiveOverrides, which is complete only after the walk
            # drains). A master reached by no projectFiles:/include: edge - named
            # only by an override declared in a sibling branch - would otherwise
            # be absent from copyRoots/providerName and _reconcile would KeyError
            # on it. A newly-scanned master may declare further overrides, so
            # re-drain until no unseen target remains.
            while True:
                pending = [(target, True, self.effectiveOverrides,
                            self._maxDepth + 1)
                           for (target, _) in self.effectiveOverrides.values()
                           if target not in self._seen and os.path.exists(target)]
                if not pending:
                    break
                self._drainQueue(pending)
            return self._reconcile()
        finally:
            os.chdir(prevCwd)
            g.yamlBasePath = prevBase

    def _drainQueue(self, queue):
        # Breadth-first drain of a provider/reference queue, shared by the main
        # closure walk and the post-drain master-discovery pass so provider
        # recording, override folding, and reference enqueue stay single-sourced.
        # Each entry carries its BFS depth (root project = 0, its references = 1,
        # ...); children enqueue one level deeper. Depth annotates the
        # effective-override fold for same-depth conflict detection.
        while queue:
            nxt = []
            for (f, viaProjectFiles, inherited, depth) in queue:
                if f in self._seen:
                    continue
                self._seen.add(f)
                if depth > self._maxDepth:
                    self._maxDepth = depth
                raw = self._fastLoad(os.path.join(g.yamlBasePath, f))
                nextOverrides = inherited
                # A projectFiles-slot file carrying the project sentinel set
                # opens a copy scope. The scanner ALWAYS reads its own
                # closure (readRaw skips redirected copies here) and
                # tolerates a second copy of an already-seen projectName.
                if viaProjectFiles and self._isChildProjectFile(raw):
                    projName = raw['projectName']
                    self.providerName[f] = projName
                    self.providerFileAliases[f] = f
                    self.copyRoots[f] = self._resolveRoot(
                        os.path.dirname(f), raw['dirs'])
                    nextOverrides = self._mergeOverrides(
                        raw, os.path.dirname(f), inherited)
                    # Fold this copy's own overrides into the reconciled map
                    # (shallow-to-deep BFS => shallowest declarer wins), with its
                    # declaring depth so a same-depth sibling redirecting the same
                    # projectName elsewhere fails loud instead of silent first-win.
                    self._foldEffective(raw, os.path.dirname(f), depth)
                    # An ancestor override may redirect this projName onto a
                    # target copy the walk would not otherwise reach (e.g. the
                    # override target is a lexically-distinct path reached only
                    # via include: or the override itself). Mirror the live
                    # _selectProvider redirect and scan that target as a
                    # provider too, so BOTH the discovered copy and the master
                    # target are known and reconcile onto one logical identity.
                    # The scanner keeps both copies (never collapses one onto
                    # the other); _seen dedups when the target is already known.
                    if projName in inherited:
                        targetKey = inherited[projName][0]
                        if (os.path.exists(targetKey)
                                and targetKey not in self._seen):
                            nxt.append((targetKey, True, inherited, depth))
                (todo, include, projectSlot) = self.getFileList(
                    raw, os.path.dirname(f), self.yamlDependancies)
                refs = set(projectSlot) | set(include)
                self.yamlReferences[f] = refs
                if f in self.yamlDependancies:
                    self.yamlDependancies[f].update(include)
                else:
                    self.yamlDependancies[f] = include
                # Enqueue in declaration order (todoNorm), filtered to this
                # file's references, matching the live walk order.
                for t in todo:
                    if t in refs and t not in self._seen:
                        nxt.append((t, t in projectSlot, nextOverrides,
                                    depth + 1))
            queue = nxt

    def _foldEffective(self, raw, declDir, depth):
        # Fold one child project's projectOverrides into the reconciled effective
        # map. Shallow-to-deep BFS means the first fold of a projectName is the
        # shallowest declarer and wins (parity with _mergeOverrides). The winning
        # depth is retained per projectName: a strictly-deeper declarer is a
        # legitimate shadow (ancestor wins, skipped), but two NON-dominating
        # declarers at the SAME depth selecting DIFFERENT targets for one
        # projectName are contradictory under the one-master-per-projectName
        # model and fail loud. Target normalization matches _mergeOverrides
        # (lexical relpath, no symlink deref).
        overrides = raw.get('projectOverrides')
        if not overrides:
            return
        for projName, path in overrides.items():
            targetKey = os.path.relpath(
                os.path.join(declDir, path), g.yamlBasePath)
            if projName not in self.effectiveOverrides:
                self.effectiveOverrides[projName] = (targetKey, declDir)
                self.overrideDepth[projName] = depth
            elif depth == self.overrideDepth[projName]:
                existingTarget, existingDecl = self.effectiveOverrides[projName]
                if existingTarget != targetKey:
                    raise ValueError(
                        f"conflicting projectOverrides for projectName "
                        f"'{projName}': '{existingDecl}' selects "
                        f"'{existingTarget}' and '{declDir}' selects "
                        f"'{targetKey}' at the same nesting depth ({depth}); "
                        f"neither declarer dominates the other, so no single "
                        f"master can be chosen.")

    def _referenceClosure(self, seeds, ownProvider):
        # Walk the projectFiles:/include: reference graph from `seeds`,
        # collecting every file the walking project owns and the canonical
        # nested provider project files it directly reaches. A reference to any
        # provider path (a discovered child project file or an
        # override-redirected alias of one) other than the walker's own
        # `ownProvider` is a boundary: it is recorded as a child boundary and NOT
        # crossed, so a nested project's files are left for that project to
        # claim. The walker's own provider file is owned. Reads the scanner's own
        # providerFileAliases / yamlReferences graph. Returns
        # (owned, childBoundaries).
        owned = {ownProvider} if ownProvider is not None else set()
        childBoundaries = set()
        seen = set(seeds)
        stack = list(seeds)
        while stack:
            cur = stack.pop()
            canon = self.providerFileAliases.get(cur)
            if canon is not None:
                # cur is a provider boundary (or an alias of one).
                if canon != ownProvider:
                    childBoundaries.add(canon)
                continue
            owned.add(cur)
            for ref in self.yamlReferences[cur]:
                if ref not in seen:
                    seen.add(ref)
                    stack.append(ref)
        return owned, childBoundaries

    def _assignOwnership(self):
        # Deepest-provider ownership by reference closure, multi-copy tolerant:
        # provider -> name is file-keyed (self.providerName) so distinct copies of
        # one projectName each own their own closure, and each copy's files are
        # reattributed to the copy's declaring projectName. The root reference
        # closure is owned by the root project; every child provider's closure is
        # walked shallow-to-deep and the deepest closure reaching a shared file
        # wins (equal-depth ties break lexically on the provider path). Also
        # records the winning provider file per context so the logical key can
        # anchor on that copy's own $root. Returns (ownership, owningProvider).
        ownership = {}
        owningProvider = {}
        _, rootChildren = self._referenceClosure(self.rootReferences, None)
        depth = {}
        providerOwned = {}
        frontier = list(rootChildren)
        curDepth = 1
        while True:
            nextLevel = []
            for b in frontier:
                if b in depth:
                    continue
                depth[b] = curDepth
                owned, children = self._referenceClosure(
                    self.yamlReferences[b], b)
                providerOwned[b] = owned
                nextLevel.extend(children)
            if nextLevel:
                frontier = nextLevel
                curDepth += 1
                continue
            # The reference-graph wave has drained. Seed any provider discovered
            # in scan() but not reached through a projectFiles:/include: edge - an
            # override target enqueued as the master copy is such an orphan (only
            # the override, not a reference edge, names it). Attribute its closure
            # too, matching the live parse where the _selectProvider redirect wires
            # the master target into the reference graph. Continue until every
            # discovered provider is walked (an orphan's closure may reach more).
            orphans = [p for p in self.providerName if p not in depth]
            if not orphans:
                break
            # An override master reached only by the override sits below the
            # whole reference wave (curDepth = max+1), so its closure out-ranks
            # any reference-reached provider for a file they share - the master
            # owns its own closure.
            frontier = orphans
            curDepth += 1
        for f in sorted(self._seen):
            ownership[f] = self.rootName
            owningProvider[f] = None
        # Shallow-to-deep so the deepest closure that reaches a shared file wins;
        # equal-depth ties break lexically on the provider path.
        for b in sorted(providerOwned, key=lambda x: (depth[x], x)):
            name = self.providerName[b]
            for f in providerOwned[b]:
                ownership[f] = name
                owningProvider[f] = b
        return ownership, owningProvider

    def _selectMasters(self):
        # Master provider file per projectName: the projectOverride target where
        # an override selects one, else the sole discovered copy. Nested overrides
        # are reconciled highest-ancestor-wins through self.effectiveOverrides (the
        # shallowest declarer's target), so an override declared by a child project
        # is honored when no shallower ancestor overrides that projectName. A
        # projectName with multiple copies and no override has no
        # projectOverride-derived master and is left unselected. Target validation
        # matches the live _selectProvider (LENIENT): the target need only EXIST,
        # pass _isChildProjectFile, and DECLARE the requested projectName. scan()'s
        # master-discovery pass already applies that gate and records every valid
        # target as a provider (so it has a copyRoot), so here a discovered target
        # is accepted and an undiscovered one is the invalid case - reported as
        # missing, not-a-child-project-file, or wrong-projectName, exactly the
        # rejections live raises. Returns the provider-file map; callers derive the
        # master $root from copyRoots.
        namesToProviders = {}
        for providerFile, name in self.providerName.items():
            namesToProviders.setdefault(name, []).append(providerFile)
        masterProviderByName = {}
        for name, providers in namesToProviders.items():
            if name in self.effectiveOverrides:
                target, declDir = self.effectiveOverrides[name]
                declared = self.providerName.get(target)
                if declared is None:
                    # scan()'s pre-reconcile master-discovery pass records every
                    # override target that EXISTS and passes _isChildProjectFile
                    # (the single acceptance gate, mirroring live _selectProvider's
                    # exist + _isChildProjectFile + name rule). An undiscovered
                    # target is therefore invalid; report which of live's
                    # structural rejections applies.
                    if not os.path.exists(target):
                        raise ValueError(
                            f"projectOverrides in '{declDir}' selects '{target}' "
                            f"for projectName '{name}', but that file does not "
                            f"exist.")
                    raise ValueError(
                        f"projectOverrides in '{declDir}' selects '{target}' "
                        f"for projectName '{name}', but that file is not a child "
                        f"project file (missing the projectName/dirs/"
                        f"fileGeneration sentinel).")
                if declared != name:
                    raise ValueError(
                        f"projectOverrides in '{declDir}' selects '{target}' "
                        f"for projectName '{name}', but that file declares "
                        f"projectName '{declared}'.")
                masterProviderByName[name] = target
            elif len(providers) == 1:
                masterProviderByName[name] = providers[0]
        return masterProviderByName

    def _canonicalContent(self, member):
        # Layout- and comment-insensitive content identity of one scanned file:
        # its PARSED document re-emitted with sorted keys. Two copies that differ
        # only in comments, a copyright year, whitespace, anchor use, or mapping
        # order carry identical content and are NOT divergent. Bytes come from the
        # shared read cache the scan walk already populated, so this parses from
        # memory and touches no disk.
        doc = self._fastLoad(os.path.join(g.yamlBasePath, member))
        return _pyyaml.safe_dump(doc, sort_keys=True, default_flow_style=False)

    def _reportCopyDivergence(self, logicalGroups, masterMember):
        # Warn when the non-master copies of one logical file disagree with EACH
        # OTHER: the composed sub-projects were developed against different
        # content of the same shared file, and the single selected master
        # silently replaces all of them, so at least one sub-project is composed
        # against content it never saw. A copy that differs only from the MASTER
        # is expected - the master is the copy development happens in, so the
        # vendored copies legitimately lag it - and is logged at debug level,
        # never warned. Only groups with more than one member are compared, so a
        # single-copy (monolithic or plain nested) project parses nothing here.
        for logical, members in sorted(logicalGroups.items()):
            master = masterMember.get(logical)
            if master is None:
                continue
            copies = sorted(m for m in members if m != master)
            if not copies:
                continue
            byContent = {}
            for m in copies:
                byContent.setdefault(self._canonicalContent(m), []).append(m)
            if len(byContent) > 1:
                variants = "; ".join(", ".join(same)
                                     for same in sorted(byContent.values()))
                printWarning(
                    f"composed copies of '{logical[0]}::{logical[1]}' differ "
                    f"from each other: {variants}. The projectOverride master "
                    f"'{master}' replaces all of them, so at least one "
                    f"sub-project is composed against content it was not "
                    f"developed against.")
            elif self._canonicalContent(master) not in byContent:
                printIfDebug(
                    f"copy divergence '{logical[0]}::{logical[1]}': master "
                    f"'{master}' differs from its copies "
                    f"({', '.join(copies)}); expected while development happens "
                    f"in the master copy, so not warned.")

    def _reconcile(self):
        ownership, owningProvider = self._assignOwnership()
        logicalKey = {}
        logicalGroups = {}
        for f, owner in ownership.items():
            provider = owningProvider[f]
            copyRoot = self.copyRoots[provider] if provider is not None \
                else self.rootRoot
            copyRelPath = os.path.relpath(
                os.path.join(g.yamlBasePath, f), copyRoot)
            logical = (owner, copyRelPath)
            logicalKey[f] = logical
            logicalGroups.setdefault(logical, []).append(f)

        masterProviderByName = self._selectMasters()
        masterByProject = {name: self.copyRoots[providerFile]
                           for name, providerFile in masterProviderByName.items()}

        aliasMemberToMaster = {}
        masterMember = {}
        for logical, members in logicalGroups.items():
            name = logical[0]
            if name not in masterProviderByName:
                continue
            masterProvider = masterProviderByName[name]
            masters = [m for m in members
                       if owningProvider[m] == masterProvider]
            if not masters:
                # The selected master copy has no counterpart for this logical
                # member, so its non-master copies cannot be aliased onto one.
                # Surface it rather than silently skipping: benign copy
                # asymmetry, but also the signature of an override target whose
                # key normalized off the copies it was meant to unify.
                printWarning(
                    f"projectOverride master for projectName '{name}' has no "
                    f"member for '{logical[1]}'; leaving these copies "
                    f"unaliased: {', '.join(sorted(members))}")
                continue
            master = masters[0]
            masterMember[logical] = master
            for m in members:
                if m != master:
                    aliasMemberToMaster[m] = master

        self._reportCopyDivergence(logicalGroups, masterMember)

        return ScanResult(
            logicalKey=logicalKey,
            copyRoots=dict(self.copyRoots),
            logicalGroups=logicalGroups,
            masterByProject=masterByProject,
            ownership=ownership,
            aliasMemberToMaster=aliasMemberToMaster,
        )
