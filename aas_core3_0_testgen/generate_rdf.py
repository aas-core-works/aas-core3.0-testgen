"""Generate test data in RDF for the meta-model V3aas-core3.0-testgen."""
import argparse
import base64
import io
import pathlib
import textwrap
import urllib.parse
from typing import (
    List,
    Optional,
    Union,
)

import aas_core_codegen.common
import aas_core_codegen.naming
import aas_core_codegen.rdf_shacl.common
import aas_core_codegen.rdf_shacl.naming
from aas_core_codegen import intermediate
from aas_core_codegen.common import Identifier, Stripped
from icontract import ensure, require

from aas_core3_0_testgen import common, generation
from aas_core3_0_testgen.codegened import preserialization

_INDENT = "    "


@ensure(lambda result: not result.is_absolute())
def _relative_path(test_case: generation.CaseUnion) -> pathlib.Path:
    """Generate the relative path based on the test case."""
    assert test_case.__class__.__name__.startswith("Case")

    cls_name = aas_core_codegen.rdf_shacl.naming.class_name(test_case.cls.name)

    base_pth = pathlib.Path("Rdf")

    if test_case.container_class is test_case.cls:
        base_pth /= "SelfContained"
    else:
        container_class_name = aas_core_codegen.naming.capitalized_camel_case(
            test_case.container_class.name
        )
        base_pth /= f"ContainedIn{container_class_name}"

    if test_case.expected:
        base_pth = base_pth / "Expected" / cls_name

    else:
        assert test_case.__class__.__name__.startswith("Case")
        cause = test_case.__class__.__name__[len("Case") :]

        base_pth = base_pth / "Unexpected" / cause / cls_name

    if isinstance(test_case, generation.CaseMinimal):
        return base_pth / "minimal.ttl"

    elif isinstance(test_case, generation.CaseMaximal):
        return base_pth / "maximal.ttl"

    elif isinstance(test_case, generation.CaseTypeViolation):
        prop_name = aas_core_codegen.rdf_shacl.naming.property_name(
            test_case.property_name
        )

        return base_pth / f"{prop_name}.ttl"

    elif isinstance(test_case, generation.CasePositivePatternExample):
        prop_name = aas_core_codegen.rdf_shacl.naming.property_name(
            test_case.property_name
        )

        return (
            base_pth
            / f"{prop_name}OverPatternExamples"
            / f"{test_case.example_name}.ttl"
        )

    elif isinstance(test_case, generation.CasePatternViolation):
        prop_name = aas_core_codegen.rdf_shacl.naming.property_name(
            test_case.property_name
        )

        return base_pth / prop_name / f"{test_case.example_name}.ttl"

    elif isinstance(test_case, generation.CaseRequiredViolation):
        prop_name = aas_core_codegen.rdf_shacl.naming.property_name(
            test_case.property_name
        )

        return base_pth / f"{prop_name}.ttl"

    elif isinstance(test_case, generation.CaseNullViolation):
        # NOTE (mristin, 2023-03-15):
        # Null violations are going to be skipped, but we add the handler here for
        # completeness.
        prop_name = aas_core_codegen.naming.xml_property(test_case.property_name)

        return base_pth / f"{prop_name}.xml"

    elif isinstance(test_case, generation.CaseMinLengthViolation):
        prop_name = aas_core_codegen.rdf_shacl.naming.property_name(test_case.prop.name)

        return base_pth / f"{prop_name}.ttl"

    elif isinstance(test_case, generation.CaseMaxLengthViolation):
        prop_name = aas_core_codegen.rdf_shacl.naming.property_name(
            test_case.property_name
        )

        return base_pth / f"{prop_name}.ttl"

    elif isinstance(test_case, generation.CaseUnexpectedAdditionalProperty):
        return base_pth / "invalid.ttl"

    elif isinstance(test_case, generation.CaseDateTimeUtcViolationOnFebruary29th):
        prop_name = aas_core_codegen.rdf_shacl.naming.property_name(
            test_case.property_name
        )

        return base_pth / f"{prop_name}.ttl"

    elif isinstance(test_case, generation.CasePositiveValueExample):
        return (
            base_pth
            / "OverValueExamples"
            / test_case.data_type_def_literal.name
            / f"{test_case.example_name}.ttl"
        )

    elif isinstance(test_case, generation.CaseInvalidValueExample):
        return (
            base_pth
            / test_case.data_type_def_literal.name
            / f"{test_case.example_name}.ttl"
        )

    elif isinstance(test_case, generation.CasePositiveMinMaxExample):
        return (
            base_pth
            / "OverMinMaxExamples"
            / test_case.data_type_def_literal.name
            / f"{test_case.example_name}.ttl"
        )

    elif isinstance(test_case, generation.CaseInvalidMinMaxExample):
        return (
            base_pth
            / test_case.data_type_def_literal.name
            / f"{test_case.example_name}.ttl"
        )

    elif isinstance(test_case, generation.CaseEnumViolation):
        enum_name = aas_core_codegen.rdf_shacl.naming.class_name(test_case.enum.name)

        prop_name = aas_core_codegen.rdf_shacl.naming.property_name(test_case.prop.name)

        return base_pth / f"{prop_name}_as_{enum_name}.ttl"

    elif isinstance(test_case, generation.CasePositiveManual):
        return base_pth / f"{test_case.name}.ttl"

    elif isinstance(test_case, generation.CaseSetViolation):
        prop_name = aas_core_codegen.rdf_shacl.naming.property_name(
            test_case.property_name
        )

        return base_pth / f"{prop_name}.ttl"

    elif isinstance(test_case, generation.CaseConstraintViolation):
        return base_pth / f"{test_case.name}.ttl"

    else:
        aas_core_codegen.common.assert_never(test_case)


