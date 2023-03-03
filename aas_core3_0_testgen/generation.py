"""Generate the intermediate representation of the test data."""
import collections
import contextlib
import hashlib
import json
import pathlib
import re
from typing import (
    OrderedDict,
    Union,
    List,
    Sequence,
    Any,
    MutableMapping,
    Optional,
    Callable,
    Tuple,
    Iterable,
    Iterator,
    Set,
    Mapping, get_args,
)

import aas_core_codegen.common
import aas_core_meta.v3
from aas_core_codegen import intermediate, infer_for_schema
from aas_core_codegen.common import Identifier, assert_never
from icontract import require, ensure, DBC

from aas_core3_0_testgen import ontology
from aas_core3_0_testgen.frozen_examples import (
    pattern as frozen_examples_pattern,
    xs_value as frozen_examples_xs_value,
)


PrimitiveValueUnion = Union[bool, int, float, str, bytearray]

PrimitiveValueTuple = (bool, int, float, str, bytearray)
assert PrimitiveValueTuple == get_args(PrimitiveValueUnion)

ValueUnion = Union[PrimitiveValueUnion, "Instance", "ListOfInstances"]


class Instance:
    """Represent an instance of a class."""

    def __init__(
        self, properties: OrderedDict[str, ValueUnion], model_type: Identifier
    ) -> None:
        """
        Initialize with the given values.

        The ``model_type`` needs to be always indicated. Whether it is represented in
        the final serialization depends on the context of the serialization.

        The ``model_type`` corresponds to the class name in the meta-model, not to the
        class name in the respective serialization.
        """
        self.properties = properties
        self.model_type = model_type


class ListOfInstances:
    """Represent a list of instances."""

    def __init__(self, values: List[Instance]) -> None:
        """Initialize with the given values."""
        self.values = values


def _to_jsonable(value: ValueUnion) -> Any:
    """
    Represent the ``value`` as a JSON-able object.

    This is meant for debugging, not for the end-user serialization.
    """
    if isinstance(value, PrimitiveValueTuple):
        if isinstance(value, bytearray):
            return repr(value)
        else:
            return value
    elif isinstance(value, Instance):
        obj = collections.OrderedDict()  # type: MutableMapping[str, Any]
        obj["model_type"] = value.model_type

        properties_dict = collections.OrderedDict()  # type: MutableMapping[str, Any]
        for prop_name, prop_value in value.properties.items():
            properties_dict[prop_name] = _to_jsonable(prop_value)

        obj["properties"] = properties_dict

        return obj
    elif isinstance(value, ListOfInstances):
        return [_to_jsonable(item) for item in value.values]
    else:
        assert_never(value)


def dump(value: ValueUnion) -> str:
    """
    Represent the ``value`` as a string.

    This is meant for debugging, not for the end-user serialization.
    """
    return json.dumps(_to_jsonable(value), indent=2)


def dereference(
    container: Instance, path_segments: Sequence[Union[int, str]]
) -> Instance:
    """Dereference the path to an instance starting from a container instance."""
    cursor = container  # type: Any
    for i, segment in enumerate(path_segments):
        if isinstance(segment, str):
            if not isinstance(cursor, Instance):
                raise AssertionError(
                    f"Expected the path {_posix_path(path_segments)} "
                    f"in the container instance: {dump(container)}; "
                    f"however, the cursor at the segment {i} "
                    f"does not point to an instance, but to: {dump(cursor)}"
                )

            if segment not in cursor.properties:
                raise AssertionError(
                    f"Expected the path {_posix_path(path_segments)} "
                    f"in the container instance: {dump(container)}; "
                    f"however, the segment {i + 1},{segment}, "
                    f"does not exist as a property "
                    f"in the instance: {dump(cursor)}"
                )

            cursor = cursor.properties[segment]

        elif isinstance(segment, int):
            if not isinstance(cursor, ListOfInstances):
                raise AssertionError(
                    f"Expected the path {_posix_path(path_segments)} "
                    f"in the container instance: {dump(container)}; "
                    f"however, the cursor at the segment {i} "
                    f"does not point to a list of instances, but to: {dump(cursor)}"
                )

            if segment >= len(cursor.values):
                raise AssertionError(
                    f"Expected the path {_posix_path(path_segments)} "
                    f"in the container instance: {dump(container)}; "
                    f"however, the segment {i + 1}, {segment}, "
                    f"does not exist as an item "
                    f"in the list of instances: {dump(cursor)}"
                )

            cursor = cursor.values[segment]
        else:
            aas_core_codegen.common.assert_never(segment)

    if not isinstance(cursor, Instance):
        raise AssertionError(
            f"Expected the path {_posix_path(path_segments)} "
            f"in the container instance: {json.dumps(container, indent=2)} "
            f"to dereference an instance, but got: {dump(cursor)}"
        )

    return cursor


def _deep_copy(value: ValueUnion) -> ValueUnion:
    """Make a deep copy of the given value."""
    if isinstance(value, PrimitiveValueTuple):
        return value
    elif isinstance(value, Instance):
        props = collections.OrderedDict()  # type: OrderedDict[str, ValueUnion]
        for prop_name, prop_value in value.properties.items():
            props[prop_name] = _deep_copy(prop_value)

        return Instance(properties=props, model_type=value.model_type)

    elif isinstance(value, ListOfInstances):
        values = []  # type: List[Instance]
        for item in value.values:
            a_copy = _deep_copy(item)
            assert isinstance(a_copy, Instance)
            values.append(a_copy)

        return ListOfInstances(values=values)
    else:
        aas_core_codegen.common.assert_never(value)


# noinspection RegExpSimplifiable
_HEX_RE = re.compile(r"[a-fA-F0-9]+")


@ensure(lambda result: _HEX_RE.fullmatch(result))
def _hash_path(path_segments: Sequence[Union[str, int]]) -> str:
    """Hash the given path to a value in the model."""
    hsh = hashlib.md5()
    hsh.update(("".join(repr(segment) for segment in path_segments)).encode("utf-8"))
    return hsh.hexdigest()[:8]


def _posix_path(path_segments: Sequence[Union[str, int]]) -> pathlib.PurePosixPath:
    """Make a POSIX path out of the path segments."""
    pth = pathlib.PurePosixPath("/")
    for segment in path_segments:
        pth = pth / str(segment)

    return pth


@require(lambda length: length > 0)
@ensure(lambda result, length: len(result) == length)
def _generate_long_string(
    length: int,
    path_segments: List[Union[int, str]],
) -> str:
    """
    Generate a string longer than the ``length``.

    >>> _generate_long_string(2, ['some', 3, 'path'])
    'x9'

    >>> _generate_long_string(9, ['some', 3, 'path'])
    'x99ef1573'

    >>> _generate_long_string(10, ['some', 3, 'path'])
    'x99ef15730'

    >>> _generate_long_string(15, ['some', 3, 'path'])
    'x99ef1573012345'

    >>> _generate_long_string(20, ['some', 3, 'path'])
    'x99ef157301234567890'

    >>> _generate_long_string(21, ['some', 3, 'path'])
    'x99ef1573012345678901'
    """
    prefix = f"x{_hash_path(path_segments=path_segments)}"
    if len(prefix) > length:
        return prefix[:length]

    ruler = "1234567890"

    if length <= 10:
        return prefix + ruler[len(prefix) : length]

    tens = length // 10
    remainder = length % 10
    return "".join(
        [prefix, ruler[len(prefix) : 10], ruler * (tens - 1), ruler[:remainder]]
    )


