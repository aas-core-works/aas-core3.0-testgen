"""Generate the pre-serialized representation of the test data."""
import copy
from typing import Union, MutableMapping, Iterator, Sequence, Tuple, List, Optional

import aas_core3.types as aas_types
import aas_core_codegen.common
from aas_core_codegen import intermediate, infer_for_schema
from aas_core_codegen.common import Identifier
from icontract import require, DBC
from typing_extensions import assert_never

from aas_core3_0_testgen import fixing, common, primitiving
from aas_core3_0_testgen.codegened import creation, wrapping, preserialization
from aas_core3_0_testgen.frozen_examples import (
    pattern as frozen_examples_pattern
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


class CaseMinimal(Case):
    """Represent a minimal test case."""

    def __init__(
            self,
            container_class: intermediate.ConcreteClass,
            preserialized_container: preserialization.Instance,
            preserialized_instance: preserialization.Instance,
            cls: intermediate.ConcreteClass,
            replica: "Replica"
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
            replica: "Replica"
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

    instance_of_aas.derived_from = fixing.generate_model_reference(
        common.hash_path(path_hash, path_to_aas + ["derived_from"]),
        expected_type=aas_types.KeyTypes.ASSET_ADMINISTRATION_SHELL
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

    instance_of_aas.derived_from = fixing.generate_model_reference(
        common.hash_path(path_hash, path_to_aas + ["derived_from"]),
        aas_types.KeyTypes.ASSET_ADMINISTRATION_SHELL
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

    instance_of_aas.derived_from = fixing.generate_model_reference(
        common.hash_path(path_hash, path_to_aas + ["derived_from"]),
        aas_types.KeyTypes.ASSET_ADMINISTRATION_SHELL
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
    instance_of_aas.derived_from = fixing.generate_model_reference(
        path_hash,
        aas_types.KeyTypes.ASSET_ADMINISTRATION_SHELL
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

            preserialized_container, instance_to_preserialized = (
                preserialization.preserialize(environment)
            )

            return CaseMinimal(
                container_class=environment_cls,
                preserialized_container=preserialized_container,
                preserialized_instance=instance_to_preserialized[instance],
                cls=cls,
                replica=Replica(container=environment, instance=instance, path=path)
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

            preserialized_container, instance_to_preserialized = preserialization.preserialize(
                environment)

            return CaseMaximal(
                container_class=environment_cls,
                preserialized_container=preserialized_container,
                preserialized_instance=instance_to_preserialized[instance],
                cls=cls,
                replica=Replica(container=environment, instance=instance, path=path)
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


def _generate_type_violations(
        maximal_case: CaseMaximal
) -> Iterator[CaseTypeViolation]:
    """Generate a type violation for every property in the pre-serialization."""
    # Abbreviate for readability
    replica = maximal_case.replica

    for prop in maximal_case.cls.properties:
        if prop.name not in maximal_case.preserialized_instance.properties:
            continue

        # region Replicate
        preserialized_container, instance_to_preserialized = (
            preserialization.preserialize(replica.container)
        )
        preserialized_instance = instance_to_preserialized[replica.instance]
        # endregion

        # region Mutate
        type_anno = intermediate.beneath_optional(prop.type_annotation)

        # NOTE (mristin, 2023-03-13):
        # If it is a primitive property or an enumeration, set it to a list. If it
        # is not a primitive property, set it to an unexpected string.
        #
        # This way we are sure that we will have a type violation according to
        # the schema.

        maybe_primitive_type = intermediate.try_primitive_type(type_anno)

        if (
                maybe_primitive_type is not None
                or (
                isinstance(type_anno, intermediate.OurTypeAnnotation)
                and isinstance(type_anno.our_type, intermediate.Enumeration)
        )
        ):
            # fmt: off
            preserialized_instance.properties[prop.name] = (
                preserialization.ListOfInstances(values=[])
            )
            # fmt: on
        else:
            preserialized_instance.properties[prop.name] = "Unexpected string value"

        yield CaseTypeViolation(
            container_class=maximal_case.container_class,
            preserialized_container=preserialized_container,
            cls=maximal_case.cls,
            property_name=prop.name
        )
        # endregion


def _generate_positive_and_negative_pattern_examples(
        maximal_case: CaseMaximal,
        constraints_by_property: infer_for_schema.ConstraintsByProperty
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
            preserialized_container, instance_to_preserialized = (
                preserialization.preserialize(replica.container)
            )
            preserialized_instance = instance_to_preserialized[replica.instance]
            # endregion

            # region Mutate
            preserialized_instance.properties[prop.name] = example_text

            yield CasePositivePatternExample(
                container_class=maximal_case.container_class,
                preserialized_container=preserialized_container,
                cls=maximal_case.cls,
                property_name=prop.name,
                example_name=example_name
            )
            # endregion

        for example_name, example_text in pattern_examples.negatives.items():
            # region Replicate
            preserialized_container, instance_to_preserialized = (
                preserialization.preserialize(replica.container)
            )
            preserialized_instance = instance_to_preserialized[replica.instance]
            # endregion

            # region Mutate
            preserialized_instance.properties[prop.name] = example_text

            yield CasePatternViolation(
                container_class=maximal_case.container_class,
                preserialized_container=preserialized_container,
                cls=maximal_case.cls,
                property_name=prop.name,
                example_name=example_name
            )
            # endregion


def _generate_required_violations(
        minimal_case: CaseMinimal
) -> Iterator[CaseRequiredViolation]:
    """Generate positive and negative pattern examples."""
    # Abbreviate for readability
    replica = minimal_case.replica

    for prop in minimal_case.cls.properties:
        if prop.name not in minimal_case.preserialized_instance.properties:
            continue

        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            continue

        # region Replicate
        preserialized_container, instance_to_preserialized = (
            preserialization.preserialize(replica.container)
        )
        preserialized_instance = instance_to_preserialized[replica.instance]
        # endregion

        # region Mutate
        del preserialized_instance.properties[prop.name]

        yield CaseRequiredViolation(
            container_class=minimal_case.container_class,
            preserialized_container=preserialized_container,
            cls=minimal_case.cls,
            property_name=prop.name
        )
        # endregion


def _generate_length_violations(
        maximal_case: CaseMaximal,
        constraints_by_property: infer_for_schema.ConstraintsByProperty
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
            preserialized_container, instance_to_preserialized = (
                preserialization.preserialize(replica.container)
            )
            preserialized_instance = instance_to_preserialized[replica.instance]
            # endregion

            # region Mutate
            prop_value = preserialized_instance.properties[prop.name]
            assert isinstance(
                prop_value,
                (str, bytes, preserialization.ListOfInstances)
            ), (
                f"Only strings, bytes and lists expected with length constraints, "
                f"but got type {type(prop_value)} "
                f"for instance: {preserialization.dump(preserialized_instance)}"
            )

            new_prop_value: Optional[
                Union[str, bytes, preserialization.ListOfInstances]
            ] = None

            if isinstance(prop_value, (str, bytes)):
                new_prop_value = prop_value[:(len_constraints.min_value - 1)]

                assert len(new_prop_value) < len_constraints.min_value, (
                    f"{len(new_prop_value)=}, {len(prop_value)=}, "
                    f"{len_constraints.min_value=}"
                )

            elif isinstance(prop_value, preserialization.ListOfInstances):
                new_prop_value = preserialization.ListOfInstances(
                    values=prop_value.values[:(len_constraints.min_value - 1)]
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
                min_value=len_constraints.min_value
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
            preserialized_container, instance_to_preserialized = (
                preserialization.preserialize(replica.container)
            )
            preserialized_instance = instance_to_preserialized[replica.instance]
            # endregion

            # region Mutate
            prop_value = preserialized_instance.properties[prop.name]
            assert isinstance(
                prop_value,
                (str, bytes, preserialization.ListOfInstances)
            ), (
                f"Only strings, bytes and lists expected with length constraints, "
                f"but got type {type(prop_value)} "
                f"for instance: {preserialization.dump(preserialized_instance)}"
            )

            new_prop_value: Optional[
                str, bytes, preserialization.ListOfInstances
            ] = None

            if isinstance(prop_value, str):
                # NOTE (mristin, 2023-03-13):
                # This might violate other constraints as well, but will *certainly*
                # violate the length constraint.
                new_prop_value = (
                        prop_value
                        + primitiving.generate_str_padding(
                    len_constraints.max_value - len(prop_value) + 1
                )
                )

                assert len(new_prop_value) > len_constraints.max_value, (
                    f"{len(prop_value)=}, {len(new_prop_value)=}, "
                    f"{len_constraints.max_value=}"
                )
            elif isinstance(prop_value, bytes):
                # NOTE (mristin, 2023-03-13):
                # This might violate other constraints as well, but will *certainly*
                # violate the length constraint.
                new_prop_value = (
                        prop_value
                        + primitiving.generate_bytes_padding(
                    len_constraints.max_value - len(prop_value) + 1
                )
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
                            + [last_value] * (
                                    len_constraints.max_value
                                    - len(prop_value.values)
                                    + 1
                            )
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
                property_name=prop.name
            )
            # endregion


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
            constraints_by_property=constraints_by_class[our_type]
        )

        yield from _generate_required_violations(minimal_case=minimal_case)

        yield from _generate_length_violations(
            maximal_case=maximal_case,
            constraints_by_property=constraints_by_class[our_type]
        )

        # TODO (mristin, 2023-03-10): implement other cases once debugging done
