"""Generate additional custom-tailored test cases for Submodel element list."""

# NOTE (mristin, 2023-03-15):
# This code has been originally part of the ``generation`` module, but we refactored
# it out for readability. Additionally, we wanted to avoid name conflicts and explicitly
# list the dependencies between the functions. In particular, in the beginning, all
# the functions were nested in a generation function, so the dependencies were difficult
# to trace between the local scope and the non-local scope.
from typing import Iterator, Union, cast

from aas_core3 import types as aas_types
from aas_core_codegen import intermediate
from icontract import require

from aas_core3_0_testgen import fixing, common
from aas_core3_0_testgen.codegened import preserialization
from aas_core3_0_testgen.generation import (
    Replica,
    CaseMinimal, CasePositiveManual, CaseConstraintViolation
)


def _set_up_submodel_element_list_of_boolean_properties(
        minimal_replica: Replica,
        path_hash_to_instance: common.CanHash
) -> Replica:
    """
    Create a replica as a submodel element list with two items.

    The items are both instances of ``Property`` with the same semantic ID.

    The given ``minimal_replica`` should not be modified.
    """
    replica = minimal_replica.deepcopy()

    assert isinstance(replica.instance, aas_types.SubmodelElementList)

    replica.instance.value_type_list_element = aas_types.DataTypeDefXSD.BOOLEAN

    # fmt: off
    replica.instance.type_value_list_element = (
        aas_types.AASSubmodelElements.PROPERTY
    )
    # fmt: on

    replica.instance.semantic_id_list_element = fixing.generate_external_reference(
        common.hash_path(path_hash_to_instance, ["semantic_id_list_element"])
    )

    replica.instance.value = [
        aas_types.Property(
            value_type=aas_types.DataTypeDefXSD.BOOLEAN,
            semantic_id=replica.instance.semantic_id_list_element
        ),
        aas_types.Property(
            value_type=aas_types.DataTypeDefXSD.BOOLEAN,
            semantic_id=replica.instance.semantic_id_list_element
        )
    ]

    return replica


class EnvironmentClass(intermediate.ConcreteClass):
    """Represent the environment class."""

    @require(lambda that: that.name == "Environment")
    def __new__(
            cls,
            that: intermediate.ConcreteClass,
            **kwargs
    ) -> "EnvironmentClass":
        return cast(EnvironmentClass, that)


class SubmodelElementListClass(intermediate.ConcreteClass):
    """Represent the submodel element list class."""

    @require(lambda that: that.name == "Submodel_element_list")
    def __new__(
            cls,
            that: intermediate.ConcreteClass,
            **kwargs
    ) -> "SubmodelElementListClass":
        return cast(SubmodelElementListClass, that)


def _preserialize_to_positive_manual_case(
        replica: Replica,
        name: str,
        environment_cls: EnvironmentClass,
        submodel_element_list_cls: SubmodelElementListClass
) -> CasePositiveManual:
    """Translate ``replica`` into a positive manual case."""
    preserialized_container, _ = preserialization.preserialize(
        replica.container
    )

    assert isinstance(replica.container, aas_types.Environment)
    assert isinstance(replica.instance, aas_types.SubmodelElementList)

    return CasePositiveManual(
        container_class=environment_cls,
        preserialized_container=preserialized_container,
        cls=submodel_element_list_cls,
        name=name
    )


def _generate_one_child_without_semantic_id(
        minimal_replica: Replica,
        path_hash_to_instance: common.CanHash,
        environment_cls: EnvironmentClass,
        submodel_element_list_cls: SubmodelElementListClass
) -> CasePositiveManual:
    """Generate the case where one child does not have the semantic ID set."""
    replica = _set_up_submodel_element_list_of_boolean_properties(
        minimal_replica=minimal_replica,
        path_hash_to_instance=path_hash_to_instance
    )

    assert isinstance(replica.instance, aas_types.SubmodelElementList)
    assert isinstance(replica.instance.value[0], aas_types.Property)

    replica.instance.value[0].semantic_id = None

    return _preserialize_to_positive_manual_case(
        replica=replica,
        name="one_child_without_semantic_ID",
        environment_cls=environment_cls,
        submodel_element_list_cls=submodel_element_list_cls
    )


def _generate_no_semantic_id_list_element(
        minimal_replica: Replica,
        path_hash_to_instance: common.CanHash,
        environment_cls: EnvironmentClass,
        submodel_element_list_cls: SubmodelElementListClass
) -> CasePositiveManual:
    """Generate the case where semantic ID is unset in the list."""
    replica = _set_up_submodel_element_list_of_boolean_properties(
        minimal_replica=minimal_replica,
        path_hash_to_instance=path_hash_to_instance
    )

    assert isinstance(replica.instance, aas_types.SubmodelElementList)

    replica.instance.semantic_id_list_element = None

    return _preserialize_to_positive_manual_case(
        replica=replica,
        name="no_semantic_ID_list_element",
        environment_cls=environment_cls,
        submodel_element_list_cls=submodel_element_list_cls
    )


# fmt: off
@require(
    lambda minimal_case:
    isinstance(minimal_case.replica.instance, aas_types.SubmodelElementList)
)
@require(
    lambda minimal_case:
    isinstance(minimal_case.replica.container, aas_types.Environment)
)
@require(
    lambda minimal_case:
    minimal_case.container_class.name == "Environment"
)
@require(
    lambda minimal_case:
    minimal_case.cls == "Submodel_element_list"
)
# fmt: on
def generate_cases(
        minimal_case: CaseMinimal
) -> Iterator[Union[CasePositiveManual, CaseConstraintViolation]]:
    """Generate additional custom-tailored cases for submodel element list."""
    path_hash_to_instance = common.hash_path(None, minimal_case.replica.path)

    environment_cls = EnvironmentClass(minimal_case.container_class)
    submodel_element_list_cls = SubmodelElementListClass(minimal_case.cls)

    yield _generate_one_child_without_semantic_id(
        minimal_replica=minimal_case.replica,
        path_hash_to_instance=path_hash_to_instance,
        environment_cls=environment_cls,
        submodel_element_list_cls=submodel_element_list_cls
    )

    yield _generate_no_semantic_id_list_element(
        minimal_replica=minimal_case.replica,
        path_hash_to_instance=path_hash_to_instance,
        environment_cls=environment_cls,
        submodel_element_list_cls=submodel_element_list_cls
    )

    # TODO (mristin, 2023-03-15): continue here
