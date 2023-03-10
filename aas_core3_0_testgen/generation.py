"""Generate the pre-serialized representation of the test data."""
import copy
from typing import Union, MutableMapping, Iterator, Sequence, Tuple

import aas_core_codegen.common
from aas_core_codegen import intermediate, infer_for_schema
from aas_core_codegen.common import Identifier
from icontract import require, DBC
import aas_core3.types as aas_types

from aas_core3_0_testgen.codegened import creation, wrapping, preserialization
from aas_core3_0_testgen import fixing, common


class Case(DBC):
    """Represent an abstract test case."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        preserialized_container: preserialization.Instance,
        expected: bool,
        cls: intermediate.ConcreteClass,
    ) -> None:
        """Initialize with the given values."""
        self.container_class = container_class
        self.preserialized_container = preserialized_container
        self.expected = expected
        self.cls = cls


class CaseMinimal(Case):
    """Represent a minimal test case."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        preserialized_container: preserialization.Instance,
        cls: intermediate.ConcreteClass,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
            expected=True,
            cls=cls,
        )


class CaseMaximal(Case):
    """Represent a maximal test case."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        preserialized_container: preserialization.Instance,
        cls: intermediate.ConcreteClass,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
            expected=True,
            cls=cls,
        )


class CaseTypeViolation(Case):
    """Represent a test case where a property has invalid type."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        preserialized_container: preserialization.Instance,
        cls: intermediate.ConcreteClass,
        property_name: Identifier,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
            expected=False,
            cls=cls,
        )
        self.property_name = property_name


class CasePositivePatternExample(Case):
    """Represent a test case with a property set to a pattern example."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        preserialized_container: preserialization.Instance,
        cls: intermediate.ConcreteClass,
        property_name: Identifier,
        example_name: str,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
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
        preserialized_container: preserialization.Instance,
        cls: intermediate.ConcreteClass,
        property_name: Identifier,
        example_name: str,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
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
        preserialized_container: preserialization.Instance,
        cls: intermediate.ConcreteClass,
        property_name: Identifier,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
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
        preserialized_container: preserialization.Instance,
        cls: intermediate.ConcreteClass,
        prop: intermediate.Property,
        min_value: int,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
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
        preserialized_container: preserialization.Instance,
        cls: intermediate.ConcreteClass,
        property_name: Identifier,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
            expected=False,
            cls=cls,
        )
        self.property_name = property_name


class CaseUnexpectedAdditionalProperty(Case):
    """Represent a test case where there is an unexpected property in the instance."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        preserialized_container: preserialization.Instance,
        cls: intermediate.ConcreteClass,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
            expected=False,
            cls=cls,
        )


class CaseDateTimeUtcViolationOnFebruary29th(Case):
    """Represent a test case where we supply an invalid UTC date time stamp."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        preserialized_container: preserialization.Instance,
        cls: intermediate.ConcreteClass,
        property_name: Identifier,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
            expected=False,
            cls=cls,
        )
        self.property_name = property_name


class CasePositiveValueExample(Case):
    """Represent a test case with a XSD value set to a positive example."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        preserialized_container: preserialization.Instance,
        cls: intermediate.ConcreteClass,
        data_type_def_literal: intermediate.EnumerationLiteral,
        example_name: str,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
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
        preserialized_container: preserialization.Instance,
        cls: intermediate.ConcreteClass,
        data_type_def_literal: intermediate.EnumerationLiteral,
        example_name: str,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
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
        preserialized_container: preserialization.Instance,
        cls: intermediate.ConcreteClass,
        data_type_def_literal: intermediate.EnumerationLiteral,
        example_name: str,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
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
        preserialized_container: preserialization.Instance,
        cls: intermediate.ConcreteClass,
        data_type_def_literal: intermediate.EnumerationLiteral,
        example_name: str,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
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
        preserialized_container: preserialization.Instance,
        enum: intermediate.Enumeration,
        cls: intermediate.ConcreteClass,
        prop: intermediate.Property,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
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
        preserialized_container: preserialization.Instance,
        cls: intermediate.ConcreteClass,
        name: str,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
            expected=True,
            cls=cls,
        )
        self.name = name


