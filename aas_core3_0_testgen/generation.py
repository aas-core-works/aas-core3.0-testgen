"""Generate the pre-serialized representation of the test data."""
import copy
import inspect
from typing import (
    Union,
    MutableMapping,
    Iterator,
    Sequence,
    Tuple,
    List,
    Optional,
    Set,
    cast,
)

import aas_core_codegen.common
from aas_core_codegen import intermediate, infer_for_schema
from aas_core_codegen.common import Identifier
from icontract import require, DBC
from typing_extensions import assert_never

import aas_core3.constants as aas_constants
import aas_core3.types as aas_types
from aas_core3_0_testgen import fixing, common, primitiving
from aas_core3_0_testgen.codegened import creation, wrapping, preserialization
from aas_core3_0_testgen.frozen_examples import (
    pattern as frozen_examples_pattern,
    xs_value as frozen_examples_xs_value,
)


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

    def replicate(self) -> "Replica":
        """Make another deep copy of the replica."""

        container = copy.deepcopy(self.container)
        path = copy.copy(self.path)

        instance, error = common.dereference_instance(container, path)
        if error is not None:
            raise AssertionError(
                f"Could not dereference instance "
                f"at the path {common.instance_path_as_posix(path)} "
                f"in a deep-copied container: {error}"
            )

        assert instance is not None

        return Replica(container=container, instance=instance, path=path)


