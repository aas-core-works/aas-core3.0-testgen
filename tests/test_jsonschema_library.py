"""Test the intricacies of the JSON schema library we use for the tests."""

# pylint: disable=missing-docstring

import re
import unittest

import jsonschema


class TestUnicode(unittest.TestCase):
    def test_for_above_bmp(self) -> None:
        schema = {
            "type": "string",
            "pattern": (
                "^[\\x09\\x0A\\x0D\\x20-\\uD7FF\\uE000-\\uFFFD\\U00010000-\\U0010FFFF]*$"
            ),
        }
        assert re.match(schema["pattern"], "\U000fe800")

        jsonschema.validate(instance='"\U000fe800"', schema=schema)


if __name__ == "__main__":
    unittest.main()
