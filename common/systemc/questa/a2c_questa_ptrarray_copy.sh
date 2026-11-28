#!/bin/sh
# QUESTA_PTRARRAY_COPY=1 (a2c-systemc.mk): writes <copy dir>, a copy of Questa's
# SystemC include directory to build against. Every entry is a symbolic link to
# the installed one, except ptrarray.h, in which the static member
# ptrarray<T*>::m_default_init_size is defined in the class instead of out of
# class (Siemens case #02437403; SIMULATOR_INTEGRATION.md section 2.3). The copy
# is made in the build tree from the site's own install; no Questa file is part
# of arch2code. A copy made from the same install is kept.
# Usage: a2c_questa_ptrarray_copy.sh <Questa include/systemc> <copy dir>
set -eu
q=$1; out=$2; src=$q/ptrarray.h
if [ -f "$out/.a2c_source" ] && [ "$(cat "$out/.a2c_source")" = "$q" ] && [ -f "$out/ptrarray.h" ]; then
    exit 0
fi
tmp=$out.tmp.$$
rm -rf "$tmp"; mkdir -p "$tmp"
for e in "$q"/*; do ln -s "$e" "$tmp/"; done
rm "$tmp/ptrarray.h"
awk '/^class ptrarray<T\*>/ { spec = 1 }
     spec && /^ *static +int m_default_init_size;/ { sub(/static +int m_default_init_size;/, "static constexpr int m_default_init_size = 16;"); spec = 0 }
     /^template <typename T>$/ { held = $0; next }
     held != "" { h = held; held = ""; if ($0 == "int ptrarray<T*>::m_default_init_size = 16;") next; print h }
     { print }' "$src" > "$tmp/ptrarray.h"
# Exactly the two edits: the member defined in the class, its out-of-class
# definition removed. Any other ptrarray.h stops the build.
if [ "$(grep -c 'static constexpr int m_default_init_size = 16;' "$tmp/ptrarray.h")" != 1 ] ||
   [ "$(diff "$src" "$tmp/ptrarray.h" | grep -c '^[<>]')" != 4 ] ||
   grep -q 'ptrarray<T\*>::m_default_init_size' "$tmp/ptrarray.h"; then
    rm -rf "$tmp"
    echo "a2c_questa_ptrarray_copy: $src is not the ptrarray.h this copy expects; build with QUESTA_PTRARRAY_COPY=0" >&2
    exit 1
fi
printf '%s\n' "$q" > "$tmp/.a2c_source"
rm -rf "$out"
# A parallel make may have written the same copy meanwhile; keep the first.
mv -T "$tmp" "$out" 2>/dev/null || rm -rf "$tmp"
