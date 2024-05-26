"""Generate test data in XML for the meta-model V3aas-core3.0-testgen."""
import argparse
import base64
import enum
import math
import pathlib
import re
from typing import (
    List,
    Optional,
)
from xml.dom import minidom

import aas_core_codegen.common
import aas_core_codegen.naming
from aas_core_codegen import intermediate
from aas_core_codegen.common import Identifier
from icontract import ensure, require
from aas_core3 import xmlization as aasxmlization, verification as aasverification

from aas_core3_0_testgen import common, generation
from aas_core3_0_testgen.codegened import preserialization

_XML_1_0_TEXT_RE = re.compile(
    r"^[\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]*$"
)


def _conforms_to_xml_1_0(value: Optional[preserialization.ValueUnion]) -> bool:
    """Check recursively that the value conforms to XML 1.0."""
    if value is None:
        return True

    if isinstance(value, preserialization.PrimitiveValueTuple):
        if isinstance(value, str):
            return _XML_1_0_TEXT_RE.match(value) is not None
        else:
            return True
    elif isinstance(value, preserialization.Instance):
        # noinspection PyTypeChecker
        for prop_value in value.properties.values():
            if not _conforms_to_xml_1_0(prop_value):
                return False

        return True
    elif isinstance(value, preserialization.ListOfInstances):
        for instance in value.values:
            if not _conforms_to_xml_1_0(instance):
                return False

        return True

    else:
        aas_core_codegen.common.assert_never(value)


# NOTE (mristin):
# We explicitly decouple the path generation code from JSON and other formats since it
# is completely accidental that they coincide. We anticipate that there will be
# differences in the future. For example, we will most probably introduce different
# kinds of negative examples.


class KindOfNegative(enum.Enum):
    """Define possible kinds of negative examples."""

    UNSERIALIZABLE = "Unserializable"
    INVALID = "Invalid"


@require(lambda relative_path: not relative_path.is_absolute())
@require(lambda relative_path: relative_path.suffix == ".xml")
def _generate_expected_path(
    base_path: pathlib.Path, cls_name: str, relative_path: pathlib.Path
) -> pathlib.Path:
    """
    Generate the path to the positive example.

    >>> _generate_expected_path(
    ...     base_path=pathlib.Path("ContainedInEnvironment"),
    ...     cls_name="property",
    ...     relative_path=pathlib.Path("maximal.xml")
    ... ).as_posix()
    'ContainedInEnvironment/Expected/property/maximal.xml'
    """
    return base_path / "Expected" / cls_name / relative_path


