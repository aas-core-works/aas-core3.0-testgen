"""Generate the creation functions based on the meta-model."""

import argparse
import enum
import os
import pathlib
import sys
from typing import Union, List, Optional, Sequence, Tuple, Mapping

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

    assert len(literals) > 0

    if len(literals) == 1:
        return Stripped(f"[{literals[0]}]")

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
    prop_name_literal = python_common.string_literal(prop.name)

    if set_of_primitives_constraint is not None:
        literals_literal = _generate_primitive_value_out_of_set(
            set_of_primitives_constraint
        )

        return Stripped(
            f"""\
primitiving.choose_value(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I}),
{I}{indent_but_first_line(literals_literal, I)}
)"""
        ), None

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


def _generate_enumeration_literal(
        prop: intermediate.Property,
        set_of_enumeration_literals_constraint: Optional[
            infer_for_schema.SetOfEnumerationLiteralsConstraint
        ]
) -> Stripped:
    """Generate the code for literal generation."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)
    assert isinstance(type_anno, intermediate.OurTypeAnnotation)
    assert isinstance(type_anno.our_type, intermediate.Enumeration)

    enumeration = type_anno.our_type

    prop_name_literal = python_common.string_literal(prop.name)

    if set_of_enumeration_literals_constraint is not None:
        enum_name = python_naming.enum_name(enumeration.name)
        literals = [
            f"aas_types.{enum_name}.{python_naming.enum_literal_name(literal.name)}"
            for literal in set_of_enumeration_literals_constraint.literals
        ]
        assert len(literals) > 0

        if len(literals) == 1:
            literals_literal = f"[{literals[0]}]"
        else:
            literals_joined = ",\n".join(literals)
            literals_literal = f"""\
[
{I}{indent_but_first_line(literals_joined, I)}
]"""

        return Stripped(
            f"""\
primitiving.choose_value(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I}),
{I}{indent_but_first_line(literals_literal, I)}
)"""
        )

    pick_function_name = python_naming.function_name(
        Identifier(f"pick_{enumeration.name}")
    )

    return Stripped(
        f"""\
{pick_function_name}(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I})
)"""
    )


def _generate_minimal_instance(prop: intermediate.Property) -> Stripped:
    """Generate the code to create a minimal instance as the property value."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)
    assert isinstance(type_anno, intermediate.OurTypeAnnotation)
    assert isinstance(type_anno.our_type, intermediate.Class)

    cls = type_anno.our_type

    minimal_function_name = python_naming.function_name(
        Identifier(f"minimal_{cls.name}")
    )

    prop_name_literal = python_common.string_literal(prop.name)

    return Stripped(
        f"""\
{minimal_function_name}(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I})
)"""
    )


def _generate_list_of_instances(
        prop: intermediate.Property,
        len_constraint: Optional[infer_for_schema.LenConstraint],
) -> Stripped:
    """Generate the code to generate a list of instances."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    assert isinstance(type_anno, intermediate.ListTypeAnnotation)
    assert (
            isinstance(type_anno.items, intermediate.OurTypeAnnotation)
            and isinstance(type_anno.items.our_type, intermediate.Class)
    )

    cls = type_anno.items.our_type

    prop_name_literal = python_common.string_literal(prop.name)

    minimal_function_name = python_naming.function_name(
        Identifier(f"minimal_{cls.name}")
    )

    count = 1
    if len_constraint is not None:
        if len_constraint.min_value is not None:
            count = len_constraint.min_value

        if len_constraint.max_value == 0:
            count = 0



    if count == 0:
        return Stripped("[]")
    elif count == 1:
        return Stripped(
            f"""\
[
{I}{minimal_function_name}(
{II}common.hash_path(
{III}path_hash,
{III}{prop_name_literal}
{II})
{I})
]"""
        )
    else:
        return Stripped(
            f"""\
[
{I}{minimal_function_name}(
{II}common.hash_path(
{III}path_hash,
{III}[{prop_name_literal}, i]
{II})
{I})
{I}for i in range({count})
]"""
)

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
    elif isinstance(type_anno, intermediate.OurTypeAnnotation):
        our_type = type_anno.our_type

        if isinstance(our_type, intermediate.Enumeration):
            block = _generate_enumeration_literal(
                prop,
                set_of_enumeration_literals_constraint
            )
            return block, None
        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            raise AssertionError("Should have been handled before")

        elif isinstance(
                our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            block = _generate_minimal_instance(prop)
            return block, None

        else:
            assert_never(our_type)
    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        assert isinstance(
            type_anno.items, intermediate.OurTypeAnnotation
        ) and isinstance(type_anno.items.our_type, intermediate.Class), (
            "(mristin, 2023-03-08) We handle only lists of classes in the generation "
            "at the moment. The meta-model does not contain "
            "any other lists, so we wanted to keep the code as simple as "
            "possible, and avoid unrolling. Please contact the developers "
            "if you need this feature."
        )

        block = _generate_list_of_instances(prop, len_constraint)
        return block, None
    else:
        assert_never(type_anno)


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def generate_concrete_constructor_call(
        cls: intermediate.ConcreteClass,
        creation_kind: CreationKind,
        constraints_by_class: Mapping[
            intermediate.ClassUnion,
            infer_for_schema.ConstraintsByProperty
        ]
) -> Tuple[Optional[Stripped], Optional[str]]:
    """Generate the code to create the instance."""
    # fmt: off
    assert (
            sorted(
                (arg.name, str(arg.type_annotation))
                for arg in cls.constructor.arguments
            ) == sorted(
        (prop.name, str(prop.type_annotation))
        for prop in cls.properties
    )
    ), (
        "(mristin, 2023-03-08) We assume that the properties and constructor arguments "
        "are identical at this point. If this is not the case, we have to re-write the "
        "logic substantially! Please contact the developers if you see this."
    )
    # fmt: on

    arguments = []  # type: List[Stripped]
    for prop in cls.properties:
        if (
                isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation)
                and creation_kind is CreationKind.MINIMAL
        ):
            continue

        arg_name = python_naming.argument_name(prop.name)
        arg_name_literal = python_common.string_literal(prop.name)

        constraints_by_prop = constraints_by_class[cls]

        # fmt: off
        value_code, error = _generate_property_value(
            prop=prop,
            len_constraint=constraints_by_prop.len_constraints_by_property.get(
                prop, None
            ),
            pattern_constraints=constraints_by_prop.patterns_by_property.get(
                prop, None
            ),
            set_of_primitives_constraint=(
                    constraints_by_prop.set_of_primitives_by_property.get(
                    prop, None
                )
            ),
            set_of_enumeration_literals_constraint=(
                constraints_by_prop.set_of_enumeration_literals_by_property(
                    prop, None
                )
            )
        )
        # fmt: on

        if error is not None:
            return None, error

        assert value_code is not None

        arguments.append(
            Stripped(
                    f"""\
{arg_name}=(
{I}{indent_but_first_line(value_code, I)}
)"""
                )
            )

    # TODO (mristin, 2023-03-8): continue here
    # TODO (mristin, 2023-03-8): add call to constructor
    # TODO (mristin, 2023-03-8): return


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