def _generate_time_of_day(path_segments: List[Union[int, str]]) -> str:
    """Generate a random time of the day based on the path to the value."""
    hsh = _hash_path(path_segments=path_segments)

    hsh_as_int = int(hsh, base=16)

    remainder = hsh_as_int
    hours = (remainder // 3600) % 24
    remainder = remainder % 3600
    minutes = (remainder // 60) % 60
    seconds = remainder % 60

    fraction = hsh_as_int % 1000000

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{fraction}"


def _extend_lang_string_set_to_have_an_entry_at_least_in_English(
    lang_string_set: ListOfInstances,
        path_segments: List[Union[int, str]],
        lang_string_cls: intermediate.Class
) -> None:
    """Extend the Lang String Set to contain at least one entry in English."""
    hsh = _hash_path(path_segments=path_segments)

    has_english = False
    for lang_string in lang_string_set.values:
        language = lang_string.properties["language"]
        assert isinstance(language, str)
        if language == "en" or language.startswith("en-"):
            has_english = True
            break

    if not has_english:
        lang_string_set.values.append(
            Instance(
                collections.OrderedDict(
                    [
                        ("language", "en-UK"),
                        ("text", f"Something random in English {hsh}"),
                    ]
                ),
                model_type=Identifier(lang_string_cls.name),
            )
        )


# fmt: off
@require(
    lambda primitive_type, set_of_primitives_constraint:
    not (set_of_primitives_constraint is not None)
    or primitive_type is set_of_primitives_constraint.a_type,
    "If there is a set of primitives constraint, the type annotation must match it"
)
# fmt: on
def _generate_primitive_value(
    primitive_type: intermediate.PrimitiveType,
    path_segments: List[Union[str, int]],
    len_constraint: Optional[infer_for_schema.LenConstraint],
    pattern_constraints: Optional[Sequence[infer_for_schema.PatternConstraint]],
    set_of_primitives_constraint: Optional[infer_for_schema.SetOfPrimitivesConstraint],
) -> PrimitiveValueUnion:
    """Generate the primitive value based on the ``path_segments``."""

    # noinspection PyUnusedLocal
    def implementation() -> Union[bool, int, float, str, bytearray]:
        """Wrap the body so that we can ensure the len constraints."""
        hsh = _hash_path(path_segments=path_segments)
        hsh_as_int = int(hsh, base=16)

        # region Pick an item of a set constraint if constrained

        if set_of_primitives_constraint is not None:
            literal = set_of_primitives_constraint.literals[
                hsh_as_int % len(set_of_primitives_constraint.literals)
            ]

            return literal.value

        # endregion

        # region Handle the special case of a single pattern constraint first

        # NOTE (mristin, 2023-03-01):
        # We drop the constraint for XML serializable strings since it permeates
        # all the specification. However, once we drop it, all the types have a single
        # constraint.
        if pattern_constraints is not None:
            pattern_constraints_without_xml_strings = [
                pattern_constraint
                for pattern_constraint in pattern_constraints
                if pattern_constraint.pattern
                   !=
                   '^[\\x09\\x0A\\x0D\\x20-\\uD7FF\\uE000-\\uFFFD\\U00010000-\\U0010FFFF]*$'
            ]
        else:
            pattern_constraints_without_xml_strings = None

        if (
                pattern_constraints_without_xml_strings is not None
                and len(pattern_constraints_without_xml_strings) >= 1
        ):
            if len(pattern_constraints_without_xml_strings) > 1:
                patterns = [
                    pattern_constraint.pattern
                    for pattern_constraint in pattern_constraints_without_xml_strings
                ]
                raise NotImplementedError(
                    "We did not implement the generation of a value based on two or "
                    "more pattern constraints, which is the case "
                    f"for the value {_posix_path(path_segments)}: {patterns}"
                )

            if primitive_type is not intermediate.PrimitiveType.STR:
                raise NotImplementedError(
                    "We did not implement the generation of a non-string value with "
                    "the pattern constraint, which is the case "
                    f"for the value {_posix_path(path_segments)}"
                )

            assert primitive_type is intermediate.PrimitiveType.STR

            assert len(pattern_constraints_without_xml_strings) > 0, (
                "Unexpected empty pattern constraints"
            )

            pattern = pattern_constraints_without_xml_strings[0].pattern
            pattern_examples = frozen_examples_pattern.BY_PATTERN.get(pattern, None)
            if pattern_examples is None:
                raise NotImplementedError(
                    f"The entry is missing "
                    f"in the {frozen_examples_pattern.__name__!r} "
                    f"for the pattern {pattern!r} "
                    f"when generating the value at {_posix_path(path_segments)}"
                )

            if len(pattern_examples.positives) == 0:
                raise NotImplementedError(
                    f"Unexpected an empty list of positive examples "
                    f"in the {frozen_examples_pattern.__name__!r} "
                    f"for the pattern {pattern!r} "
                    f"when generating the value at {_posix_path(path_segments)}"
                )

            for value in pattern_examples.positives.values():
                return value

            raise AssertionError("Expected to check for at least one positive example")

        # endregion

        assert primitive_type is not None
        if primitive_type is intermediate.PrimitiveType.BOOL:
            return hsh_as_int % 2 == 0

        elif primitive_type is intermediate.PrimitiveType.INT:
            # NOTE (mristin, 2022-09-01):
            # We make sure that the integer is not above 2^64 so that we can
            # safely represent it as a 64-bit long integer.
            return hsh_as_int % (2**63 - 1)

        elif primitive_type is intermediate.PrimitiveType.FLOAT:
            return float(hsh_as_int) / 100

        elif primitive_type is intermediate.PrimitiveType.STR:
            return f"something_{hsh}"

        elif primitive_type is intermediate.PrimitiveType.BYTEARRAY:
            return bytearray.fromhex(hsh)
        else:
            aas_core_codegen.common.assert_never(primitive_type)

    # NOTE (mristin, 2022-05-11):
    # We ensure here that the constraint on ``len(.)`` of the result is satisfied.
    # This covers some potential errors, but mind that still does not check
    # the constraints. Hence, you have to manually inspect the generated data and
    # decide yourself whether you need to write a generator manually.

    result = implementation()

    if len_constraint is not None:
        if primitive_type in (
            intermediate.PrimitiveType.BOOL,
            intermediate.PrimitiveType.INT,
            intermediate.PrimitiveType.FLOAT,
        ):
            raise ValueError(
                f"We do not know how to apply the length constraint "
                f"on the primitive type: {primitive_type.value}; path: {path_segments}"
            )

        assert isinstance(result, (str, bytearray))

        if (
            len_constraint.min_value is not None
            and len(result) < len_constraint.min_value
        ) or (
            len_constraint.max_value is not None
            and len(result) > len_constraint.max_value
        ):
            raise ValueError(
                f"Expected the value {_posix_path(path_segments)} "
                f"to satisfy the length constraint "
                f"[{len_constraint.min_value!r}, {len_constraint.max_value!r}], "
                f"but got the length {len(result)}. You have to write the generator "
                f"for this value instance yourself"
            )

    return result


@contextlib.contextmanager
def _extend_in_place(
    path_segments: List[Union[str, int]], extension: Iterable[Union[str, int]]
) -> Iterator[Any]:
    """Extend the ``path_segments`` with the ``extension`` and revert it on exit."""
    path_segments.extend(extension)
    try:
        yield
    finally:
        for _ in extension:
            path_segments.pop()


def _generate_model_reference(
    expected_type: aas_core_meta.v3.Key_types,
    path_segments: List[Union[str, int]],
) -> Instance:
    """Generate a model Reference pointing to an instance of ``expected_type``."""
    props = collections.OrderedDict()  # type: OrderedDict[str, Any]
    props["type"] = aas_core_meta.v3.Reference_types.Model_reference.value

    if expected_type in (
        aas_core_meta.v3.Key_types.Asset_administration_shell,
        aas_core_meta.v3.Key_types.Concept_description,
        aas_core_meta.v3.Key_types.Submodel,
    ):
        with _extend_in_place(path_segments, ["keys", 0, "value"]):
            props["keys"] = ListOfInstances(
                values=[
                    Instance(
                        properties=collections.OrderedDict(
                            [
                                ("type", expected_type.value),
                                ("value", _hash_path(path_segments)),
                            ]
                        ),
                        model_type=Identifier("Key"),
                    )
                ]
            )

    elif expected_type is aas_core_meta.v3.Key_types.Referable:
        with _extend_in_place(path_segments, ["keys", 0, "value"]):
            key0 = Instance(
                properties=collections.OrderedDict(
                    [
                        ("type", aas_core_meta.v3.Key_types.Submodel.value),
                        ("value", f"something_random_{_hash_path(path_segments)}"),
                    ]
                ),
                model_type=Identifier("Key"),
            )

        with _extend_in_place(path_segments, ["keys", 1, "value"]):
            key1 = Instance(
                properties=collections.OrderedDict(
                    [
                        # NOTE (mristin, 2022-07-10):
                        # Blob is an instance of a referable.
                        ("type", aas_core_meta.v3.Key_types.Blob.value),
                        ("value", f"something_random_{_hash_path(path_segments)}"),
                    ]
                ),
                model_type=Identifier("Key"),
            )

        props["keys"] = ListOfInstances(values=[key0, key1])
    else:
        raise NotImplementedError(
            f"Unhandled {expected_type=}; when we developed this script there were "
            f"no other key types expected in the meta-model as a reference, "
            f"but this has obvious changed. Please contact the developers."
        )

    return Instance(properties=props, model_type=Identifier("Reference"))


def _generate_global_reference(
    path_segments: List[Union[str, int]],
) -> Instance:
    """Generate an instance of a global Reference."""

    props = collections.OrderedDict()  # type: OrderedDict[str, ValueUnion]
    props["type"] = aas_core_meta.v3.Reference_types.External_reference.value

    with _extend_in_place(path_segments, ["keys", 0, "value"]):
        key = Instance(
            properties=collections.OrderedDict(
                [
                    ("type", aas_core_meta.v3.Key_types.Global_reference.value),
                    ("value", f"something_random_{_hash_path(path_segments)}"),
                ]
            ),
            model_type=Identifier("Key"),
        )
        props["keys"] = ListOfInstances(values=[key])

    return Instance(properties=props, model_type=Identifier("Reference"))


# fmt: off
@require(
    lambda type_annotation, set_of_enumeration_literals_constraint:
    not (set_of_enumeration_literals_constraint is not None)
    or (
        isinstance(type_annotation, intermediate.OurTypeAnnotation)
        and (
            type_annotation.our_type is
            set_of_enumeration_literals_constraint.enumeration
        )
    ),
    "If set of enumeration literals constraint is defined, the type annotation must "
    "refer to the enumeration"
)
# fmt: on
def _generate_property_value(
    type_annotation: intermediate.TypeAnnotationExceptOptional,
    path_segments: List[Union[str, int]],
    len_constraint: Optional[infer_for_schema.LenConstraint],
    pattern_constraints: Optional[Sequence[infer_for_schema.PatternConstraint]],
    set_of_primitives_constraint: Optional[infer_for_schema.SetOfPrimitivesConstraint],
    set_of_enumeration_literals_constraint: Optional[
        infer_for_schema.SetOfEnumerationLiteralsConstraint
    ],
    generate_instance: Callable[
        [intermediate.ClassUnion, List[Union[str, int]]], Instance
    ],
) -> ValueUnion:
    """
    Generate the value for the given property.

    Since ``path_segments`` are extended in-place, this function is not thread-safe.

    The callable ``generate_instance`` instructs how to generate the instances
    recursively.
    """
    maybe_primitive_type = intermediate.try_primitive_type(type_annotation)

    if maybe_primitive_type is not None:
        return _generate_primitive_value(
            primitive_type=maybe_primitive_type,
            path_segments=path_segments,
            len_constraint=len_constraint,
            pattern_constraints=pattern_constraints,
            set_of_primitives_constraint=set_of_primitives_constraint,
        )

    assert not isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation)

    if isinstance(type_annotation, intermediate.OurTypeAnnotation):
        if pattern_constraints is not None:
            raise ValueError(
                f"Unexpected pattern constraints for a value "
                f"of type {type_annotation} at {_posix_path(path_segments)}"
            )

        if len_constraint is not None:
            raise ValueError(
                f"Unexpected len constraint for a value "
                f"of type {type_annotation} at {_posix_path(path_segments)}"
            )

        if isinstance(type_annotation.our_type, intermediate.Enumeration):
            hsh_as_int = int(_hash_path(path_segments=path_segments), base=16)

            if set_of_enumeration_literals_constraint is not None:
                assert len(set_of_enumeration_literals_constraint.literals) > 0, (
                    "Expected at least one literal in the set of enumeration literals "
                    "constraint, but got none"
                )

                enum_literal = set_of_enumeration_literals_constraint.literals[
                    hsh_as_int % len(set_of_enumeration_literals_constraint.literals)
                ]

                return enum_literal.value

            return type_annotation.our_type.literals[
                hsh_as_int % len(type_annotation.our_type.literals)
            ].value

        elif isinstance(type_annotation.our_type, intermediate.ConstrainedPrimitive):
            raise AssertionError(
                f"Should have been handled before: {type_annotation.our_type}"
            )

        elif isinstance(
            type_annotation.our_type,
            (intermediate.AbstractClass, intermediate.ConcreteClass),
        ):
            return generate_instance(type_annotation.our_type, path_segments)
        else:
            aas_core_codegen.common.assert_never(type_annotation.our_type)

    elif isinstance(type_annotation, intermediate.ListTypeAnnotation):
        if pattern_constraints is not None:
            raise ValueError(
                f"Unexpected pattern constraints for a value "
                f"of type {type_annotation} at {_posix_path(path_segments)}"
            )

        if not isinstance(
            type_annotation.items, intermediate.OurTypeAnnotation
        ) or not isinstance(
            type_annotation.items.our_type,
            (intermediate.AbstractClass, intermediate.ConcreteClass),
        ):
            raise NotImplementedError(
                f"Implemented only handling lists of classes, "
                f"but got: {type_annotation}; please contact the developers"
            )

        with _extend_in_place(path_segments, [0]):
            instance = generate_instance(type_annotation.items.our_type, path_segments)

        result = ListOfInstances(values=[instance])

        if len_constraint is not None:
            if (
                len_constraint.min_value is not None
                and len(result.values) < len_constraint.min_value
            ) or (
                len_constraint.max_value is not None
                and len(result.values) > len_constraint.max_value
            ):
                raise ValueError(
                    f"Expected the value {_posix_path(path_segments)} "
                    f"to satisfy the len constraint "
                    f"[{len_constraint.min_value!r}, {len_constraint.max_value!r}], "
                    f"but got the list of length {len(result.values)}. "
                    f"You have to write the generator for this value yourself."
                )

        return result
    else:
        aas_core_codegen.common.assert_never(type_annotation)


def _generate_concrete_minimal_instance(
    cls: intermediate.ConcreteClass,
    path_segments: List[Union[str, int]],
    constraints_by_class: MutableMapping[
        intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
    ],
    symbol_table: intermediate.SymbolTable,
) -> Instance:
    """
    Generate an instance with only required properties of exactly type ``cls``.

    The ``path_segments`` refer to the path leading to the instance of the ``cls``.

    We recursively generate minimal instances for all the nested classes.
    We will re-use the ``path_segments`` in the subsequent recursive calls to avoid
    the quadratic time complexity, so beware that this function is *NOT* thread-safe.

    The generation is deterministic, *i.e.*, re-generating with the same input
    should yield the same output.
    """
    reference_cls = symbol_table.must_find_concrete_class(Identifier("Reference"))
    if cls is reference_cls:
        # NOTE (mristin, 2022-06-19):
        # We generate a global reference by default, since this makes for much better
        # examples with less confusion for the reader. If you need something else, fix
        # it afterwards.
        return _generate_global_reference(path_segments=path_segments)

    constraints_by_prop = constraints_by_class[cls]

    props = collections.OrderedDict()  # type: OrderedDict[str, ValueUnion]

    def generate_a_minimal_instance(
        a_cls: intermediate.ClassUnion, a_path_segments: List[Union[str, int]]
    ) -> Instance:
        """Generate an instance passing over the parameters from the closure."""
        return generate_minimal_instance(
            cls=a_cls,
            path_segments=a_path_segments,
            constraints_by_class=constraints_by_class,
            symbol_table=symbol_table,
        )

    for prop in cls.properties:
        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            continue

        with _extend_in_place(path_segments, [prop.name]):
            # fmt: off
            props[prop.name] = _generate_property_value(
                type_annotation=prop.type_annotation,
                path_segments=path_segments,
                len_constraint=constraints_by_prop.len_constraints_by_property.get(
                    prop, None
                ),
                pattern_constraints=constraints_by_prop.patterns_by_property.get(
                    prop, None
                ),
                set_of_primitives_constraint=(
                    constraints_by_prop
                    .set_of_primitives_by_property
                    .get(
                        prop, None
                    )
                ),
                set_of_enumeration_literals_constraint=(
                    constraints_by_prop
                    .set_of_enumeration_literals_by_property
                    .get(
                        prop, None
                    )
                ),
                generate_instance=generate_a_minimal_instance,
            )
            # fmt: on

    return Instance(properties=props, model_type=cls.name)

    # endregion


def generate_minimal_instance(
    cls: intermediate.ClassUnion,
    path_segments: List[Union[str, int]],
    constraints_by_class: MutableMapping[
        intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
    ],
    symbol_table: intermediate.SymbolTable,
) -> Instance:
    """
    Generate an instance with only required properties of type ``cls``.

    The ``path_segments`` refer to the path leading to the instance of the ``cls``.

    If the ``cls`` is abstract or has concrete descendants, we arbitrarily pick one
    of the concrete descending classes or the ``cls`` itself, if it is concrete.

    We recursively generate minimal instances for all the nested classes.
    We will re-use the ``path_segments`` in the subsequent recursive calls to avoid
    the quadratic time complexity, so beware that this function is *NOT* thread-safe.

    The generation is deterministic, *i.e.*, re-generating with the same input
    should yield the same output.
    """
    if cls.interface is not None:
        hsh_as_int = int(_hash_path(path_segments=path_segments), base=16)

        concrete_classes = cls.interface.implementers

        if len(concrete_classes) == 0:
            raise AssertionError(
                f"Unexpected a class with an interface, "
                f"but no implementers: {cls.name}"
            )

        concrete_cls = concrete_classes[hsh_as_int % len(concrete_classes)]
    else:
        assert isinstance(cls, intermediate.ConcreteClass)
        concrete_cls = cls

    return _generate_concrete_minimal_instance(
        cls=concrete_cls,
        path_segments=path_segments,
        constraints_by_class=constraints_by_class,
        symbol_table=symbol_table,
    )


# noinspection PyMethodMayBeStatic
class Handyman:
    """
    Fix the instances recursively in-place so that the constraints are preserved.

    We assume that it is easier to fix the instances after the generation than to
    generate them correctly in the first pass.
    """

    def __init__(
        self,
        symbol_table: intermediate.SymbolTable,
        constraints_by_class: MutableMapping[
            intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
        ],
    ) -> None:
        """Initialize with the given values."""
        self.symbol_table = symbol_table
        self.constraints_by_class = constraints_by_class

        self._dispatch_concrete = {
            "Administrative_information": Handyman._fix_administrative_information,
            "Asset_information": Handyman._fix_asset_information,
            "Asset_administration_shell": Handyman._fix_asset_administration_shell,
            "Basic_event_element": Handyman._fix_basic_event_element,
            "Concept_description": Handyman._fix_concept_description,
            "Data_specification_IEC_61360": Handyman._fix_data_specification_iec_61360,
            "Entity": Handyman._fix_entity,
            "Event_payload": Handyman._fix_event_payload,
            "Extension": Handyman._fix_extension,
            "Property": Handyman._fix_property,
            "Qualifier": Handyman._fix_qualifier,
            "Range": Handyman._fix_range,
            "Submodel": Handyman._fix_submodel,
            "Submodel_element_collection": Handyman._fix_submodel_element_collection,
            "Submodel_element_list": Handyman._fix_submodel_element_list,
        }

        # region Ensure that all the dispatches has been properly defined
        inverted_dispatch = set(
            method.__name__ for method in self._dispatch_concrete.values()
        )

        for attr_name in dir(Handyman):
            if attr_name.startswith("_fix_") and attr_name not in inverted_dispatch:
                raise AssertionError(
                    f"The method {attr_name} is missing in the dispatch set."
                )
        # endregion

        # region Ensure that the dispatch map is correct
        for cls_name in self._dispatch_concrete:
            _ = self.symbol_table.must_find_concrete_class(name=Identifier(cls_name))
        # endregion

        # region Ensure that the dispatch methods are appropriate

        for cls_name, method in self._dispatch_concrete.items():
            method_stem = re.sub(r"^_fix_", "", method.__name__)
            assert (
                cls_name.lower() == method_stem.lower()
            ), f"{cls_name=}, {method_stem=}, {method.__name__=}"

        # endregion

    def fix_instance(
        self, instance: Instance, path_segments: List[Union[str, int]]
    ) -> None:
        """Fix the ``instance`` recursively in-place."""
        dispatch = self._dispatch_concrete.get(instance.model_type, None)
        if dispatch is not None:
            # noinspection PyArgumentList
            dispatch(self, instance, path_segments)
        else:
            self._recurse_into_properties(
                instance=instance, path_segments=path_segments
            )

    def fix_list_of_instances(
        self, list_of_instances: ListOfInstances, path_segments: List[Union[str, int]]
    ) -> None:
        """Fix the instances recursively in-place."""
        for i, instance in enumerate(list_of_instances.values):
            with _extend_in_place(path_segments, [i]):
                self.fix_instance(instance=instance, path_segments=path_segments)

    def _recurse_into_properties(
        self, instance: Instance, path_segments: List[Union[str, int]]
    ) -> None:
        """Fix the properties of the ``instance`` recursively in-place."""
        for prop_name, prop_value in instance.properties.items():
            if isinstance(prop_value, PrimitiveValueTuple):
                # NOTE (mristin, 2022-06-20):
                # There is nothing to recurse into primitive properties.
                pass

            elif isinstance(prop_value, Instance):
                with _extend_in_place(path_segments, [prop_name]):
                    self.fix_instance(prop_value, path_segments)

            elif isinstance(prop_value, ListOfInstances):
                with _extend_in_place(path_segments, [prop_name]):
                    self.fix_list_of_instances(prop_value, path_segments)

            else:
                aas_core_codegen.common.assert_never(prop_value)

    def _fix_administrative_information(
            self,
            instance: Instance,
            path_segments: List[Union[str, int]]
    ) -> None:
        # Fix version type
        version_type = instance.properties.get("version_type", None)
        if version_type is not None and len(version_type) > 4:
            instance.properties["version_type"] = version_type[:4]

        # Fix revision type
        revision_type = instance.properties.get("revision_type", None)
        if revision_type is not None and len(revision_type) > 4:
            instance.properties["revision_type"] = revision_type[:4]

    def _fix_basic_event_element(
        self, instance: Instance, path_segments: List[Union[str, int]]
    ) -> None:
        # Fix that the observed is a proper model reference
        if "observed" in instance.properties:
            with _extend_in_place(path_segments, ["observed"]):
                instance.properties["observed"] = _generate_model_reference(
                    expected_type=aas_core_meta.v3.Key_types.Referable,
                    path_segments=path_segments,
                )

        # Override that the direction is output so that we can always set
        # the max interval
        if "direction" in instance.properties:
            direction_enum = self.symbol_table.must_find_enumeration(
                Identifier("Direction")
            )

            instance.properties["direction"] = direction_enum.literals_by_name[
                "Output"
            ].value

        # Fix that the message broker is a proper model reference
        if "message_broker" in instance.properties:
            with _extend_in_place(path_segments, ["message_broker"]):
                instance.properties["message_broker"] = _generate_model_reference(
                    expected_type=aas_core_meta.v3.Key_types.Referable,
                    path_segments=path_segments,
                )

        self._recurse_into_properties(instance=instance, path_segments=path_segments)

    def _fix_asset_information(
        self, instance: Instance, path_segments: List[Union[str, int]]
   ) -> None:
        # Fix for AASd-131: Either the global asset ID shall be defined or at least one
        # specific asset ID.
        if (
                "global_asset_ID" not in instance.properties
                and "specific_asset_IDs" not in instance.properties
        ):
            with _extend_in_place(path_segments, "global_asset_ID"):
                hsh = _hash_path(path_segments=path_segments)
                instance.properties["global_asset_ID"] = f"something_random_{hsh}"

    def _fix_asset_administration_shell(
        self, instance: Instance, path_segments: List[Union[str, int]]
    ) -> None:
        # Fix the invariant that the derivedFrom is a reference to a shell
        if "derived_from" in instance.properties:
            with _extend_in_place(path_segments, ["derived_from"]):
                instance.properties["derived_from"] = _generate_model_reference(
                    expected_type=(
                        aas_core_meta.v3.Key_types.Asset_administration_shell
                    ),
                    path_segments=path_segments,
                )

        # Fix the submodels to be proper model references
        if "submodels" in instance.properties:
            with _extend_in_place(path_segments, ["submodels", 0]):
                instance.properties["submodels"] = ListOfInstances(
                    values=[
                        _generate_model_reference(
                            expected_type=aas_core_meta.v3.Key_types.Submodel,
                            path_segments=path_segments,
                        )
                    ]
                )

        self._recurse_into_properties(instance=instance, path_segments=path_segments)

    def _fix_concept_description(
        self, instance: Instance, path_segments: List[Union[str, int]]
    ) -> None:
        category = instance.properties.get("category", None)
        embedded_data_specifications = instance.properties.get(
            "embedded_data_specifications", None
        )

        if embedded_data_specifications is not None:
            assert isinstance(embedded_data_specifications, ListOfInstances)

            for i, embedded_data_specification in enumerate(
                embedded_data_specifications.values
            ):
                content = embedded_data_specification.properties[
                    "data_specification_content"
                ]
                assert isinstance(content, Instance)

                if content.model_type == "Data_specification_IEC_61360":
                    with _extend_in_place(
                        path_segments, ["embedded_data_specifications", i]
                    ):
                        if category != "VALUE":
                            # Fix AASc-3a-008: If not category "VALUE",
                            # the definition at least in English
                            if "definition" not in content.properties:
                                content.properties["definition"] = ListOfInstances([])

                            with _extend_in_place(path_segments, ["definition"]):
                                assert isinstance(
                                    content.properties["definition"], ListOfInstances
                                )

                                _extend_lang_string_set_to_have_an_entry_at_least_in_English(
                                    lang_string_set=content.properties["definition"],
                                    path_segments=path_segments,
                                    lang_string_cls=self.symbol_table.must_find_class(
                                        Identifier(
                                            'Lang_string_definition_type_IEC_61360'
                                        )
                                    )
                                )

        self._recurse_into_properties(instance=instance, path_segments=path_segments)

    def _fix_data_specification_iec_61360(
        self, instance: Instance, path_segments: List[Union[str, int]]
    ) -> None:
        # TODO (mristin, 2023-03-3): rem
        instance.properties["XXX"] = "YYY"

        # If value and value_list, pick value
        if "value" in instance.properties and "value_list" in instance.properties:
            del instance.properties["value_list"]

        # If neither value nor value_list, set value
        if (
            "value" not in instance.properties
            and "value_list" not in instance.properties
        ):
            with _extend_in_place(path_segments, ["value"]):
                hsh = _hash_path(path_segments=path_segments)
                instance.properties["value"] = f"something_random_{hsh}"

        assert "value" in instance.properties or "value_list" in instance.properties

        # Set dummy unit and unit ID if the data type requires it
        data_type = instance.properties.get("data_type", None)
        if data_type is not None:
            iec_61360_data_types_with_unit_enum = self.symbol_table.constants_by_name[
                Identifier("IEC_61360_data_types_with_unit")
            ]

            assert isinstance(
                iec_61360_data_types_with_unit_enum,
                intermediate.ConstantSetOfEnumerationLiterals,
            )

            if any(
                data_type == literal.value
                for literal in iec_61360_data_types_with_unit_enum.literals
            ):
                if "unit" not in instance.properties:
                    with _extend_in_place(path_segments, ["unit"]):
                        hsh = _hash_path(path_segments=path_segments)
                        instance.properties["unit"] = f"something_random_{hsh}"

                if "unit_ID" not in instance.properties:
                    with _extend_in_place(path_segments, ["unit_ID"]):
                        hsh = _hash_path(path_segments=path_segments)
                        instance.properties["unit_ID"] = f"something_random_{hsh}"

        # If no English in the preferred_name, add an entry
        with _extend_in_place(path_segments, ["preferred_name"]):
            assert isinstance(instance.properties["preferred_name"], ListOfInstances)

            _extend_lang_string_set_to_have_an_entry_at_least_in_English(
                lang_string_set=instance.properties["preferred_name"],
                path_segments=path_segments,
                lang_string_cls=self.symbol_table.must_find_class(
                    Identifier(
                        'Lang_string_definition_type_IEC_61360'
                    )
                )
            )

        self._recurse_into_properties(instance=instance, path_segments=path_segments)

    def _fix_entity(
        self, instance: Instance, path_segments: List[Union[str, int]]
    ) -> None:
        entity_type = instance.properties.get("entity_type", None)
        if entity_type is not None:
            entity_type_enum = self.symbol_table.must_find_enumeration(
                Identifier("Entity_type")
            )

            self_managed_entity_literal = entity_type_enum.literals_by_name[
                "Self_managed_entity"
            ]

            if entity_type == self_managed_entity_literal.value:
                instance.properties.pop("specific_asset_ID", None)
            else:
                instance.properties.pop("specific_asset_ID", None)
                instance.properties.pop("global_asset_ID", None)

        self._recurse_into_properties(instance=instance, path_segments=path_segments)

    def _fix_event_payload(
        self, instance: Instance, path_segments: List[Union[str, int]]
    ) -> None:
        # Fix that the source is a proper model reference
        if "source" in instance.properties:
            with _extend_in_place(path_segments, ["source"]):
                instance.properties["source"] = _generate_model_reference(
                    expected_type=aas_core_meta.v3.Key_types.Referable,
                    path_segments=path_segments,
                )

        # Fix that the observable reference is a proper model reference
        if "observable_reference" in instance.properties:
            with _extend_in_place(path_segments, ["observable_reference"]):
                instance.properties["observable_reference"] = _generate_model_reference(
                    expected_type=aas_core_meta.v3.Key_types.Referable,
                    path_segments=path_segments,
                )

        self._recurse_into_properties(instance=instance, path_segments=path_segments)

    def _fix_extension(
        self, instance: Instance, path_segments: List[Union[str, int]]
    ) -> None:
        extension_cls = self.symbol_table.must_find_concrete_class(
            Identifier("Extension")
        )

        # NOTE (mristin, 2022-06-20):
        # We need to assert this as we are automatically setting the ``value_type``.
        assert not isinstance(
            extension_cls.properties_by_name[Identifier("value_type")],
            intermediate.OptionalTypeAnnotation,
        )

        instance.properties["value_type"] = "xs:boolean"
        if "value" in instance.properties:
            instance.properties["value"] = "true"

        self._recurse_into_properties(instance=instance, path_segments=path_segments)

    def _fix_property(
        self, instance: Instance, path_segments: List[Union[str, int]]
    ) -> None:
        property_cls = self.symbol_table.must_find_concrete_class(
            Identifier("Property")
        )

        # NOTE (mristin, 2022-06-20):
        # We need to assert this as we are automatically setting the ``value_type``.
        assert not isinstance(
            property_cls.properties_by_name[Identifier("value_type")],
            intermediate.OptionalTypeAnnotation,
        )

        instance.properties["value_type"] = "xs:boolean"
        if "value" in instance.properties:
            instance.properties["value"] = "true"

        self._recurse_into_properties(instance=instance, path_segments=path_segments)

    def _fix_qualifier(
        self, instance: Instance, path_segments: List[Union[str, int]]
    ) -> None:
        qualifier_cls = self.symbol_table.must_find_concrete_class(
            Identifier("Qualifier")
        )

        # NOTE (mristin, 2022-06-20):
        # We need to assert this as we are automatically setting the ``value_type``.
        assert not isinstance(
            qualifier_cls.properties_by_name[Identifier("value_type")],
            intermediate.OptionalTypeAnnotation,
        )

        instance.properties["value_type"] = "xs:boolean"
        if "value" in instance.properties:
            instance.properties["value"] = "true"

        self._recurse_into_properties(instance=instance, path_segments=path_segments)

    def _fix_range(
        self, instance: Instance, path_segments: List[Union[str, int]]
    ) -> None:
        range_cls = self.symbol_table.must_find_concrete_class(Identifier("Range"))

        # NOTE (mristin, 2022-06-20):
        # We need to assert this as we are automatically setting the ``value_type``.
        assert not isinstance(
            range_cls.properties_by_name[Identifier("value_type")],
            intermediate.OptionalTypeAnnotation,
        )

        instance.properties["value_type"] = "xs:int"
        if "min" in instance.properties:
            instance.properties["min"] = "1234"

        if "max" in instance.properties:
            instance.properties["max"] = "4321"

        self._recurse_into_properties(instance=instance, path_segments=path_segments)

    def _fix_submodel(
        self, instance: Instance, path_segments: List[Union[str, int]]
    ) -> None:
        submodel_elements = instance.properties.get("submodel_elements", None)
        if submodel_elements is not None:
            assert isinstance(submodel_elements, ListOfInstances)

            for i, submodel_element in enumerate(submodel_elements.values):
                # NOTE (mristin, 2022-06-20):
                # ID-shorts are mandatory, so we always override them, regardless if
                # they existed or not.
                with _extend_in_place(path_segments, ["submodel_elements", i]):
                    submodel_element.properties[
                        "ID_short"
                    ] = f"some_id_short_{_hash_path(path_segments)}"

        # region Fix qualifiers for the constraint AASd-119

        qualifier_kind_enum = self.symbol_table.must_find_enumeration(
            Identifier("Qualifier_kind")
        )

        qualifier_kind_template_qualifier = qualifier_kind_enum.literals_by_name[
            "Template_qualifier"
        ].value

        qualifiers = instance.properties.get("qualifiers", None)
        if qualifiers is not None:
            must_be_modelling_kind_template = False

            assert isinstance(qualifiers, ListOfInstances)
            for qualifier in qualifiers.values:
                if (
                    qualifier.properties.get("kind", None)
                    == qualifier_kind_template_qualifier
                ):
                    must_be_modelling_kind_template = True
                    break

            if must_be_modelling_kind_template:
                modelling_kind_enum = self.symbol_table.must_find_enumeration(
                    Identifier("Modelling_kind")
                )

                modelling_kind_template = modelling_kind_enum.literals_by_name[
                    "Template"
                ].value

                instance.properties["kind"] = modelling_kind_template

        # endregion

        self._recurse_into_properties(instance=instance, path_segments=path_segments)

    def _fix_submodel_element_collection(
        self, instance: Instance, path_segments: List[Union[str, int]]
    ) -> None:
        # Fix that ID-shorts are always defined for the items of a submodel element
        # collection
        value = instance.properties.get("value", None)
        if value is not None:
            assert isinstance(value, ListOfInstances)

            for item in value.values:
                if "ID_short" not in item.properties:
                    with _extend_in_place(path_segments, ["ID_short"]):
                        hsh = _hash_path(path_segments=path_segments)
                        item.properties["ID_short"] = f"something_random_{hsh}"

        self._recurse_into_properties(instance=instance, path_segments=path_segments)

    def _fix_submodel_element_list(
        self, instance: Instance, path_segments: List[Union[str, int]]
    ) -> None:
        value = instance.properties.get("value", None)
        if value is not None:
            # NOTE (mristin, 2022-06-22):
            # Re-create the elements according to a fixed recipe. This is brutish, but
            # otherwise it is too complex to get the fixing logic right.

            property_cls = self.symbol_table.must_find_concrete_class(
                Identifier("Property")
            )

            data_type_def_xsd_enum = self.symbol_table.must_find_enumeration(
                Identifier("Data_type_def_XSD")
            )

            xs_boolean_literal = data_type_def_xsd_enum.literals_by_name["Boolean"]

            aas_submodel_elements_enum = self.symbol_table.must_find_enumeration(
                Identifier("AAS_submodel_elements")
            )

            property_literal = aas_submodel_elements_enum.literals_by_name["Property"]

            semantic_id = _generate_global_reference(path_segments)

            with _extend_in_place(path_segments, ["value", 0]):
                value0 = generate_minimal_instance(
                    cls=property_cls,
                    path_segments=path_segments,
                    constraints_by_class=self.constraints_by_class,
                    symbol_table=self.symbol_table,
                )
                value0.properties["value_type"] = xs_boolean_literal.value
                value0.properties["semantic_ID"] = semantic_id

            with _extend_in_place(path_segments, ["value", 1]):
                value1 = generate_minimal_instance(
                    cls=property_cls,
                    path_segments=path_segments,
                    constraints_by_class=self.constraints_by_class,
                    symbol_table=self.symbol_table,
                )
                value1.properties["value_type"] = xs_boolean_literal.value
                value1.properties["semantic_ID"] = semantic_id

            values = [value0, value1]

            instance.properties["value"] = ListOfInstances(values=values)
            instance.properties["type_value_list_element"] = property_literal.value
            instance.properties["value_type_list_element"] = xs_boolean_literal.value
            instance.properties["semantic_ID_list_element"] = semantic_id

        self._recurse_into_properties(instance=instance, path_segments=path_segments)


@ensure(lambda result: result[0].model_type == "Environment")
def generate_minimal_instance_in_minimal_environment(
    cls: intermediate.ConcreteClass,
    class_graph: ontology.ClassGraph,
    constraints_by_class: MutableMapping[
        intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
    ],
    symbol_table: intermediate.SymbolTable,
) -> Tuple[Instance, List[Union[str, int]]]:
    """
    Generate the minimal instance of ``cls`` in a minimal environment instance.

    The environment needs to be fixed after the generation. Use :class:`~Handyman`.

    Return the environment and the path to the instance.
    """
    if cls is symbol_table.must_find_concrete_class(Identifier("Reference")):
        # NOTE (mristin, 2022-07-10):
        # We manually create the environment for the ``Reference`` class as we want
        # to avoid any constraints on the target.
        path_segments = ["submodels", 0, "semantic_ID"]  # type: List[Union[str, int]]
        container = Instance(
            properties=collections.OrderedDict(
                [
                    (
                        "submodels",
                        ListOfInstances(
                            values=[
                                Instance(
                                    properties=collections.OrderedDict(
                                        [
                                            ("ID", "some_submodel"),
                                            (
                                                "semantic_ID",
                                                _generate_global_reference(
                                                    path_segments=path_segments
                                                ),
                                            ),
                                        ]
                                    ),
                                    model_type=Identifier("Submodel"),
                                )
                            ]
                        ),
                    )
                ]
            ),
            model_type=Identifier("Environment"),
        )

        return container, path_segments

    shortest_path_in_class_graph_from_environment = class_graph.shortest_paths[cls.name]

    if len(shortest_path_in_class_graph_from_environment) == 0:
        # NOTE (mristin, 2022-06-25):
        # Cover the edge case where we have to generate the environment itself
        environment_cls = symbol_table.must_find_concrete_class(
            Identifier("Environment")
        )

        return (
            generate_minimal_instance(
                cls=environment_cls,
                path_segments=[],
                constraints_by_class=constraints_by_class,
                symbol_table=symbol_table,
            ),
            [],
        )

    environment_instance: Optional[Instance] = None

    path_segments = []
    source_instance: Optional[Instance] = None

    instance_path = None  # type: Optional[List[Union[int, str]]]

    for i, edge in enumerate(shortest_path_in_class_graph_from_environment):
        if source_instance is None:
            assert edge.source.name == "Environment", (
                "Expected the generation to start from an instance "
                "of the class 'Environment'"
            )
            source_instance = generate_minimal_instance(
                cls=edge.source,
                path_segments=[],
                constraints_by_class=constraints_by_class,
                symbol_table=symbol_table,
            )
            environment_instance = source_instance

        target_instance: Optional[Instance] = None

        if isinstance(edge.relationship, ontology.PropertyRelationship):
            prop_name = edge.relationship.property_name

            path_segments.append(prop_name)

            target_instance = generate_minimal_instance(
                cls=edge.target,
                path_segments=path_segments,
                constraints_by_class=constraints_by_class,
                symbol_table=symbol_table,
            )

            source_instance.properties[prop_name] = target_instance

        elif isinstance(edge.relationship, ontology.ListPropertyRelationship):
            prop_name = edge.relationship.property_name
            path_segments.append(prop_name)
            path_segments.append(0)

            target_instance = generate_minimal_instance(
                cls=edge.target,
                path_segments=path_segments,
                constraints_by_class=constraints_by_class,
                symbol_table=symbol_table,
            )

            source_instance.properties[prop_name] = ListOfInstances(
                values=[target_instance]
            )

        else:
            aas_core_codegen.common.assert_never(edge.relationship)

        if i == len(shortest_path_in_class_graph_from_environment) - 1:
            instance_path = list(path_segments)

        assert target_instance is not None
        source_instance = target_instance

    # NOTE (mristin, 2022-05-12):
    # The name ``source_instance`` is a bit of a misnomer here. We actually refer to
    # the last generated instance which should be our desired final instance.
    assert source_instance is not None

    assert environment_instance is not None
    assert instance_path is not None

    return environment_instance, instance_path


def make_minimal_instance_complete(
    instance: Instance,
    path_segments: List[Union[int, str]],
    cls: intermediate.ConcreteClass,
    constraints_by_class: MutableMapping[
        intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
    ],
    symbol_table: intermediate.SymbolTable,
) -> None:
    """
    Set all the optional properties in the ``instance`` in-place.

    The containing environment needs to be fixed afterwards. Use :class:`~Handyman`.
    """
    constraints_by_prop = constraints_by_class[cls]

    for prop in cls.properties:
        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            type_anno = intermediate.beneath_optional(prop.type_annotation)

            with _extend_in_place(path_segments, [prop.name]):
                # fmt: off
                instance.properties[prop.name] = _generate_property_value(
                    type_annotation=type_anno,
                    path_segments=path_segments,
                    len_constraint=constraints_by_prop.len_constraints_by_property.get(
                        prop, None
                    ),
                    pattern_constraints=constraints_by_prop.patterns_by_property.get(
                        prop, None
                    ),
                    set_of_primitives_constraint=(
                        constraints_by_prop
                        .set_of_primitives_by_property
                        .get(
                            prop, None
                        )
                    ),
                    set_of_enumeration_literals_constraint=(
                        constraints_by_prop
                        .set_of_enumeration_literals_by_property
                        .get(
                            prop, None
                        )
                    ),
                    generate_instance=(
                        lambda a_cls, a_path_segments: generate_minimal_instance(
                            cls=a_cls,
                            path_segments=a_path_segments,
                            constraints_by_class=constraints_by_class,
                            symbol_table=symbol_table,
                        )
                    ),
                )
                # fmt: on


class ContainerInstanceReplicator:
    """Make a deep copy of the container and dereference the instance in the copy."""

    def __init__(
        self,
        container: Instance,
        container_class: intermediate.ConcreteClass,
        path_to_instance: Sequence[Union[str, int]],
    ) -> None:
        """Initialize with the given values."""
        # NOTE (mristin, 2022-06-20):
        # Make a copy so that modifications do not mess it up
        self.container = _deep_copy(container)
        self.container_class = container_class
        self.path_to_instance = list(path_to_instance)

    def replicate(self) -> Tuple[Instance, Instance, List[Union[str, int]]]:
        """Replicate the environment and dereference the instance in the copy."""
        new_container = _deep_copy(self.container)
        assert isinstance(new_container, Instance)

        return (
            new_container,
            dereference(
                container=new_container,
                path_segments=self.path_to_instance,
            ),
            list(self.path_to_instance),
        )


class _Replication:
    """Structure the information necessary to replicate a starting point of a case."""

    def __init__(
        self,
        minimal: ContainerInstanceReplicator,
        complete: ContainerInstanceReplicator,
    ) -> None:
        self.minimal = minimal
        self.complete = complete


class Case(DBC):
    """Represent an abstract test case."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        expected: bool,
        cls: intermediate.ConcreteClass,
    ) -> None:
        """Initialize with the given values."""
        self.container_class = container_class
        self.container = container
        self.expected = expected
        self.cls = cls


class CaseMinimal(Case):
    """Represent a minimal test case."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        cls: intermediate.ConcreteClass,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=True,
            cls=cls,
        )


