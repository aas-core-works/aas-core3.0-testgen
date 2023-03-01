"""Provide common methods for generation of data in different formats."""

import io
import pathlib
import re
from typing import MutableMapping, Tuple

import aas_core_codegen.common
import aas_core_codegen.parse
import aas_core_codegen.run
import aas_core_meta.v3rc2
from aas_core_codegen import intermediate, infer_for_schema

from aas_core3_0_testgen import generation


_XML_1_0_TEXT_RE = re.compile(
    r"^[\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]*$"
)


def conforms_to_xml_1_0(value: generation.ValueUnion) -> bool:
    """Check recursively that the value conforms to XML 1.0."""
    if isinstance(value, generation.PrimitiveValueTuple):
        if isinstance(value, str):
            return _XML_1_0_TEXT_RE.match(value) is not None
        else:
            return True
    elif isinstance(value, generation.Instance):
        # noinspection PyTypeChecker
        for prop_value in value.properties.values():
            if not conforms_to_xml_1_0(prop_value):
                return False

        return True
    elif isinstance(value, generation.ListOfInstances):
        for instance in value.values:
            if not conforms_to_xml_1_0(instance):
                return False

        return True

    else:
        aas_core_codegen.common.assert_never(value)
