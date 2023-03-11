"""Generate the pre-serialized representation of the test data."""
import copy
from typing import Union, MutableMapping, Iterator, Sequence, Tuple, List

import aas_core3.types as aas_types
import aas_core_codegen.common
from aas_core_codegen import intermediate, infer_for_schema
from aas_core_codegen.common import Identifier
from icontract import require, DBC

from aas_core3_0_testgen import fixing, common
from aas_core3_0_testgen.codegened import creation, wrapping, preserialization


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


def _generate_customized_environment_and_minimal_instance_for_key(
) -> Tuple[aas_types.Environment, aas_types.Key, List[Union[str, int]]]:
    """
    Generate a custom-tailored minimal instance of the class Key wrapped in Environment.

    This customization is necessary as Reference constraints are tricky to fix in
    ``_Handyman``, so we hard-wire the generation here.
    """
    path_hash = common.hash_path(None, [])
    environment, instance_of_aas, path_to_aas = wrapping.minimal_in_environment(
        "Asset_administration_shell"
    )
    fixing.fix(environment)
    fixing.assert_instance_at_path_in_environment(
        environment, instance_of_aas, path_to_aas
    )

    assert isinstance(instance_of_aas, aas_types.AssetAdministrationShell)

    instance_of_aas.derived_from = fixing.generate_external_reference(
        common.hash_path(
            path_hash, path_to_aas + ["derived_from"]
        )
    )

    key = instance_of_aas.derived_from.keys[0]
    path = path_to_aas + ["derived_from", "keys", 0]

    fixing.assert_instance_at_path_in_environment(environment, key, path)
    return environment, key, path


def _generate_customized_environment_and_maximal_instance_for_key(
) -> Tuple[aas_types.Environment, aas_types.Key, List[Union[str, int]]]:
    """
    Generate a custom-tailored maximal instance of the class Key wrapped in Environment.

    This customization is necessary as Reference constraints are tricky to fix in
    ``_Handyman``, so we hard-wire the generation here.
    """
    path_hash = common.hash_path(None, [])
    environment, instance_of_aas, path_to_aas = wrapping.minimal_in_environment(
        "Asset_administration_shell"
    )
    fixing.fix(environment)
    fixing.assert_instance_at_path_in_environment(
        environment, instance_of_aas, path_to_aas
    )

    assert isinstance(instance_of_aas, aas_types.AssetAdministrationShell)

    instance_of_aas.derived_from = fixing.generate_external_reference(
        common.hash_path(
            path_hash, path_to_aas + ["derived_from"]
        )
    )

    key = instance_of_aas.derived_from.keys[0]
    path = path_to_aas + ["derived_from", "keys", 0]

    fixing.assert_instance_at_path_in_environment(environment, key, path)
    return environment, key, path


def _generate_customized_environment_and_minimal_instance_for_reference(
) -> Tuple[aas_types.Environment, aas_types.Reference, List[Union[str, int]]]:
    """
    Generate a tailored minimal instance of the class Reference wrapped in Environment.

    This customization is necessary as Reference constraints are tricky to fix in
    ``_Handyman``, so we hard-wire the generation here.
    """
    path_hash = common.hash_path(None, [])
    environment, instance_of_aas, path_to_aas = wrapping.minimal_in_environment(
        "Asset_administration_shell"
    )
    fixing.fix(environment)
    fixing.assert_instance_at_path_in_environment(
        environment, instance_of_aas, path_to_aas
    )

    assert isinstance(instance_of_aas, aas_types.AssetAdministrationShell)

    instance_of_aas.derived_from = fixing.generate_external_reference(
        common.hash_path(
            path_hash, path_to_aas + ["derived_from"]
        )
    )

    reference = instance_of_aas.derived_from
    path = path_to_aas + ["derived_from"]

    fixing.assert_instance_at_path_in_environment(environment, reference, path)
    return environment, reference, path


