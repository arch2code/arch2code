#!/usr/bin/env bash
#
# test_gen_file_equivalence.sh — #22 acceptance gate.
#
# Before #22 the makefiles discovered the generated-source set at build time by
# scanning the manifest's source dirs for files carrying GENERATED_CODE_ markers
# (a2c-common.mk find_gen_cpp_sources / find_gen_sv_sources feeding
# SC_GEN_FILES / SV_GEN_FILES). #22 replaces that with the DB-derived manifest
# enumeration (A2C_SC_GEN_FILES / A2C_SV_GEN_FILES) plus the user seam
# (EXTRA_SC_GEN_FILES / EXTRA_SV_GEN_FILES for hand-authored files that carry
# generated regions but are not DB-defined).
#
# This gate proves, per example, that the NEW make-consumed set (manifest +
# seam, wildcard-filtered to on-disk files, exactly what SC_GEN_FILES /
# SV_GEN_FILES expand to) reproduces the OLD find/grep set, modulo documented,
# expected deltas:
#   1. known build orphans: fw/src integration firmware, a composed child's
#      nested verif/vl_wrap standalone entry (see test_build_manifest.py).
#   2. stale alternate-extension orphans: a pre-.cppm-migration file superseded
#      by a manifest .cppm of the same dir+stem (e.g. base/<b>Base.h beside the
#      current base/<b>Base.cppm, or a now-parameterizable block's <b>.cpp/.h
#      beside <b>.cppm). The current fileMap emits only the .cppm; the old find
#      also picked up the un-swept legacy file.
#   3. nested sub-project standalone artifacts: a composed build regenerates only
#      the composed top's set; a child project's standalone-only files (its own
#      TB-top include or a leaf whose RTL is replaced in composition) sit on disk
#      under the child tree but are not part of the composed top's generation.
#
# Any OLD-only file that matches none of these, or any NEW-only file (the
# manifest/seam builds something the old find would not), is a FAIL.
#
# Usage:  test_gen_file_equivalence.sh            # all examples
#         test_gen_file_equivalence.sh apbDecode  # a subset

set -u

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # builder/base
EXAMPLES_DIR="$BASE_DIR/examples"
SKIP="pySocket"   # not migrated to yamlFormat: 2

mfval() { grep "^$1 " "$2" | sed "s/^$1 := //"; }

# Fully expanded SC_GEN_FILES / SV_GEN_FILES as make consumes them (manifest
# baseline + EXTRA_ seam, already wildcard-filtered to on-disk files).
expand_gen() {   # $1 example dir ; writes $2 (sc) $3 (sv, .f dropped)
  local ex="$1"
  local ev='printgen: ; @printf "%s\n" $(SC_GEN_FILES) > .gen/_eq_sc.txt ; printf "%s\n" $(SV_GEN_FILES) > .gen/_eq_sv.txt'
  make -C "$ex" --no-print-directory --eval="$ev" printgen >/dev/null 2>&1
  sort -u "$ex/.gen/_eq_sc.txt" > "$2"
  grep -v '\.f$' "$ex/.gen/_eq_sv.txt" | sort -u > "$3"
}

old_find() {   # $1 dirs ; $2 name-pattern args
  local dirs="$1"; shift
  for d in $dirs; do
    [ -d "$d" ] && find -L "$d" -type f "$@" -exec grep -l 'GENERATED_CODE_' {} \;
  done | sort -u
}

# Nested sub-project roots: ancestor dir of a */prj/yaml/*Project.yaml that is
# not the example root itself.
nested_roots() {   # $1 example dir
  local ex="$1"
  find "$ex" -path '*/prj/yaml/*Project.yaml' 2>/dev/null | while read -r pj; do
    local root; root="$(dirname "$(dirname "$(dirname "$pj")")")"
    [ "$root" != "$ex" ] && echo "$root"
  done | sort -u
}

