"""Generate test data in JSON for the meta-model V3aas-core3.0-testgen."""
import argparse
import base64
import collections
import collections.abc
import enum
import json
import pathlib
from typing import (
    Union,
    OrderedDict,
    List,
    Any,
    MutableMapping,
    Sequence,
    Optional,
)

import aas_core_codegen.common
import aas_core_codegen.naming
from aas_core_codegen import intermediate
from aas_core_codegen.common import Identifier
from icontract import ensure, require
from typing_extensions import assert_never

from aas_core3 import jsonization as aasjsonization, verification as aasverification
from aas_core3_0_testgen import common, generation
from aas_core3_0_testgen.codegened import preserialization


# NOTE (mristin):
# We explicitly decouple the path generation code from XML and other formats since it
# is completely accidental that they coincide. We anticipate that there will be
# differences in the future. For example, we will most probably introduce different
# kinds of negative examples.


class KindOfNegative(enum.Enum):
    """Define possible kinds of negative examples."""

    UNSERIALIZABLE = "Unserializable"
    INVALID = "Invalid"


@require(lambda relative_path: not relative_path.is_absolute())
@require(lambda relative_path: relative_path.suffix == ".json")
def _generate_expected_path(
    base_path: pathlib.Path, cls_name: str, relative_path: pathlib.Path
) -> pathlib.Path:
    """
    Generate the path to the positive example.

    >>> _generate_expected_path(
    ...     base_path=pathlib.Path("ContainedInEnvironment"),
    ...     cls_name="Property",
    ...     relative_path=pathlib.Path("maximal.json")
    ... ).as_posix()
    'ContainedInEnvironment/Expected/Property/maximal.json'
    """
    return base_path / "Expected" / cls_name / relative_path


@require(lambda relative_path: not relative_path.is_absolute())
@require(lambda relative_path: relative_path.suffix == ".json")
def _generate_unexpected_path(
    base_path: pathlib.Path,
    kind: KindOfNegative,
    cause: str,
    cls_name: str,
    relative_path: pathlib.Path,
) -> pathlib.Path:
    """
    Generate the path to the negative example.

    >>> _generate_unexpected_path(
    ...     base_path=pathlib.Path("Json/ContainedInEnvironment"),
    ...     kind=KindOfNegative.INVALID,
    ...     cause="MaxLengthViolation",
    ...     cls_name="Property",
    ...     relative_path=pathlib.Path("idShort.json")
    ... ).as_posix()
    'Json/ContainedInEnvironment/Unexpected/Invalid/MaxLengthViolation/Property/idShort.json'
    """
    return base_path / "Unexpected" / kind.value / cause / cls_name / relative_path


