"""Generate the creation functions based on the meta-model."""

import argparse
import enum
import os
import pathlib
import sys
from typing import Union, List, Optional, Sequence, Tuple, Mapping

from aas_core_codegen.common import (
    Stripped,
    indent_but_first_line,
    Identifier,
    assert_never,
)
from aas_core_codegen import intermediate, infer_for_schema
from aas_core_codegen.python import common as python_common, naming as python_naming
from aas_core_codegen.python.common import INDENT as I, INDENT2 as II, INDENT3 as III
from icontract import ensure, require

import aas_core3_0_testgen.common

import dev_scripts.codegen.common


class CreationKind(enum.Enum):
    """Represent different kinds of creation functions."""

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
    set_of_primitives_constraint: infer_for_schema.SetOfPrimitivesConstraint,
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
    lambda prop, primitive_type: intermediate.try_primitive_type(
        intermediate.beneath_optional(prop.type_annotation)
    )
    is primitive_type
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_primitive_property_value(
    prop: intermediate.Property,
    primitive_type: intermediate.PrimitiveType,
    len_constraint: Optional[infer_for_schema.LenConstraint],
    pattern_constraints: Optional[Sequence[infer_for_schema.PatternConstraint]],
    set_of_primitives_constraint: Optional[infer_for_schema.SetOfPrimitivesConstraint],
) -> Tuple[Optional[Stripped], Optional[str]]:
    """Generate the code to generate a primitive value."""
    prop_name_literal = python_common.string_literal(prop.name)

    if set_of_primitives_constraint is not None:
        literals_literal = _generate_primitive_value_out_of_set(
            set_of_primitives_constraint
        )

        return (
            Stripped(
                f"""\
primitiving.choose_value(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I}),
{I}{indent_but_first_line(literals_literal, I)}
)"""
            ),
            None,
        )

    if primitive_type in (
        intermediate.PrimitiveType.BOOL,
        intermediate.PrimitiveType.INT,
        intermediate.PrimitiveType.FLOAT,
    ):
        if len_constraint is not None:
            return None, (
                f"Unexpected len constraint on {primitive_type.name}: {len_constraint}"
            )

    if primitive_type in (
        intermediate.PrimitiveType.BOOL,
        intermediate.PrimitiveType.INT,
        intermediate.PrimitiveType.FLOAT,
        intermediate.PrimitiveType.BYTEARRAY,
    ):
        if pattern_constraints is not None:
            pattern_constraints_str = ", ".join(
                str(pattern_constraint) for pattern_constraint in pattern_constraints
            )
            return None, (
                f"Unexpected pattern constraint(s) on {primitive_type.name}: "
                f"{pattern_constraints_str}"
            )

    if (
        primitive_type is intermediate.PrimitiveType.BOOL
        or primitive_type is intermediate.PrimitiveType.INT
        or primitive_type is intermediate.PrimitiveType.FLOAT
    ):
        primitiving_function = PRIMITIVE_TYPE_TO_PRIMITIVING_FUNCTION[primitive_type]

        return (
            Stripped(
                f"""\
{primitiving_function}(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I})
)"""
            ),
            None,
        )

    elif primitive_type is intermediate.PrimitiveType.STR:
        pattern_constraint = None  # type: Optional[infer_for_schema.PatternConstraint]
        if pattern_constraints is not None:
            # NOTE (mristin, 2023-03-01):
            # We drop the constraint for XML serializable strings since it permeates
            # all the specification. However, once we drop it, all the types have a single
            # constraint.
            # noinspection SpellCheckingInspection
            pattern_constraints_without_xml = [
                pattern_constraint
                for pattern_constraint in pattern_constraints
                if pattern_constraint.pattern
                != "^[\\x09\\x0A\\x0D\\x20-\\uD7FF\\uE000-\\uFFFD\\U00010000-\\U0010FFFF]*$"
            ]

            if len(pattern_constraints_without_xml) > 1:
                pattern_constraints_joined = ", ".join(str(pattern_constraints))
                return None, (
                    f"(mristin, 2023-03-08): Currently, we only support frozen "
                    f"examples for a single constraint. However, two or more "
                    f"more pattern constraints had to be satisfied: "
                    f"{pattern_constraints_joined}"
                )

            assert len(pattern_constraints_without_xml) <= 1

            if len(pattern_constraints_without_xml) == 1:
                pattern_constraint = pattern_constraints_without_xml[0]

        if pattern_constraint is not None:
            pattern_literal = python_common.string_literal(pattern_constraint.pattern)
            return (
                Stripped(
                    f"""\
primitiving.generate_str_satisfying_pattern(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I}),
{I}{pattern_literal}
)"""
                ),
                None,
            )

        if len_constraint is not None:
            return (
                Stripped(
                    f"""\
primitiving.generate_str(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I}),
{I}min_len={repr(len_constraint.min_value)},
{I}max_len={repr(len_constraint.max_value)}
)"""
                ),
                None,
            )

        return (
            Stripped(
                f"""\
primitiving.generate_str(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I})
)"""
            ),
            None,
        )

    elif primitive_type is intermediate.PrimitiveType.BYTEARRAY:
        if len_constraint is not None:
            return (
                Stripped(
                    f"""\
primitiving.generate_bytes(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I}),
{I}min_len={repr(len_constraint.min_value)},
{I}max_len={repr(len_constraint.max_value)}
)"""
                ),
                None,
            )

        return (
            Stripped(
                f"""\
primitiving.generate_bytes(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I})
)"""
            ),
            None,
        )

    else:
        assert_never(primitive_type)