check_example() {
  local name="$1"
  local ex="$EXAMPLES_DIR/$name"
  ( cd "$ex" && make clean >/dev/null 2>&1 && make db >/dev/null 2>&1 && make gen >/dev/null 2>&1 ) \
    || { echo "  [FAIL ] $name (regen failed)"; return 1; }
  local mk="$ex/.gen/build.mk"
  [ -f "$mk" ] || { echo "  [FAIL ] $name (no build.mk)"; return 1; }

  local scdirs svdirs
  scdirs="$(mfval A2C_SC_SRC_DIRS "$mk") $(mfval A2C_VL_WRAP_DIRS "$mk")"
  svdirs="$(mfval A2C_SV_SRC_DIRS "$mk") $(mfval A2C_VL_WRAP_DIRS "$mk")"

  local T; T="$(mktemp -d)"
  old_find "$scdirs" \( -name '*.cpp' -o -name '*.h' -o -name '*.cppm' \) > "$T/old_sc"
  old_find "$svdirs" \( -name '*.sv' -o -name '*.svh' \) > "$T/old_sv"
  expand_gen "$ex" "$T/new_sc" "$T/new_sv"

  # dir|stem index of the new set (for stale alternate-ext acceptance).
  awk -F/ '{f=$NF; sub(/\.[^.]*$/,"",f); d=$0; sub(/[^/]*$/,"",d); print d"|"f}' \
      "$T/new_sc" "$T/new_sv" | sort -u > "$T/new_stems"
  nested_roots "$ex" > "$T/nested"

  local problems=0 notes=""
  # NEW-only: manifest/seam builds something the old find did not -> hard fail.
  local newonly; newonly="$(comm -13 <(cat "$T/old_sc" "$T/old_sv" | sort -u) \
                                      <(cat "$T/new_sc" "$T/new_sv" | sort -u))"
  if [ -n "$newonly" ]; then
    echo "  [FAIL ] $name  NEW-only (not seen by old find):"
    echo "$newonly" | sed "s|$ex/|    +|"
    problems=1
  fi
  # OLD-only: every one must match an accepted category.
  local oldonly; oldonly="$(comm -23 <(cat "$T/old_sc" "$T/old_sv" | sort -u) \
                                      <(cat "$T/new_sc" "$T/new_sv" | sort -u))"
  local unexplained="" orphan="" stale="" subproj=""
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    local rel="${f#$ex/}"
    local dir; dir="$(dirname "$f")/"; local stem; stem="$(basename "$f")"; stem="${stem%.*}"
    if [ "$rel" = "fw/src" ] || [[ "$rel" == fw/src/* ]] || [[ "$f" == */verif/vl_wrap/* && "$(echo "$rel" | tr -cd / | wc -c)" -gt 2 ]]; then
      orphan="$orphan $rel"
    elif grep -qxF "$dir|$stem" "$T/new_stems"; then
      stale="$stale $rel"
    elif grep -q -F -f <(sed "s|\$|/|" "$T/nested") <<<"$f/" 2>/dev/null; then
      subproj="$subproj $rel"
    else
      unexplained="$unexplained $rel"
    fi
  done <<< "$oldonly"

  [ -n "$orphan" ]  && notes="$notes; orphan:$orphan"
  [ -n "$stale" ]   && notes="$notes; stale-cppm-superseded:$stale"
  [ -n "$subproj" ] && notes="$notes; subproject-standalone:$subproj"
  if [ -n "$unexplained" ]; then
    echo "  [FAIL ] $name  OLD-only unexplained:$unexplained"
    problems=1
  fi
  [ $problems -eq 0 ] && echo "  [OK   ] $name${notes:+  (accepted deltas${notes})}"
  rm -rf "$T"
  return $problems
}

main() {
  local names=("$@")
  if [ ${#names[@]} -eq 0 ]; then
    for d in "$EXAMPLES_DIR"/*/; do
      local n; n="$(basename "$d")"
      [ "$n" = "$SKIP" ] && continue
      [ -f "$d/Makefile" ] && names+=("$n")
    done
  fi
  local fails=0
  for n in "${names[@]}"; do
    check_example "$n" || fails=$((fails+1))
  done
  echo
  if [ $fails -ne 0 ]; then
    echo "FAIL: gen-file set diverges from the old find set for $fails example(s)."
    return 1
  fi
  echo "PASS: manifest+seam reproduces the old find generated-file set (accepted deltas excepted)."
  return 0
}

main "$@"
