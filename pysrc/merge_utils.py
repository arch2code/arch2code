from __future__ import annotations

from typing import Any, Dict, Hashable, Iterable, Mapping, MutableMapping, Sequence, Tuple


Path = Tuple[Hashable, ...]
MergeSpec = Mapping[Path, str]


def _get_merge_strategy(path: Iterable[Hashable], spec: MergeSpec | None, default_strategy: str) -> str:
    """Return merge strategy string for the given path."""
    if not spec:
        return default_strategy
    return spec.get(tuple(path), default_strategy)


def merge_with_spec(base: Any, override: Any, spec: MergeSpec | None, path: Path = ()) -> Any:
    """Merge two values according to type-based defaults and a path spec.

    Dictionaries are shallow-merged by default (keys from override replace
    base keys at this level, and values are not recursed into) unless the
    spec marks the current path (or a child path) as a different strategy.

    Supported strategies:
      - dict_shallow: shallow dict merge at that node (default)
      - dict_deep: deep-merge child dicts by default
      - dict_replace: ignore base and use override dict as-is
      - list_override: override list
      - list_append: append override list elements after base (default)
      - replace: generic full replacement
    """
    # If there is no override, keep base as-is.
    if override is None:
        return base

    # If base is None, just take override.
    if base is None:
        return override

    # Dict handling.
    if isinstance(base, dict) and isinstance(override, dict):
        strategy = _get_merge_strategy(path, spec, "dict_shallow")

        if strategy == "dict_replace":
            return override

        # For both dict_deep and dict_shallow we walk keys. dict_deep
        # deep-merges child dicts by default, while dict_shallow only
        # recurses into children that have an explicit spec entry.
        result: Dict[Any, Any] = dict(base)
        for key, o_val in override.items():
            if key not in result:
                result[key] = o_val
                continue

            b_val = result[key]
            child_path = path + (key,)
            child_strategy = _get_merge_strategy(child_path, spec, None)

            if isinstance(b_val, dict) and isinstance(o_val, dict):
                if child_strategy == "dict_replace":
                    # Explicit replace for this child node.
                    result[key] = o_val
                elif child_strategy in ("dict_shallow", "dict_deep"):
                    # Explicit child dict strategy: recurse so that the
                    # child's own strategy controls how it is merged.
                    result[key] = merge_with_spec(
                        b_val, o_val, spec, child_path
                    )
                elif strategy == "dict_deep":
                    # Parent is deep-merge: recurse by default.
                    result[key] = merge_with_spec(
                        b_val, o_val, spec, child_path
                    )
                else:
                    # Parent is dict_shallow and no child spec: shallow
                    # at this child, so override wins without recursion.
                    result[key] = o_val
            elif isinstance(b_val, list) and isinstance(o_val, list):
                # Lists under dicts honour explicit child strategy when
                # present, otherwise fall back to the default list
                # behaviour (which is append by default).
                result[key] = merge_with_spec(
                    b_val, o_val, spec, child_path
                )
            else:
                # Scalars or mismatched types: override
                result[key] = o_val

        return result

    # List handling.
    if isinstance(base, list) and isinstance(override, list):
        strategy = _get_merge_strategy(path, spec, "list_append")
        if strategy == "list_append":
            return list(base) + list(override)
        # Default and list_override: override list.
        return override

    # Fallback: replace scalar or mismatched types.
    return override