class CaseComplete(Case):
    """Represent a complete test case."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        cls: intermediate.ConcreteClass,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=True,
            cls=cls,
        )


class CaseTypeViolation(Case):
    """Represent a test case where a property has invalid type."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        cls: intermediate.ConcreteClass,
        property_name: Identifier,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=False,
            cls=cls,
        )
        self.property_name = property_name


class CasePositivePatternExample(Case):
    """Represent a test case with a property set to a pattern example."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        cls: intermediate.ConcreteClass,
        property_name: Identifier,
        example_name: str,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=True,
            cls=cls,
        )
        self.property_name = property_name
        self.example_name = example_name


class CasePatternViolation(Case):
    """Represent a test case with a property set to a pattern example."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        cls: intermediate.ConcreteClass,
        property_name: Identifier,
        example_name: str,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=False,
            cls=cls,
        )
        self.property_name = property_name
        self.example_name = example_name


class CaseRequiredViolation(Case):
    """Represent a test case where a required property is missing."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        cls: intermediate.ConcreteClass,
        property_name: Identifier,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=False,
            cls=cls,
        )
        self.property_name = property_name


class CaseMinLengthViolation(Case):
    """Represent a test case where a min. len constraint is violated."""

    @require(lambda cls, prop: id(prop) in cls.property_id_set)
    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        cls: intermediate.ConcreteClass,
        prop: intermediate.Property,
        min_value: int,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=False,
            cls=cls,
        )
        self.prop = prop
        self.min_value = min_value


class CaseMaxLengthViolation(Case):
    """Represent a test case where a max. len constraint is violated."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        cls: intermediate.ConcreteClass,
        property_name: Identifier,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=False,
            cls=cls,
        )
        self.property_name = property_name


