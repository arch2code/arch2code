#!/usr/bin/env python3

import contextlib
import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pysrc.gen_cpp_module_map import render_module_map


PASS = 0
FAIL = 0


def check(condition, message):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"PASS: {message}")
    else:
        FAIL += 1
        print(f"FAIL: {message}")


def write(path, content):
    with open(path, "w", encoding="utf-8") as source:
        source.write(content)


def expect_value_error(action, text, message):
    try:
        action()
    except ValueError as error:
        check(text in str(error), message)
    else:
        check(False, message)


def test_module_map():
    with tempfile.TemporaryDirectory() as root:
        alpha = os.path.join(root, "user_alpha.cppm")
        beta = os.path.join(root, "generated_beta.cppm")
        write(
            alpha,
            "module;\n"
            "export module user.alpha;\n"
            "import generated.beta;\n"
            "export import external.module;\n"
            "import generated.beta;\n",
        )
        write(beta, "export module generated.beta;\n")

        rendered = render_module_map([alpha, beta])
        check(
            "CPP_MODULE_NAMES := generated.beta user.alpha" in rendered,
            "providers are ordered by source path",
        )
        check(
            f"CPP_MODULE_PROVIDER_user.alpha := {alpha}" in rendered,
            "user module provider path is emitted",
        )
        check(
            "CPP_MODULE_IMPORTS_user.alpha := generated.beta external.module"
            in rendered,
            "named and exported imports are emitted once in source order",
        )

        duplicate = os.path.join(root, "second_beta.cppm")
        write(duplicate, "export module generated.beta;\n")
        expect_value_error(
            lambda: render_module_map([beta, duplicate]),
            "provided by both",
            "duplicate module providers are rejected",
        )

        # A .cppm without an `export module` declaration provides no module: it
        # is skipped with a stderr warning naming the file, and the scan still
        # succeeds (does not raise). This keeps empty freshly-scaffolded units
        # from poisoning every make target.
        not_module = os.path.join(root, "not_module.cppm")
        write(not_module, "int value;\n")
        warnings = io.StringIO()
        with contextlib.redirect_stderr(warnings):
            rendered_skip = render_module_map([beta, not_module])
        check(
            "no 'export module <name>;' declaration" in warnings.getvalue()
            and not_module in warnings.getvalue(),
            "a cppm without an exported module is skipped with a warning naming it",
        )
        check(
            "CPP_MODULE_NAMES := generated.beta" in rendered_skip
            and "not_module" not in rendered_skip,
            "the skipped module is absent from the map while others remain",
        )


if __name__ == "__main__":
    test_module_map()
    print(f"\n{PASS} passed, {FAIL} failed")
    raise SystemExit(1 if FAIL else 0)