def _generate_customized_environment_and_maximal_instance_for_reference(
) -> Tuple[aas_types.Environment, aas_types.Reference, List[Union[str, int]]]:
    """
    Generate a tailored maximal instance of the class Reference wrapped in Environment.

    This customization is necessary as Reference constraints are tricky to fix in
    ``_Handyman``, so we hard-wire the generation here.
    """
    environment_path_hash = common.hash_path(None, [])
    environment, instance_of_aas, path_to_aas = wrapping.minimal_in_environment(
        "Asset_administration_shell"
    )
    fixing.fix(environment)
    fixing.assert_instance_at_path_in_environment(
        environment, instance_of_aas, path_to_aas
    )

    assert isinstance(instance_of_aas, aas_types.AssetAdministrationShell)

    path_hash = common.hash_path(
        environment_path_hash, path_to_aas + ["derived_from"]
    )
    instance_of_aas.derived_from = fixing.generate_external_reference(path_hash)
    path = path_to_aas + ["derived_from"]

    reference = instance_of_aas.derived_from
    reference.referred_semantic_id = fixing.generate_external_reference(
        common.hash_path(path_hash, "referred_semantic_id")
    )
    # TODO (mristin, 2023-03-11): implement is_maximal, is_maximal_{cls} in creation
    #  also is_minimal, is_minimal_{cls}
    #  🠒 put it here as ensure and other custom-tailored functions

    fixing.assert_instance_at_path_in_environment(environment, reference, path)
    return environment, reference, path


@require(lambda environment_cls: environment_cls.name == "Environment")
def _generate_minimal_case(
        cls: intermediate.ConcreteClass, environment_cls: intermediate.ConcreteClass
) -> Tuple[CaseMinimal, Replica]:
    """Generate the example of a minimal instance ready for serialization."""
    # TODO (mristin, 2023-03-11): add post-condition that the generated instance is minimal.
    try:
        if wrapping.lives_in_environment(cls.name):
            if cls.name == "Key":
                # fmt: off
                environment, instance, path = (
                    _generate_customized_environment_and_minimal_instance_for_key()
                )
                # fmt: on
            elif cls.name == "Reference":
                # fmt: off
                environment, instance, path = (
                    _generate_customized_environment_and_minimal_instance_for_reference()
                )
                # fmt: on
            else:
                environment, instance, path = wrapping.minimal_in_environment(cls.name)
                fixing.fix(environment)

            fixing.assert_instance_at_path_in_environment(
                environment, instance, path
            )

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
            instance = creation.exact_concrete_minimal(path_hash, cls.name)
            fixing.fix(instance)

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
    except Exception as exception:
        raise AssertionError(
            f"Failed to generate a minimal case for class {cls.name!r}"
        ) from exception


@require(lambda environment_cls: environment_cls.name == "Environment")
def _generate_maximal_case(
        cls: intermediate.ConcreteClass, environment_cls: intermediate.ConcreteClass
) -> Tuple[CaseMaximal, Replica]:
    """Generate the example of a minimal instance ready for serialization."""
    # TODO (mristin, 2023-03-11): add post-condition that the generate instance is maximal.
    try:
        if wrapping.lives_in_environment(cls.name):
            if cls.name == "Key":
                # fmt: off
                environment, instance, path = (
                    _generate_customized_environment_and_maximal_instance_for_key()
                )
                # fmt: on
            elif cls.name == "Reference":
                # fmt: off
                environment, instance, path = (
                    _generate_customized_environment_and_maximal_instance_for_reference()
                )
                # fmt: on
            else:
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
            instance = creation.exact_concrete_maximal(path_hash, cls.name)
            fixing.fix(instance)

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
    except Exception as exception:
        raise AssertionError(
            f"Failed to generate a maximal case for class {cls.name!r}"
        ) from exception


def generate(
        symbol_table: intermediate.SymbolTable,
        constraints_by_class: MutableMapping[
            intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
        ],
) -> Iterator[CaseUnion]:
    """Generate the test cases."""
    environment_cls = symbol_table.must_find_concrete_class(Identifier("Environment"))

    for our_type in sorted(
            symbol_table.our_types,
            key=lambda an_our_type: an_our_type.name
    ):
        if not isinstance(our_type, intermediate.ConcreteClass):
            continue

        # TODO (mristin, 2023-03-11): Revisit Concept_description once aas-core-meta fixed
        if our_type.name == "Concept_description":
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