class CaseUnexpectedAdditionalProperty(Case):
    """Represent a test case where there is an unexpected property in the instance."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        cls: intermediate.ConcreteClass,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=False,
            cls=cls,
        )


class CaseDateTimeUtcViolationOnFebruary29th(Case):
    """Represent a test case where we supply an invalid UTC date time stamp."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        cls: intermediate.ConcreteClass,
        property_name: Identifier,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=False,
            cls=cls,
        )
        self.property_name = property_name


class CasePositiveValueExample(Case):
    """Represent a test case with a XSD value set to a positive example."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        cls: intermediate.ConcreteClass,
        data_type_def_literal: intermediate.EnumerationLiteral,
        example_name: str,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=True,
            cls=cls,
        )
        self.data_type_def_literal = data_type_def_literal
        self.example_name = example_name


class CaseInvalidValueExample(Case):
    """Represent a test case with a XSD value set to a negative example."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        cls: intermediate.ConcreteClass,
        data_type_def_literal: intermediate.EnumerationLiteral,
        example_name: str,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=False,
            cls=cls,
        )
        self.data_type_def_literal = data_type_def_literal
        self.example_name = example_name


class CasePositiveMinMaxExample(Case):
    """Represent a test case with a min/max XSD values set to a positive example."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        cls: intermediate.ConcreteClass,
        data_type_def_literal: intermediate.EnumerationLiteral,
        example_name: str,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=True,
            cls=cls,
        )
        self.data_type_def_literal = data_type_def_literal
        self.example_name = example_name


class CaseInvalidMinMaxExample(Case):
    """Represent a test case with a min/max XSD values set to a negative example."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        cls: intermediate.ConcreteClass,
        data_type_def_literal: intermediate.EnumerationLiteral,
        example_name: str,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=False,
            cls=cls,
        )
        self.data_type_def_literal = data_type_def_literal
        self.example_name = example_name


