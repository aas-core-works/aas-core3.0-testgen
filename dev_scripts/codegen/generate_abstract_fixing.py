"""Generate the code to pre-serialize instances for further modification."""

import argparse
import os
import pathlib
import sys
from typing import List, Optional, Tuple

from aas_core_codegen import intermediate
from aas_core_codegen.common import (
    Stripped,
    indent_but_first_line,
    assert_never,
    Identifier,
)
from aas_core_codegen.python import common as python_common, naming as python_naming
from aas_core_codegen.python.common import INDENT as I, INDENT2 as II, INDENT3 as III
from icontract import ensure

import aas_core3_0_testgen.common
import dev_scripts.codegen.common
import dev_scripts.codegen.ontology


def _generate_fix_method(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate an empty fix method for ``cls``."""
    method_name = python_naming.method_name(Identifier(f"_fix_{cls.name}"))
    cls_name = python_naming.class_name(cls.name)

    return Stripped(
        f"""\
def {method_name}(
{I}self,
{I}that: aas_types.{cls_name},
{I}path_hash: common.CanHash
) -> None:
{I}\"\"\"
{I}Fix ``that`` instance in-place.

{I}Do *not* recurse into children. This is handled by ``visit_**`` methods since
{I}we have to couple the path hash and property names.
{I}\"\"\"
{I}# Intentionally empty, to be overridden
{I}return"""
    )


def _generate_visit_method(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate the visit method that fixes the instances and recurses into children."""
    fix_method = python_naming.method_name(Identifier(f"_fix_{cls.name}"))
    blocks = [Stripped(f"self.{fix_method}(that, context)")]

    for prop in cls.properties:
        type_anno = intermediate.beneath_optional(prop.type_annotation)

        prop_name = python_naming.property_name(prop.name)
        prop_name_literal = python_common.string_literal(prop_name)

        block = None  # type: Optional[Stripped]

        if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
            # No descent into primitive values.
            continue
        elif isinstance(type_anno, intermediate.OurTypeAnnotation):
            if isinstance(type_anno.our_type, intermediate.Enumeration):
                # No descent into enumerations.
                continue
            elif isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive):
                # No descent into primitive values.
                continue

            elif isinstance(
                type_anno.our_type,
                (intermediate.AbstractClass, intermediate.ConcreteClass),
            ):

                block = Stripped(
                    f"""\
self.visit_with_context(
{I}that.{prop_name},
{I}common.hash_path(
{II}context,
{II}{prop_name_literal}
{I})
)"""
                )
            else:
                assert_never(type_anno.our_type)

        elif isinstance(type_anno, intermediate.ListTypeAnnotation):
            assert isinstance(type_anno.items, intermediate.OurTypeAnnotation), (
                f"NOTE (mristin, 2023-03-10): We expect only lists of our types "
                f"at the moment, but you specified {type_anno}. "
                f"Please contact the developers if you need this feature."
            )

            prop_hash_var = python_naming.variable_name(
                Identifier(f"hash_for_{prop.name}")
            )

            block = Stripped(
                f"""\
{prop_hash_var} = common.hash_path(
{I}context,
{I}{prop_name_literal}
)
for i, item_of_{prop_name} in enumerate(
{II}that.{prop_name}
):
{I}self.visit_with_context(
{II}item_of_{prop_name},
{II}common.hash_path(
{III}{prop_hash_var},
{III}i
{II})
{I})"""
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

    body = "\n\n".join(blocks)

    method_name = python_naming.method_name(
        Identifier(f"visit_{cls.name}_with_context")
    )
    cls_name = python_naming.class_name(cls.name)

    return Stripped(
        f"""\
def {method_name}(
{I}self,
{I}that: aas_types.{cls_name},
{I}context: common.CanHash
) -> None:
{I}{indent_but_first_line(body, I)}"""
    )


def _generate_abstract_handyman(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate an abstract handyman that you fill out to fix instances."""
    methods = []  # type: List[Stripped]
    for our_type in symbol_table.our_types:
        if not isinstance(our_type, intermediate.ConcreteClass):
            continue

        methods.append(_generate_fix_method(cls=our_type))

    for our_type in symbol_table.our_types:
        if not isinstance(our_type, intermediate.ConcreteClass):
            continue

        methods.append(_generate_visit_method(cls=our_type))

    body = "\n\n".join(methods)

    return Stripped(
        f"""\
class AbstractHandyman(aas_types.AbstractVisitorWithContext[common.CanHash]):
{I}\"\"\"Fix instances recursively on best-effort basis.\"\"\"

{I}{indent_but_first_line(body, I)}"""
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate(
    symbol_table: intermediate.SymbolTable,
) -> Tuple[Optional[Stripped], Optional[str]]:
    """Generate the module."""
    warning = dev_scripts.codegen.common.generate_warning(os.path.realpath(__file__))

    blocks = [
        Stripped('"""Provide an abstract structure for fixing model instances."""'),
        warning,
        Stripped(
            """\
from aas_core3_0_testgen import common
from aas_core3 import types as aas_types"""
        ),
        _generate_abstract_handyman(symbol_table=symbol_table),
        warning,
    ]

    return Stripped("\n\n\n".join(blocks)), None


def generate_and_write(
    model_path: pathlib.Path, codegened_dir: pathlib.Path
) -> Optional[str]:
    """Generate the code and write it to the pre-defined file."""
    # fmt: off
    symbol_table, _ = (
        aas_core3_0_testgen.common.load_symbol_table_and_infer_constraints_for_schema(
            model_path=model_path
        )
    )
    # fmt: on

    code, error = _generate(symbol_table)
    if error is not None:
        return error

    assert code is not None

    path = codegened_dir / "abstract_fixing.py"
    path.write_text(code + "\n", encoding="utf-8")

    return None


def main() -> int:
    """Execute the main routine."""
    repo_dir = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_path", help="path to the meta-model", required=True)
    parser.add_argument(
        "--codegened_dir",
        help="path to the directory containing the generated code",
        default=str(repo_dir / "aas_core3_0_testgen" / "codegened"),
    )
    args = parser.parse_args()

    model_path = pathlib.Path(args.model_path)
    codegened_dir = pathlib.Path(args.codegened_dir)

    error = generate_and_write(model_path=model_path, codegened_dir=codegened_dir)
    if error is not None:
        print(error, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
