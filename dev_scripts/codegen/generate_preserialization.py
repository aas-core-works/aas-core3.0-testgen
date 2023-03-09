"""Generate the code to pre-serialize instances for further modification."""

import argparse
import os
import pathlib
import sys
from typing import List, Optional, Tuple

from aas_core_codegen import intermediate
from aas_core_codegen.common import (
    Stripped, indent_but_first_line, assert_never, Identifier
)
from aas_core_codegen.python import (
    common as python_common,
    naming as python_naming
)
from aas_core_codegen.python.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III
)
from icontract import ensure

import aas_core3_0_testgen.common
import dev_scripts.codegen.common
import dev_scripts.codegen.ontology

_REPO_DIR = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent


def _generate_preserialization_classes() -> List[Stripped]:
    """Generate the classes representing the pre-serialization."""
    return [
        Stripped("PrimitiveValueUnion = Union[bool, int, float, str, bytes]"),
        Stripped(
            f"""\
PrimitiveValueTuple = (bool, int, float, str, bytes)
assert PrimitiveValueTuple == get_args(PrimitiveValueUnion)"""
        ),
        Stripped(
            'ValueUnion = Union[PrimitiveValueUnion, "Instance", "ListOfInstances"]'
        ),
        Stripped(
            f"""\
class Instance:
{I}\"\"\"Represent an instance of a class.\"\"\"

{I}def __init__(
{II}self, properties: OrderedDict[str, ValueUnion], model_type: Identifier
{I}) -> None:
{II}\"\"\"
{II}Initialize with the given values.

{II}The ``model_type`` needs to be always indicated. Whether it is represented in
{II}the final serialization depends on the context of the serialization.

{II}The ``model_type`` corresponds to the class name in the meta-model, not to the
{II}class name in the respective serialization.
{II}\"\"\"
{II}self.properties = properties
{II}self.model_type = model_type"""
        ),
        Stripped(
            f"""\
class ListOfInstances:
{I}\"\"\"Represent a list of instances.\"\"\"

{I}def __init__(self, values: List[Instance]) -> None:
{II}\"\"\"Initialize with the given values.\"\"\"
{II}self.values = values"""
        ),
        Stripped(
            f"""\
def _to_jsonable(value: ValueUnion) -> Any:
{I}\"\"\"
{I}Represent the ``value`` as a JSON-able object.

{I}This is meant for debugging, not for the end-user serialization.
{I}\"\"\"
{I}if isinstance(value, PrimitiveValueTuple):
{II}if isinstance(value, bytes):
{III}return repr(value)
{II}else:
{III}return value
{I}elif isinstance(value, Instance):
{II}obj = collections.OrderedDict()  # type: MutableMapping[str, Any]
{II}obj["model_type"] = value.model_type

{II}properties_dict = collections.OrderedDict()  # type: MutableMapping[str, Any]
{II}for prop_name, prop_value in value.properties.items():
{III}properties_dict[prop_name] = _to_jsonable(prop_value)

{II}obj["properties"] = properties_dict

{II}return obj
{I}elif isinstance(value, ListOfInstances):
{II}return [_to_jsonable(item) for item in value.values]
{I}else:
{II}assert_never(value)"""
        ),
        Stripped(
            f"""\
def dump(value: ValueUnion) -> str:
{I}\"\"\"
{I}Represent the ``value`` as a string.

{I}This is meant for debugging, not for the end-user serialization.
{I}\"\"\"
{I}return json.dumps(_to_jsonable(value), indent=2)"""
        )
    ]