class CaseMinimal(Case):
    """Represent a minimal test case."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        preserialized_container: preserialization.Instance,
        preserialized_instance: preserialization.Instance,
        cls: intermediate.ConcreteClass,
        replica: "Replica",
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
            expected=True,
            cls=cls,
        )
        self.preserialized_instance = preserialized_instance
        self.replica = replica


class CaseMaximal(Case):
    """Represent a maximal test case."""

    def __init__(
        self,
        container_class: intermediate.ConcreteClass,
        preserialized_container: preserialization.Instance,
        preserialized_instance: preserialization.Instance,
        cls: intermediate.ConcreteClass,
        replica: "Replica",
    ) -> None:
        """Initialize with the given values."""
        Case.__init__(
            self,
            container_class=container_class,
            preserialized_container=preserialized_container,
            expected=True,
            cls=cls,
        )
        self.preserialized_instance = preserialized_instance
        self.replica = replica


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


class CaseNullViolation(Case):
    """Represent an unexpected case where values are set to None instead of removed."""

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
    CaseNullViolation,
]

aas_core_codegen.common.assert_union_of_descendants_exhaustive(
    union=CaseUnion, base_class=Case
)


def _generate_customized_environment_and_minimal_instance_for_key() -> Tuple[
    aas_types.Environment, aas_types.Key, List[Union[str, int]]
]:
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

    instance_of_aas.derived_from = fixing.generate_model_reference(
        common.hash_path(path_hash, path_to_aas + ["derived_from"]),
        expected_type=aas_types.KeyTypes.ASSET_ADMINISTRATION_SHELL,
    )

    key = instance_of_aas.derived_from.keys[0]
    path = path_to_aas + ["derived_from", "keys", 0]

    fixing.assert_instance_at_path_in_environment(environment, key, path)
    return environment, key, path


def _generate_customized_environment_and_maximal_instance_for_key() -> Tuple[
    aas_types.Environment, aas_types.Key, List[Union[str, int]]
]:
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

    instance_of_aas.derived_from = fixing.generate_model_reference(
        common.hash_path(path_hash, path_to_aas + ["derived_from"]),
        aas_types.KeyTypes.ASSET_ADMINISTRATION_SHELL,
    )

    key = instance_of_aas.derived_from.keys[0]
    path = path_to_aas + ["derived_from", "keys", 0]

    fixing.assert_instance_at_path_in_environment(environment, key, path)
    return environment, key, path


def _generate_customized_environment_and_minimal_instance_for_reference() -> Tuple[
    aas_types.Environment, aas_types.Reference, List[Union[str, int]]
]:
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

    instance_of_aas.derived_from = fixing.generate_model_reference(
        common.hash_path(path_hash, path_to_aas + ["derived_from"]),
        aas_types.KeyTypes.ASSET_ADMINISTRATION_SHELL,
    )

    reference = instance_of_aas.derived_from
    path = path_to_aas + ["derived_from"]

    fixing.assert_instance_at_path_in_environment(environment, reference, path)
    return environment, reference, path


def _generate_customized_environment_and_maximal_instance_for_reference() -> Tuple[
    aas_types.Environment, aas_types.Reference, List[Union[str, int]]
]:
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

    path_hash = common.hash_path(environment_path_hash, path_to_aas + ["derived_from"])
    instance_of_aas.derived_from = fixing.generate_model_reference(
        path_hash, aas_types.KeyTypes.ASSET_ADMINISTRATION_SHELL
    )
    path = path_to_aas + ["derived_from"]

    reference = instance_of_aas.derived_from
    reference.referred_semantic_id = fixing.generate_external_reference(
        common.hash_path(path_hash, "referred_semantic_id")
    )

    fixing.assert_instance_at_path_in_environment(environment, reference, path)
    return environment, reference, path


@require(lambda environment_cls: environment_cls.name == "Environment")
def _generate_minimal_case(
    cls: intermediate.ConcreteClass, environment_cls: intermediate.ConcreteClass
) -> CaseMinimal:
    """Generate the example of a minimal instance ready for serialization."""
    try:
        instance = None  # type: Optional[aas_types.Class]

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

            fixing.assert_instance_at_path_in_environment(environment, instance, path)

            (
                preserialized_container,
                instance_to_preserialized,
            ) = preserialization.preserialize(environment)

            return CaseMinimal(
                container_class=environment_cls,
                preserialized_container=preserialized_container,
                preserialized_instance=instance_to_preserialized[instance],
                cls=cls,
                replica=Replica(container=environment, instance=instance, path=path),
            )
        else:
            path_hash = common.hash_path(None, [])
            instance = creation.exact_concrete_minimal(path_hash, cls.name)
            fixing.fix(instance)

            preserialized_instance, _ = preserialization.preserialize(instance)

            # NOTE (mristin, 2023-03-10):
            # The instance is self-contained, so the container is also
            # the instance.

            return CaseMinimal(
                container_class=cls,
                preserialized_container=preserialized_instance,
                preserialized_instance=preserialized_instance,
                cls=cls,
                replica=Replica(container=instance, instance=instance, path=[]),
            )
    except Exception as exception:
        raise AssertionError(
            f"Failed to generate a minimal case for class {cls.name!r}"
        ) from exception


@require(lambda environment_cls: environment_cls.name == "Environment")
def _generate_maximal_case(
    cls: intermediate.ConcreteClass, environment_cls: intermediate.ConcreteClass
) -> CaseMaximal:
    """Generate the example of a minimal instance ready for serialization."""
    try:
        instance = None  # type: Optional[aas_types.Class]

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

            (
                preserialized_container,
                instance_to_preserialized,
            ) = preserialization.preserialize(environment)

            return CaseMaximal(
                container_class=environment_cls,
                preserialized_container=preserialized_container,
                preserialized_instance=instance_to_preserialized[instance],
                cls=cls,
                replica=Replica(container=environment, instance=instance, path=path),
            )
        else:
            path_hash = common.hash_path(None, [])
            instance = creation.exact_concrete_maximal(path_hash, cls.name)
            fixing.fix(instance)

            preserialized_instance, _ = preserialization.preserialize(instance)

            # NOTE (mristin, 2023-03-10):
            # The instance is self-contained, so the container is also
            # the instance.
            return CaseMaximal(
                container_class=cls,
                preserialized_container=preserialized_instance,
                preserialized_instance=preserialized_instance,
                cls=cls,
                replica=Replica(container=instance, instance=instance, path=[]),
            )
    except Exception as exception:
        raise AssertionError(
            f"Failed to generate a maximal case for class {cls.name!r}"
        ) from exception


def _generate_type_violations(maximal_case: CaseMaximal) -> Iterator[CaseTypeViolation]:
    """Generate a type violation for every property in the pre-serialization."""
    # Abbreviate for readability
    replica = maximal_case.replica

    for prop in maximal_case.cls.properties:
        if prop.name not in maximal_case.preserialized_instance.properties:
            continue

        # region Replicate
        (
            preserialized_container,
            instance_to_preserialized,
        ) = preserialization.preserialize(replica.container)
        preserialized_instance = instance_to_preserialized[replica.instance]
        # endregion

        # region Mutate
        type_anno = intermediate.beneath_optional(prop.type_annotation)

        if not isinstance(type_anno, intermediate.ListTypeAnnotation):
            unexpected_instance, _ = preserialization.preserialize(
                aas_types.Reference(
                    type=aas_types.ReferenceTypes.EXTERNAL_REFERENCE,
                    keys=[
                        aas_types.Key(
                            type=aas_types.KeyTypes.GLOBAL_REFERENCE,
                            value="unexpected instance",
                        )
                    ],
                )
            )

            # fmt: off
            preserialized_instance.properties[prop.name] = (
                preserialization.ListOfInstances(
                    values=[unexpected_instance]
                )
            )
            # fmt: on
        else:
            preserialized_instance.properties[prop.name] = "Unexpected string value"

        yield CaseTypeViolation(
            container_class=maximal_case.container_class,
            preserialized_container=preserialized_container,
            cls=maximal_case.cls,
            property_name=prop.name,
        )
        # endregion


def _generate_positive_and_negative_pattern_examples(
    maximal_case: CaseMaximal,
    constraints_by_property: infer_for_schema.ConstraintsByProperty,
) -> Iterator[Union[CasePositivePatternExample, CasePatternViolation]]:
    """Generate positive and negative pattern examples."""
    # Abbreviate for readability
    replica = maximal_case.replica

    for prop in maximal_case.cls.properties:
        if prop.name not in maximal_case.preserialized_instance.properties:
            continue

        pattern_constraints = constraints_by_property.patterns_by_property.get(
            prop, None
        )

        if pattern_constraints is None:
            continue

        # NOTE (mristin, 2023-03-13):
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

        if len(pattern_constraints_without_xml) == 0:
            continue

        if len(pattern_constraints_without_xml) > 1:
            raise NotImplementedError(
                f"The property {prop.name!r} of class {maximal_case.cls.name!r} "
                f"has multiple properties. We currently do not know how to handle "
                f"this case. Please contact the developers."
            )

        pattern = pattern_constraints_without_xml[0].pattern

        pattern_examples = frozen_examples_pattern.BY_PATTERN[pattern]

        for example_name, example_text in pattern_examples.positives.items():
            # region Replicate
            (
                preserialized_container,
                instance_to_preserialized,
            ) = preserialization.preserialize(replica.container)
            preserialized_instance = instance_to_preserialized[replica.instance]
            # endregion

            # region Mutate
            preserialized_instance.properties[prop.name] = example_text

            yield CasePositivePatternExample(
                container_class=maximal_case.container_class,
                preserialized_container=preserialized_container,
                cls=maximal_case.cls,
                property_name=prop.name,
                example_name=example_name,
            )
            # endregion

        for example_name, example_text in pattern_examples.negatives.items():
            # region Replicate
            (
                preserialized_container,
                instance_to_preserialized,
            ) = preserialization.preserialize(replica.container)
            preserialized_instance = instance_to_preserialized[replica.instance]
            # endregion

            # region Mutate
            preserialized_instance.properties[prop.name] = example_text

            yield CasePatternViolation(
                container_class=maximal_case.container_class,
                preserialized_container=preserialized_container,
                cls=maximal_case.cls,
                property_name=prop.name,
                example_name=example_name,
            )
            # endregion


def _generate_required_violations(
    minimal_case: CaseMinimal,
) -> Iterator[CaseRequiredViolation]:
    """Generate violations where required properties are removed."""
    # Abbreviate for readability
    replica = minimal_case.replica

    for prop in minimal_case.cls.properties:
        if prop.name not in minimal_case.preserialized_instance.properties:
            continue

        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            continue

        # region Replicate
        (
            preserialized_container,
            instance_to_preserialized,
        ) = preserialization.preserialize(replica.container)
        preserialized_instance = instance_to_preserialized[replica.instance]
        # endregion

        # region Mutate
        del preserialized_instance.properties[prop.name]

        yield CaseRequiredViolation(
            container_class=minimal_case.container_class,
            preserialized_container=preserialized_container,
            cls=minimal_case.cls,
            property_name=prop.name,
        )
        # endregion


def _generate_null_violations(minimal_case: CaseMinimal) -> Iterator[CaseNullViolation]:
    """Generate violations where required properties are set to ``None``."""
    # Abbreviate for readability
    replica = minimal_case.replica

    for prop in minimal_case.cls.properties:
        if prop.name not in minimal_case.preserialized_instance.properties:
            continue

        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            continue

        # region Replicate
        (
            preserialized_container,
            instance_to_preserialized,
        ) = preserialization.preserialize(replica.container)
        preserialized_instance = instance_to_preserialized[replica.instance]
        # endregion

        # region Mutate
        preserialized_instance.properties[prop.name] = None

        yield CaseNullViolation(
            container_class=minimal_case.container_class,
            preserialized_container=preserialized_container,
            cls=minimal_case.cls,
            property_name=prop.name,
        )
        # endregion


def _generate_length_violations(
    maximal_case: CaseMaximal,
    constraints_by_property: infer_for_schema.ConstraintsByProperty,
) -> Iterator[Union[CaseMinLengthViolation, CaseMaxLengthViolation]]:
    """Generate positive and negative pattern examples."""
    # Abbreviate for readability
    replica = maximal_case.replica

    for prop in maximal_case.cls.properties:
        if prop.name not in maximal_case.preserialized_instance.properties:
            continue

        len_constraints = constraints_by_property.len_constraints_by_property.get(
            prop, None
        )

        if len_constraints is None:
            continue

        if len_constraints.min_value is not None and len_constraints.min_value > 0:
            # region Replicate
            (
                preserialized_container,
                instance_to_preserialized,
            ) = preserialization.preserialize(replica.container)
            preserialized_instance = instance_to_preserialized[replica.instance]
            # endregion

            # region Mutate
            prop_value = preserialized_instance.properties[prop.name]
            assert isinstance(
                prop_value, (str, bytes, preserialization.ListOfInstances)
            ), (
                f"Only strings, bytes and lists expected with length constraints, "
                f"but got type {type(prop_value)} "
                f"for instance: {preserialization.dump(preserialized_instance)}"
            )

            new_prop_value: Optional[
                Union[str, bytes, preserialization.ListOfInstances]
            ] = None

            if isinstance(prop_value, (str, bytes)):
                new_prop_value = prop_value[: (len_constraints.min_value - 1)]

                assert len(new_prop_value) < len_constraints.min_value, (
                    f"{len(new_prop_value)=}, {len(prop_value)=}, "
                    f"{len_constraints.min_value=}"
                )

            elif isinstance(prop_value, preserialization.ListOfInstances):
                new_prop_value = preserialization.ListOfInstances(
                    values=prop_value.values[: (len_constraints.min_value - 1)]
                )
            else:
                assert_never(prop_value)

            assert new_prop_value is not None

            preserialized_instance.properties[prop.name] = new_prop_value

            yield CaseMinLengthViolation(
                container_class=maximal_case.container_class,
                preserialized_container=preserialized_container,
                cls=maximal_case.cls,
                prop=prop,
                min_value=len_constraints.min_value,
            )
            # endregion

        if len_constraints.max_value is not None:
            # NOTE (mristin, 2023-03-13):
            # Since we are dealing with a maximal example, we assume that the value
            # is non-empty, and simply extend it.
            #
            # This is quite brutish, and might violate other constraints as well, but
            # it will *certainly* violate the max value constraint.

            # region Replicate
            (
                preserialized_container,
                instance_to_preserialized,
            ) = preserialization.preserialize(replica.container)
            preserialized_instance = instance_to_preserialized[replica.instance]
            # endregion

            # region Mutate
            prop_value = preserialized_instance.properties[prop.name]
            assert isinstance(
                prop_value, (str, bytes, preserialization.ListOfInstances)
            ), (
                f"Only strings, bytes and lists expected with length constraints, "
                f"but got type {type(prop_value)} "
                f"for instance: {preserialization.dump(preserialized_instance)}"
            )

            new_prop_value = None

            if isinstance(prop_value, str):
                # NOTE (mristin, 2023-03-13):
                # This might violate other constraints as well, but will *certainly*
                # violate the length constraint.
                new_prop_value = prop_value + primitiving.generate_str_padding(
                    len_constraints.max_value - len(prop_value) + 1
                )

                assert len(new_prop_value) > len_constraints.max_value, (
                    f"{len(prop_value)=}, {len(new_prop_value)=}, "
                    f"{len_constraints.max_value=}"
                )
            elif isinstance(prop_value, bytes):
                # NOTE (mristin, 2023-03-13):
                # This might violate other constraints as well, but will *certainly*
                # violate the length constraint.
                new_prop_value = prop_value + primitiving.generate_bytes_padding(
                    len_constraints.max_value - len(prop_value) + 1
                )

            elif isinstance(prop_value, preserialization.ListOfInstances):
                assert len(prop_value.values) >= 1, (
                    f"Maximal instance expected to have non-empty lists "
                    f"for property {prop.name!r}, "
                    f"but got: {preserialization.dump(preserialized_instance)}"
                )

                last_value = prop_value.values[-1]

                new_prop_value = preserialization.ListOfInstances(
                    values=(
                        prop_value.values
                        + [last_value]
                        * (len_constraints.max_value - len(prop_value.values) + 1)
                    )
                )

            else:
                assert_never(prop_value)

            assert new_prop_value is not None

            preserialized_instance.properties[prop.name] = new_prop_value

            yield CaseMaxLengthViolation(
                container_class=maximal_case.container_class,
                preserialized_container=preserialized_container,
                cls=maximal_case.cls,
                property_name=prop.name,
            )
            # endregion


def _generate_enum_violations(maximal_case: CaseMaximal) -> Iterator[CaseEnumViolation]:
    """Generate the test cases where enums have invalid literals."""
    # Abbreviate for readability
    replica = maximal_case.replica

    for prop in maximal_case.cls.properties:
        type_anno = intermediate.beneath_optional(prop.type_annotation)

        if not isinstance(type_anno, intermediate.OurTypeAnnotation) or not isinstance(
            type_anno.our_type, intermediate.Enumeration
        ):
            continue

        # region Replicate
        (
            preserialized_container,
            instance_to_preserialized,
        ) = preserialization.preserialize(replica.container)
        preserialized_instance = instance_to_preserialized[replica.instance]
        # endregion

        # region Mutate
        invalid_literal = "totally utterly invalid"
        while invalid_literal in type_anno.our_type.literals_by_value:
            invalid_literal = "so " + invalid_literal

        preserialized_instance.properties[prop.name] = invalid_literal

        yield CaseEnumViolation(
            container_class=maximal_case.container_class,
            preserialized_container=preserialized_container,
            enum=type_anno.our_type,
            cls=maximal_case.cls,
            prop=prop,
        )
        # endregion


def _generate_unexpected_additional_properties(
    minimal_case: CaseMinimal,
) -> Iterator[CaseUnexpectedAdditionalProperty]:
    """Generate invalid cases with unexpected properties in the preserialization."""
    # region Replicate
    preserialized_container, instance_to_preserialized = preserialization.preserialize(
        minimal_case.replica.container
    )
    preserialized_instance = instance_to_preserialized[minimal_case.replica.instance]
    # endregion

    # region Mutate
    additional_prop_name = "unexpected_additional_property"
    while additional_prop_name in minimal_case.cls.properties_by_name:
        additional_prop_name = f"really_{additional_prop_name}"

    preserialized_instance.properties[additional_prop_name] = "INVALID"

    yield CaseUnexpectedAdditionalProperty(
        container_class=minimal_case.container_class,
        preserialized_container=preserialized_container,
        cls=minimal_case.cls,
    )
    # endregion


def _generate_date_time_utc_violation_on_february_29th(
    minimal_case: CaseMinimal,
    date_time_utc_constrained_primitive: intermediate.ConstrainedPrimitive,
) -> Iterator[CaseDateTimeUtcViolationOnFebruary29th]:
    """Generate the cases where an invalid date-time satisfies the pattern."""
    # Abbreviate for readability
    replica = minimal_case.replica

    for prop in minimal_case.cls.properties:
        type_anno = intermediate.beneath_optional(prop.type_annotation)

        if (
            isinstance(type_anno, intermediate.OurTypeAnnotation)
            and type_anno.our_type is date_time_utc_constrained_primitive
        ):
            # region Replicate
            (
                preserialized_container,
                instance_to_preserialized,
            ) = preserialization.preserialize(replica.container)
            preserialized_instance = instance_to_preserialized[replica.instance]
            # endregion

            # region Mutate
            preserialized_instance.properties[prop.name] = "2022-02-29T12:13:14Z"

            yield CaseDateTimeUtcViolationOnFebruary29th(
                container_class=minimal_case.container_class,
                preserialized_container=preserialized_container,
                cls=minimal_case.cls,
                property_name=prop.name,
            )
            # endregion


def _generate_outside_set_of_primitives(
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


def _generate_violation_of_set_constraint_on_primitive_property(
    minimal_case: CaseMinimal,
    constraints_by_property: infer_for_schema.ConstraintsByProperty,
) -> Iterator[CaseSetViolation]:
    """Generate examples which violate the set constraint on a primitive property."""
    # Abbreviate for readability
    replica = minimal_case.replica

    for prop in minimal_case.cls.properties:
        # fmt: off
        constraint = (
            constraints_by_property
            .set_of_primitives_by_property
            .get(prop, None)
        )
        # fmt: on

        if constraint is None:
            continue

        # region Replicate
        (
            preserialized_container,
            instance_to_preserialized,
        ) = preserialization.preserialize(replica.container)
        preserialized_instance = instance_to_preserialized[replica.instance]
        # endregion

        # region Mutate
        # fmt: off
        preserialized_instance.properties[prop.name] = (
            _generate_outside_set_of_primitives(
                constraint=constraint
            )
        )
        # fmt: on

        yield CaseSetViolation(
            container_class=minimal_case.container_class,
            preserialized_container=preserialized_container,
            cls=minimal_case.cls,
            property_name=prop.name,
        )
        # endregion


@require(
    lambda constraint: len(constraint.enumeration.literals) > len(constraint.literals),
    "At least one literal left outside",
)
def _generate_outside_set_of_enumeration_literals(
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


def _generate_violation_of_set_constraint_on_enum_property(
    minimal_case: CaseMinimal,
    constraints_by_property: infer_for_schema.ConstraintsByProperty,
) -> Iterator[CaseSetViolation]:
    """Generate examples which violate the set constraint on a primitive property."""
    # Abbreviate for readability
    replica = minimal_case.replica

    for prop in minimal_case.cls.properties:
        # fmt: off
        constraint = (
            constraints_by_property
            .set_of_enumeration_literals_by_property
            .get(prop, None)
        )
        # fmt: on

        if constraint is None:
            continue

        if len(constraint.enumeration.literals) == len(constraint.literals):
            continue

        # region Replicate
        (
            preserialized_container,
            instance_to_preserialized,
        ) = preserialization.preserialize(replica.container)
        preserialized_instance = instance_to_preserialized[replica.instance]
        # endregion

        # region Mutate
        # fmt: off
        preserialized_instance.properties[prop.name] = (
            _generate_outside_set_of_enumeration_literals(constraint=constraint)
        )
        # fmt: on

        yield CaseSetViolation(
            container_class=minimal_case.container_class,
            preserialized_container=preserialized_container,
            cls=minimal_case.cls,
            property_name=prop.name,
        )
        # endregion


def _generate_cases_for_value_and_value_types(
    minimal_case: CaseMinimal, data_type_def_xsd_enum: intermediate.Enumeration
) -> Iterator[Union[CasePositiveValueExample, CaseInvalidValueExample]]:
    """Generate cases for different ``value``'s of XSD data type."""
    for literal in aas_types.DataTypeDefXSD:
        examples = frozen_examples_xs_value.BY_VALUE_TYPE.get(literal.value, None)

        if examples is None:
            raise NotImplementedError(
                f"The entry is missing "
                f"in the {frozen_examples_xs_value.__name__!r} "
                f"for the value type {literal.value!r}"
            )

        for example_name, example_value in examples.positives.items():
            # Replicate
            replica = minimal_case.replica.replicate()

            assert isinstance(
                replica.instance,
                (aas_types.Extension, aas_types.Qualifier, aas_types.Property),
            )

            # Mutate
            replica.instance.value_type = literal
            replica.instance.value = example_value

            preserialized_container, _ = preserialization.preserialize(
                replica.container
            )

            yield CasePositiveValueExample(
                container_class=minimal_case.container_class,
                preserialized_container=preserialized_container,
                cls=minimal_case.cls,
                data_type_def_literal=data_type_def_xsd_enum.literals_by_value[
                    literal.value
                ],
                example_name=example_name,
            )

        for example_name, example_value in examples.negatives.items():
            # Replicate
            replica = minimal_case.replica.replicate()

            assert isinstance(
                replica.instance,
                (aas_types.Extension, aas_types.Qualifier, aas_types.Property),
            )

            # Mutate
            replica.instance.value_type = literal
            replica.instance.value = example_value

            preserialized_container, _ = preserialization.preserialize(
                replica.container
            )

            yield CaseInvalidValueExample(
                container_class=minimal_case.container_class,
                preserialized_container=preserialized_container,
                cls=minimal_case.cls,
                data_type_def_literal=data_type_def_xsd_enum.literals_by_value[
                    literal.value
                ],
                example_name=example_name,
            )


