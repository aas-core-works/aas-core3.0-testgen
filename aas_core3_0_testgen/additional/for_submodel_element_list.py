"""Generate additional custom-tailored test cases for Submodel element list."""

# NOTE (mristin, 2023-03-15):
# This code has been originally part of the ``generation`` module, but we refactored
# it out for readability. Additionally, we wanted to avoid name conflicts and explicitly
# list the dependencies between the functions. In particular, in the beginning, all
# the functions were nested in a generation function, so the dependencies were difficult
# to trace between the local scope and the non-local scope.

from aas_core3 import types as aas_types
from aas_core_codegen import intermediate
from icontract import require

from aas_core3_0_testgen import fixing, common
from aas_core3_0_testgen.codegened import preserialization
from aas_core3_0_testgen.generation import (
    Replica,
    CaseMinimal, CasePositiveManual
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


# fmt: off
@require(
    lambda environment_cls:
    environment_cls.name == "Environment"
)
@require(
    lambda submodel_element_list_cls:
    submodel_element_list_cls.name == "Submodel_element_list"
)
# fmt: on
def _preserialize_to_positive_manual_case(
        replica: Replica,
        name: str,
        environment_cls: intermediate.ConcreteClass,
        submodel_element_list_cls: intermediate.ConcreteClass
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

# TODO (mristin, 2023-03-15): continue refactoring here