def _generate_transform(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate the pre-serialization method."""
    blocks = [
        Stripped(
            f"""\
properties = collections.OrderedDict(
)  # type: OrderedDict[str, ValueUnion]"""
        )
    ]  # type: List[Stripped]

    for prop in cls.properties:
        type_anno = intermediate.beneath_optional(prop.type_annotation)

        prop_name = python_naming.property_name(prop.name)

        # NOTE (mristin, 2023-03-09):
        # We explicitly use meta-model names for properties, not the Python
        # names! This is necessary for the downstream serialization phase.
        prop_name_literal = python_common.string_literal(prop.name)

        block = None  # type: Optional[Stripped]

        if (
                isinstance(type_anno, intermediate.PrimitiveTypeAnnotation)
                or (
                isinstance(type_anno, intermediate.OurTypeAnnotation)
                and isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive)
        )
        ):
            primitive_type = intermediate.try_primitive_type(type_anno)
            assert primitive_type is not None

            block = Stripped(
                f"""\
properties[{prop_name_literal}] = (
{I}that.{prop_name}
)"""
            )

        elif isinstance(type_anno, intermediate.OurTypeAnnotation):
            our_type = type_anno.our_type

            if isinstance(our_type, intermediate.Enumeration):
                block = Stripped(
                    f"""\
properties[{prop_name_literal}] = (
{I}that.{prop_name}.value
)"""
                )

            elif isinstance(our_type, intermediate.ConstrainedPrimitive):
                raise AssertionError("Should have been handled before")

            elif isinstance(
                    our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
            ):
                block = Stripped(
                    f"""\
properties[{prop_name_literal}] = (
{I}self.transform(that.{prop_name})
)"""
                )

            else:
                assert_never(our_type)

        elif isinstance(type_anno, intermediate.ListTypeAnnotation):
            assert isinstance(
                type_anno.items, intermediate.OurTypeAnnotation
            ) and isinstance(type_anno.items.our_type, intermediate.Class), (
                "(mristin, 2023-03-09) We handle only lists of classes in "
                "the generation at the moment. The meta-model does not contain "
                "any other lists, so we wanted to keep the code as simple as "
                "possible, and avoid unrolling. Please contact the developers "
                "if you need this feature."
            )

            block = Stripped(
                f"""\
properties[{prop_name_literal}] = (
{I}ListOfInstances(
{II}[
{III}self.transform(item)
{III}for item in that.{prop_name}
{II}]
{I})
)"""
            )

        else:
            assert_never(type_anno)

        assert block is not None

        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            block = Stripped(
                f"""\
if that.{prop_name} is not None:
{I}{indent_but_first_line(block, I)}"""
            )

        blocks.append(block)

    # NOTE (mristin, 2023-03-09):
    # We explicitly format the model type as a name according to aas-core-meta, and
    # *not* according to JSON or XML schema. This canonical format is necessary since
    # we need to adequately further transform it in the downstream serialization.
    blocks.append(
        Stripped(
            f"""\
return Instance(
{I}properties=properties,
{I}model_type=Identifier(
{II}{python_common.string_literal(cls.name)}
{I})
)"""
        )
    )

    body = "\n\n".join(blocks)

    transform_name = python_naming.method_name(
        Identifier(f"transform_{cls.name}")
    )
    cls_name = python_naming.class_name(cls.name)

    return Stripped(
        f"""\
def {transform_name}(
{I}self,
{I}that: aas_types.{cls_name}
) -> Instance:
{I}{indent_but_first_line(body, I)}"""
    )


def _generate_preserializer(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate the preserializer as a transformer."""
    methods = []  # type: List[Stripped]
    for our_type in symbol_table.our_types:
        if not isinstance(our_type, intermediate.ConcreteClass):
            continue

        methods.append(_generate_transform(cls=our_type))

    body = "\n\n".join(methods)

    return Stripped(
        f"""\
class _Preserializer(
{I}aas_types.AbstractTransformer[Instance]
):
{I}\"\"\"Transform instances to a pre-serialized representation.\"\"\"
{I}{indent_but_first_line(body, I)}"""
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate(
        symbol_table: intermediate.SymbolTable
) -> Tuple[Optional[Stripped], Optional[str]]:
    """Generate the module."""
    warning = dev_scripts.codegen.common.generate_warning(__file__)

    blocks = [
        Stripped('"""Pre-serialize the instances for further modification."""'),
        warning,
        Stripped(
            f"""\
import collections
import json
from typing import (
{I}Any,
{I}get_args,
{I}List,
{I}MutableMapping,
{I}OrderedDict,
{I}Union
)

from aas_core_codegen.common import Identifier, assert_never

from aas_core3 import types as aas_types"""
        )
    ]

    blocks.extend(
        _generate_preserialization_classes()
    )

    blocks.extend(
        [
            _generate_preserializer(symbol_table=symbol_table),
            Stripped("_PRESERIALIZER = _Preserializer()"),
            Stripped(
                f"""\
def preserialize(
{I}that: aas_types.Class
) -> Instance:
{I}\"\"\"Pre-serialize ``that`` instance for further modification.\"\"\"
{I}return _PRESERIALIZER.transform(that)"""
            ),
            warning
        ]
    )

    return Stripped("\n\n\n".join(blocks)), None


def generate_and_write() -> Optional[str]:
    """Generate the code and write it to the pre-defined file."""
    # fmt: off
    symbol_table, _ = (
        aas_core3_0_testgen.common.load_symbol_table_and_infer_constraints_for_schema()
    )
    # fmt: on

    code, error = _generate(symbol_table)
    if error is not None:
        return error

    path = _REPO_DIR / "aas_core3_0_testgen" / "codegened" / "preserialization.py"
    path.write_text(code + "\n")


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.parse_args()

    error = generate_and_write()
    if error is not None:
        print(error, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