@require(lambda instance: instance.class_name == "Environment")
def _serialize_environment(
    instance: preserialization.Instance, symbol_table: intermediate.SymbolTable
) -> Stripped:
    """Serialize all the identifiables in the environment as blocks of RDF turtle."""
    environment_cls = symbol_table.must_find_concrete_class(Identifier("Environment"))

    identifiable_cls = symbol_table.must_find_abstract_class(Identifier("Identifiable"))

    blocks = [
        Stripped(
            f"""\
@prefix aas: <{symbol_table.meta_model.xml_namespace}/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xs: <http://www.w3.org/2001/XMLSchema#> ."""
        )
    ]  # type: List[Stripped]

    for prop_name, value in instance.properties.items():
        prop = environment_cls.properties_by_name[Identifier(prop_name)]

        type_anno = intermediate.beneath_optional(prop.type_annotation)
        assert isinstance(type_anno, intermediate.ListTypeAnnotation)

        assert (
            isinstance(type_anno.items, intermediate.OurTypeAnnotation)
            and isinstance(type_anno.items.our_type, intermediate.Class)
            and type_anno.items.our_type.is_subclass_of(identifiable_cls)
        ), (
            f"Expected the property {prop_name!r} of the {environment_cls.name} to "
            f"be a list of {identifiable_cls.name!r}"
        )

        assert isinstance(value, preserialization.ListOfInstances)

        for identifiable in value.values:
            blocks.append(
                _serialize_root_identifiable(
                    instance=identifiable, symbol_table=symbol_table
                )
            )

    return Stripped("\n\n".join(blocks))


def _serialize_primitive_value(value: preserialization.PrimitiveValueUnion) -> Stripped:
    """Serialize the given primitive value into an RDF literal."""
    content = None  # type: Optional[str]
    xs_type = None  # type: Optional[str]

    if isinstance(value, bool):
        content = "true" if value else "false"
        xs_type = "xs:boolean"
    elif isinstance(value, int):
        content = str(value)
        assert abs(value) < (2**63 - 1)
        xs_type = "xs:long"
    elif isinstance(value, float):
        content = str(value)
        xs_type = "xs:double"
    elif isinstance(value, str):
        content = value
        xs_type = "xs:string"
    elif isinstance(value, bytes):
        content = base64.b64encode(value).decode(encoding="ascii")
        xs_type = "xs:base64Binary"
    else:
        aas_core_codegen.common.assert_never(value)

    assert content is not None
    assert xs_type is not None

    return Stripped(
        f"{aas_core_codegen.rdf_shacl.common.string_literal(content)}^^{xs_type}"
    )