class CaseSetViolation(Case):
    """Represent a case where a property is outside a constrained set."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        preserialized_container: preserialization.Instance,
        cls: intermediate.ConcreteClass,
        property_name: Identifier,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
            expected=False,
            cls=cls,
        )
        self.property_name = property_name


class CaseConstraintViolation(Case):
    """Represent a custom-tailored negative case that violates a constraint."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        preserialized_container: preserialization.Instance,
        cls: intermediate.ConcreteClass,
        name: str,
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
            expected=False,
            cls=cls,
        )
        self.name = name


CaseUnion = Union[
    CaseMinimal,
    CaseMaximal,
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


class Replica:
    """
    Replicate the test example.

    This is usually used to replicate a minimal or a maximal example.
    """

    def __init__(
        self,
        container: aas_types.Class,
        instance: aas_types.Class,
        path: Sequence[Union[str, int]],
    ) -> None:
        """Initialize with the given values."""
        self.container = container
        self.instance = instance
        self.path = path

    def deepcopy(self) -> "Replica":
        """Make another deep copy of the replica."""

        container = copy.deepcopy(self.container)
        path = copy.copy(self.path)

        instance, error = common.dereference_instance(container, path, aas_types.Class)
        if error is not None:
            raise AssertionError(
                f"Could not dereference instance "
                f"at the path {common.instance_path_as_posix(path)} "
                f"in a deep-copied container: {error}"
            )

        assert instance is not None

        return Replica(container=container, instance=instance, path=path)


@require(lambda environment_cls: environment_cls.name == "Environment")
def _generate_minimal_case(
    cls: intermediate.ConcreteClass, environment_cls: intermediate.ConcreteClass
) -> Tuple[CaseMinimal, Replica]:
    """Generate the example of a minimal instance ready for serialization."""
    if wrapping.lives_in_environment(cls.name):
        environment, instance, path = wrapping.minimal_in_environment(cls.name)
        fixing.fix(environment)
        fixing.assert_instance_at_path_in_environment(environment, instance, path)

        return (
            CaseMinimal(
                container_class=environment_cls,
                preserialized_container=preserialization.preserialize(instance),
                cls=cls,
            ),
            Replica(container=environment, instance=instance, path=path),
        )
    else:
        path_hash = common.hash_path(None, [])
        instance = creation.concrete_minimal(path_hash, cls.name)

        return (
            CaseMinimal(
                container_class=environment_cls,
                preserialized_container=preserialization.preserialize(instance),
                cls=cls,
            ),
            # NOTE (mristin, 2023-03-10):
            # The instance is self-contained, so the container is also the instance.
            Replica(container=instance, instance=instance, path=[]),
        )


@require(lambda environment_cls: environment_cls.name == "Environment")
def _generate_maximal_case(
    cls: intermediate.ConcreteClass, environment_cls: intermediate.ConcreteClass
) -> Tuple[CaseMaximal, Replica]:
    """Generate the example of a minimal instance ready for serialization."""
    if wrapping.lives_in_environment(cls.name):
        environment, instance, path = wrapping.maximal_in_environment(cls.name)
        fixing.fix(environment)
        fixing.assert_instance_at_path_in_environment(environment, instance, path)

        return (
            CaseMaximal(
                container_class=environment_cls,
                preserialized_container=preserialization.preserialize(instance),
                cls=cls,
            ),
            Replica(container=environment, instance=instance, path=path),
        )
    else:
        path_hash = common.hash_path(None, [])
        instance = creation.concrete_maximal(path_hash, cls.name)

        return (
            CaseMaximal(
                container_class=environment_cls,
                preserialized_container=preserialization.preserialize(instance),
                cls=cls,
            ),
            # NOTE (mristin, 2023-03-10):
            # The instance is self-contained, so the container is also the instance.
            Replica(container=instance, instance=instance, path=[]),
        )


def generate(
    symbol_table: intermediate.SymbolTable,
    constraints_by_class: MutableMapping[
        intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
    ],
) -> Iterator[CaseUnion]:
    """Generate the test cases."""
    environment_cls = symbol_table.must_find_concrete_class(Identifier("Environment"))

    for our_type in symbol_table.our_types:
        if not isinstance(our_type, intermediate.ConcreteClass):
            continue

        # region Minimal example

        minimal_case, minimal_replica = _generate_minimal_case(
            cls=our_type, environment_cls=environment_cls
        )

        yield minimal_case

        # endregion

        # region Maximal example

        maximal_case, maximal_replica = _generate_maximal_case(
            cls=our_type, environment_cls=environment_cls
        )
        yield maximal_case

        # endregion

        # TODO (mristin, 2023-03-10): implement other cases once debugging done
