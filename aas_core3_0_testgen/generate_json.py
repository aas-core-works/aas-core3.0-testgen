"""Generate test data in JSON for the meta-model V3aas-core3.0-testgen."""
import base64
import collections
import collections.abc
import json
import os
import pathlib
from typing import (
    Union,
    OrderedDict,
    List,
    Any,
    MutableMapping,
    Sequence,
)

import aas_core_codegen.common
import aas_core_codegen.naming
from aas_core_codegen import intermediate
from aas_core_codegen.common import Identifier
from icontract import ensure
from typing_extensions import assert_never

from aas_core3_0_testgen import common, generation
from aas_core3_0_testgen.codegened import preserialization


@ensure(lambda result: not result.is_absolute())
def _relative_path(test_case: generation.CaseUnion) -> pathlib.Path:
    """Generate the relative path based on the test case."""
    assert test_case.__class__.__name__.startswith("Case")

    cls_name = aas_core_codegen.naming.json_model_type(test_case.cls.name)

    base_pth = pathlib.Path("Json")

    if test_case.container_class is test_case.cls:
        base_pth /= "SelfContained"
    else:
        container_model_type = aas_core_codegen.naming.json_model_type(
            test_case.container_class.name
        )
        base_pth /= f"ContainedIn{container_model_type}"

    if test_case.expected:
        base_pth = base_pth / "Expected" / cls_name

    else:
        assert test_case.__class__.__name__.startswith("Case")
        cause = test_case.__class__.__name__[len("Case") :]

        base_pth = base_pth / "Unexpected" / cause / cls_name

    if isinstance(test_case, generation.CaseMinimal):
        return base_pth / "minimal.json"

    elif isinstance(test_case, generation.CaseMaximal):
        return base_pth / "maximal.json"

    elif isinstance(test_case, generation.CaseTypeViolation):
        prop_name = aas_core_codegen.naming.json_property(test_case.property_name)

        return base_pth / f"{prop_name}.json"

    elif isinstance(test_case, generation.CasePositivePatternExample):
        prop_name = aas_core_codegen.naming.json_property(test_case.property_name)

        return (
            base_pth
            / f"{prop_name}OverPatternExamples"
            / f"{test_case.example_name}.json"
        )

    elif isinstance(test_case, generation.CasePatternViolation):
        prop_name = aas_core_codegen.naming.json_property(test_case.property_name)

        return base_pth / prop_name / f"{test_case.example_name}.json"

    elif isinstance(test_case, generation.CaseRequiredViolation):
        prop_name = aas_core_codegen.naming.json_property(test_case.property_name)

        return base_pth / f"{prop_name}.json"

    elif isinstance(test_case, generation.CaseMinLengthViolation):
        prop_name = aas_core_codegen.naming.json_property(test_case.prop.name)

        return base_pth / f"{prop_name}.json"

    elif isinstance(test_case, generation.CaseMaxLengthViolation):
        prop_name = aas_core_codegen.naming.json_property(test_case.property_name)

        return base_pth / f"{prop_name}.json"

    elif isinstance(test_case, generation.CaseDateTimeUtcViolationOnFebruary29th):
        prop_name = aas_core_codegen.naming.json_property(test_case.property_name)

        return base_pth / f"{prop_name}.json"

    elif isinstance(test_case, generation.CasePositiveValueExample):
        return (
            base_pth
            / "OverValueExamples"
            / test_case.data_type_def_literal.name
            / f"{test_case.example_name}.json"
        )

    elif isinstance(test_case, generation.CaseInvalidValueExample):
        return (
            base_pth
            / test_case.data_type_def_literal.name
            / f"{test_case.example_name}.json"
        )

    elif isinstance(test_case, generation.CasePositiveMinMaxExample):
        return (
            base_pth
            / "OverMinMaxExamples"
            / test_case.data_type_def_literal.name
            / f"{test_case.example_name}.json"
        )

    elif isinstance(test_case, generation.CaseInvalidMinMaxExample):
        return (
            base_pth
            / test_case.data_type_def_literal.name
            / f"{test_case.example_name}.json"
        )

    elif isinstance(test_case, generation.CaseUnexpectedAdditionalProperty):
        return base_pth / "invalid.json"

    elif isinstance(test_case, generation.CaseEnumViolation):
        enum_name = aas_core_codegen.naming.json_model_type(test_case.enum.name)
        prop_name = aas_core_codegen.naming.json_property(test_case.prop.name)

        return base_pth / f"{prop_name}_as_{enum_name}.json"

    elif isinstance(test_case, generation.CasePositiveManual):
        return base_pth / f"{test_case.name}.json"

    elif isinstance(test_case, generation.CaseSetViolation):
        prop_name = aas_core_codegen.naming.json_property(test_case.property_name)

        return base_pth / f"{prop_name}.json"

    elif isinstance(test_case, generation.CaseConstraintViolation):
        return base_pth / f"{test_case.name}.json"

    else:
        aas_core_codegen.common.assert_never(test_case)


