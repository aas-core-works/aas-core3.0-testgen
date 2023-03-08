"""Generate the creation functions based on the meta-model."""

import argparse
import enum
import os
import pathlib
import sys
from typing import Union, List, Optional, Sequence, Tuple

from aas_core_codegen.common import (
    Stripped, indent_but_first_line, Identifier, assert_never
)
from aas_core_codegen import intermediate, infer_for_schema
from aas_core_codegen.python import (
    common as python_common,
    naming as python_naming
)
from aas_core_codegen.python.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III
)

# TODO (mristin, 2023-03-8): generate_concrete_create_minimal

# TODO (mristin, 2023-03-8): generate MINIMAL_TO_CONCRETE_MINIMAL

# TODO (mristin, 2023-03-8): generate pick_literal_of_{enum}(path_hash)

# TODO (mristin, 2023-03-8): generate pick_item_of_{constant enum set}(path_hash)

# TODO (mristin, 2023-03-8): generate pick_item_of_{constant value set}(path_hash)
from icontract import ensure, require


class CreationKind(enum.Enum):
    MINIMAL = 0
    MAXIMAL = 1


PRIMITIVE_TYPE_TO_PRIMITIVING_FUNCTION = {
    intermediate.PrimitiveType.BOOL: "primitiving.generate_bool",
    intermediate.PrimitiveType.INT: "primitiving.generate_int64",
    intermediate.PrimitiveType.FLOAT: "primitiving.generate_float",
    intermediate.PrimitiveType.STR: "primitiving.generate_str",
    intermediate.PrimitiveType.BYTEARRAY: "primitiving.generate_bytes",
}
assert all(
    a_type in PRIMITIVE_TYPE_TO_PRIMITIVING_FUNCTION
    for a_type in intermediate.PrimitiveType
)


def _generate_primitive_value_out_of_set(
        set_of_primitives_constraint: infer_for_schema.SetOfPrimitivesConstraint
) -> Stripped:
    """Generate the code to pick a random value out of the inferred set."""
    literals = []  # type: List[Stripped]
    for literal in set_of_primitives_constraint.literals:
        if isinstance(literal.value, (bool, int, float, str)):
            literals.append(Stripped(repr(literal.value)))
        elif isinstance(literal.value, bytearray):
            literals.append(Stripped(repr(bytes(literal.value))))
        else:
            assert_never(literal)

    if len(literals) == 0:
        return Stripped("[]")
    elif len(literals) == 1:
        return Stripped(f"[{literals[0]}]")
    else:
        literals_joined = ",\n".join(literals)
        return Stripped(
            f"""\
[
{I}{indent_but_first_line(literals_joined, I)}
]"""
        )


