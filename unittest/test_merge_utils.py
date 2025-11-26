import os
import unittest

from pysrc.merge_utils import merge_with_spec


class TestMergeUtils(unittest.TestCase):
    def test_file_generation_file_map_shallow_entries(self):
        # Base and pro project-like dicts focused on fileGeneration.fileMap.
        base = {
            "fileGeneration": {
                "dirs": {"root": "../..", "cppBase": "../../mdl"},
                "fileMap": {
                    "block": {"name": "", "ext": {"hdr": "h", "src": "cpp"}},
                    "rtlModule": {"name": "", "ext": {"sv": "sv"}},
                },
            }
        }
        pro = {
            "fileGeneration": {
                "dirs": {"svBase": "../../rtl"},
                "fileMap": {
                    # Override existing key with a different value dict.
                    "block": {
                        "name": "",
                        "ext": {"hdr": "hpp", "src": "cc"},
                        "extra": True,
                    },
                    # New key only in pro.
                    "newEntry": {"name": "X", "ext": {"sv": "sv"}},
                },
            }
        }

        spec = {
            ("fileGeneration",): "dict_shallow",
            ("fileGeneration", "fileMap"): "dict_shallow",
        }

        merged = merge_with_spec(base, pro, spec, path=())

        # Top-level keys: both base and pro preserved.
        self.assertIn("fileGeneration", merged)

        fg = merged["fileGeneration"]
        # dirs is shallow at this level: base and pro dirs combined.
        self.assertEqual(
            fg["dirs"],
            {
                "root": "../..",
                "cppBase": "../../mdl",
                "svBase": "../../rtl",
            },
        )

        # fileMap keys: base+pro merged at key level.
        file_map = fg["fileMap"]
        self.assertCountEqual(file_map.keys(), ["block", "rtlModule", "newEntry"])

        # block entry should be exactly pro's dict (shallow, no deep merge
        # of inner ext dict).
        self.assertEqual(
            file_map["block"],
            {
                "name": "",
                "ext": {"hdr": "hpp", "src": "cc"},
                "extra": True,
            },
        )

        # rtlModule comes from base unchanged.
        self.assertEqual(
            file_map["rtlModule"],
            {"name": "", "ext": {"sv": "sv"}},
        )

        # newEntry comes from pro unchanged.
        self.assertEqual(
            file_map["newEntry"],
            {"name": "X", "ext": {"sv": "sv"}},
        )


if __name__ == "__main__":
    unittest.main()