def _generate_cases_for_min_max_of_range(
    minimal_case: CaseMinimal, data_type_def_xsd_enum: intermediate.Enumeration
) -> Iterator[Union[CasePositiveMinMaxExample, CaseInvalidMinMaxExample]]:
    """Generate examples of valid and invalid ranges."""
    for literal in aas_types.DataTypeDefXSD:
        examples = frozen_examples_xs_value.BY_VALUE_TYPE.get(literal.value, None)

        if examples is None:
            raise NotImplementedError(
                f"The entry is missing "
                f"in the {frozen_examples_xs_value.__name__!r} "
                f"for the value type {literal.value!r}"
            )

        for example_name, example_value in examples.positives.items():
            # Replicate
            replica = minimal_case.replica.replicate()

            assert isinstance(replica.instance, aas_types.Range)

            # Mutate
            replica.instance.value_type = literal
            replica.instance.min = example_value
            replica.instance.max = example_value

            preserialized_container, _ = preserialization.preserialize(
                replica.container
            )

            yield CasePositiveMinMaxExample(
                container_class=minimal_case.container_class,
                preserialized_container=preserialized_container,
                cls=minimal_case.cls,
                data_type_def_literal=data_type_def_xsd_enum.literals_by_value[
                    literal.value
                ],
                example_name=example_name,
            )

        for example_name, example_value in examples.negatives.items():
            # Replicate
            replica = minimal_case.replica.replicate()

            assert isinstance(replica.instance, aas_types.Range)

            # Mutate
            replica.instance.value_type = literal
            replica.instance.min = example_value
            replica.instance.max = example_value

            preserialized_container, _ = preserialization.preserialize(
                replica.container
            )

            yield CaseInvalidMinMaxExample(
                container_class=minimal_case.container_class,
                preserialized_container=preserialized_container,
                cls=minimal_case.cls,
                data_type_def_literal=data_type_def_xsd_enum.literals_by_value[
                    literal.value
                ],
                example_name=example_name,
            )