class CaseEnumViolation(Case):
    """Represent a test case with a min/max XSD values set to a negative example."""

    # fmt: off
    @require(
        lambda enum, prop: (
            type_anno := intermediate.beneath_optional(prop.type_annotation),
            isinstance(type_anno, intermediate.OurTypeAnnotation)
            and type_anno.our_type == enum,
        )[1],
        "Enum corresponds to the property",
    )
    @require(
        lambda cls, prop: id(prop) in cls.property_id_set,
        "Property belongs to the class",
    )
    # fmt: on
    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        enum: intermediate.Enumeration,
        cls: intermediate.ConcreteClass,
        prop: intermediate.Property,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=False,
            cls=cls,
        )
        self.enum = enum
        self.prop = prop


class CasePositiveManual(Case):
    """Represent a custom-tailored positive case."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        cls: intermediate.ConcreteClass,
        name: str,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=True,
            cls=cls,
        )
        self.name = name


class CaseSetViolation(Case):
    """Represent a case where a property is outside a constrained set."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        cls: intermediate.ConcreteClass,
        property_name: Identifier,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=False,
            cls=cls,
        )
        self.property_name = property_name


class CaseConstraintViolation(Case):
    """Represent a custom-tailored negative case that violates a constraint."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        container: Instance,
        cls: intermediate.ConcreteClass,
        name: str,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            container=container,
            expected=False,
            cls=cls,
        )
        self.name = name


CaseUnion = Union[
    CaseMinimal,
    CaseComplete,
    CaseTypeViolation,
    CasePositivePatternExample,
    CasePatternViolation,
    CaseRequiredViolation,
    CaseMinLengthViolation,
    CaseMaxLengthViolation,
    CaseUnexpectedAdditionalProperty,
    CaseDateTimeUtcViolationOnFebruary29th,
    CasePositiveValueExample,
    CaseInvalidValueExample,
    CasePositiveMinMaxExample,
    CaseInvalidMinMaxExample,
    CaseEnumViolation,
    CasePositiveManual,
    CaseSetViolation,
    CaseConstraintViolation,
]

aas_core_codegen.common.assert_union_of_descendants_exhaustive(
    union=CaseUnion, base_class=Case
)


# fmt: off
# noinspection PyUnusedLocal
@require(
    lambda len_constraint:
    len_constraint.min_value is not None
    and len_constraint.min_value > 0
)
# fmt: on
def _make_instance_violate_min_len_constraint(
    instance: Instance,
    prop: intermediate.Property,
    len_constraint: infer_for_schema.LenConstraint,
) -> None:
    """Modify the ``instance`` in-place so that it violates the ``len_constraint``."""
    # NOTE (mristin, 2022-05-15):
    # We handle only a subset of cases here automatically since
    # otherwise it would be too difficult to implement. The
    # remainder of the cases needs to be implemented manually.

    type_anno = intermediate.beneath_optional(prop.type_annotation)

    # NOTE (mristin, 2022-06-20):
    # Please consider that the ``min_value > 0`` is in the pre-conditions.

    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
        if type_anno.a_type is intermediate.PrimitiveType.STR:
            instance.properties[prop.name] = ""

    elif (
        isinstance(type_anno, intermediate.OurTypeAnnotation)
        and isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive)
        and (type_anno.our_type.constrainee is intermediate.PrimitiveType.STR)
    ):
        instance.properties[prop.name] = ""

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        instance.properties[prop.name] = ListOfInstances(values=[])

    else:
        raise NotImplementedError(
            f"We did not implement the violation of len constraint "
            f"on property {prop.name!r} of type {prop.type_annotation}. "
            f"Please contact the developers."
        )


# fmt: off
# noinspection PyUnusedLocal
@require(
    lambda len_constraint:
    len_constraint.max_value is not None
)
# fmt: on
def _make_instance_violate_max_len_constraint(
    instance: Instance,
    prop: intermediate.Property,
    path_segments: List[Union[str, int]],
    len_constraint: infer_for_schema.LenConstraint,
) -> None:
    """
    Modify the ``instance`` in-place so that it violates the ``len_constraint``.

    ``path_segments`` refer to the instance, not property.
    """
    # NOTE (mristin, 2022-05-15):
    # We handle only a subset of cases here automatically since
    # otherwise it would be too difficult to implement. The
    # remainder of the cases needs to be implemented manually.
    #
    # We also optimistically assume we do not break any patterns,
    # invariants *etc.* If that is the case, you have to write
    # manual generation code.

    type_anno = intermediate.beneath_optional(prop.type_annotation)

    assert len_constraint.max_value is not None  # for mypy

    with _extend_in_place(path_segments, [prop.name]):
        too_long_text = _generate_long_string(
            length=len_constraint.max_value + 1, path_segments=path_segments
        )

    handled = False

    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
        if type_anno.a_type is intermediate.PrimitiveType.STR:
            instance.properties[prop.name] = too_long_text
            handled = True

        else:
            handled = False

    elif (
        isinstance(type_anno, intermediate.OurTypeAnnotation)
        and isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive)
        and (type_anno.our_type.constrainee is intermediate.PrimitiveType.STR)
    ):
        instance.properties[prop.name] = too_long_text
        handled = True

    else:
        handled = False

    if not handled:
        raise NotImplementedError(
            "We could not generate the data to violate the length constraint for "
            f"the property {prop.name!r} at {_posix_path(path_segments)}. "
            f"You have to either generate the data manually, or contact the developers "
            f"to implement this missing feature."
        )


def _generate_additional_cases_for_submodel_element_list(
    replication_map: Mapping[Identifier, _Replication],
    constraints_by_class: MutableMapping[
        intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
    ],
    symbol_table: intermediate.SymbolTable,
) -> Iterator[CaseUnion]:
    # region Dependencies
    cls = symbol_table.must_find_concrete_class(Identifier("Submodel_element_list"))

    property_cls = symbol_table.must_find_concrete_class(Identifier("Property"))

    data_type_def_xsd_enum = symbol_table.must_find_enumeration(
        Identifier("Data_type_def_XSD")
    )

    xs_boolean_literal = data_type_def_xsd_enum.literals_by_name["Boolean"]
    xs_int_literal = data_type_def_xsd_enum.literals_by_name["Int"]

    aas_submodel_elements_enum = symbol_table.must_find_enumeration(
        Identifier("AAS_submodel_elements")
    )

    property_literal = aas_submodel_elements_enum.literals_by_name["Property"]

    range_cls = symbol_table.must_find_concrete_class(Identifier("Range"))

    semantic_id = _generate_global_reference(path_segments=["some-dummy"])
    another_semantic_id = _generate_global_reference(path_segments=["another-dummy"])

    # endregion

    # region Prepare replicator

    replication = replication_map[Identifier("Submodel_element_list")]

    replicator = replication.minimal
    container, instance, path_segments = replicator.replicate()

    with _extend_in_place(path_segments, ["value", 0]):
        value0 = generate_minimal_instance(
            cls=property_cls,
            path_segments=path_segments,
            constraints_by_class=constraints_by_class,
            symbol_table=symbol_table,
        )
        value0.properties["value_type"] = xs_boolean_literal.value
        value0.properties["semantic_ID"] = semantic_id

    with _extend_in_place(path_segments, ["value", 1]):
        value1 = generate_minimal_instance(
            cls=property_cls,
            path_segments=path_segments,
            constraints_by_class=constraints_by_class,
            symbol_table=symbol_table,
        )
        value1.properties["value_type"] = xs_boolean_literal.value
        value1.properties["semantic_ID"] = semantic_id

    values = [value0, value1]

    instance.properties["value"] = ListOfInstances(values=values)
    instance.properties["type_value_list_element"] = property_literal.value
    instance.properties["value_type_list_element"] = xs_boolean_literal.value
    instance.properties["semantic_ID_list_element"] = semantic_id

    # Set up a new replicator
    replicator = ContainerInstanceReplicator(
        container=container,
        container_class=replicator.container_class,
        path_to_instance=path_segments,
    )

    # region Expected: one child without semantic ID

    container, instance, path_segments = replicator.replicate()
    assert isinstance(instance.properties["value"], ListOfInstances)
    del instance.properties["value"].values[0].properties["semantic_ID"]

    yield CasePositiveManual(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="one_child_without_semantic_ID",
    )

    # endregion

    # region Expected: no semantic_ID_list_element

    container, instance, path_segments = replicator.replicate()
    del instance.properties["semantic_ID_list_element"]

    yield CasePositiveManual(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="no_semantic_id_list_element",
    )

    # endregion

    # region Unexpected: values property and range against type_value_list_element

    container, instance, path_segments = replicator.replicate()

    with _extend_in_place(path_segments, ["value", 0]):
        value0 = generate_minimal_instance(
            cls=property_cls,
            path_segments=path_segments,
            constraints_by_class=constraints_by_class,
            symbol_table=symbol_table,
        )
        value0.properties["value_type"] = xs_boolean_literal.value
        value0.properties["semantic_ID"] = semantic_id

    with _extend_in_place(path_segments, ["value", 1]):
        value1 = generate_minimal_instance(
            cls=range_cls,
            path_segments=path_segments,
            constraints_by_class=constraints_by_class,
            symbol_table=symbol_table,
        )
        value1.properties["value_type"] = xs_boolean_literal.value
        value1.properties["semantic_ID"] = semantic_id

    instance.properties["value"] = ListOfInstances(values=[value0, value1])

    yield CaseConstraintViolation(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="against_type_value_list_element",
    )

    # endregion

    # region Unexpected: a property against value_type_list_element

    container, instance, path_segments = replicator.replicate()

    with _extend_in_place(path_segments, ["value", 0]):
        value0 = generate_minimal_instance(
            cls=property_cls,
            path_segments=path_segments,
            constraints_by_class=constraints_by_class,
            symbol_table=symbol_table,
        )
        value0.properties["value_type"] = xs_int_literal.value
        value0.properties["semantic_ID"] = semantic_id

    instance.properties["value"] = ListOfInstances(values=[value0])

    yield CaseConstraintViolation(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="against_value_type_list_element",
    )

    # endregion

    # region Unexpected: against semantic_id_list_element

    container, instance, path_segments = replicator.replicate()

    with _extend_in_place(path_segments, ["value", 0]):
        value0 = generate_minimal_instance(
            cls=property_cls,
            path_segments=path_segments,
            constraints_by_class=constraints_by_class,
            symbol_table=symbol_table,
        )
        value0.properties["value_type"] = xs_boolean_literal.value
        value0.properties["semantic_ID"] = another_semantic_id

    instance.properties["value"] = ListOfInstances(values=[value0])

    yield CaseConstraintViolation(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="against_semantic_id_list_element",
    )

    # endregion

    # region Unexpected: no semantic_id_list_element, but mismatch in values

    container, instance, path_segments = replicator.replicate()

    with _extend_in_place(path_segments, ["value", 0]):
        value0 = generate_minimal_instance(
            cls=property_cls,
            path_segments=path_segments,
            constraints_by_class=constraints_by_class,
            symbol_table=symbol_table,
        )
        value0.properties["value_type"] = xs_boolean_literal.value
        value0.properties["semantic_ID"] = semantic_id

    with _extend_in_place(path_segments, ["value", 1]):
        value1 = generate_minimal_instance(
            cls=property_cls,
            path_segments=path_segments,
            constraints_by_class=constraints_by_class,
            symbol_table=symbol_table,
        )
        value1.properties["value_type"] = xs_boolean_literal.value
        value1.properties["semantic_ID"] = another_semantic_id

    instance.properties["value"] = ListOfInstances(values=[value0, value1])
    del instance.properties["semantic_ID_list_element"]

    yield CaseConstraintViolation(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="no_semantic_id_list_element_but_semantic_id_mismatch_in_value",
    )

    # endregion

    # region Unexpected: element with ID-short

    container, instance, path_segments = replicator.replicate()

    with _extend_in_place(path_segments, ["value", 0]):
        value0 = generate_minimal_instance(
            cls=property_cls,
            path_segments=path_segments,
            constraints_by_class=constraints_by_class,
            symbol_table=symbol_table,
        )
        value0.properties["value_type"] = xs_boolean_literal.value
        value0.properties["semantic_ID"] = semantic_id

        value0.properties["ID_short"] = "unexpected"

    instance.properties["value"] = ListOfInstances(values=[value0])

    yield CaseConstraintViolation(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="id_short_in_a_value",
    )

    # endregion


class _ReferenceConstructor:
    """Help make the construction code of the references a bit more succinct."""

    def __init__(
        self,
        replicator: ContainerInstanceReplicator,
        symbol_table: intermediate.SymbolTable,
        reference_type: str,
    ) -> None:
        """Initialize with the given values."""
        self.replicator = replicator
        self.symbol_table = symbol_table

        reference_types_enum = symbol_table.must_find_enumeration(
            Identifier("Reference_types")
        )

        # fmt: off
        reference_type_literal = (
            reference_types_enum.literals_by_name.get(reference_type, None)
        )
        # fmt: on

        if reference_type_literal is None:
            raise KeyError(
                f"The reference type {reference_type!r} could not be found as literal "
                f"in {reference_types_enum.name}"
            )

        self.reference_type = reference_type_literal.value

        # List of (key type, key value)
        self._chain = []  # type: List[Tuple[str, str]]

        self.key_types_enum = symbol_table.must_find_enumeration(
            Identifier("Key_types")
        )

    def add_key(self, key_type: str, key_value: str) -> None:
        """Add the key to reference keys."""
        literal = self.key_types_enum.literals_by_name.get(key_type, None)
        if literal is None:
            raise KeyError(
                f"The key type {key_type!r} could not be found "
                f"in the enumeration {self.key_types_enum.name}"
            )

        self._chain.append((literal.value, key_value))

    def construct(self) -> Tuple[Instance, Instance, List[Union[int, str]]]:
        """
        Construct the reference based on the instructions.

        Return the container, the instance and the path segments to the instance.
        """
        container, instance, path_segments = self.replicator.replicate()

        instance.properties["type"] = self.reference_type

        instance.properties["keys"] = ListOfInstances(
            values=[
                Instance(
                    properties=collections.OrderedDict(
                        [("type", key_type), ("value", key_value)]
                    ),
                    model_type=Identifier("Key"),
                )
                for key_type, key_value in self._chain
            ]
        )

        return container, instance, path_segments


def _generate_additional_cases_for_reference(
    replication_map: Mapping[Identifier, _Replication],
    constraints_by_class: MutableMapping[
        intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
    ],
    symbol_table: intermediate.SymbolTable,
) -> Iterator[CaseUnion]:
    # NOTE (mristin, 2022-07-10):
    # Originally, we wrote this function as a long monolith. This was easier to read
    # on a first pass, but it was very difficult to maintain as small changes forced
    # us to check long code in too much detail.
    #
    # Therefore, we introduced a couple of helper functions which help to keep the focus
    # of the reader on the important details, instead of the boilerplate. Please bear
    # with us, dear reader, and make first the mental map of the helper functions first
    # before you try to understand the body of this function.

    # region Dependencies

    cls = symbol_table.must_find_concrete_class(Identifier("Reference"))

    replication = replication_map[Identifier("Reference")]
    replicator = replication.minimal

    def new_constructor_of_model_reference() -> _ReferenceConstructor:
        """
        Produce a constructor of a model reference.

        This makes the code much shorter and the examples a bit more readable even
        though it takes the reader a bit longer to understand the code in
        the first pass.
        """
        return _ReferenceConstructor(
            replicator=replicator,
            symbol_table=symbol_table,
            reference_type="Model_reference",
        )

    def new_constructor_of_external_reference() -> _ReferenceConstructor:
        """
        Produce a constructor of an external reference.

        This makes the code much shorter and the examples a bit more readable even
        though it takes the reader a bit longer to understand the code in
        the first pass.
        """
        return _ReferenceConstructor(
            replicator=replicator,
            symbol_table=symbol_table,
            reference_type="External_reference",
        )

    def assert_key_type_in_set(
        key_type: str,
        the_set: str,
    ) -> None:
        """Assert in a succinct way that the Key type is in a set of Key types."""
        key_types_enum = symbol_table.must_find_enumeration(Identifier("Key_types"))

        key_types_literal = key_types_enum.literals_by_name.get(
            Identifier(key_type), None
        )

        assert key_types_literal is not None, f"{key_type=}"

        constant = symbol_table.constants_by_name.get(Identifier(the_set), None)
        assert constant is not None, f"{the_set=}"
        assert isinstance(constant, intermediate.ConstantSetOfEnumerationLiterals)

        assert (
            id(key_types_literal) in constant.literal_id_set
        ), f"{key_type=}, {constant=}"

    def assert_key_type_outside_set(
        key_type: str,
        the_set: str,
    ) -> None:
        """Assert in a succinct way that the Key type is outside a set of Key types."""
        key_types_enum = symbol_table.must_find_enumeration(Identifier("Key_types"))

        key_types_literal = key_types_enum.literals_by_name.get(
            Identifier(key_type), None
        )

        assert key_types_literal is not None, f"{key_type=}"

        constant = symbol_table.constants_by_name.get(Identifier(the_set), None)
        assert constant is not None, f"{constant=}"
        assert isinstance(constant, intermediate.ConstantSetOfEnumerationLiterals)

        assert (
            id(key_types_literal) not in constant.literal_id_set
        ), f"{key_type=}, {the_set=}"

    # endregion

    # NOTE (mristin, 2022-07-10):
    # We start with the negative examples first.

    # region First key not in Globally identifiables

    assert_key_type_outside_set(key_type="Blob", the_set="Globally_identifiables")

    constructor = new_constructor_of_model_reference()

    constructor.add_key(key_type="Blob", key_value="something")

    container, _, _ = constructor.construct()

    yield CaseConstraintViolation(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="first_key_not_in_globally_identifiables",
    )

    # endregion

    # region For an external references, first key not in Generic globally identifiables

    assert_key_type_outside_set(
        key_type="Blob", the_set="Generic_globally_identifiables"
    )

    constructor = new_constructor_of_external_reference()

    constructor.add_key(key_type="Blob", key_value="something")

    container, _, _ = constructor.construct()

    yield CaseConstraintViolation(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="for_an_external_reference_first_key_not_in_generic_globally_identifiables",
    )

    # endregion

    # region For a model reference, first key not in AAS identifiables

    assert_key_type_outside_set(
        key_type="Global_reference", the_set="AAS_identifiables"
    )

    constructor = new_constructor_of_model_reference()

    constructor.add_key(key_type="Global_reference", key_value="something")

    container, _, _ = constructor.construct()

    yield CaseConstraintViolation(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="for_a_model_reference_first_key_not_in_AAS_identifiables",
    )

    # endregion

    # region For an external reference invalid last key

    assert_key_type_outside_set(
        key_type="Blob", the_set="Generic_globally_identifiables"
    )

    assert_key_type_outside_set(key_type="Blob", the_set="Generic_fragment_keys")

    constructor = new_constructor_of_external_reference()

    constructor.add_key(key_type="Global_reference", key_value="something")
    constructor.add_key(key_type="Blob", key_value="something_more")

    container, _, _ = constructor.construct()

    yield CaseConstraintViolation(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="for_an_external_reference_invalid_last_key",
    )

    # endregion

    # region For a model reference second key not in fragment keys

    assert_key_type_outside_set(key_type="Global_reference", the_set="Fragment_keys")

    constructor = new_constructor_of_model_reference()

    constructor.add_key(key_type="Submodel", key_value="something")
    constructor.add_key(key_type="Global_reference", key_value="something_more")

    container, _, _ = constructor.construct()

    yield CaseConstraintViolation(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="for_a_model_reference_second_key_not_in_fragment_keys",
    )

    # endregion

    # region For a model reference generic fragment key in the middle

    assert_key_type_in_set(
        key_type="Fragment_reference", the_set="Generic_fragment_keys"
    )

    constructor = new_constructor_of_model_reference()

    constructor.add_key(key_type="Submodel", key_value="something")
    constructor.add_key(key_type="Fragment_reference", key_value="something_more")
    constructor.add_key(key_type="Property", key_value="yet_something_more")

    container, _, _ = constructor.construct()

    yield CaseConstraintViolation(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="for_a_model_reference_fragment_reference_in_the_middle",
    )

    # endregion

    # region For a model reference fragment reference not after file or blob

    assert_key_type_in_set(
        key_type="Fragment_reference", the_set="Generic_fragment_keys"
    )

    constructor = new_constructor_of_model_reference()

    constructor.add_key(key_type="Submodel", key_value="something")
    constructor.add_key(key_type="Property", key_value="something_more")
    constructor.add_key(key_type="Fragment_reference", key_value="yet_something_more")

    container, _, _ = constructor.construct()

    yield CaseConstraintViolation(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="for_a_model_reference_fragment_reference_not_after_file_or_blob",
    )

    # endregion

    # region For a model reference, invalid key value after submodel element list

    constructor = new_constructor_of_model_reference()

    constructor.add_key(key_type="Submodel", key_value="something")
    constructor.add_key(key_type="Submodel_element_list", key_value="something_more")
    constructor.add_key(key_type="Property", key_value="-1")

    container, _, _ = constructor.construct()

    yield CaseConstraintViolation(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="for_a_model_reference_invalid_key_value_after_submodel_element_list",
    )

    # endregion

    # NOTE (mristin, 2022-07-10):
    # Now we generate the positive examples.

    # region For an external references, first key in Generic globally identifiables

    assert_key_type_in_set(
        key_type="Global_reference", the_set="Globally_identifiables"
    )

    constructor = new_constructor_of_external_reference()

    constructor.add_key(key_type="Global_reference", key_value="something")

    container, _, _ = constructor.construct()

    yield CasePositiveManual(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="for_a_global_reference_first_key_in_generic_globally_identifiables",
    )

    # endregion

    # region For a model references, first key in globally and AAS identifiables

    assert_key_type_in_set(key_type="Submodel", the_set="Globally_identifiables")

    assert_key_type_in_set(key_type="Submodel", the_set="AAS_identifiables")

    constructor = new_constructor_of_model_reference()

    constructor.add_key(key_type="Submodel", key_value="something")

    container, _, _ = constructor.construct()

    yield CasePositiveManual(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="for_a_model_reference_first_key_in_globally_and_aas_identifiables",
    )

    # endregion

    # region For a global references, last key in generic globally identifiable

    assert_key_type_in_set(
        key_type="Global_reference", the_set="Generic_globally_identifiables"
    )

    constructor = new_constructor_of_external_reference()

    constructor.add_key(key_type="Global_reference", key_value="something")
    constructor.add_key(key_type="Global_reference", key_value="something_more")

    container, _, _ = constructor.construct()

    yield CasePositiveManual(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="for_a_global_reference_last_key_in_generic_globally_identifiable",
    )

    # endregion

    # region For a global references, last key in generic fragment keys

    assert_key_type_in_set(
        key_type="Fragment_reference", the_set="Generic_fragment_keys"
    )

    constructor = new_constructor_of_external_reference()

    constructor.add_key(key_type="Global_reference", key_value="something")
    constructor.add_key(key_type="Fragment_reference", key_value="something_more")

    container, _, _ = constructor.construct()

    yield CasePositiveManual(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="for_a_global_reference_last_key_in_generic_fragment_keys",
    )

    # endregion

    # region For a model references, fragment after blob

    constructor = new_constructor_of_model_reference()

    constructor.add_key(key_type="Submodel", key_value="something")
    constructor.add_key(key_type="Blob", key_value="something_more")
    constructor.add_key(key_type="Fragment_reference", key_value="yet_something_more")

    container, _, _ = constructor.construct()

    yield CasePositiveManual(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="for_a_model_reference_fragment_after_blob",
    )

    # endregion

    # region For a model reference, positive key value after submodel element list

    constructor = new_constructor_of_model_reference()

    constructor.add_key(key_type="Submodel", key_value="something")
    constructor.add_key(key_type="Submodel_element_list", key_value="something_more")
    constructor.add_key(key_type="Property", key_value="123")

    container, _, _ = constructor.construct()

    yield CasePositiveManual(
        container_class=replicator.container_class,
        container=container,
        cls=cls,
        name="for_a_model_reference_valid_key_value_after_submodel_element_list",
    )

    # endregion


def _compute_replication_map(
    symbol_table: intermediate.SymbolTable,
    constraints_by_class: MutableMapping[
        intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
    ],
    class_graph: ontology.ClassGraph,
    handyman: Handyman,
) -> MutableMapping[Identifier, _Replication]:
    """Determine for each class the starting minimal and complete test case."""
    environment_cls = symbol_table.must_find_concrete_class(Identifier("Environment"))

    replication_map = dict()  # type: MutableMapping[Identifier, _Replication]
    for our_type in symbol_table.our_types:
        if not isinstance(our_type, intermediate.ConcreteClass):
            continue

        if our_type.name not in class_graph.shortest_paths:
            # It is a self-contained class.

            container = generate_minimal_instance(
                cls=our_type,
                path_segments=[],
                constraints_by_class=constraints_by_class,
                symbol_table=symbol_table,
            )
            handyman.fix_instance(instance=container, path_segments=[])

            min_replicator = ContainerInstanceReplicator(
                container=container, container_class=our_type, path_to_instance=[]
            )

            make_minimal_instance_complete(
                instance=container,
                path_segments=[],
                cls=our_type,
                constraints_by_class=constraints_by_class,
                symbol_table=symbol_table,
            )

            handyman.fix_instance(instance=container, path_segments=[])

            complete_replicator = ContainerInstanceReplicator(
                container=container, container_class=our_type, path_to_instance=[]
            )
        else:
            env, path_segments = generate_minimal_instance_in_minimal_environment(
                cls=our_type,
                class_graph=class_graph,
                constraints_by_class=constraints_by_class,
                symbol_table=symbol_table,
            )

            instance = dereference(container=env, path_segments=path_segments)

            handyman.fix_instance(instance=env, path_segments=[])

            min_replicator = ContainerInstanceReplicator(
                container=env,
                container_class=environment_cls,
                path_to_instance=path_segments,
            )

            make_minimal_instance_complete(
                instance=instance,
                path_segments=path_segments,
                cls=our_type,
                constraints_by_class=constraints_by_class,
                symbol_table=symbol_table,
            )

            # TODO (mristin, 2023-03-3): continue here; property XXX is simply not added to data specification iec 6130!

            handyman.fix_instance(instance=env, path_segments=[])

            complete_replicator = ContainerInstanceReplicator(
                container=env,
                container_class=environment_cls,
                path_to_instance=path_segments,
            )

        replication_map[our_type.name] = _Replication(
            minimal=min_replicator, complete=complete_replicator
        )

    return replication_map


def _outside_set_of_primitives(
    constraint: infer_for_schema.SetOfPrimitivesConstraint,
) -> Union[bool, int, float, str, bytearray]:
    """Generate the value outside the constant set of primitive values."""
    if constraint.a_type in (
        intermediate.PrimitiveType.BOOL,
        intermediate.PrimitiveType.INT,
        intermediate.PrimitiveType.FLOAT,
        intermediate.PrimitiveType.BYTEARRAY,
    ):
        raise NotImplementedError(
            "We haven't implemented the generation of non-strings "
            "outside a set of primitives. Please contact the developers"
        )

    assert constraint.a_type is intermediate.PrimitiveType.STR

    value_set = set()  # type: Set[str]
    for literal in constraint.literals:
        assert isinstance(literal.value, str)
        value_set.add(literal.value)

    value = "unexpected value"
    while value in value_set:
        value = f"really {value}"

    return value


@require(
    lambda constraint: len(constraint.enumeration.literals) > len(constraint.literals),
    "At least one literal left outside",
)
def _outside_set_of_enumeration_literals(
    constraint: infer_for_schema.SetOfEnumerationLiteralsConstraint,
) -> str:
    """Generate a literal value for the enumeration outside the set of literals."""
    literal_id_set = set()  # type: Set[int]

    for literal in constraint.literals:
        literal_id_set.add(id(literal))

    # NOTE (mristin, 2022-07-10):
    # We pick the first to make the generation deterministic.

    for literal in constraint.enumeration.literals:
        if id(literal) not in literal_id_set:
            return literal.value

    raise AssertionError(
        f"No literals of the enumeration {constraint.enumeration.name!r} "
        f"are outside of the constraint"
    )


def generate(
    symbol_table: intermediate.SymbolTable,
    constraints_by_class: MutableMapping[
        intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
    ],
    class_graph: ontology.ClassGraph,
) -> Iterator[CaseUnion]:
    """Generate the test cases."""
    handyman = Handyman(
        symbol_table=symbol_table, constraints_by_class=constraints_by_class
    )

    replication_map = _compute_replication_map(
        symbol_table=symbol_table,
        constraints_by_class=constraints_by_class,
        class_graph=class_graph,
        handyman=handyman,
    )

    for our_type in symbol_table.our_types:
        if not isinstance(our_type, intermediate.ConcreteClass):
            continue

        replication = replication_map[our_type.name]

        # region Minimal example

        replicator = replication.minimal
        container, _, _ = replicator.replicate()

        yield CaseMinimal(
            container_class=replicator.container_class,
            container=container,
            cls=our_type,
        )

        # endregion

        # region Complete example

        replicator = replication.complete
        container, _, _ = replicator.replicate()

        yield CaseComplete(
            container_class=replicator.container_class,
            container=container,
            cls=our_type,
        )

        # endregion

        # region Type violation

        for prop in our_type.properties:
            replicator = replication.complete
            container, instance, path_segments = replicator.replicate()

            type_anno = intermediate.beneath_optional(prop.type_annotation)

            # NOTE (mristin, 2022-06-20):
            # If it is a primitive, supply a global reference.
            # If it is not a primitive, supply a string.

            if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation) or (
                isinstance(type_anno, intermediate.OurTypeAnnotation)
                and isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive)
            ):
                with _extend_in_place(path_segments, [prop.name]):
                    instance.properties[prop.name] = _generate_global_reference(
                        path_segments=path_segments
                    )

            else:
                with _extend_in_place(path_segments, [prop.name]):
                    instance.properties[prop.name] = "Unexpected string value"

            yield CaseTypeViolation(
                container_class=replicator.container_class,
                container=container,
                cls=our_type,
                property_name=prop.name,
            )

        # endregion

        # region Positive and negative pattern examples

        constraints_by_prop = constraints_by_class[our_type]

        for prop in our_type.properties:
            pattern_constraints = constraints_by_prop.patterns_by_property.get(
                prop, None
            )

            if pattern_constraints is None:
                continue

            if len(pattern_constraints) > 1:
                # NOTE (mristin, 2022-06-20):
                # We currently do not know how to handle multiple patterns,
                # so we skip these properties.
                continue

            pattern_examples = frozen_examples_pattern.BY_PATTERN[
                pattern_constraints[0].pattern
            ]

            for example_name, example_text in pattern_examples.positives.items():
                replicator = replication.minimal
                container, instance, path_segments = replicator.replicate()

                instance.properties[prop.name] = example_text

                yield CasePositivePatternExample(
                    container_class=replicator.container_class,
                    container=container,
                    cls=our_type,
                    property_name=prop.name,
                    example_name=example_name,
                )

            for example_name, example_text in pattern_examples.negatives.items():
                replicator = replication.minimal
                container, instance, _ = replicator.replicate()

                instance.properties[prop.name] = example_text

                yield CasePatternViolation(
                    container_class=replicator.container_class,
                    container=container,
                    cls=our_type,
                    property_name=prop.name,
                    example_name=example_name,
                )

        # endregion

        # region Required violation

        for prop in our_type.properties:
            if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
                continue

            replicator = replication.minimal
            container, instance, path_segments = replicator.replicate()

            del instance.properties[prop.name]

            yield CaseRequiredViolation(
                container_class=replicator.container_class,
                container=container,
                cls=our_type,
                property_name=prop.name,
            )

        # endregion

        # region Length violation

        for prop in our_type.properties:
            len_constraint = constraints_by_prop.len_constraints_by_property.get(
                prop, None
            )

            if len_constraint is None:
                continue

            if len_constraint.min_value is not None and len_constraint.min_value > 0:
                replicator = replication.minimal
                container, instance, path_segments = replicator.replicate()

                _make_instance_violate_min_len_constraint(
                    instance=instance, prop=prop, len_constraint=len_constraint
                )

                yield CaseMinLengthViolation(
                    container_class=replicator.container_class,
                    container=container,
                    cls=our_type,
                    prop=prop,
                    min_value=len_constraint.min_value,
                )

            if len_constraint.max_value is not None:
                replicator = replication.minimal
                container, instance, path_segments = replicator.replicate()

                _make_instance_violate_max_len_constraint(
                    instance=instance,
                    path_segments=path_segments,
                    prop=prop,
                    len_constraint=len_constraint,
                )

                yield CaseMaxLengthViolation(
                    container_class=replicator.container_class,
                    container=container,
                    cls=our_type,
                    property_name=prop.name,
                )

        # endregion

        # region Add unexpected additional property

        replicator = replication.minimal
        container, instance, path_segments = replicator.replicate()

        additional_prop_name = "unexpected_additional_property"
        while additional_prop_name in our_type.properties_by_name:
            additional_prop_name = f"really_{additional_prop_name}"

        instance.properties[additional_prop_name] = "INVALID"

        yield CaseUnexpectedAdditionalProperty(
            container_class=replicator.container_class,
            container=container,
            cls=our_type,
        )

        # endregion

        # region Break date-time with UTC with February 29th

        date_time_utc_symbol = symbol_table.must_find_constrained_primitive(
            Identifier("Date_time_UTC")
        )

        for prop in our_type.properties:
            type_anno = intermediate.beneath_optional(prop.type_annotation)
            if (
                isinstance(type_anno, intermediate.OurTypeAnnotation)
                and type_anno.our_type is date_time_utc_symbol
            ):
                replicator = replication.minimal
                container, instance, path_segments = replicator.replicate()

                with _extend_in_place(path_segments, [prop.name]):
                    time_of_day = _generate_time_of_day(path_segments=path_segments)

                    instance.properties[prop.name] = f"2022-02-29T{time_of_day}Z"

                    yield CaseDateTimeUtcViolationOnFebruary29th(
                        container_class=replicator.container_class,
                        container=container,
                        cls=our_type,
                        property_name=prop.name,
                    )

        # endregion

        # region Break property outside a constrained constant set of primitives

        for prop in our_type.properties:
            # fmt: off
            set_of_primitives_constraint = (
                constraints_by_prop
                .set_of_primitives_by_property
                .get(prop, None)
            )
            # fmt: on

            if set_of_primitives_constraint is not None:
                replicator = replication.minimal
                container, instance, path_segments = replicator.replicate()

                with _extend_in_place(path_segments, [prop.name]):
                    instance.properties[prop.name] = _outside_set_of_primitives(
                        constraint=set_of_primitives_constraint
                    )

                    yield CaseSetViolation(
                        container_class=replicator.container_class,
                        container=container,
                        cls=our_type,
                        property_name=prop.name,
                    )

        # endregion

        # region Break property outside a constrained constant set of enum literals

        for prop in our_type.properties:
            # fmt: off
            set_of_enum_literals_constraint = (
                constraints_by_prop
                .set_of_enumeration_literals_by_property
                .get(prop, None)
            )
            # fmt: on

            if set_of_enum_literals_constraint is not None and (
                len(set_of_enum_literals_constraint.enumeration.literals)
                > len(set_of_enum_literals_constraint.literals)
            ):
                replicator = replication.minimal
                container, instance, path_segments = replicator.replicate()

                with _extend_in_place(path_segments, [prop.name]):
                    instance.properties[
                        prop.name
                    ] = _outside_set_of_enumeration_literals(
                        constraint=set_of_enum_literals_constraint
                    )

                    yield CaseSetViolation(
                        container_class=replicator.container_class,
                        container=container,
                        cls=our_type,
                        property_name=prop.name,
                    )

        # endregion

    # region Generate positive and negative examples for Property and Range

    property_cls = symbol_table.must_find_concrete_class(Identifier("Property"))
    range_cls = symbol_table.must_find_concrete_class(Identifier("Range"))
    extension_cls = symbol_table.must_find_concrete_class(Identifier("Extension"))
    qualifier_cls = symbol_table.must_find_concrete_class(Identifier("Qualifier"))

    data_type_def_xsd_symbol = symbol_table.must_find_enumeration(
        Identifier("Data_type_def_XSD")
    )

    for cls in (property_cls, range_cls, extension_cls, qualifier_cls):
        replication = replication_map[cls.name]

        for literal in data_type_def_xsd_symbol.literals:
            examples = frozen_examples_xs_value.BY_VALUE_TYPE.get(literal.value, None)

            if examples is None:
                raise NotImplementedError(
                    f"The entry is missing "
                    f"in the {frozen_examples_xs_value.__name__!r} "
                    f"for the value type {literal.value!r}"
                )

            if cls in (property_cls, extension_cls, qualifier_cls):
                for example_name, example_value in examples.positives.items():
                    replicator = replication.minimal
                    container, instance, path_segments = replicator.replicate()

                    instance.properties["value"] = example_value
                    instance.properties["value_type"] = literal.value

                    yield CasePositiveValueExample(
                        container_class=replicator.container_class,
                        container=container,
                        cls=cls,
                        data_type_def_literal=literal,
                        example_name=example_name,
                    )

                for example_name, example_value in examples.negatives.items():
                    replicator = replication.minimal
                    container, instance, path_segments = replicator.replicate()

                    instance.properties["value"] = example_value
                    instance.properties["value_type"] = literal.value

                    yield CaseInvalidValueExample(
                        container_class=replicator.container_class,
                        container=container,
                        cls=cls,
                        data_type_def_literal=literal,
                        example_name=example_name,
                    )

            elif cls is range_cls:
                for example_name, example_value in examples.positives.items():
                    replicator = replication.minimal
                    container, instance, path_segments = replicator.replicate()

                    instance.properties["min"] = example_value
                    instance.properties["max"] = example_value
                    instance.properties["value_type"] = literal.value

                    yield CasePositiveMinMaxExample(
                        container_class=replicator.container_class,
                        container=container,
                        cls=cls,
                        data_type_def_literal=literal,
                        example_name=example_name,
                    )

                for example_name, example_value in examples.negatives.items():
                    replicator = replication.minimal
                    container, instance, path_segments = replicator.replicate()

                    instance.properties["min"] = example_value
                    instance.properties["max"] = example_value
                    instance.properties["value_type"] = literal.value

                    yield CaseInvalidMinMaxExample(
                        container_class=replicator.container_class,
                        container=container,
                        cls=cls,
                        data_type_def_literal=literal,
                        example_name=example_name,
                    )
            else:
                raise AssertionError(f"Unexpected {cls=}")

    # endregion

    # region Generate enum violations

    # fmt: off
    enums_props_classes: List[
        Tuple[
            intermediate.Enumeration,
            intermediate.Property,
            intermediate.ConcreteClass
        ]
    ] = []
    # fmt: on

    observed_enums = set()  # type: Set[Identifier]

    for our_type in symbol_table.our_types:
        if not isinstance(our_type, intermediate.ConcreteClass):
            continue

        for prop in our_type.properties:
            type_anno = intermediate.beneath_optional(prop.type_annotation)

            if not (
                isinstance(type_anno, intermediate.OurTypeAnnotation)
                and isinstance(type_anno.our_type, intermediate.Enumeration)
                and type_anno.our_type.name not in observed_enums
            ):
                continue

            enums_props_classes.append((type_anno.our_type, prop, our_type))

    for enum, prop, cls in enums_props_classes:
        replication = replication_map[cls.name]

        replicator = replication.minimal
        container, instance, path_segments = replicator.replicate()

        literal_value_set = {literal.value for literal in enum.literals}

        with _extend_in_place(path_segments, [prop.name]):
            literal_value = "invalid-literal"
            while literal_value in literal_value_set:
                literal_value = f"really-{literal_value}"

            instance.properties[prop.name] = literal_value

        yield CaseEnumViolation(
            container_class=replicator.container_class,
            container=container,
            enum=enum,
            cls=cls,
            prop=prop,
        )

    # endregion

    yield from _generate_additional_cases_for_submodel_element_list(
        replication_map=replication_map,
        constraints_by_class=constraints_by_class,
        symbol_table=symbol_table,
    )

    yield from _generate_additional_cases_for_reference(
        replication_map=replication_map,
        constraints_by_class=constraints_by_class,
        symbol_table=symbol_table,
    )
