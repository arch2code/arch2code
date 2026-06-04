from pysrc.arch2codeHelper import printError, warningAndErrorReport


class ValueResolver:
    """Resolve create-time integer values against context-keyed project data."""

    def __init__(self, project, values=None, context=''):
        self.project = project
        self.values = dict(values or {})
        self.context = context

    def _fail(self, message):
        printError(message)
        exit(warningAndErrorReport())

    def _label(self, label, source=None):
        if source is None:
            return label
        lc = source.get('lc') if isinstance(source, dict) else None
        line = lc.line + 1 if lc is not None else '?'
        return f"{label} at {self.context}:{line}"

    def _lookupQualified(self, section, key, label):
        try:
            return self.project.flatData[section][key]
        except KeyError:
            return self._fail(
                f"Internal error: {label} '{key}' is not present in "
                f"project.flatData['{section}'].")

    def lookupNamedRow(self, key, label):
        constants = self.project.flatData['constants']
        if key in constants:
            return constants[key]
        if key in self.project.qualEnums:
            enumRow = self.project.qualEnums[key]
            return {
                'value': enumRow['value'],
                'isParameterizable': False,
                'maxValue': 0,
            }
        return self._fail(
            f"Internal error: {label} '{key}' is not present in "
            f"project data.")

    def lookupVisibleRow(self, name, context, label):
        """Look up a constant or enum row by bare name through the include
        chain of `context`. Returns the constant entry directly, or for an
        enum synthesizes a non-parameterizable record with the same shape
        ({'value', 'isParameterizable', 'maxValue'}) so callers can branch
        uniformly. Hard-fails on miss with a user-tone error."""
        constants = self.project.data['constants']
        enums = self.project.enums
        for myContext in self._contextSearchOrder(context):
            if myContext in constants and name in constants[myContext]:
                return constants[myContext][name]
            if myContext in enums and name in enums[myContext]:
                enumRow = enums[myContext][name]
                return {
                    'value': enumRow['value'],
                    'isParameterizable': False,
                    'maxValue': 0,
                }
        return self._fail(
            f"{label}: constant or enum '{name}' is not declared in "
            f"'{context}' or any file it includes.")

    def _visibleNamedKey(self, name, context, label):
        constants = self.project.data['constants']
        enums = self.project.enums
        for myContext in self._contextSearchOrder(context):
            if myContext in constants and name in constants[myContext]:
                return f"{name}/{myContext}"
            if myContext in enums and name in enums[myContext]:
                return f"{name}/{myContext}"
        return self._fail(
            f"{label}: constant or enum '{name}' is not declared in "
            f"'{context}' or any file it includes.")

    def _contextSearchOrder(self, context):
        yamlContext = self.project.yamlContext
        if context == 'global':
            return list(yamlContext.keys())
        if context in yamlContext:
            return list(yamlContext[context].keys())
        return [context]

    def _toInt(self, raw, label):
        if isinstance(raw, bool):
            return self._fail(
                f"{label} must resolve to a positive integer; got "
                f"boolean value {raw!r}.")
        if isinstance(raw, float):
            return self._fail(
                f"{label} must resolve to a positive integer; got "
                f"floating-point value {raw!r}.")
        try:
            return int(raw)
        except (TypeError, ValueError):
            if isinstance(raw, str):
                try:
                    return int(raw, 0)
                except ValueError:
                    pass
            return self._fail(
                f"{label} must resolve to a positive integer; got "
                f"{type(raw).__name__} {raw!r}.")

    def _resolveActiveValue(self, ref, context, label, source=None):
        if isinstance(ref, int) and not isinstance(ref, bool):
            return ref
        if isinstance(ref, float):
            label = self._label(label, source)
            return self._fail(
                f"{label} must resolve to a positive integer; got "
                f"floating-point value {ref!r}.")
        if isinstance(ref, str) and ref != '':
            try:
                return int(ref)
            except ValueError:
                try:
                    return int(ref, 0)
                except ValueError:
                    pass

        if not isinstance(ref, str) or ref == '':
            label = self._label(label, source)
            return self._fail(
                f"{label} must resolve to a positive integer; got "
                f"{type(ref).__name__} {ref!r}.")

        if ref in self.values:
            return self._toInt(self.values[ref], f"override '{ref}'")

        if '/' in ref:
            key = ref
        else:
            if not context:
                return self._fail(
                    f"Internal error: unqualified value reference '{ref}' has "
                    f"no resolver context.")
            key = self._visibleNamedKey(ref, context, label)
            if key in self.values:
                return self._toInt(self.values[key], f"override '{key}'")

        row = self.lookupNamedRow(key, label)
        return self._toInt(row['value'], f"{label} '{key}'")

    def _resolveMaxValue(self, key, label):
        row = self.lookupNamedRow(key, label)
        if row['isParameterizable']:
            n = self._toInt(row['maxValue'], f"{label} '{key}' maxValue")
            if n <= 0:
                return self._fail(
                    f"{label} '{key}' maxValue must resolve to a "
                    f"positive integer, got {n}.")
            return n
        return self._toInt(row['value'], f"{label} '{key}'")

    def value(self, ref, label='value reference', source=None):
        return self._resolveActiveValue(ref, self.context, label, source=source)

    def qualifyKey(self, ref, context, fatal=True):
        """Resolve a constant/enum reference to its qualified storage key.

        Primary parse-time helper for foreign-key columns: keep `ret[field]`
        as the user-typed token and stamp `ret[field+'Key']` with the
        qualification so later code knows which scope the symbol lives in
        without re-walking the include chain.

        Numeric values (int / float / bool, plus numeric strings parseable as
        int or float) return '' — they are literals carrying no symbol to
        qualify. Bare-name symbols return 'name/context' by walking the
        include chain of `context` through constants and enums.

        fatal=True (default): unknown symbols hard-fail with a user-tone error.
        fatal=False: unknown symbols return None so the caller can compose a
                     richer error (e.g. the param ftype caller, which knows
                     the owning block name and reports both rejection paths)."""
        if isinstance(ref, (int, float)):
            return ''
        if isinstance(ref, str):
            try:
                int(ref, 0)
                return ''
            except (TypeError, ValueError):
                pass
            try:
                float(ref)
                return ''
            except (TypeError, ValueError):
                pass
            constants = self.project.data['constants']
            enums = self.project.enums
            for myContext in self._contextSearchOrder(context):
                if myContext in constants and ref in constants[myContext]:
                    return f"{ref}/{myContext}"
                if myContext in enums and ref in enums[myContext]:
                    return f"{ref}/{myContext}"
            if not fatal:
                return None
            return self._fail(
                f"Constant or enum '{ref}' is not declared in "
                f"'{context}' or any file it includes.")
        if not fatal:
            return None
        return self._fail(
            f"Cannot qualify {type(ref).__name__} value {ref!r} as a "
            f"constant or enum reference.")

    def _typeWidth(self, typeRef, use_max=False):
        if isinstance(typeRef, str):
            typeRow = self._lookupQualified('types', typeRef, 'type')
            typeLabel = typeRef
        else:
            typeRow = typeRef
            typeLabel = typeRow.get('typeKey') or typeRow.get('type') or '<anonymous>'
        isSigned = bool(typeRow['isSigned'])
        for mode in ('width', 'widthLog2', 'widthLog2minus1'):
            key = typeRow[mode + 'Key'] or ''
            raw = typeRow[mode]
            if key or (raw not in (None, '', 0)):
                label = f"type '{typeLabel}' {mode}"
                if use_max and key:
                    n = self._resolveMaxValue(key, label)
                else:
                    n = self._resolveActiveValue(
                        key if key else raw,
                        typeRow['_context'],
                        label)
                if mode == 'widthLog2':
                    width = int(n).bit_length()
                    if isSigned:
                        width += 1
                elif mode == 'widthLog2minus1':
                    width = int(n - 1).bit_length()
                    if isSigned:
                        width += 1
                else:
                    width = n
                return width
        return self._fail(
            f"Internal error: type '{typeLabel}' has no width / widthLog2 / "
            f"widthLog2minus1 populated; create-time validation cannot "
            f"resolve its bit width.")

    def typeWidth(self, typeRef):
        return self._typeWidth(typeRef)

    def typeMaxWidth(self, typeRef):
        if isinstance(typeRef, str):
            typeRow = self._lookupQualified('types', typeRef, 'type')
        else:
            typeRow = typeRef
        if typeRow['isParameterizable'] and typeRow['maxBitwidth']:
            return self._toInt(typeRow['maxBitwidth'], "type maxBitwidth")
        return self._typeWidth(typeRow, use_max=True)

    def arraySize(self, varRow, use_max=False, field_name='arraySize'):
        key = varRow['arraySizeKey'] or ''
        raw = varRow['arraySize']
        if key:
            if use_max:
                n = self._resolveMaxValue(key, field_name)
            else:
                n = self._resolveActiveValue(
                    key, varRow['_context'], field_name)
            return n if n > 0 else 1
        if raw in (None, ''):
            return 1
        n = self._resolveActiveValue(
            raw,
            varRow['_context'],
            f"{field_name} '{raw}'")
        return n if n > 0 else 1

    def _structureWidth(self, structRef, use_max=False):
        if isinstance(structRef, str):
            structRow = self._lookupQualified('structures', structRef, 'structure')
            structLabel = structRef
        else:
            structRow = structRef
            structLabel = structRow.get('structureKey') or structRow.get('structure') or '<anonymous>'
        if use_max and structRow['isParameterizable'] and structRow['maxBitwidth']:
            return self._toInt(
                structRow['maxBitwidth'],
                f"structure '{structLabel}' maxBitwidth")
        if 'vars' in structRow:
            total = 0
            for varName, varRow in structRow['vars'].items():
                width = self.varWidth(
                    varRow,
                    use_max=use_max,
                    field_name=varName)
                total += width
            return total
        return self._toInt(
            structRow['width'], f"structure '{structLabel}' width")

    def varWidth(self, varRow, use_max=False, field_name='field'):
        entryType = varRow['entryType']
        arraySize = self.arraySize(
            varRow,
            use_max=use_max,
            field_name=f"field '{field_name}' arraySize")
        if entryType == 'NamedStruct':
            elemWidth = self._structureWidth(
                varRow['subStructKey'], use_max=use_max)
        elif entryType == 'Reserved':
            elemWidth = self._resolveActiveValue(
                varRow['align'],
                varRow['_context'],
                f"Reserved field '{field_name}' align")
        else:
            typeKey = varRow['varTypeKey'] or ''
            if typeKey:
                elemWidth = (
                    self.typeMaxWidth(typeKey)
                    if use_max else self.typeWidth(typeKey)
                )
            else:
                elemWidth = self._resolveActiveValue(
                    varRow['bitwidth'],
                    varRow['_context'],
                    f"field '{field_name}' bitwidth")
        return elemWidth * arraySize

    def structPackedFields(self, structKey):
        return self._structPackedFields(
            structKey, visiting=set(), prefix='')

    def _structPackedFields(self, structKey, visiting, prefix):
        if structKey in visiting:
            return self._fail(
                f"Internal error: structure '{structKey}' recursively "
                f"references itself during create-time validation.")
        structRow = self._lookupQualified('structures', structKey, 'structure')
        fields = []
        offset = 0
        visiting = visiting | {structKey}
        for varName, varRow in structRow['vars'].items():
            fieldName = f"{prefix}.{varName}" if prefix else varName
            entryType = varRow['entryType']
            arraySize = self.arraySize(varRow)
            if entryType == 'NamedStruct':
                subKey = varRow['subStructKey']
                subFields = self._structPackedFields(
                    subKey, visiting=visiting, prefix=fieldName)
                elemWidth = self._fieldSpan(subFields)
                for index in range(arraySize):
                    indexPrefix = (
                        f"{fieldName}[{index}]" if arraySize > 1
                        else fieldName)
                    for name, width, subOffset in subFields:
                        if arraySize > 1:
                            suffix = name[len(fieldName):]
                            name = indexPrefix + suffix
                        fields.append(
                            (name, width, offset + index * elemWidth + subOffset))
                offset += elemWidth * arraySize
            elif entryType == 'Reserved':
                width = self._resolveActiveValue(
                    varRow['align'],
                    varRow['_context'],
                    f"Reserved field '{fieldName}' align")
                width *= arraySize
                fields.append((fieldName, width, offset))
                offset += width
            else:
                typeKey = varRow['varTypeKey'] or ''
                if typeKey:
                    elemWidth = self.typeWidth(typeKey)
                else:
                    elemWidth = self._resolveActiveValue(
                        varRow['bitwidth'],
                        varRow['_context'],
                        f"field '{fieldName}' bitwidth")
                width = elemWidth * arraySize
                fields.append((fieldName, width, offset))
                offset += width
        return fields

    def _fieldSpan(self, fields):
        if not fields:
            return 0
        return max(offset + width for (_name, width, offset) in fields)