def _serialize_root_identifiable(
    instance: preserialization.Instance, symbol_table: intermediate.SymbolTable
) -> Stripped:
    """Serialize the identifiable instance as a block of RDF turtle."""
    identifiable_cls = symbol_table.must_find_abstract_class(Identifier("Identifiable"))

    cls = symbol_table.must_find_concrete_class(instance.class_name)

    assert cls.is_subclass_of(identifiable_cls)

    iri = instance.properties.get("ID", "ID-UNSPECIFIED")
    if iri is None:
        raise AssertionError(
            f"The generated identifiable instance of class {cls.name!r} lacks "
            f"the 'ID' property; why was it not set?"
        )

    assert isinstance(
        iri, str
    ), f"Expected the property ID to be a string, but got {type(iri)}: {iri=}"

    rdf_name = aas_core_codegen.rdf_shacl.naming.class_name(cls.name)

    stmts = []  # type: List[Stripped]

    for prop_name, value in instance.properties.items():
        assert (
            value is not None
        ), f"Unexpected ``None`` for property {prop_name!r} of class {cls.name!r}"

        prop = cls.properties_by_name[Identifier(prop_name)]
        stmts.append(
            _serialize_property(prop=prop, value=value, symbol_table=symbol_table)
        )

    writer = io.StringIO()
    writer.write(f"<{iri}> rdf:type aas:{rdf_name} ;\n")

    for stmt in stmts:
        writer.write(textwrap.indent(stmt, _INDENT))
        writer.write("\n")

    writer.write(".")

    return Stripped(writer.getvalue())


def _serialize_instance(
    instance: preserialization.Instance, symbol_table: intermediate.SymbolTable
) -> Stripped:
    """Generate the literal representing the instance."""
    cls = symbol_table.must_find_concrete_class(instance.class_name)

    rdf_name = aas_core_codegen.rdf_shacl.naming.class_name(cls.name)

    stmts = [Stripped(f"rdf:type aas:{rdf_name} ;")]  # type: List[Stripped]

    for prop_name, value in instance.properties.items():
        assert (
            value is not None
        ), f"Unexpected ``None`` for the property {prop_name!r} of class {cls.name!r}"

        prop = cls.properties_by_name[Identifier(prop_name)]
        stmt = _serialize_property(prop=prop, value=value, symbol_table=symbol_table)

        stmts.append(stmt)

    writer = io.StringIO()
    writer.write("[\n")
    for stmt in stmts:
        writer.write(textwrap.indent(stmt, _INDENT))
        writer.write("\n")
    writer.write("]")

    return Stripped(writer.getvalue())


TypeAnnotationExceptOptionalAndList = Union[
    intermediate.PrimitiveTypeAnnotation,
    intermediate.OurTypeAnnotation,
]

aas_core_codegen.common.assert_union_without_excluded(
    original_union=intermediate.TypeAnnotationUnion,
    subset_union=TypeAnnotationExceptOptionalAndList,
    excluded=[intermediate.OptionalTypeAnnotation, intermediate.ListTypeAnnotation],
)