def _generate_enumeration_literal(
    prop: intermediate.Property,
    set_of_enumeration_literals_constraint: Optional[
        infer_for_schema.SetOfEnumerationLiteralsConstraint
    ],
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

    enum_name = python_naming.enum_name(enumeration.name)

    return Stripped(
        f"""\
primitiving.choose_value(
{I}common.hash_path(
{II}path_hash,
{II}{prop_name_literal}
{I}),
{I}list(aas_types.{enum_name})
)"""
    )


def _generate_call_to_create_minimal(prop: intermediate.Property) -> Stripped:
    """Generate the code to create a minimal instance as the property value."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)
    assert isinstance(type_anno, intermediate.OurTypeAnnotation)
    assert isinstance(type_anno.our_type, intermediate.Class)

    cls = type_anno.our_type

    function_name = python_naming.function_name(Identifier(f"minimal_{cls.name}"))

    prop_name_literal = python_common.string_literal(prop.name)

    return Stripped(
        f"""\
{function_name}(
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
    assert isinstance(type_anno.items, intermediate.OurTypeAnnotation) and isinstance(
        type_anno.items.our_type, intermediate.Class
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
    set_of_primitives_constraint: Optional[infer_for_schema.SetOfPrimitivesConstraint],
    set_of_enumeration_literals_constraint: Optional[
        infer_for_schema.SetOfEnumerationLiteralsConstraint
    ],
) -> Tuple[Optional[Stripped], Optional[str]]:
    """
    Generate the snippet to generate a value for the property.

    We ignore the constraints if they do not apply to the property type.
    """
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation) or (
        isinstance(type_anno, intermediate.OurTypeAnnotation)
        and isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive)
    ):
        primitive_type = intermediate.try_primitive_type(type_anno)
        assert primitive_type is not None

        block, error = _generate_primitive_property_value(
            prop=prop,
            primitive_type=primitive_type,
            len_constraint=len_constraint,
            pattern_constraints=pattern_constraints,
            set_of_primitives_constraint=set_of_primitives_constraint,
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
                prop, set_of_enumeration_literals_constraint
            )
            return block, None
        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            raise AssertionError("Should have been handled before")

        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            block = _generate_call_to_create_minimal(prop)
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
def _generate_concrete_constructor_call(
    cls: intermediate.ConcreteClass,
    creation_kind: CreationKind,
    constraints_by_property: infer_for_schema.ConstraintsByProperty,
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

        # fmt: off
        value_code, error = _generate_property_value(
            prop=prop,
            len_constraint=constraints_by_property.len_constraints_by_property.get(
                prop, None
            ),
            pattern_constraints=constraints_by_property.patterns_by_property.get(
                prop, None
            ),
            set_of_primitives_constraint=(
                    constraints_by_property.set_of_primitives_by_property.get(
                    prop, None
                )
            ),
            set_of_enumeration_literals_constraint=(
                constraints_by_property.set_of_enumeration_literals_by_property.get(
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

    class_name = python_naming.class_name(cls.name)

    if len(arguments) == 0:
        return Stripped(f"aas_types.{class_name}()"), None

    arguments_joined = ",\n".join(arguments)

    return (
        Stripped(
            f"""\
aas_types.{class_name}(
{I}{indent_but_first_line(arguments_joined, I)}
)"""
        ),
        None,
    )


@require(lambda cls: len(cls.concrete_descendants) > 0)
def _generate_concrete_create_minimal_cls(
    cls: intermediate.ConcreteClass,
    constraints_by_property: infer_for_schema.ConstraintsByProperty,
) -> Tuple[Optional[Stripped], Optional[str]]:
    """Generate the function to be dispatched to create an instance of ``cls``."""
    constructor_call, error = _generate_concrete_constructor_call(
        cls=cls,
        creation_kind=CreationKind.MINIMAL,
        constraints_by_property=constraints_by_property,
    )

    if error is not None:
        return None, error
    assert constructor_call is not None

    function_name = python_naming.function_name(
        Identifier(f"concrete_minimal_{cls.name}")
    )
    cls_name = python_naming.class_name(cls.name)

    body = f"return {constructor_call}"

    return (
        Stripped(
            f"""\
def {function_name}(
{I}path_hash: common.CanHash
) -> aas_types.{cls_name}:
{I}\"\"\"
{I}Generate a minimal instance based on the ``path_hash``.

{I}.. note::

{II}You usually do not call this function directly. It will be dispatched
{II}to.

{I}.. note::

{II}The generated instance satisfies only the type constraints.
{II}That means it can be serialized as-is, but probably violates one or
{II}more meta-model constraints.
{I}\"\"\"
{I}{indent_but_first_line(body, I)}"""
        ),
        None,
    )


def _generate_class_name_to_concrete_minimals(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Generate the dispatching map to minimal functions."""
    items = []  # type: List[Tuple[Stripped, Stripped]]
    for our_type in symbol_table.our_types:
        if not isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            continue

        if len(our_type.concrete_descendants) == 0:
            continue

        concrete_functions = []  # type: List[Stripped]
        if isinstance(our_type, intermediate.ConcreteClass):
            concrete_functions.append(
                python_naming.function_name(
                    Identifier(f"concrete_minimal_{our_type.name}")
                )
            )

        for concrete_descendant in our_type.concrete_descendants:
            concrete_functions.append(
                python_naming.function_name(
                    Identifier(f"minimal_{concrete_descendant.name}")
                )
            )

        concrete_functions_joined = ",\n".join(concrete_functions)
        concrete_functions_literal = Stripped(
            f"""\
[
{I}{indent_but_first_line(concrete_functions_joined, I)}
]"""
        )

        items.append(
            (python_common.string_literal(our_type.name), concrete_functions_literal)
        )

    items_literals = [
        Stripped(
            f"""\
{key}:
{value}"""
        )
        for key, value in items
    ]
    items_literals_joined = ",\n".join(items_literals)

    return Stripped(
        f"""\
_CLASS_NAME_TO_CONCRETE_MINIMALS = {{
{I}{indent_but_first_line(items_literals_joined, I)}
}}  # type: Mapping[str, Sequence[Callable[[common.CanHash], aas_types.Class]]]"""
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_create_minimal_cls(
    cls: Union[intermediate.AbstractClass, intermediate.ConcreteClass],
    constraints_by_property: infer_for_schema.ConstraintsByProperty,
) -> Tuple[Optional[Stripped], Optional[str]]:
    """Generate the function to generate the minimal instance of the ``cls``."""
    # noinspection PyUnusedLocal
    body = None  # type: Optional[Stripped]

    # Class name in Python
    cls_name = python_naming.class_name(cls.name)

    if len(cls.concrete_descendants) > 0:
        body = Stripped(
            f"""\
number = int(path_hash.hexdigest()[:8], base=16)
concrete_minimal_functions = _CLASS_NAME_TO_CONCRETE_MINIMALS[
{I}{python_common.string_literal(cls.name)}
]
concrete_minimal_function = concrete_minimal_functions[
{I}number % len(concrete_minimal_functions)
]
instance = concrete_minimal_function(path_hash)
assert isinstance(
{I}instance,
{I}aas_types.{cls_name},
)
return instance"""
        )
    else:
        if isinstance(cls, intermediate.AbstractClass):
            raise AssertionError(
                f"Unexpected abstract class without concrete descendants: {cls.name!r}"
            )

        constructor_call, error = _generate_concrete_constructor_call(
            cls=cls,
            creation_kind=CreationKind.MINIMAL,
            constraints_by_property=constraints_by_property,
        )

        if error is not None:
            return None, error
        assert constructor_call is not None

        body = Stripped(
            f"""\
return {constructor_call}"""
        )

    function_name = python_naming.function_name(Identifier(f"minimal_{cls.name}"))

    assert body is not None
    return (
        Stripped(
            f"""\
def {function_name}(
{I}path_hash: common.CanHash
) -> aas_types.{cls_name}:
{I}\"\"\"
{I}Generate a minimal instance based on the ``path_hash``.

{I}.. note::

{II}The generated instance satisfies only the type constraints.
{II}That means it can be serialized as-is, but probably violates one or
{II}more meta-model constraints.
{I}\"\"\"
{I}{indent_but_first_line(body, I)}"""
        ),
        None,
    )


def _generate_class_name_to_exact_concrete_minimal(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Generate the dispatching map to the exact concrete minimal function."""
    items = []  # type: List[Tuple[Stripped, Stripped]]
    for our_type in symbol_table.our_types:
        if not isinstance(our_type, intermediate.ConcreteClass):
            continue

        if len(our_type.concrete_descendants) > 0:
            concrete_minimal_function = python_naming.function_name(
                Identifier(f"concrete_minimal_{our_type.name}")
            )
        else:
            concrete_minimal_function = python_naming.function_name(
                Identifier(f"minimal_{our_type.name}")
            )

        items.append(
            (python_common.string_literal(our_type.name), concrete_minimal_function)
        )

    items_literals = [
        Stripped(
            f"""\
{key}:
{value}"""
        )
        for key, value in items
    ]
    items_literals_joined = ",\n".join(items_literals)

    return Stripped(
        f"""\
_CLASS_NAME_TO_EXACT_CONCRETE_MINIMAL = {{
{I}{indent_but_first_line(items_literals_joined, I)}
}}"""
    )


def _generate_create_exact_concrete_minimal() -> Stripped:
    """Generate the function to generate the minimal instance based on a class name."""
    return Stripped(
        f"""\
def exact_concrete_minimal(
{I}path_hash: common.CanHash,
{I}class_name: str
) -> aas_types.Class:
{I}\"\"\"
{I}Create a minimal instance of exactly ``class_name``.

{I}.. note::

{II}The generated instance satisfies only the type constraints.
{II}That means it can be serialized as-is, but probably violates one or
{II}more meta-model constraints.
{I}\"\"\"
{I}dispatch = _CLASS_NAME_TO_EXACT_CONCRETE_MINIMAL.get(class_name, None)
{I}if dispatch is None:
{II}raise KeyError(
{III}f"The class name {{class_name!r}} does not denote a concrete class "
{III}f"in the meta-model. Did you spell its name in the format of "
{III}f"aas-core-meta (*not* Python)?"
{II})
{I}return dispatch(path_hash)"""
    )


@require(lambda cls: len(cls.concrete_descendants) > 0)
def _generate_concrete_create_maximal_cls(
    cls: intermediate.ConcreteClass,
    constraints_by_property: infer_for_schema.ConstraintsByProperty,
) -> Tuple[Optional[Stripped], Optional[str]]:
    """Generate the function to be dispatched to create an instance of ``cls``."""
    constructor_call, error = _generate_concrete_constructor_call(
        cls=cls,
        creation_kind=CreationKind.MAXIMAL,
        constraints_by_property=constraints_by_property,
    )

    if error is not None:
        return None, error
    assert constructor_call is not None

    function_name = python_naming.function_name(
        Identifier(f"concrete_maximal_{cls.name}")
    )
    cls_name = python_naming.class_name(cls.name)

    body = f"return {constructor_call}"

    return (
        Stripped(
            f"""\
def {function_name}(
{I}path_hash: common.CanHash
) -> aas_types.{cls_name}:
{I}\"\"\"
{I}Generate a maximal instance based on the ``path_hash``.

{I}.. note::

{II}You usually do not call this function directly. It will be dispatched
{II}to.

{I}.. note::

{II}The generated instance satisfies only the type constraints.
{II}That means it can be serialized as-is, but probably violates one or
{II}more meta-model constraints.
{I}\"\"\"
{I}{indent_but_first_line(body, I)}"""
        ),
        None,
    )


def _generate_class_name_to_concrete_maximals(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Generate the dispatching map to minimal functions."""
    items = []  # type: List[Tuple[Stripped, Stripped]]
    for our_type in symbol_table.our_types:
        if not isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            continue

        if len(our_type.concrete_descendants) == 0:
            continue

        concrete_functions = []  # type: List[Stripped]
        if isinstance(our_type, intermediate.ConcreteClass):
            concrete_functions.append(
                python_naming.function_name(
                    Identifier(f"concrete_maximal_{our_type.name}")
                )
            )

        for concrete_descendant in our_type.concrete_descendants:
            concrete_functions.append(
                python_naming.function_name(
                    Identifier(f"maximal_{concrete_descendant.name}")
                )
            )

        concrete_functions_joined = ",\n".join(concrete_functions)
        concrete_functions_literal = Stripped(
            f"""\
[
{I}{indent_but_first_line(concrete_functions_joined, I)}
]"""
        )

        items.append(
            (python_common.string_literal(our_type.name), concrete_functions_literal)
        )

    items_literals = [
        Stripped(
            f"""\
{key}:
{value}"""
        )
        for key, value in items
    ]
    items_literals_joined = ",\n".join(items_literals)

    return Stripped(
        f"""\
_CLASS_NAME_TO_CONCRETE_MAXIMALS = {{
{I}{indent_but_first_line(items_literals_joined, I)}
}}    # type: Mapping[str, Sequence[Callable[[common.CanHash], aas_types.Class]]]"""
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_create_maximal_cls(
    cls: Union[intermediate.AbstractClass, intermediate.ConcreteClass],
    constraints_by_property: infer_for_schema.ConstraintsByProperty,
) -> Tuple[Optional[Stripped], Optional[str]]:
    """Generate the function to generate the maximal instance of the ``cls``."""
    # noinspection PyUnusedLocal
    body = None  # type: Optional[Stripped]

    # Class name in Python
    cls_name = python_naming.class_name(cls.name)

    if len(cls.concrete_descendants) > 0:
        body = Stripped(
            f"""\
number = int(path_hash.hexdigest()[:8], base=16)
concrete_maximal_functions = _CLASS_NAME_TO_CONCRETE_MAXIMALS[
{I}{python_common.string_literal(cls.name)}
]
concrete_maximal_function = concrete_maximal_functions[
{I}number % len(concrete_maximal_functions)
]
instance = concrete_maximal_function(path_hash)
assert isinstance(
{I}instance,
{I}aas_types.{cls_name},
)
return instance"""
        )
    else:
        if isinstance(cls, intermediate.AbstractClass):
            raise AssertionError(
                f"Unexpected abstract class without concrete descendants: {cls.name!r}"
            )

        constructor_call, error = _generate_concrete_constructor_call(
            cls=cls,
            creation_kind=CreationKind.MAXIMAL,
            constraints_by_property=constraints_by_property,
        )

        if error is not None:
            return None, error
        assert constructor_call is not None

        body = Stripped(
            f"""\
return {constructor_call}"""
        )

    function_name = python_naming.function_name(Identifier(f"maximal_{cls.name}"))

    assert body is not None
    return (
        Stripped(
            f"""\
def {function_name}(
{I}path_hash: common.CanHash
) -> aas_types.{cls_name}:
{I}\"\"\"
{I}Generate a minimal instance based on the ``path_hash``.

{I}.. note::

{II}The generated instance satisfies only the type constraints.
{II}That means it can be serialized as-is, but probably violates one or
{II}more meta-model constraints.
{I}\"\"\"
{I}{indent_but_first_line(body, I)}"""
        ),
        None,
    )


def _generate_class_name_to_exact_concrete_maximal(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Generate the dispatching map to the exact concrete maximal function."""
    items = []  # type: List[Tuple[Stripped, Stripped]]
    for our_type in symbol_table.our_types:
        if not isinstance(our_type, intermediate.ConcreteClass):
            continue

        if len(our_type.concrete_descendants) > 0:
            concrete_maximal_function = python_naming.function_name(
                Identifier(f"concrete_maximal_{our_type.name}")
            )
        else:
            concrete_maximal_function = python_naming.function_name(
                Identifier(f"maximal_{our_type.name}")
            )

        items.append(
            (python_common.string_literal(our_type.name), concrete_maximal_function)
        )

    items_literals = [
        Stripped(
            f"""\
{key}:
{value}"""
        )
        for key, value in items
    ]
    items_literals_joined = ",\n".join(items_literals)

    return Stripped(
        f"""\
_CLASS_NAME_TO_EXACT_CONCRETE_MAXIMAL = {{
{I}{indent_but_first_line(items_literals_joined, I)}
}}"""
    )


def _generate_create_exact_concrete_maximal() -> Stripped:
    """Generate the function to generate the maximal instance based on a class name."""
    return Stripped(
        f"""\
def exact_concrete_maximal(
{I}path_hash: common.CanHash,
{I}class_name: str
) -> aas_types.Class:
{I}\"\"\"
{I}Create a maximal instance of exactly ``class_name``.

{I}.. note::

{II}The generated instance satisfies only the type constraints.
{II}That means it can be serialized as-is, but probably violates one or
{II}more meta-model constraints.
{I}\"\"\"
{I}dispatch = _CLASS_NAME_TO_EXACT_CONCRETE_MAXIMAL.get(class_name, None)
{I}if dispatch is None:
{II}raise KeyError(
{III}f"The class name {{class_name!r}} does not denote a concrete class "
{III}f"in the meta-model. Did you spell its name in the format of "
{III}f"aas-core-meta (*not* Python)?"
{II})
{I}return dispatch(path_hash)"""
    )


_REPO_DIR = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate(
    symbol_table: intermediate.SymbolTable,
    constraints_by_class: Mapping[
        intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
    ],
) -> Tuple[Optional[Stripped], Optional[str]]:
    """Generate the creation module."""
    warning = dev_scripts.codegen.common.generate_warning(__file__)

    blocks = [
        Stripped('"""Create instances which satisfy the type constraints."""'),
        warning,
        Stripped("# pylint: disable=line-too-long"),
        Stripped(
            f"""\
from typing import (
{I}Callable,
{I}Mapping,
{I}Sequence
)

from aas_core3_0_testgen import common
from aas_core3_0_testgen import primitiving
from aas_core3 import types as aas_types"""
        ),
    ]  # type: List[Stripped]

    for our_type in symbol_table.our_types:
        if not isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            continue

        constraints_by_property = constraints_by_class[our_type]

        if (
            isinstance(our_type, intermediate.ConcreteClass)
            and len(our_type.concrete_descendants) > 0
        ):
            concrete_minimal, error = _generate_concrete_create_minimal_cls(
                cls=our_type, constraints_by_property=constraints_by_property
            )
            if error is not None:
                return None, (
                    f"Failed to generate the concrete minimal function "
                    f"for class {our_type.name}: {error}"
                )

            assert concrete_minimal is not None
            blocks.append(concrete_minimal)

        minimal, error = _generate_create_minimal_cls(
            cls=our_type, constraints_by_property=constraints_by_property
        )
        if error is not None:
            return None, (
                f"Failed to generate the minimal function "
                f"for class {our_type.name}: {error}"
            )

        assert minimal is not None
        blocks.append(minimal)

    blocks.append(_generate_class_name_to_concrete_minimals(symbol_table))
    blocks.append(_generate_class_name_to_exact_concrete_minimal(symbol_table))
    blocks.append(_generate_create_exact_concrete_minimal())

    for our_type in symbol_table.our_types:
        if not isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            continue

        constraints_by_property = constraints_by_class[our_type]

        if (
            isinstance(our_type, intermediate.ConcreteClass)
            and len(our_type.concrete_descendants) > 0
        ):
            concrete_maximal, error = _generate_concrete_create_maximal_cls(
                cls=our_type, constraints_by_property=constraints_by_property
            )
            if error is not None:
                return None, (
                    f"Failed to generate the concrete maximal function "
                    f"for class {our_type.name}: {error}"
                )

            assert concrete_maximal is not None
            blocks.append(concrete_maximal)

        maximal, error = _generate_create_maximal_cls(
            cls=our_type, constraints_by_property=constraints_by_property
        )
        if error is not None:
            return None, (
                f"Failed to generate the maximal function "
                f"for class {our_type.name}: {error}"
            )

        assert maximal is not None
        blocks.append(maximal)

    blocks.append(_generate_class_name_to_concrete_maximals(symbol_table))
    blocks.append(_generate_class_name_to_exact_concrete_maximal(symbol_table))
    blocks.append(_generate_create_exact_concrete_maximal())

    blocks.append(warning)

    return Stripped("\n\n\n".join(blocks)), None


def generate_and_write() -> Optional[str]:
    """Generate the code and write it to the pre-defined file."""
    # fmt: off
    symbol_table, constraints_by_class = (
        aas_core3_0_testgen.common.load_symbol_table_and_infer_constraints_for_schema()
    )
    # fmt: on

    code, error = _generate(symbol_table, constraints_by_class)
    if error is not None:
        return error

    assert code is not None

    path = _REPO_DIR / "aas_core3_0_testgen" / "codegened" / "creation.py"
    path.write_text(code + "\n", encoding="utf-8")

    return None


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