class EnvironmentClass(intermediate.ConcreteClass):
    """Represent the environment class."""

    # noinspection PyInitNewSignature
    @require(lambda that: that.name == "Environment")
    def __new__(cls, that: intermediate.ConcreteClass) -> "EnvironmentClass":
        return cast(EnvironmentClass, that)


class SubmodelElementListClass(intermediate.ConcreteClass):
    """Represent the submodel element list class."""

    # noinspection PyInitNewSignature
    @require(lambda that: that.name == "Submodel_element_list")
    def __new__(cls, that: intermediate.ConcreteClass) -> "SubmodelElementListClass":
        return cast(SubmodelElementListClass, that)


class ReferenceClass(intermediate.ConcreteClass):
    """Represent the submodel element list class."""

    # noinspection PyInitNewSignature
    @require(lambda that: that.name == "Reference")
    def __new__(cls, that: intermediate.ConcreteClass) -> "ReferenceClass":
        return cast(ReferenceClass, that)


def _test_name_from_function_name() -> str:
    """Analyze the call stack and produce the name for the test case."""
    current_frame = inspect.currentframe()
    assert current_frame is not None
    assert current_frame.f_back is not None
    function_name = current_frame.f_back.f_code.co_name
    assert function_name.startswith("_generate_"), f"{function_name=}"
    return function_name[10:]