def _serialize_value(
    value: preserialization.ValueUnion,
    type_annotation: TypeAnnotationExceptOptionalAndList,
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Serialize the given value as an RDF literal."""
    if isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation):
        assert isinstance(value, preserialization.PrimitiveValueTuple)
        return _serialize_primitive_value(value=value)

    elif isinstance(type_annotation, intermediate.OurTypeAnnotation):
        if isinstance(type_annotation.our_type, intermediate.Enumeration):
            assert isinstance(value, str)

            literal = type_annotation.our_type.literals_by_value.get(value, None)
            if literal is not None:
                literal_name = literal.name
            else:
                # NOTE (mristin, 2022-09-01):
                # This is a case where the literal value is invalid. We synthesise
                # one on the spot.
                literal_name = Identifier("non_existing_literal")
                while literal_name in type_annotation.our_type.literals_by_name:
                    literal_name = Identifier(f"really_{literal_name}")

            iri = "/".join(
                [
                    symbol_table.meta_model.xml_namespace,
                    urllib.parse.quote(
                        aas_core_codegen.rdf_shacl.naming.class_name(
                            type_annotation.our_type.name
                        )
                    ),
                    urllib.parse.quote(
                        aas_core_codegen.rdf_shacl.naming.enumeration_literal(
                            literal_name
                        )
                    ),
                ]
            )

            return Stripped(f"<{iri}>")

        elif isinstance(type_annotation.our_type, intermediate.ConstrainedPrimitive):
            assert isinstance(value, preserialization.PrimitiveValueTuple)
            return _serialize_primitive_value(value=value)

        elif isinstance(
            type_annotation.our_type,
            (intermediate.AbstractClass, intermediate.ConcreteClass),
        ):
            assert isinstance(
                value, preserialization.Instance
            ), f"{value=} as {type(value)=}"

            return Stripped(
                _serialize_instance(instance=value, symbol_table=symbol_table)
            )
        else:
            aas_core_codegen.common.assert_never(type_annotation.our_type)
    else:
        aas_core_codegen.common.assert_never(type_annotation)

    raise AssertionError("Unexpected execution path")


def _serialize_property(
    prop: intermediate.Property,
    value: preserialization.ValueUnion,
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    iri = "/".join(
        [
            symbol_table.meta_model.xml_namespace,
            urllib.parse.quote(
                aas_core_codegen.rdf_shacl.naming.class_name(prop.specified_for.name)
            ),
            urllib.parse.quote(
                aas_core_codegen.rdf_shacl.naming.property_name(prop.name)
            ),
        ]
    )

    if isinstance(
        type_anno,
        (intermediate.PrimitiveTypeAnnotation, intermediate.OurTypeAnnotation),
    ):
        serialized_value = _serialize_value(
            value=value, type_annotation=type_anno, symbol_table=symbol_table
        )

        return Stripped(f"<{iri}> {serialized_value} ;")

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        assert isinstance(value, preserialization.ListOfInstances)

        stmts = []  # type: List[Stripped]

        for item in value.values:
            if isinstance(type_anno.items, intermediate.ListTypeAnnotation):
                raise NotImplementedError(
                    "Currently, we do not handle nested lists when serializing "
                    "instances for RDF. Please contact the developers if you need this "
                    "feature."
                )

            if isinstance(type_anno.items, intermediate.OptionalTypeAnnotation):
                raise NotImplementedError(
                    "Currently, we do not handle lists of optionals when serializing "
                    "instances for RDF. Please contact the developers if you need this "
                    "feature."
                )

            serialized_value = _serialize_value(
                value=item, type_annotation=type_anno.items, symbol_table=symbol_table
            )

            stmts.append(Stripped(f"<{iri}> {serialized_value} ;"))

        return Stripped("\n".join(stmts))
    else:
        aas_core_codegen.common.assert_never(type_anno)

    raise AssertionError("Unexpected execution path")


def generate(model_path: pathlib.Path, test_data_dir: pathlib.Path) -> None:
    """Generate the XML files."""
    (
        symbol_table,
        constraints_by_class,
    ) = common.load_symbol_table_and_infer_constraints_for_schema(model_path=model_path)

    identifiable_cls = symbol_table.must_find_abstract_class(Identifier("Identifiable"))

    environment_cls = symbol_table.must_find_concrete_class(Identifier("Environment"))

    for test_case in generation.generate(
        symbol_table=symbol_table, constraints_by_class=constraints_by_class
    ):
        # NOTE (mristin, 2023-03-15):
        # We can not represent ``null`` in RDF.
        if isinstance(test_case, generation.CaseNullViolation):
            continue

        if (
            isinstance(test_case, generation.CaseMinLengthViolation)
            and test_case.min_value == 1
            and isinstance(
                intermediate.beneath_optional(test_case.prop.type_annotation),
                intermediate.ListTypeAnnotation,
            )
        ):
            # NOTE (mristin, 2023-03-15):
            # RDF can not easily represent empty lists, so we skip these negative
            # cases where an empty list is the only fulfilling example.
            continue

        if isinstance(test_case, generation.CaseUnexpectedAdditionalProperty):
            # NOTE (mristin, 2023-03-15):
            # We need typing information to generate properties of an instance in RDF.
            # Thus, we can not generate an additional property for which we do not know
            # the type in advance.
            continue

        if isinstance(test_case, generation.CaseTypeViolation):
            # NOTE (mristin, 2023-03-15):
            # Type violations are hard to generate right in RDF. We omit them at this
            # moment due to lack of time.
            continue

        if (
            isinstance(test_case, generation.CaseRequiredViolation)
            and test_case.cls.is_subclass_of(identifiable_cls)
            and test_case.property_name == "id"
        ):
            # NOTE (mristin, 2023-03-15):
            # We skip cases where the identifiable is missing the ID as this case can
            # not be represented in RDF at all.
            continue

        if test_case.container_class != environment_cls:
            # NOTE (mristin, 2023-03-15):
            # We can only flatten and serialize an instance of an Environment.
            # While theoretically we could also handle any list of identifiables,
            # we simply skip these edge cases due to lack of time at the moment.
            continue

        relative_pth = _relative_path(test_case=test_case)

        pth = test_data_dir / relative_pth

        parent = pth.parent
        if not parent.exists():
            parent.mkdir(parents=True)

        try:
            text = _serialize_environment(
                instance=test_case.preserialized_container, symbol_table=symbol_table
            )
        except Exception as exception:
            raise RuntimeError(
                f"Failed to serialize the container "
                f"for the case {test_case.__class__.__name__} to {pth}"
            ) from exception

        with pth.open("wt", encoding="utf-8") as fid:
            fid.write(text)
            fid.write("\n")


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


if __name__ == "__main__":
    main()