@ensure(lambda result: not result.is_absolute())
@ensure(lambda result: len(result.parts) > 0 and result.parts[0] == "Json")
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

    cause = None  # type: Optional[str]
    if not test_case.expected:
        assert test_case.__class__.__name__.startswith("Case")
        cause = test_case.__class__.__name__[len("Case") :]

    if isinstance(test_case, generation.CaseMinimal):
        return _generate_expected_path(
            base_path=base_pth,
            cls_name=cls_name,
            relative_path=pathlib.Path("minimal.json"),
        )

    elif isinstance(test_case, generation.CaseMaximal):
        return _generate_expected_path(
            base_path=base_pth,
            cls_name=cls_name,
            relative_path=pathlib.Path("maximal.json"),
        )

    elif isinstance(test_case, generation.CaseTypeViolation):
        prop_name = aas_core_codegen.naming.json_property(test_case.property_name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.UNSERIALIZABLE,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{prop_name}.json"),
        )

    elif isinstance(test_case, generation.CasePositivePatternExample):
        prop_name = aas_core_codegen.naming.json_property(test_case.property_name)

        return _generate_expected_path(
            base_path=base_pth,
            cls_name=cls_name,
            relative_path=(
                pathlib.Path(f"{prop_name}OverPatternExamples")
                / f"{test_case.example_name}.json"
            ),
        )

    elif isinstance(test_case, generation.CasePatternViolation):
        prop_name = aas_core_codegen.naming.json_property(test_case.property_name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.INVALID,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(prop_name) / f"{test_case.example_name}.json",
        )

    elif isinstance(test_case, generation.CaseRequiredViolation):
        prop_name = aas_core_codegen.naming.json_property(test_case.property_name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.UNSERIALIZABLE,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{prop_name}.json"),
        )

    elif isinstance(test_case, generation.CaseNullViolation):
        prop_name = aas_core_codegen.naming.json_property(test_case.property_name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.UNSERIALIZABLE,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{prop_name}.json"),
        )

    elif isinstance(test_case, generation.CaseMinLengthViolation):
        prop_name = aas_core_codegen.naming.json_property(test_case.prop.name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.INVALID,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{prop_name}.json"),
        )

    elif isinstance(test_case, generation.CaseMaxLengthViolation):
        prop_name = aas_core_codegen.naming.json_property(test_case.property_name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.INVALID,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{prop_name}.json"),
        )

    elif isinstance(test_case, generation.CaseDateTimeUtcViolationOnFebruary29th):
        prop_name = aas_core_codegen.naming.json_property(test_case.property_name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.INVALID,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{prop_name}.json"),
        )

    elif isinstance(test_case, generation.CasePositiveValueExample):
        return _generate_expected_path(
            base_path=base_pth,
            cls_name=cls_name,
            relative_path=(
                pathlib.Path("OverValueExamples")
                / test_case.data_type_def_literal.name
                / f"{test_case.example_name}.json"
            ),
        )

    elif isinstance(test_case, generation.CaseInvalidValueExample):
        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.INVALID,
            cause=cause,
            cls_name=cls_name,
            relative_path=(
                pathlib.Path(test_case.data_type_def_literal.name)
                / f"{test_case.example_name}.json"
            ),
        )

    elif isinstance(test_case, generation.CasePositiveMinMaxExample):
        return _generate_expected_path(
            base_path=base_pth,
            cls_name=cls_name,
            relative_path=(
                pathlib.Path("OverMinMaxExamples")
                / test_case.data_type_def_literal.name
                / f"{test_case.example_name}.json"
            ),
        )

    elif isinstance(test_case, generation.CaseInvalidMinMaxExample):
        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.INVALID,
            cause=cause,
            cls_name=cls_name,
            relative_path=(
                pathlib.Path(test_case.data_type_def_literal.name)
                / f"{test_case.example_name}.json"
            ),
        )

    elif isinstance(test_case, generation.CaseUnexpectedAdditionalProperty):
        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.UNSERIALIZABLE,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path("invalid.json"),
        )

    elif isinstance(test_case, generation.CaseEnumViolation):
        enum_name = aas_core_codegen.naming.json_model_type(test_case.enum.name)
        prop_name = aas_core_codegen.naming.json_property(test_case.prop.name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.UNSERIALIZABLE,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{prop_name}_as_{enum_name}.json"),
        )

    elif isinstance(test_case, generation.CasePositiveManual):
        return _generate_expected_path(
            base_path=base_pth,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{test_case.name}.json"),
        )

    elif isinstance(test_case, generation.CaseSetViolation):
        prop_name = aas_core_codegen.naming.json_property(test_case.property_name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.INVALID,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{prop_name}.json"),
        )

    elif isinstance(test_case, generation.CaseConstraintViolation):
        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.INVALID,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{test_case.name}.json"),
        )

    else:
        aas_core_codegen.common.assert_never(test_case)


class _Serializer:
    """Serialize a container to a JSON object."""

    def __init__(self, symbol_table: intermediate.SymbolTable) -> None:
        """Initialize with the given values."""
        self.symbol_table = symbol_table

    def _serialize_value(self, value: Optional[preserialization.ValueUnion]) -> Any:
        if value is None:
            return None

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
            raise AssertionError("Unexpected execution path")

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


class _SerializerWithoutModelType(_Serializer):
    """Serialize a container to a JSON object with a lacking ``modelType``."""

    def __init__(
        self,
        symbol_table: intermediate.SymbolTable,
        target_instance: preserialization.Instance,
    ) -> None:
        """Initialize with the given values."""
        self.target_instance = target_instance

        super().__init__(symbol_table=symbol_table)

    def serialize_instance(
        self, instance: preserialization.Instance
    ) -> OrderedDict[str, Any]:
        """Convert the ``instance`` to a JSON-able data structure."""
        jsonable = super().serialize_instance(instance)

        if instance is self.target_instance:
            assert "modelType" in jsonable
            del jsonable["modelType"]

        return jsonable


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


def _generate_unserializables_without_model_type(
    symbol_table: intermediate.SymbolTable, test_data_dir: pathlib.Path
) -> None:
    """Generate the special cases where the required ``modelType`` is missing."""
    environment_cls = symbol_table.must_find_concrete_class(Identifier("Environment"))

    for cls in symbol_table.concrete_classes:
        if not cls.serialization.with_model_type:
            continue

        minimal_case = generation.generate_minimal_case(
            cls=cls, environment_cls=environment_cls
        )

        serializer_without_model_type = _SerializerWithoutModelType(
            symbol_table=symbol_table,
            target_instance=minimal_case.preserialized_instance,
        )

        base_pth: pathlib.Path
        if minimal_case.container_class is minimal_case.cls:
            base_pth = pathlib.Path("Json/SelfContained")
        else:
            container_model_type = aas_core_codegen.naming.json_model_type(
                minimal_case.container_class.name
            )
            base_pth = pathlib.Path(f"Json/ContainedIn{container_model_type}")

        relative_pth = _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.UNSERIALIZABLE,
            cause="MissingModelType",
            cls_name=aas_core_codegen.naming.json_model_type(minimal_case.cls.name),
            relative_path=pathlib.Path("withoutModelType.json"),
        )

        jsonable = serializer_without_model_type.serialize_instance(
            instance=minimal_case.preserialized_container
        )

        pth = test_data_dir / relative_pth

        parent = pth.parent
        parent.mkdir(parents=True, exist_ok=True)

        with pth.open("wt") as fid:
            json.dump(jsonable, fid, indent=2, sort_keys=True)