class _AdditionalForSubmodelElementList:
    """Encapsulate generation for additional test cases for submodel element list."""

    @staticmethod
    def _create_replica_with_two_boolean_properties() -> Replica:
        """Create a replica of a submodel element list with two boolean properties."""
        path_to_instance = [
            "submodels",
            0,
            "submodel_elements",
            0,
        ]  # type: List[Union[str, int]]

        path_hash_to_instance = common.hash_path(None, path_to_instance)

        semantic_id_list_element = fixing.generate_external_reference(
            common.hash_path(path_hash_to_instance, ["semantic_id_list_element"])
        )

        submodel_element_list = aas_types.SubmodelElementList(
            value_type_list_element=aas_types.DataTypeDefXSD.BOOLEAN,
            type_value_list_element=aas_types.AASSubmodelElements.PROPERTY,
            semantic_id_list_element=semantic_id_list_element,
            id_short="someList",
            value=[
                aas_types.Property(
                    value_type=aas_types.DataTypeDefXSD.BOOLEAN,
                    semantic_id=semantic_id_list_element,
                ),
                aas_types.Property(
                    value_type=aas_types.DataTypeDefXSD.BOOLEAN,
                    semantic_id=semantic_id_list_element,
                ),
            ],
        )

        submodel = aas_types.Submodel(
            id="https://example.com/some-submodel",
            id_short="someSubmodel",
            submodel_elements=[submodel_element_list],
        )

        environment = aas_types.Environment(submodels=[submodel])

        return Replica(
            container=environment, instance=submodel_element_list, path=path_to_instance
        )

    @staticmethod
    def _preserialize_to_positive_manual_case(
        replica: Replica,
        name: str,
        environment_cls: EnvironmentClass,
        submodel_element_list_cls: SubmodelElementListClass,
    ) -> CasePositiveManual:
        """Translate ``replica`` into a positive manual case."""
        preserialized_container, _ = preserialization.preserialize(replica.container)

        assert isinstance(replica.container, aas_types.Environment)
        assert isinstance(replica.instance, aas_types.SubmodelElementList)

        return CasePositiveManual(
            container_class=environment_cls,
            preserialized_container=preserialized_container,
            cls=submodel_element_list_cls,
            name=name,
        )

    @staticmethod
    def _preserialize_to_constraint_violation(
        replica: Replica,
        name: str,
        environment_cls: EnvironmentClass,
        submodel_element_list_cls: SubmodelElementListClass,
    ) -> CaseConstraintViolation:
        """Translate ``replica`` into a case of constraint violation."""
        preserialized_container, _ = preserialization.preserialize(replica.container)

        assert isinstance(replica.container, aas_types.Environment)
        assert isinstance(replica.instance, aas_types.SubmodelElementList)

        return CaseConstraintViolation(
            container_class=environment_cls,
            preserialized_container=preserialized_container,
            cls=submodel_element_list_cls,
            name=name,
        )

    @staticmethod
    def _generate_one_child_without_semantic_id(
        environment_cls: EnvironmentClass,
        submodel_element_list_cls: SubmodelElementListClass,
    ) -> CasePositiveManual:
        """Generate the case where one child does not have the semantic ID set."""
        # Abbreviate for readability
        static = _AdditionalForSubmodelElementList

        replica = static._create_replica_with_two_boolean_properties()

        assert isinstance(replica.instance, aas_types.SubmodelElementList)
        assert replica.instance.value is not None
        assert isinstance(replica.instance.value[0], aas_types.Property)

        replica.instance.value[0].semantic_id = None

        return static._preserialize_to_positive_manual_case(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            submodel_element_list_cls=submodel_element_list_cls,
        )

    @staticmethod
    def _generate_no_semantic_id_list_element(
        environment_cls: EnvironmentClass,
        submodel_element_list_cls: SubmodelElementListClass,
    ) -> CasePositiveManual:
        """Generate the case where semantic ID is unset in the list."""
        # Abbreviate for readability
        static = _AdditionalForSubmodelElementList

        replica = static._create_replica_with_two_boolean_properties()

        assert isinstance(replica.instance, aas_types.SubmodelElementList)

        replica.instance.semantic_id_list_element = None

        return static._preserialize_to_positive_manual_case(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            submodel_element_list_cls=submodel_element_list_cls,
        )

    @staticmethod
    def _generate_against_type_value_list_element(
        environment_cls: EnvironmentClass,
        submodel_element_list_cls: SubmodelElementListClass,
    ) -> CaseConstraintViolation:
        """Generate the case where one item violates ``type_value_list_element``."""
        # Abbreviate for readability
        static = _AdditionalForSubmodelElementList

        replica = static._create_replica_with_two_boolean_properties()

        assert isinstance(replica.instance, aas_types.SubmodelElementList)

        replica.instance.value = [
            aas_types.Range(
                value_type=aas_types.DataTypeDefXSD.BOOLEAN,
                semantic_id=replica.instance.semantic_id_list_element,
            )
        ]

        return static._preserialize_to_constraint_violation(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            submodel_element_list_cls=submodel_element_list_cls,
        )

    @staticmethod
    def _generate_against_value_type_list_element(
        environment_cls: EnvironmentClass,
        submodel_element_list_cls: SubmodelElementListClass,
    ) -> CaseConstraintViolation:
        """Generate the case where one item violates ``type_value_list_element``."""
        # Abbreviate for readability
        static = _AdditionalForSubmodelElementList

        replica = static._create_replica_with_two_boolean_properties()

        assert isinstance(replica.instance, aas_types.SubmodelElementList)
        assert replica.instance.value is not None

        value0 = replica.instance.value[0]
        assert isinstance(value0, aas_types.Property)

        value0.value_type = aas_types.DataTypeDefXSD.INT

        replica.instance.value = [value0]

        return static._preserialize_to_constraint_violation(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            submodel_element_list_cls=submodel_element_list_cls,
        )

    @staticmethod
    def _generate_against_semantic_id_list_element(
        environment_cls: EnvironmentClass,
        submodel_element_list_cls: SubmodelElementListClass,
    ) -> CaseConstraintViolation:
        """Generate the case where one item violates ``semantic_ID_list_element``."""
        # Abbreviate for readability
        static = _AdditionalForSubmodelElementList

        replica = static._create_replica_with_two_boolean_properties()
        path_hash_to_instance = common.hash_path(None, replica.path)

        assert isinstance(replica.instance, aas_types.SubmodelElementList)
        assert replica.instance.value is not None

        value0 = replica.instance.value[0]
        assert isinstance(value0, aas_types.Property)

        value0.semantic_id = fixing.generate_external_reference(
            path_hash=common.hash_path(
                path_hash_to_instance, ["value", 0, "semantic_id"]
            )
        )

        replica.instance.value = [value0]

        return static._preserialize_to_constraint_violation(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            submodel_element_list_cls=submodel_element_list_cls,
        )

    @staticmethod
    def _generate_no_semantic_id_list_element_but_semantic_id_mismatch_in_value(
        environment_cls: EnvironmentClass,
        submodel_element_list_cls: SubmodelElementListClass,
    ) -> CaseConstraintViolation:
        """Generate the case where one item violates ``semantic_ID_list_element``."""
        # Abbreviate for readability
        static = _AdditionalForSubmodelElementList

        replica = static._create_replica_with_two_boolean_properties()
        path_hash_to_instance = common.hash_path(None, replica.path)

        assert isinstance(replica.instance, aas_types.SubmodelElementList)
        assert replica.instance.value is not None

        value0 = replica.instance.value[0]
        assert isinstance(value0, aas_types.Property)

        value1 = replica.instance.value[1]
        assert isinstance(value1, aas_types.Property)

        # The list mandates no semantic ID for the elements.
        replica.instance.semantic_id_list_element = None

        # ... but the semantic IDs of the elements differ.
        value0.semantic_id = fixing.generate_external_reference(
            path_hash=common.hash_path(
                path_hash_to_instance, ["value", 0, "semantic_id"]
            )
        )

        value1.semantic_id = fixing.generate_external_reference(
            path_hash=common.hash_path(
                path_hash_to_instance, ["value", 1, "semantic_id"]
            )
        )

        replica.instance.value = [value0, value1]

        return static._preserialize_to_constraint_violation(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            submodel_element_list_cls=submodel_element_list_cls,
        )

    @staticmethod
    def _generate_id_short_in_a_value(
        environment_cls: EnvironmentClass,
        submodel_element_list_cls: SubmodelElementListClass,
    ) -> CaseConstraintViolation:
        """Generate the case where one item violates ``semantic_ID_list_element``."""
        # Abbreviate for readability
        static = _AdditionalForSubmodelElementList

        replica = static._create_replica_with_two_boolean_properties()

        assert isinstance(replica.instance, aas_types.SubmodelElementList)
        assert replica.instance.value is not None

        value0 = replica.instance.value[0]
        assert isinstance(value0, aas_types.Property)
        value0.id_short = "unexpected"

        replica.instance.value = [value0]

        return static._preserialize_to_constraint_violation(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            submodel_element_list_cls=submodel_element_list_cls,
        )

    @staticmethod
    def generate_cases(
        environment_cls: EnvironmentClass,
        submodel_element_list_cls: SubmodelElementListClass,
    ) -> Iterator[Union[CasePositiveManual, CaseConstraintViolation]]:
        """Generate additional custom-tailored cases for submodel element list."""
        # Abbreviate for readability
        static = _AdditionalForSubmodelElementList

        yield static._generate_one_child_without_semantic_id(
            environment_cls=environment_cls,
            submodel_element_list_cls=submodel_element_list_cls,
        )

        yield static._generate_no_semantic_id_list_element(
            environment_cls=environment_cls,
            submodel_element_list_cls=submodel_element_list_cls,
        )

        yield static._generate_against_type_value_list_element(
            environment_cls=environment_cls,
            submodel_element_list_cls=submodel_element_list_cls,
        )

        yield static._generate_against_value_type_list_element(
            environment_cls=environment_cls,
            submodel_element_list_cls=submodel_element_list_cls,
        )

        yield static._generate_against_semantic_id_list_element(
            environment_cls=environment_cls,
            submodel_element_list_cls=submodel_element_list_cls,
        )

        # fmt: off
        yield (
            static
            ._generate_no_semantic_id_list_element_but_semantic_id_mismatch_in_value(
                environment_cls=environment_cls,
                submodel_element_list_cls=submodel_element_list_cls
            )
        )
        # fmt: on

        yield static._generate_id_short_in_a_value(
            environment_cls=environment_cls,
            submodel_element_list_cls=submodel_element_list_cls,
        )