class _Serializer:
    """Serialize a container to a JSON object."""

    def __init__(self, symbol_table: intermediate.SymbolTable) -> None:
        """Initialize with the given values."""
        self.symbol_table = symbol_table

    def _serialize_value(self, value: preserialization.ValueUnion) -> Any:
        if isinstance(value, preserialization.PrimitiveValueTuple):
            return self._serialize_primitive(value)
        elif isinstance(value, preserialization.Instance):
            return self.serialize_instance(value)
        elif isinstance(value, preserialization.ListOfInstances):
            return self._serialize_list_of_instances(value)
        else:
            aas_core_codegen.common.assert_never(value)

    # noinspection PyMethodMayBeStatic
    def _serialize_primitive(
        self, value: preserialization.PrimitiveValueUnion
    ) -> Union[bool, int, float, str]:
        if isinstance(value, bytes):
            return base64.b64encode(value).decode(encoding="ascii")
        elif isinstance(value, (bool, int, float, str)):
            return value
        else:
            assert_never(value)

    def serialize_instance(
        self, instance: preserialization.Instance
    ) -> OrderedDict[str, Any]:
        """Convert the ``instance`` to a JSON-able data structure."""
        jsonable = collections.OrderedDict()  # type: OrderedDict[str, Any]

        for prop_name, prop_value in instance.properties.items():
            jsonable[
                aas_core_codegen.naming.json_property(Identifier(prop_name))
            ] = self._serialize_value(prop_value)

        cls = self.symbol_table.must_find_class(instance.class_name)

        if cls.serialization is not None and cls.serialization.with_model_type:
            jsonable["modelType"] = aas_core_codegen.naming.json_model_type(
                instance.class_name
            )

        return jsonable

    def _serialize_list_of_instances(
        self, list_of_instances: preserialization.ListOfInstances
    ) -> List[OrderedDict[str, Any]]:
        return [self.serialize_instance(value) for value in list_of_instances.values]


def to_json_path_segments(
    path: Sequence[Union[int, str]]
) -> List[Union[int, Identifier]]:
    """Convert the path segments from the case of the meta-model to JSON casing."""
    result = []  # type: List[Union[int, Identifier]]
    for segment in path:
        if isinstance(segment, int):
            result.append(segment)

        elif isinstance(segment, str):
            result.append(aas_core_codegen.naming.json_property(Identifier(segment)))

        else:
            aas_core_codegen.common.assert_never(segment)

    return result


def dereference(
    start_object: MutableMapping[str, Any],
    path: Sequence[Union[int, Identifier]],
) -> Any:
    """Get the JSON value following the ``path`` from ``start_object``"""
    cursor = start_object
    for segment in path:
        if isinstance(segment, str):
            if not isinstance(cursor, collections.abc.MutableMapping):
                raise ValueError(
                    f"Could not access the property {segment!r} "
                    f"in a JSON non-object: {cursor}; "
                    f"{start_object=}, {path=}"
                )

            cursor = cursor[segment]
        elif isinstance(segment, int):
            if not isinstance(cursor, collections.abc.Sequence):
                raise ValueError(
                    f"Could not access the index {segment!r} "
                    f"in a JSON non-array: {cursor}; "
                    f"{start_object=}, {path=}"
                )

            cursor = cursor[segment]
        else:
            aas_core_codegen.common.assert_never(segment)

    return cursor