def generate(model_path: pathlib.Path, test_data_dir: pathlib.Path) -> None:
    """Generate the JSON files."""
    (
        symbol_table,
        constraints_by_class,
    ) = common.load_symbol_table_and_infer_constraints_for_schema(model_path=model_path)

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
        parent.mkdir(parents=True, exist_ok=True)

        with pth.open("wt") as fid:
            json.dump(jsonable, fid, indent=2, sort_keys=True)

    # NOTE (mristin):
    # We generate here explicitly cases for missing modelType property. This is
    # JSON-specific, so we generate it outside the general :py:mod:`generation`
    # module.
    _generate_unserializables_without_model_type(
        symbol_table=symbol_table, test_data_dir=test_data_dir
    )


def main() -> None:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_path", help="path to the meta-model", required=True)
    parser.add_argument(
        "--test_data_dir",
        help="path to the directory where the generated data resides",
        required=True,
    )
    args = parser.parse_args()

    model_path = pathlib.Path(args.model_path)
    test_data_dir = pathlib.Path(args.test_data_dir)

    generate(model_path=model_path, test_data_dir=test_data_dir)

    # NOTE (mristin):
    # We currently verify only the instances contained in an Environment for simplicity.
    # If time permits in the future, we will also validate the self-contained instances,
    # but we need to leverage either reflection or code generation to that end.

    expected_dir = test_data_dir / "Json" / "ContainedInEnvironment" / "Expected"
    expected_paths = sorted(expected_dir.glob("**/*.json"))
    if len(expected_paths) == 0:
        raise AssertionError(f"Unexpected no positive examples in {expected_dir}")

    for pth in expected_paths:
        with pth.open("rt", encoding="utf-8") as fid:
            jsonable = json.load(fid)

        try:
            environment = aasjsonization.environment_from_jsonable(jsonable=jsonable)
        except aasjsonization.DeserializationException as exception:
            raise AssertionError(  # pylint: disable=raise-missing-from
                f"Failed to de-serialize an expected instance from {pth}: {exception}"
            )

        errors = list(aasverification.verify(environment))
        if len(errors) != 0:
            errors_joined = "\n".join(str(error) for error in errors)
            raise AssertionError(
                f"Failed to verify an expected instance from {pth}:\n{errors_joined}"
            )

    unserializable_dir = (
        test_data_dir
        / "Json"
        / "ContainedInEnvironment"
        / "Unexpected"
        / "Unserializable"
    )

    unserializable_paths = sorted(unserializable_dir.glob("**/*.json"))
    if len(unserializable_paths) == 0:
        raise AssertionError(
            f"Unexpected no paths to unserializable instances "
            f"from {unserializable_dir}"
        )

    for pth in unserializable_paths:
        with pth.open("rt", encoding="utf-8") as fid:
            jsonable = json.load(fid)

        caught = None  # type: Optional[aasjsonization.DeserializationException]
        try:
            _ = aasjsonization.environment_from_jsonable(jsonable=jsonable)
        except aasjsonization.DeserializationException as exception:
            caught = exception

        if caught is None:
            raise AssertionError(
                f"Expected a de-serialization error from {pth}, but caught none"
            )

    invalid_dir = (
        test_data_dir / "Json" / "ContainedInEnvironment" / "Unexpected" / "Invalid"
    )

    invalid_paths = sorted(invalid_dir.glob("**/*.json"))
    if len(invalid_paths) == 0:
        raise AssertionError(
            f"Unexpected no paths to invalid instances in {invalid_dir}"
        )

    for pth in invalid_paths:
        with pth.open("rt", encoding="utf-8") as fid:
            jsonable = json.load(fid)

        try:
            environment = aasjsonization.environment_from_jsonable(jsonable=jsonable)
        except aasjsonization.DeserializationException as exception:
            raise AssertionError(  # pylint: disable=raise-missing-from
                f"Failed to de-serialize an invalid, but de-serializable "
                f"instance from {pth}: {exception}"
            )

        errors = list(aasverification.verify(environment))
        if len(errors) == 0:
            raise AssertionError(
                f"Expected a verification error from {pth}, but got none"
            )


if __name__ == "__main__":
    main()