class _AdditionalForReference:
    """Encapsulate generation for additional test cases for Reference."""

    @staticmethod
    def _create_model_reference_replica() -> Replica:
        """Create a replica to a model reference."""
        reference = aas_types.Reference(
            type=aas_types.ReferenceTypes.MODEL_REFERENCE,
            keys=[
                aas_types.Key(
                    type=aas_types.KeyTypes.IDENTIFIABLE,
                    value="https://example.com/something-identifiable",
                )
            ],
        )

        reference_element = aas_types.ReferenceElement(
            id_short="someElement", value=reference
        )

        submodel = aas_types.Submodel(
            id="https://example.com/some-submodel",
            id_short="someSubmodel",
            submodel_elements=[reference_element],
        )

        environment = aas_types.Environment(submodels=[submodel])

        path: Sequence[Union[str, int]] = [
            "submodels",
            0,
            "submodel_elements",
            0,
            "value",
        ]

        assert common.must_dereference_instance(environment, path) is reference

        return Replica(container=environment, instance=reference, path=path)

    @staticmethod
    def _create_external_reference_replica() -> Replica:
        """Create a replica to a model reference."""
        reference = aas_types.Reference(
            type=aas_types.ReferenceTypes.EXTERNAL_REFERENCE,
            keys=[
                aas_types.Key(
                    type=aas_types.KeyTypes.GLOBAL_REFERENCE,
                    value="https://example.com/something-global",
                )
            ],
        )

        reference_element = aas_types.ReferenceElement(
            id_short="someElement", value=reference
        )

        submodel = aas_types.Submodel(
            id="https://example.com/some-submodel",
            id_short="someSubmodel",
            submodel_elements=[reference_element],
        )

        environment = aas_types.Environment(submodels=[submodel])

        path: Sequence[Union[str, int]] = [
            "submodels",
            0,
            "submodel_elements",
            0,
            "value",
        ]

        assert common.must_dereference_instance(environment, path) is reference

        return Replica(container=environment, instance=reference, path=path)

    @staticmethod
    def _preserialize_to_positive_manual_case(
        replica: Replica,
        name: str,
        environment_cls: EnvironmentClass,
        reference_cls: ReferenceClass,
    ) -> CasePositiveManual:
        """Translate ``replica`` into a positive manual case."""
        preserialized_container, _ = preserialization.preserialize(replica.container)

        assert isinstance(replica.container, aas_types.Environment)
        assert isinstance(replica.instance, aas_types.Reference)

        return CasePositiveManual(
            container_class=environment_cls,
            preserialized_container=preserialized_container,
            cls=reference_cls,
            name=name,
        )

    @staticmethod
    def _preserialize_to_constraint_violation(
        replica: Replica,
        name: str,
        environment_cls: EnvironmentClass,
        reference_cls: ReferenceClass,
    ) -> CaseConstraintViolation:
        """Translate ``replica`` into a case of constraint violation."""
        preserialized_container, _ = preserialization.preserialize(replica.container)

        assert isinstance(replica.container, aas_types.Environment)
        assert isinstance(replica.instance, aas_types.Reference)

        return CaseConstraintViolation(
            container_class=environment_cls,
            preserialized_container=preserialized_container,
            cls=reference_cls,
            name=name,
        )

    @staticmethod
    def _first_key_type_outside_set(
        the_set: Set[aas_types.KeyTypes],
    ) -> aas_types.KeyTypes:
        """
        Find the first key type among ``KeyTypes`` not in ``the_set``.

        If ``the_set`` contains all the keys from ``KeyTypes``, raise ``ValueError``.
        """
        for literal in aas_types.KeyTypes:
            if literal not in the_set:
                return literal

        raise ValueError(
            f"No key type could be found from KeyTypes which is outside the set: "
            f"{the_set=},\n{aas_types.KeyTypes=}"
        )

    @staticmethod
    def _generate_first_key_not_in_globally_identifiables(
        model_reference_replica: Replica,
        environment_cls: EnvironmentClass,
        reference_cls: ReferenceClass,
    ) -> CaseConstraintViolation:
        static = _AdditionalForReference

        assert aas_types.KeyTypes.BLOB not in aas_constants.GLOBALLY_IDENTIFIABLES

        replica = model_reference_replica.replicate()
        assert isinstance(replica.instance, aas_types.Reference)
        assert replica.instance.type is aas_types.ReferenceTypes.MODEL_REFERENCE

        replica.instance.keys = [
            aas_types.Key(
                type=aas_types.KeyTypes.BLOB, value="https://example.com/something"
            )
        ]

        return static._preserialize_to_constraint_violation(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            reference_cls=reference_cls,
        )

    @staticmethod
    def _generate_for_an_external_reference_first_key_not_in_generic_globally_identifiables(
        external_reference_replica: Replica,
        environment_cls: EnvironmentClass,
        reference_cls: ReferenceClass,
    ) -> CaseConstraintViolation:
        static = _AdditionalForReference

        assert aas_types.KeyTypes.BLOB not in aas_constants.GLOBALLY_IDENTIFIABLES

        replica = external_reference_replica.replicate()
        assert isinstance(replica.instance, aas_types.Reference)
        assert replica.instance.type is aas_types.ReferenceTypes.EXTERNAL_REFERENCE

        replica.instance.keys = [
            aas_types.Key(
                type=aas_types.KeyTypes.BLOB, value="https://example.com/something"
            )
        ]

        return static._preserialize_to_constraint_violation(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            reference_cls=reference_cls,
        )

    @staticmethod
    def _generate_for_a_model_reference_first_key_not_in_aas_identifiables(
        model_reference_replica: Replica,
        environment_cls: EnvironmentClass,
        reference_cls: ReferenceClass,
    ) -> CaseConstraintViolation:
        static = _AdditionalForReference

        assert (
            aas_types.KeyTypes.GLOBAL_REFERENCE not in aas_constants.AAS_IDENTIFIABLES
        )

        replica = model_reference_replica.replicate()
        assert isinstance(replica.instance, aas_types.Reference)
        assert replica.instance.type is aas_types.ReferenceTypes.MODEL_REFERENCE

        replica.instance.keys = [
            aas_types.Key(
                type=aas_types.KeyTypes.GLOBAL_REFERENCE,
                value="https://example.com/something",
            )
        ]

        return static._preserialize_to_constraint_violation(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            reference_cls=reference_cls,
        )

    @staticmethod
    def _generate_for_an_external_reference_invalid_last_key(
        external_reference_replica: Replica,
        environment_cls: EnvironmentClass,
        reference_cls: ReferenceClass,
    ) -> CaseConstraintViolation:
        static = _AdditionalForReference

        assert (
            aas_types.KeyTypes.BLOB not in aas_constants.GENERIC_GLOBALLY_IDENTIFIABLES
        )

        assert aas_types.KeyTypes.BLOB not in aas_constants.GENERIC_FRAGMENT_KEYS

        replica = external_reference_replica.replicate()
        assert isinstance(replica.instance, aas_types.Reference)
        assert replica.instance.type is aas_types.ReferenceTypes.EXTERNAL_REFERENCE

        replica.instance.keys = [
            aas_types.Key(
                type=aas_types.KeyTypes.GLOBAL_REFERENCE,
                value="https://example.com/something",
            ),
            aas_types.Key(type=aas_types.KeyTypes.BLOB, value="something_more"),
        ]

        return static._preserialize_to_constraint_violation(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            reference_cls=reference_cls,
        )

    @staticmethod
    def _generate_for_a_model_reference_second_key_not_in_fragment_keys(
        model_reference_replica: Replica,
        environment_cls: EnvironmentClass,
        reference_cls: ReferenceClass,
    ) -> CaseConstraintViolation:
        static = _AdditionalForReference

        assert aas_types.KeyTypes.GLOBAL_REFERENCE not in aas_constants.FRAGMENT_KEYS

        replica = model_reference_replica.replicate()
        assert isinstance(replica.instance, aas_types.Reference)
        assert replica.instance.type is aas_types.ReferenceTypes.MODEL_REFERENCE

        replica.instance.keys = [
            aas_types.Key(
                type=aas_types.KeyTypes.SUBMODEL, value="https://example.com/something"
            ),
            aas_types.Key(
                type=aas_types.KeyTypes.GLOBAL_REFERENCE, value="something_more"
            ),
        ]

        return static._preserialize_to_constraint_violation(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            reference_cls=reference_cls,
        )

    @staticmethod
    def _generate_for_a_model_reference_fragment_reference_in_the_middle(
        model_reference_replica: Replica,
        environment_cls: EnvironmentClass,
        reference_cls: ReferenceClass,
    ) -> CaseConstraintViolation:
        static = _AdditionalForReference

        assert (
            aas_types.KeyTypes.FRAGMENT_REFERENCE in aas_constants.GENERIC_FRAGMENT_KEYS
        )

        replica = model_reference_replica.replicate()
        assert isinstance(replica.instance, aas_types.Reference)
        assert replica.instance.type is aas_types.ReferenceTypes.MODEL_REFERENCE

        replica.instance.keys = [
            aas_types.Key(
                type=aas_types.KeyTypes.SUBMODEL, value="https://example.com/something"
            ),
            aas_types.Key(
                type=aas_types.KeyTypes.FRAGMENT_REFERENCE, value="something_more"
            ),
            aas_types.Key(type=aas_types.KeyTypes.PROPERTY, value="yet_something_more"),
        ]

        return static._preserialize_to_constraint_violation(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            reference_cls=reference_cls,
        )

    @staticmethod
    def _generate_for_a_model_reference_fragment_reference_not_after_file_or_blob(
        model_reference_replica: Replica,
        environment_cls: EnvironmentClass,
        reference_cls: ReferenceClass,
    ) -> CaseConstraintViolation:
        static = _AdditionalForReference

        assert (
            aas_types.KeyTypes.FRAGMENT_REFERENCE in aas_constants.GENERIC_FRAGMENT_KEYS
        )

        replica = model_reference_replica.replicate()
        assert isinstance(replica.instance, aas_types.Reference)
        assert replica.instance.type is aas_types.ReferenceTypes.MODEL_REFERENCE

        replica.instance.keys = [
            aas_types.Key(
                type=aas_types.KeyTypes.SUBMODEL, value="https://example.com/something"
            ),
            aas_types.Key(type=aas_types.KeyTypes.PROPERTY, value="something_more"),
            aas_types.Key(
                type=aas_types.KeyTypes.FRAGMENT_REFERENCE, value="yet_something_more"
            ),
        ]

        return static._preserialize_to_constraint_violation(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            reference_cls=reference_cls,
        )

    @staticmethod
    def _generate_for_a_model_reference_invalid_key_value_after_submodel_element_list(
        model_reference_replica: Replica,
        environment_cls: EnvironmentClass,
        reference_cls: ReferenceClass,
    ) -> CaseConstraintViolation:
        static = _AdditionalForReference

        assert (
            aas_types.KeyTypes.FRAGMENT_REFERENCE in aas_constants.GENERIC_FRAGMENT_KEYS
        )

        replica = model_reference_replica.replicate()
        assert isinstance(replica.instance, aas_types.Reference)
        assert replica.instance.type is aas_types.ReferenceTypes.MODEL_REFERENCE

        replica.instance.keys = [
            aas_types.Key(
                type=aas_types.KeyTypes.SUBMODEL, value="https://example.com/something"
            ),
            aas_types.Key(
                type=aas_types.KeyTypes.SUBMODEL_ELEMENT_LIST, value="something_more"
            ),
            aas_types.Key(type=aas_types.KeyTypes.PROPERTY, value="-1"),
        ]

        return static._preserialize_to_constraint_violation(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            reference_cls=reference_cls,
        )

    @staticmethod
    def _generate_for_an_external_reference_first_key_in_generic_globally_identifiables(
        external_reference_replica: Replica,
        environment_cls: EnvironmentClass,
        reference_cls: ReferenceClass,
    ) -> CasePositiveManual:
        static = _AdditionalForReference

        assert (
            aas_types.KeyTypes.GLOBAL_REFERENCE in aas_constants.GLOBALLY_IDENTIFIABLES
        )

        replica = external_reference_replica.replicate()
        assert isinstance(replica.instance, aas_types.Reference)
        assert replica.instance.type is aas_types.ReferenceTypes.EXTERNAL_REFERENCE

        replica.instance.keys = [
            aas_types.Key(
                type=aas_types.KeyTypes.GLOBAL_REFERENCE,
                value="https://example.com/something",
            )
        ]

        return static._preserialize_to_positive_manual_case(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            reference_cls=reference_cls,
        )

    @staticmethod
    def _generate_for_a_model_reference_first_key_in_globally_and_aas_identifiables(
        model_reference_replica: Replica,
        environment_cls: EnvironmentClass,
        reference_cls: ReferenceClass,
    ) -> CasePositiveManual:
        static = _AdditionalForReference

        assert aas_types.KeyTypes.SUBMODEL in aas_constants.GLOBALLY_IDENTIFIABLES

        assert aas_types.KeyTypes.SUBMODEL in aas_constants.AAS_IDENTIFIABLES

        replica = model_reference_replica.replicate()
        assert isinstance(replica.instance, aas_types.Reference)
        assert replica.instance.type is aas_types.ReferenceTypes.MODEL_REFERENCE

        replica.instance.keys = [
            aas_types.Key(
                type=aas_types.KeyTypes.SUBMODEL, value="https://example.com/something"
            )
        ]

        return static._preserialize_to_positive_manual_case(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            reference_cls=reference_cls,
        )

    @staticmethod
    def _generate_for_an_external_reference_last_key_in_generic_globally_identifiable(
        external_reference_replica: Replica,
        environment_cls: EnvironmentClass,
        reference_cls: ReferenceClass,
    ) -> CasePositiveManual:
        static = _AdditionalForReference

        assert (
            aas_types.KeyTypes.GLOBAL_REFERENCE in aas_constants.GLOBALLY_IDENTIFIABLES
        )

        replica = external_reference_replica.replicate()
        assert isinstance(replica.instance, aas_types.Reference)
        assert replica.instance.type is aas_types.ReferenceTypes.EXTERNAL_REFERENCE

        replica.instance.keys = [
            aas_types.Key(
                type=aas_types.KeyTypes.GLOBAL_REFERENCE,
                value="https://example.com/something",
            ),
            aas_types.Key(
                type=aas_types.KeyTypes.GLOBAL_REFERENCE, value="something-more"
            ),
        ]

        return static._preserialize_to_positive_manual_case(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            reference_cls=reference_cls,
        )

    @staticmethod
    def _generate_for_an_external_reference_last_key_in_generic_fragment_keys(
        external_reference_replica: Replica,
        environment_cls: EnvironmentClass,
        reference_cls: ReferenceClass,
    ) -> CasePositiveManual:
        static = _AdditionalForReference

        assert (
            aas_types.KeyTypes.FRAGMENT_REFERENCE in aas_constants.GENERIC_FRAGMENT_KEYS
        )

        replica = external_reference_replica.replicate()
        assert isinstance(replica.instance, aas_types.Reference)
        assert replica.instance.type is aas_types.ReferenceTypes.EXTERNAL_REFERENCE

        replica.instance.keys = [
            aas_types.Key(
                type=aas_types.KeyTypes.GLOBAL_REFERENCE,
                value="https://example.com/something",
            ),
            aas_types.Key(
                type=aas_types.KeyTypes.FRAGMENT_REFERENCE, value="something-more"
            ),
        ]

        return static._preserialize_to_positive_manual_case(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            reference_cls=reference_cls,
        )

    @staticmethod
    def _generate_for_a_model_reference_fragment_after_blob(
        model_reference_replica: Replica,
        environment_cls: EnvironmentClass,
        reference_cls: ReferenceClass,
    ) -> CasePositiveManual:
        static = _AdditionalForReference

        replica = model_reference_replica.replicate()
        assert isinstance(replica.instance, aas_types.Reference)
        assert replica.instance.type is aas_types.ReferenceTypes.MODEL_REFERENCE

        replica.instance.keys = [
            aas_types.Key(
                type=aas_types.KeyTypes.SUBMODEL, value="https://example.com/something"
            ),
            aas_types.Key(type=aas_types.KeyTypes.BLOB, value="something_more"),
            aas_types.Key(
                type=aas_types.KeyTypes.FRAGMENT_REFERENCE, value="yet_something_more"
            ),
        ]

        return static._preserialize_to_positive_manual_case(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            reference_cls=reference_cls,
        )

    @staticmethod
    def _generate_for_a_model_reference_valid_key_value_after_submodel_element_list(
        model_reference_replica: Replica,
        environment_cls: EnvironmentClass,
        reference_cls: ReferenceClass,
    ) -> CasePositiveManual:
        static = _AdditionalForReference

        replica = model_reference_replica.replicate()
        assert isinstance(replica.instance, aas_types.Reference)
        assert replica.instance.type is aas_types.ReferenceTypes.MODEL_REFERENCE

        replica.instance.keys = [
            aas_types.Key(
                type=aas_types.KeyTypes.SUBMODEL, value="https://example.com/something"
            ),
            aas_types.Key(
                type=aas_types.KeyTypes.SUBMODEL_ELEMENT_LIST, value="something_more"
            ),
            aas_types.Key(type=aas_types.KeyTypes.PROPERTY, value="123"),
        ]

        return static._preserialize_to_positive_manual_case(
            replica=replica,
            name=_test_name_from_function_name(),
            environment_cls=environment_cls,
            reference_cls=reference_cls,
        )

    @staticmethod
    def generate_cases(
        environment_cls: EnvironmentClass, reference_cls: ReferenceClass
    ) -> Iterator[Union[CasePositiveManual, CaseConstraintViolation]]:
        """Generate additional custom-tailored cases for submodel element list."""
        # Abbreviate for readability
        static = _AdditionalForReference

        model_reference_replica = static._create_model_reference_replica()

        external_reference_replica = static._create_external_reference_replica()

        # region Constraint violations

        yield static._generate_first_key_not_in_globally_identifiables(
            model_reference_replica=model_reference_replica,
            environment_cls=environment_cls,
            reference_cls=reference_cls,
        )

        # fmt: off
        yield (
            static._generate_for_an_external_reference_first_key_not_in_generic_globally_identifiables(
                external_reference_replica=external_reference_replica,
                environment_cls=environment_cls,
                reference_cls=reference_cls

            )
        )
        # fmt: on

        # fmt: off
        yield (
            static._generate_for_a_model_reference_first_key_not_in_aas_identifiables(
                model_reference_replica=model_reference_replica,
                environment_cls=environment_cls,
                reference_cls=reference_cls
            )
        )
        # fmt: on

        # fmt: off
        yield (
            static._generate_for_an_external_reference_invalid_last_key(
                external_reference_replica=external_reference_replica,
                environment_cls=environment_cls,
                reference_cls=reference_cls
            )
        )
        # fmt: on

        # fmt: off
        yield (
            static._generate_for_a_model_reference_second_key_not_in_fragment_keys(
                model_reference_replica=model_reference_replica,
                environment_cls=environment_cls,
                reference_cls=reference_cls
            )
        )
        # fmt: on

        # fmt: off
        yield (
            static._generate_for_a_model_reference_fragment_reference_in_the_middle(
                model_reference_replica=model_reference_replica,
                environment_cls=environment_cls,
                reference_cls=reference_cls
            )
        )
        # fmt: on

        # fmt: off
        yield (
            static._generate_for_a_model_reference_fragment_reference_not_after_file_or_blob(
                model_reference_replica=model_reference_replica,
                environment_cls=environment_cls,
                reference_cls=reference_cls
            )
        )
        # fmt: on

        # fmt: off
        yield (
            static._generate_for_a_model_reference_invalid_key_value_after_submodel_element_list(
                model_reference_replica=model_reference_replica,
                environment_cls=environment_cls,
                reference_cls=reference_cls
            )
        )
        # fmt: on

        # endregion

        # region Positive examples

        # fmt: off
        yield (
            static._generate_for_an_external_reference_first_key_in_generic_globally_identifiables(
                external_reference_replica=external_reference_replica,
                environment_cls=environment_cls,
                reference_cls=reference_cls
            )
        )
        # fmt: on

        # fmt: off
        yield (
            static._generate_for_a_model_reference_first_key_in_globally_and_aas_identifiables(
                model_reference_replica=model_reference_replica,
                environment_cls=environment_cls,
                reference_cls=reference_cls
            )
        )
        # fmt: on

        # fmt: off
        yield (
            static._generate_for_an_external_reference_last_key_in_generic_globally_identifiable(
                external_reference_replica=external_reference_replica,
                environment_cls=environment_cls,
                reference_cls=reference_cls
            )
        )
        # fmt: on

        # fmt: off
        yield (
            static._generate_for_an_external_reference_last_key_in_generic_fragment_keys(
                external_reference_replica=external_reference_replica,
                environment_cls=environment_cls,
                reference_cls=reference_cls
            )
        )
        # fmt: on

        # fmt: off
        yield (
            static._generate_for_a_model_reference_fragment_after_blob(
                model_reference_replica=model_reference_replica,
                environment_cls=environment_cls,
                reference_cls=reference_cls
            )
        )
        # fmt: on

        # fmt: off
        yield (
            static._generate_for_a_model_reference_valid_key_value_after_submodel_element_list(
                model_reference_replica=model_reference_replica,
                environment_cls=environment_cls,
                reference_cls=reference_cls
            )
        )
        # fmt: on

        # endregion