@require(
    lambda prop, primitive_type:
    intermediate.try_primitive_type(
        intermediate.beneath_optional(prop.type_annotation)
    ) is primitive_type
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_primitive_property_value(
        prop: intermediate.Property,
        primitive_type: intermediate.PrimitiveType,
        len_constraint: Optional[infer_for_schema.LenConstraint],
        pattern_constraints: Optional[Sequence[infer_for_schema.PatternConstraint]],
        set_of_primitives_constraint: Optional[
            infer_for_schema.SetOfPrimitivesConstraint],
) -> Tuple[Optional[Stripped], Optional[str]]:
    """Generate the code to generate a primitive value."""
    if set_of_primitives_constraint is not None:
        return _generate_primitive_value_out_of_set(set_of_primitives_constraint), None

    if (
            primitive_type in (
            intermediate.PrimitiveType.BOOL,
            intermediate.PrimitiveType.INT,
            intermediate.PrimitiveType.FLOAT
    )
    ):
        if len_constraint is not None:
            return None, (
                f"Unexpected len constraint on {primitive_type.name}: {len_constraint}"
            )

    if (
            primitive_type in (
            intermediate.PrimitiveType.BOOL,
            intermediate.PrimitiveType.INT,
            intermediate.PrimitiveType.FLOAT,
            intermediate.PrimitiveType.BYTEARRAY,
    )
    ):
        if pattern_constraints is not None:
            pattern_constraints_str = ", ".join(
                str(pattern_constraint)
                for pattern_constraint in pattern_constraints
            )
            return None, (
                f"Unexpected pattern constraint(s) on {primitive_type.name}: "
                f"{pattern_constraints_str}"
            )

    prop_name_literal = python_common.string_literal(prop.name)

    if (
            primitive_type in (
            intermediate.PrimitiveType.BOOL,
            intermediate.PrimitiveType.INT,
            intermediate.PrimitiveType.FLOAT
    )
    ):
        primitiving_function = PRIMITIVE_TYPE_TO_PRIMITIVING_FUNCTION[primitive_type]

        return Stripped(
            f"""\
{primitiving_function}(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I})
)"""
        ), None

    elif primitive_type is intermediate.PrimitiveType.STR:
        pattern_constraint = None  # type: Optional[infer_for_schema.PatternConstraint]
        if pattern_constraints is not None:
            # NOTE (mristin, 2023-03-01):
            # We drop the constraint for XML serializable strings since it permeates
            # all the specification. However, once we drop it, all the types have a single
            # constraint.
            pattern_constraints_without_xml = [
                pattern_constraint
                for pattern_constraint in pattern_constraints
                if pattern_constraint.pattern
                   !=
                   '^[\\x09\\x0A\\x0D\\x20-\\uD7FF\\uE000-\\uFFFD\\U00010000-\\U0010FFFF]*$'
            ]

            if len(pattern_constraints_without_xml) > 1:
                pattern_constraints_joined = ", ".join(str(pattern_constraints))
                return None, (
                    f"(mristin, 2023-03-08): Currently, we only support frozen "
                    f"examples for a single constraint. However, two or more "
                    f"more pattern constraints had to be satisfied: "
                    f"{pattern_constraints_joined}"
                )

            pattern_constraint = pattern_constraints_without_xml[0]

        if pattern_constraint is not None:
            pattern_literal = python_common.string_literal(pattern_constraint.pattern)
            return Stripped(
                f"""\
primitiving.generate_str_satisfying_pattern(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I}),
{I}{pattern_literal}
)"""
            ), None

        if len_constraint is not None:
            return Stripped(
                f"""\
primitiving.generate_str(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I}),
{I}min_len={repr(len_constraint.min_value)},
{I}max_len={repr(len_constraint.max_value)}
)"""
            ), None

        return Stripped(
            f"""\
primitiving.generate_str(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I})
)"""
        ), None

    elif primitive_type is intermediate.PrimitiveType.BYTEARRAY:
        if len_constraint is not None:
            return Stripped(
                f"""\
primitiving.generate_bytes(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I}),
{I}min_len={repr(len_constraint.min_value)},
{I}max_len={repr(len_constraint.max_value)}
)"""
            ), None

        return Stripped(
            f"""\
primitiving.generate_bytes(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I})
)"""
        ), None

    else:
        assert_never(primitive_type)


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_property_value(
        prop: intermediate.Property,
        len_constraint: Optional[infer_for_schema.LenConstraint],
        pattern_constraints: Optional[Sequence[infer_for_schema.PatternConstraint]],
        set_of_primitives_constraint: Optional[
            infer_for_schema.SetOfPrimitivesConstraint],
        set_of_enumeration_literals_constraint: Optional[
            infer_for_schema.SetOfEnumerationLiteralsConstraint
        ]
) -> Tuple[Optional[Stripped], Optional[str]]:
    """
    Generate the snippet to generate a value for the property.

    We ignore the constraints if they do not apply to the property type.
    """
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    if (
            isinstance(type_anno, intermediate.PrimitiveTypeAnnotation)
            or (
            isinstance(type_anno, intermediate.OurType)
            and isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive)
    )
    ):
        primitive_type = intermediate.try_primitive_type(type_anno)
        assert primitive_type is not None

        block, error = _generate_primitive_property_value(
            prop=prop,
            primitive_type=primitive_type,
            len_constraint=len_constraint,
            pattern_constraints=pattern_constraints,
            set_of_primitives_constraint=set_of_primitives_constraint
        )

        if error is not None:
            return None, (
                f"Failed to generate the generation code "
                f"for the property {prop.name!r}: {error}"
            )

        assert block is not None
        return block, None
    # TODO (mristin, 2023-03-8): continue here once done with primitive values
    else:
        assert_never(type_anno)


def generate_concrete_constructor(
        cls: intermediate.ConcreteClass,
        creation_kind: CreationKind,

) -> Stripped:
    """Generate the code to create the minimal instance."""
    arguments = []  # type: List[Stripped]
    for arg in cls.constructor.arguments:
        if (
                isinstance(arg.type_annotation, intermediate.OptionalTypeAnnotation)
                and creation_kind is CreationKind.MINIMAL
        ):
            continue

        type_anno = intermediate.beneath_optional(arg.type_annotation)

        arg_name = python_naming.argument_name(arg.name)
        arg_name_literal = python_common.string_literal(arg.name)

        if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
            primitiving_function = PRIMITIVE_TYPE_TO_PRIMITIVING_FUNCTION[
                type_anno.a_type
            ]

            arguments.append(
                Stripped(
                    f"""\
{arg_name}={primitiving_function}(
{I}hash_path(
{II}path_hash,
{II}{arg_name_literal}
{I})
)"""
                )
            )


def generate_create_minimal(
        cls: Union[intermediate.AbstractClass, intermediate.ConcreteClass]
) -> Stripped:
    """Generate the function to generate the minimal instance of the ``cls``."""
    blocks = []  # type: List[Stripped]

    if len(cls.concrete_descendants) > 0:
        cls_name = cls.name
        blocks.append(
            Stripped(
                f"""\
concrete_minimal_functions = MINIMAL_TO_CONCRETE_MINIMAL[
{I}{python_common.string_literal(cls_name)}
]
concrete_minimal_function = concrete_minimal_functions[
{I}common.int_digest(prefix_hash) % concrete_minimal_functions
]
return concrete_minimal_function(prefix_hash)"""
            )
        )
    else:


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.parse_args()

    repo_dir = pathlib.Path(os.path.realpath(__file__)).parent.parent

    return 0


if __name__ == "__main__":
    sys.exit(main())