# TODO (mristin, 2023-03-10): implement this once everything else is working
# def _generate_null_violations(
#     test_data_dir: pathlib.Path,
#     symbol_table: intermediate.SymbolTable,
#     constraints_by_class: MutableMapping[
#         intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
#     ],
#     class_graph: ontology.ClassGraph,
#     handyman: generation.Handyman,
#     serializer: _Serializer,
# ) -> None:
#     """Generate the files with the properties and items set to ``null``."""
#     environment_cls = symbol_table.must_find_concrete_class(Identifier("Environment"))
#
#     for our_type in symbol_table.our_types:
#         if not isinstance(our_type, intermediate.ConcreteClass):
#             continue
#
#         if our_type.name not in class_graph.shortest_paths:
#             path_segments = []  # type: List[Union[str, int]]
#
#             container = generation.generate_minimal_instance(
#                 cls=our_type,
#                 path_segments=path_segments,
#                 constraints_by_class=constraints_by_class,
#                 symbol_table=symbol_table,
#             )
#
#             container_class = our_type
#         else:
#             (
#                 container,
#                 path_segments,
#             ) = generation.generate_minimal_instance_in_minimal_environment(
#                 cls=our_type,
#                 class_graph=class_graph,
#                 constraints_by_class=constraints_by_class,
#                 symbol_table=symbol_table,
#             )
#
#             container_class = environment_cls
#
#         handyman.fix_instance(instance=container, path_segments=[])
#
#         replicator = generation.ContainerInstanceReplicator(
#             container_class=container_class,
#             container=container,
#             path_to_instance=path_segments,
#         )
#
#         for prop in our_type.properties:
#             type_anno = intermediate.beneath_optional(prop.type_annotation)
#
#             if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
#                 # NOTE (mristin, 2022-06-25):
#                 # We still want to check all the list properties, both optional and
#                 # required.
#                 if not isinstance(type_anno, intermediate.ListTypeAnnotation):
#                     continue
#
#             container, _, path_segments = replicator.replicate()
#
#             jsonable_container = serializer.serialize_instance(instance=container)
#
#             jsonable_instance = dereference(
#                 start_object=jsonable_container,
#                 path=to_json_path_segments(path=path_segments),
#             )
#
#             prop_name_json = aas_core_codegen.naming.json_property(prop.name)
#
#             base_pth = test_data_dir / "Json"
#             if container_class is environment_cls and our_type is not environment_cls:
#                 base_pth /= "ContainedInEnvironment"
#             else:
#                 base_pth /= "SelfContained"
#
#             if not isinstance(
#                 prop.type_annotation, intermediate.OptionalTypeAnnotation
#             ):
#                 jsonable_instance[prop_name_json] = None
#
#                 pth = (
#                     base_pth
#                     / "Unexpected"
#                     / "NullViolation"
#                     / aas_core_codegen.naming.json_model_type(our_type.name)
#                     / f"{prop_name_json}_value.json"
#                 )
#
#                 pth.parent.mkdir(parents=True, exist_ok=True)
#
#                 with pth.open("wt") as fid:
#                     json.dump(jsonable_container, fid, indent=2, sort_keys=True)
#
#             if isinstance(type_anno, intermediate.ListTypeAnnotation):
#                 jsonable_instance[prop_name_json] = [None]
#
#                 pth = (
#                     base_pth
#                     / "Unexpected"
#                     / "NullViolation"
#                     / aas_core_codegen.naming.json_model_type(our_type.name)
#                     / f"{prop_name_json}_item.json"
#                 )
#
#                 pth.parent.mkdir(parents=True, exist_ok=True)
#
#                 with pth.open("wt") as fid:
#                     json.dump(jsonable_container, fid, indent=2, sort_keys=True)


def generate(test_data_dir: pathlib.Path) -> None:
    """Generate the JSON files."""
    (
        symbol_table,
        constraints_by_class,
    ) = common.load_symbol_table_and_infer_constraints_for_schema()

    serializer = _Serializer(symbol_table=symbol_table)

    for test_case in generation.generate(
        symbol_table=symbol_table, constraints_by_class=constraints_by_class
    ):
        relative_pth = _relative_path(test_case=test_case)
        jsonable = serializer.serialize_instance(
            instance=test_case.preserialized_container
        )

        pth = test_data_dir / relative_pth

        parent = pth.parent
        if not parent.exists():
            parent.mkdir(parents=True)

        with pth.open("wt") as fid:
            json.dump(jsonable, fid, indent=2, sort_keys=True)

    # TODO (mristin, 2023-03-10): fix this once everything else is working
    # _generate_null_violations(
    #     test_data_dir=test_data_dir,
    #     symbol_table=symbol_table,
    #     constraints_by_class=constraints_by_class,
    #     class_graph=class_graph,
    #     handyman=handyman,
    #     serializer=serializer,
    # )


def main() -> None:
    """Execute the main routine."""
    this_path = pathlib.Path(os.path.realpath(__file__))
    test_data_dir = this_path.parent.parent / "test_data"

    generate(test_data_dir=test_data_dir)


if __name__ == "__main__":
    main()