@require(lambda relative_path: not relative_path.is_absolute())
@require(lambda relative_path: relative_path.suffix == ".xml")
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
    ...     base_path=pathlib.Path("ContainedInEnvironment"),
    ...     kind=KindOfNegative.INVALID,
    ...     cause="MaxLengthViolation",
    ...     cls_name="property",
    ...     relative_path=pathlib.Path("idShort.xml")
    ... ).as_posix()
    'ContainedInEnvironment/Unexpected/Invalid/MaxLengthViolation/property/idShort.xml'
    """
    return base_path / "Unexpected" / kind.value / cause / cls_name / relative_path


@ensure(lambda result: not result.is_absolute())
def _relative_path(test_case: generation.CaseUnion) -> pathlib.Path:
    """Generate the relative path based on the test case."""
    assert test_case.__class__.__name__.startswith("Case")

    cls_name = aas_core_codegen.naming.xml_class_name(test_case.cls.name)

    base_pth = pathlib.Path("Xml")

    if test_case.container_class is test_case.cls:
        base_pth /= "SelfContained"
    else:
        container_class_name = aas_core_codegen.naming.capitalized_camel_case(
            test_case.container_class.name
        )
        base_pth /= f"ContainedIn{container_class_name}"

    cause = None  # type: Optional[str]
    if not test_case.expected:
        assert test_case.__class__.__name__.startswith("Case")
        cause = test_case.__class__.__name__[len("Case") :]

    if isinstance(test_case, generation.CaseMinimal):
        return _generate_expected_path(
            base_path=base_pth,
            cls_name=cls_name,
            relative_path=pathlib.Path("minimal.xml"),
        )

    elif isinstance(test_case, generation.CaseMaximal):
        return _generate_expected_path(
            base_path=base_pth,
            cls_name=cls_name,
            relative_path=pathlib.Path("maximal.xml"),
        )

    elif isinstance(test_case, generation.CaseTypeViolation):
        prop_name = aas_core_codegen.naming.xml_property(test_case.property_name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.UNSERIALIZABLE,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{prop_name}.xml"),
        )

    elif isinstance(test_case, generation.CasePositivePatternExample):
        prop_name = aas_core_codegen.naming.xml_property(test_case.property_name)

        return _generate_expected_path(
            base_path=base_pth,
            cls_name=cls_name,
            relative_path=(
                pathlib.Path(f"{prop_name}OverPatternExamples")
                / f"{test_case.example_name}.xml"
            ),
        )

    elif isinstance(test_case, generation.CasePatternViolation):
        prop_name = aas_core_codegen.naming.xml_property(test_case.property_name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.INVALID,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(prop_name) / f"{test_case.example_name}.xml",
        )

    elif isinstance(test_case, generation.CaseRequiredViolation):
        prop_name = aas_core_codegen.naming.xml_property(test_case.property_name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.UNSERIALIZABLE,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{prop_name}.xml"),
        )

    elif isinstance(test_case, generation.CaseNullViolation):
        # NOTE (mristin, 2023-03-15):
        # Null violations are going to be skipped, but we add the handler here for
        # completeness.
        prop_name = aas_core_codegen.naming.xml_property(test_case.property_name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.UNSERIALIZABLE,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{prop_name}.xml"),
        )

    elif isinstance(test_case, generation.CaseMinLengthViolation):
        prop_name = aas_core_codegen.naming.xml_property(test_case.prop.name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.INVALID,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{prop_name}.xml"),
        )

    elif isinstance(test_case, generation.CaseMaxLengthViolation):
        prop_name = aas_core_codegen.naming.xml_property(test_case.property_name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.INVALID,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{prop_name}.xml"),
        )

    elif isinstance(test_case, generation.CaseDateTimeUtcViolationOnFebruary29th):
        prop_name = aas_core_codegen.naming.xml_property(test_case.property_name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.INVALID,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{prop_name}.xml"),
        )

    elif isinstance(test_case, generation.CasePositiveValueExample):
        return _generate_expected_path(
            base_path=base_pth,
            cls_name=cls_name,
            relative_path=(
                pathlib.Path("OverValueExamples")
                / test_case.data_type_def_literal.name
                / f"{test_case.example_name}.xml"
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
                / f"{test_case.example_name}.xml"
            ),
        )

    elif isinstance(test_case, generation.CasePositiveMinMaxExample):
        return _generate_expected_path(
            base_path=base_pth,
            cls_name=cls_name,
            relative_path=(
                pathlib.Path("OverMinMaxExamples")
                / test_case.data_type_def_literal.name
                / f"{test_case.example_name}.xml"
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
                / f"{test_case.example_name}.xml"
            ),
        )

    elif isinstance(test_case, generation.CaseUnexpectedAdditionalProperty):
        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.UNSERIALIZABLE,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path("invalid.xml"),
        )

    elif isinstance(test_case, generation.CaseEnumViolation):
        enum_name = aas_core_codegen.naming.xml_class_name(test_case.enum.name)
        prop_name = aas_core_codegen.naming.xml_property(test_case.prop.name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.UNSERIALIZABLE,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{prop_name}_as_{enum_name}.xml"),
        )

    elif isinstance(test_case, generation.CasePositiveManual):
        return _generate_expected_path(
            base_path=base_pth,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{test_case.name}.xml"),
        )

    elif isinstance(test_case, generation.CaseSetViolation):
        prop_name = aas_core_codegen.naming.xml_property(test_case.property_name)

        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.INVALID,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{prop_name}.xml"),
        )

    elif isinstance(test_case, generation.CaseConstraintViolation):
        assert cause is not None
        return _generate_unexpected_path(
            base_path=base_pth,
            kind=KindOfNegative.INVALID,
            cause=cause,
            cls_name=cls_name,
            relative_path=pathlib.Path(f"{test_case.name}.xml"),
        )

    else:
        aas_core_codegen.common.assert_never(test_case)


class _Serializer:
    """Serialize an environment to an XML element."""

    def __init__(self, symbol_table: intermediate.SymbolTable) -> None:
        """Initialize with the given values."""
        self.symbol_table = symbol_table

    def serialize_to_root_element(
        self,
        instance: preserialization.Instance,
        element_name: str,
    ) -> minidom.Element:
        """Serialize the ``environment`` to a JSON-able object."""
        impl = minidom.getDOMImplementation()
        assert impl is not None
        doc = impl.createDocument(
            namespaceURI=self.symbol_table.meta_model.xml_namespace,
            qualifiedName=element_name,
            doctype=None,
        )

        root = doc.documentElement

        # noinspection SpellCheckingInspection
        root.setAttribute("xmlns", self.symbol_table.meta_model.xml_namespace)

        sequence = self._serialize_instance(instance=instance, doc=doc)
        for node in sequence:
            root.appendChild(node)

        assert isinstance(root, minidom.Element)
        return root

    # noinspection PyMethodMayBeStatic
    def _serialize_primitive(
        self, value: preserialization.PrimitiveValueUnion, doc: minidom.Document
    ) -> minidom.Text:
        text = None  # type: Optional[str]

        if isinstance(value, bytes):
            text = base64.b64encode(value).decode(encoding="ascii")
        elif isinstance(value, bool):
            text = "true" if value else "false"
        elif isinstance(value, int):
            text = str(value)
        elif isinstance(value, float):
            if math.isnan(value):
                text = "NaN"
            else:
                if math.isinf(value):
                    text = "INF" if value >= 0 else "-INF"
                else:
                    # The 17 digits are necessary for the round trip.
                    # See: https://stackoverflow.com/questions/32685380/float-to-string-round-trip-test
                    text = f"{value:.17g}"
        elif isinstance(value, str):
            text = value
        else:
            aas_core_codegen.common.assert_never(value)

        assert text is not None
        text_node = doc.createTextNode(text)  # type: ignore
        assert isinstance(text_node, minidom.Text)
        return text_node

    def _serialize_instance(
        self, instance: preserialization.Instance, doc: minidom.Document
    ) -> List[minidom.Element]:
        sequence = []  # type: List[minidom.Element]

        # NOTE (mristin, 2022-06-20):
        # We need to re-order the sequence so that it strictly follows the order of the
        # properties in the meta-model. Otherwise, the XML schema will complain.

        cls = self.symbol_table.must_find_concrete_class(instance.class_name)

        order_map = {prop.name: i for i, prop in enumerate(cls.properties)}

        indices_prop_names = [
            (order_map[Identifier(prop_name)], prop_name)
            if prop_name in order_map
            else (math.inf, prop_name)
            for prop_name in instance.properties
        ]

        indices_prop_names.sort()

        prop_names = [prop_name for _, prop_name in indices_prop_names]

        for prop_name in prop_names:
            prop_value = instance.properties[prop_name]

            prop_element = doc.createElement(
                aas_core_codegen.naming.xml_property(Identifier(prop_name))
            )

            assert prop_value is not None, (
                f"Unexpected None value in XML in {cls.name!r} "
                f"and property {prop_name!r}"
            )

            if isinstance(prop_value, preserialization.PrimitiveValueTuple):
                text_node = self._serialize_primitive(prop_value, doc)
                prop_element.appendChild(text_node)

            elif isinstance(prop_value, preserialization.Instance):
                subsequence = self._serialize_instance(prop_value, doc)

                a_cls = self.symbol_table.must_find_class(prop_value.class_name)

                if (
                    a_cls.serialization is not None
                    and a_cls.serialization.with_model_type
                ):
                    model_type_node = doc.createElement(
                        aas_core_codegen.naming.xml_class_name(prop_value.class_name)
                    )
                    for node in subsequence:
                        model_type_node.appendChild(node)

                    prop_element.appendChild(model_type_node)
                else:
                    for node in subsequence:
                        prop_element.appendChild(node)

            elif isinstance(prop_value, preserialization.ListOfInstances):
                subsequence = self._serialize_list_of_instances(prop_value, doc)

                for node in subsequence:
                    prop_element.appendChild(node)
            else:
                aas_core_codegen.common.assert_never(prop_value)

            sequence.append(prop_element)

        return sequence

    def _serialize_list_of_instances(
        self, list_of_instances: preserialization.ListOfInstances, doc: minidom.Document
    ) -> List[minidom.Element]:
        sequence = []  # type: List[minidom.Element]

        for value in list_of_instances.values:
            model_type_node = doc.createElement(
                aas_core_codegen.naming.xml_class_name(value.class_name)
            )

            subsequence = self._serialize_instance(instance=value, doc=doc)

            for node in subsequence:
                model_type_node.appendChild(node)

            sequence.append(model_type_node)

        return sequence


def generate(model_path: pathlib.Path, test_data_dir: pathlib.Path) -> None:
    """Generate the XML files."""
    (
        symbol_table,
        constraints_by_class,
    ) = common.load_symbol_table_and_infer_constraints_for_schema(model_path=model_path)

    serializer = _Serializer(symbol_table=symbol_table)

    for test_case in generation.generate(
        symbol_table=symbol_table, constraints_by_class=constraints_by_class
    ):
        # NOTE (mristin, 2023-03-15):
        # We can not represent ``null`` in XML.
        if isinstance(test_case, generation.CaseNullViolation):
            continue

        relative_pth = _relative_path(test_case=test_case)

        pth = test_data_dir / relative_pth

        if not _conforms_to_xml_1_0(test_case.preserialized_container):
            # NOTE (mristin, 2022-09-01):
            # The test case can not be represented in XML 1.0, so we have to skip it.
            continue

        parent = pth.parent
        if not parent.exists():
            parent.mkdir(parents=True)

        element_name = aas_core_codegen.naming.xml_class_name(
            test_case.container_class.name
        )

        element = serializer.serialize_to_root_element(
            instance=test_case.preserialized_container, element_name=element_name
        )

        pth.write_text(element.toprettyxml(), encoding="utf-8")


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

    expected_dir = test_data_dir / "Xml" / "ContainedInEnvironment" / "Expected"
    expected_paths = sorted(expected_dir.glob("**/*.xml"))
    if len(expected_paths) == 0:
        raise AssertionError(f"Unexpected no positive examples in {expected_dir}")

    for pth in expected_paths:
        try:
            environment = aasxmlization.environment_from_file(path=pth)
        except aasxmlization.DeserializationException as exception:
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
        / "Xml"
        / "ContainedInEnvironment"
        / "Unexpected"
        / "Unserializable"
    )

    unserializable_paths = sorted(unserializable_dir.glob("**/*.xml"))
    if len(unserializable_paths) == 0:
        raise AssertionError(
            f"Unexpected no paths to unserializable instances "
            f"from {unserializable_dir}"
        )

    for pth in unserializable_paths:
        caught = None  # type: Optional[aasxmlization.DeserializationException]
        try:
            _ = aasxmlization.environment_from_file(path=pth)
        except aasxmlization.DeserializationException as exception:
            caught = exception

        if caught is None:
            raise AssertionError(
                f"Expected a de-serialization error from {pth}, but caught none"
            )

    invalid_dir = (
        test_data_dir / "Xml" / "ContainedInEnvironment" / "Unexpected" / "Invalid"
    )

    invalid_paths = sorted(invalid_dir.glob("**/*.xml"))
    if len(invalid_paths) == 0:
        raise AssertionError(
            f"Unexpected no paths to invalid instances in {invalid_dir}"
        )

    for pth in invalid_paths:
        try:
            environment = aasxmlization.environment_from_file(path=pth)
        except aasxmlization.DeserializationException as exception:
            raise AssertionError(  # pylint: disable=raise-missing-from
                f"Failed to de-serialize an expected instance from {pth}: {exception}"
            )

        errors = list(aasverification.verify(environment))
        if len(errors) == 0:
            raise AssertionError(
                f"Expected a verification error from {pth}, but got none"
            )


if __name__ == "__main__":
    main()