def generate(
    symbol_table: intermediate.SymbolTable,
    constraints_by_class: MutableMapping[
        intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
    ],
) -> Iterator[CaseUnion]:
    """Generate the test cases."""
    environment_cls = EnvironmentClass(
        symbol_table.must_find_concrete_class(Identifier("Environment"))
    )

    date_time_utc_constrained_primitive = symbol_table.must_find_constrained_primitive(
        Identifier("Date_time_UTC")
    )

    class_set_with_value_and_value_type = {
        symbol_table.must_find_concrete_class(Identifier("Property")),
        symbol_table.must_find_concrete_class(Identifier("Extension")),
        symbol_table.must_find_concrete_class(Identifier("Qualifier")),
    }

    data_type_def_xsd_enum = symbol_table.must_find_enumeration(
        Identifier("Data_type_def_XSD")
    )

    range_cls = symbol_table.must_find_concrete_class(Identifier("Range"))

    submodel_element_list_cls = SubmodelElementListClass(
        symbol_table.must_find_concrete_class(Identifier("Submodel_element_list"))
    )

    reference_cls = ReferenceClass(
        symbol_table.must_find_concrete_class(Identifier("Reference"))
    )

    for our_type in sorted(
        symbol_table.our_types, key=lambda an_our_type: an_our_type.name
    ):
        if not isinstance(our_type, intermediate.ConcreteClass):
            continue

        minimal_case = _generate_minimal_case(
            cls=our_type, environment_cls=environment_cls
        )

        yield minimal_case

        maximal_case = _generate_maximal_case(
            cls=our_type, environment_cls=environment_cls
        )
        yield maximal_case

        yield from _generate_type_violations(maximal_case=maximal_case)

        yield from _generate_positive_and_negative_pattern_examples(
            maximal_case=maximal_case,
            constraints_by_property=constraints_by_class[our_type],
        )

        yield from _generate_required_violations(minimal_case=minimal_case)

        yield from _generate_null_violations(minimal_case=minimal_case)

        yield from _generate_length_violations(
            maximal_case=maximal_case,
            constraints_by_property=constraints_by_class[our_type],
        )

        yield from _generate_enum_violations(maximal_case=maximal_case)

        yield from _generate_unexpected_additional_properties(minimal_case=minimal_case)

        yield from _generate_date_time_utc_violation_on_february_29th(
            minimal_case=minimal_case,
            date_time_utc_constrained_primitive=date_time_utc_constrained_primitive,
        )

        yield from _generate_violation_of_set_constraint_on_primitive_property(
            minimal_case=minimal_case,
            constraints_by_property=constraints_by_class[our_type],
        )

        yield from _generate_violation_of_set_constraint_on_enum_property(
            minimal_case=minimal_case,
            constraints_by_property=constraints_by_class[our_type],
        )

        if our_type in class_set_with_value_and_value_type:
            yield from _generate_cases_for_value_and_value_types(
                minimal_case=minimal_case, data_type_def_xsd_enum=data_type_def_xsd_enum
            )

        if our_type is range_cls:
            yield from _generate_cases_for_min_max_of_range(
                minimal_case=minimal_case, data_type_def_xsd_enum=data_type_def_xsd_enum
            )

        if our_type is submodel_element_list_cls:
            yield from _AdditionalForSubmodelElementList.generate_cases(
                environment_cls=environment_cls,
                submodel_element_list_cls=submodel_element_list_cls,
            )

    yield from _AdditionalForReference.generate_cases(
        environment_cls=environment_cls, reference_cls=reference_cls
    )
