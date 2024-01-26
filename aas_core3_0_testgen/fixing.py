"""
Fix instances in place to conform to the meta-model constraints.

.. note::

    We fix instances on the best-effort basis. It might be that something goes wrong.
    Please always verify the results.
"""
import ast
import inspect
from typing import TypeVar, List, Type, Sequence, Union, Optional

from typing_extensions import assert_never

import aas_core3.constants as aas_constants
import aas_core3.types as aas_types
import aas_core3.verification as aas_verification
from aas_core3_0_testgen import common, primitiving
from aas_core3_0_testgen.codegened import abstract_fixing, preserialization, creation
from aas_core3_0_testgen.frozen_examples import xs_value as frozen_examples_xs_value

LangStringT = TypeVar("LangStringT", bound=aas_types.AbstractLangString)


def _extend_lang_string_set_to_have_an_entry_at_least_in_english(
    path_hash: common.CanHash,
    lang_string_set: List[LangStringT],
    lang_string_class: Type[LangStringT],
) -> None:
    """Extend ``lang_string_set`` to contain at least one entry in English."""
    has_english = False
    for lang_string in lang_string_set:
        language_lower = lang_string.language.lower()
        if language_lower == "en" or language_lower.startswith("en-"):
            has_english = True
            break

    if not has_english:
        text_path_hash = common.hash_path(path_hash, [len(lang_string_set), "text"])

        lang_string_set.append(
            lang_string_class(
                language="en-GB",
                text=f"Something random in English {text_path_hash.hexdigest()[:8]}",
            )
        )


def generate_url(path_hash: common.CanHash) -> str:
    """Generate a semi-random URL based on ``path_hash``."""
    domain = primitiving.choose_value(
        path_hash,
        [
            "something.com",
            "example.com",
            "an-example.com",
            "another-example.com",
            "some-company.com",
            "another-company.com",
            "yet-another-company.com",
        ],
    )

    return f"https://{domain}/{path_hash.hexdigest()[:8]}"


def generate_urn(path_hash: common.CanHash) -> str:
    """Generate a semi-random URL based on ``path_hash``."""
    prefix = primitiving.choose_value(
        path_hash,
        [
            "urn:something",
            "urn:example",
            "urn:an-example",
            "urn:another-example",
            "urn:some-company",
            "urn:another-company",
            "urn:yet-another-company",
        ],
    )
    number = int(path_hash.hexdigest()[:8], base=16)
    random_id = f"{number % 20:02d}"

    return f"{prefix}{random_id}:{path_hash.hexdigest()[:8]}"


def generate_id_short(path_hash: common.CanHash) -> str:
    """Generate a semi-random ID-short based on ``path_hash``."""
    return f"something{path_hash.hexdigest()[:8]}"


def generate_model_reference(
    path_hash: common.CanHash,
    expected_type: aas_types.KeyTypes,
) -> aas_types.Reference:
    """Generate a model reference to something semi-random of ``expected_type``."""
    if expected_type in aas_constants.AAS_IDENTIFIABLES:
        keys = [
            aas_types.Key(
                type=expected_type,
                value=generate_urn(common.hash_path(path_hash, ["keys", 0, "value"])),
            )
        ]
    elif (
        expected_type in aas_constants.AAS_SUBMODEL_ELEMENTS_AS_KEYS
        or expected_type is aas_types.KeyTypes.REFERABLE
    ):
        keys = [
            aas_types.Key(
                type=aas_types.KeyTypes.SUBMODEL,
                value=generate_urn(common.hash_path(path_hash, ["keys", 0, "value"])),
            ),
            aas_types.Key(
                type=expected_type,
                value=generate_id_short(
                    common.hash_path(path_hash, ["keys", 1, "value"])
                ),
            ),
        ]
    else:
        raise NotImplementedError(
            f"Unhandled {expected_type=}; when we developed this module there were "
            f"no other key types expected in the meta-model as a reference, "
            f"but this has obviously changed. Please contact the developers."
        )

    return aas_types.Reference(type=aas_types.ReferenceTypes.MODEL_REFERENCE, keys=keys)


def generate_external_reference(path_hash: common.CanHash) -> aas_types.Reference:
    """Generate a semi-random external reference."""
    keys = [
        aas_types.Key(
            type=aas_types.KeyTypes.GLOBAL_REFERENCE,
            value=generate_urn(common.hash_path(path_hash, ["keys", 0, "value"])),
        )
    ]

    return aas_types.Reference(
        type=aas_types.ReferenceTypes.EXTERNAL_REFERENCE, keys=keys
    )


def generate_xs_value(
    path_hash: common.CanHash, value_type: aas_types.DataTypeDefXSD
) -> str:
    """Generate a semi-random value corresponding to the ``value_tyep``."""
    return primitiving.choose_value(
        path_hash,
        list(
            frozen_examples_xs_value.BY_VALUE_TYPE[value_type.value].positives.values()
        ),
    )


_AAS_SUBMODEL_ELEMENTS_TO_MINIMAL = {
    aas_types.AASSubmodelElements.ANNOTATED_RELATIONSHIP_ELEMENT: creation.minimal_annotated_relationship_element,
    aas_types.AASSubmodelElements.BASIC_EVENT_ELEMENT: creation.minimal_basic_event_element,
    aas_types.AASSubmodelElements.BLOB: creation.minimal_blob,
    aas_types.AASSubmodelElements.CAPABILITY: creation.minimal_capability,
    aas_types.AASSubmodelElements.DATA_ELEMENT: creation.minimal_data_element,
    aas_types.AASSubmodelElements.ENTITY: creation.minimal_entity,
    aas_types.AASSubmodelElements.EVENT_ELEMENT: creation.minimal_event_element,
    aas_types.AASSubmodelElements.FILE: creation.minimal_file,
    aas_types.AASSubmodelElements.MULTI_LANGUAGE_PROPERTY: creation.minimal_multi_language_property,
    aas_types.AASSubmodelElements.OPERATION: creation.minimal_operation,
    aas_types.AASSubmodelElements.PROPERTY: creation.minimal_property,
    aas_types.AASSubmodelElements.RANGE: creation.minimal_range,
    aas_types.AASSubmodelElements.REFERENCE_ELEMENT: creation.minimal_reference_element,
    aas_types.AASSubmodelElements.RELATIONSHIP_ELEMENT: creation.minimal_relationship_element,
    aas_types.AASSubmodelElements.SUBMODEL_ELEMENT: creation.minimal_submodel_element,
    aas_types.AASSubmodelElements.SUBMODEL_ELEMENT_LIST: creation.minimal_submodel_element_list,
    aas_types.AASSubmodelElements.SUBMODEL_ELEMENT_COLLECTION: creation.minimal_submodel_element_collection,
}
assert all(
    literal in _AAS_SUBMODEL_ELEMENTS_TO_MINIMAL
    for literal in aas_types.AASSubmodelElements
)


def generate_minimal_submodel_element(
    submodel_element_type: aas_types.AASSubmodelElements, path_hash: common.CanHash
) -> aas_types.SubmodelElement:
    """Generate a minimal instance of the given submodel element type."""
    minimal_function = _AAS_SUBMODEL_ELEMENTS_TO_MINIMAL[submodel_element_type]
    return minimal_function(path_hash)


class _Handyman(abstract_fixing.AbstractHandyman):
    """Fix the instances recursively on the best-effort basis."""

    def _fix_annotated_relationship_element(
        self, that: aas_types.AnnotatedRelationshipElement, path_hash: common.CanHash
    ) -> None:
        # Fix for AASd-117
        if that.annotations is not None:
            for i, annotation in enumerate(that.annotations):
                if annotation.id_short is None:
                    annotation.id_short = primitiving.generate_str(
                        common.hash_path(path_hash, ["annotations", i, "id_short"])
                    )

    def _fix_asset_administration_shell(
        self, that: aas_types.AssetAdministrationShell, path_hash: common.CanHash
    ) -> None:
        # Fix: Derived-from must be a model reference to an asset administration shell.
        if that.derived_from is not None:
            that.derived_from = generate_model_reference(
                common.hash_path(path_hash, "derived_from"),
                expected_type=aas_types.KeyTypes.ASSET_ADMINISTRATION_SHELL,
            )

        # Fix: All submodels must be model references to a submodel.
        if that.submodels is not None:
            that.submodels = [
                generate_model_reference(
                    common.hash_path(path_hash, ["submodels", 0]),
                    expected_type=aas_types.KeyTypes.SUBMODEL,
                )
            ]

    def _fix_asset_information(
        self, that: aas_types.AssetInformation, path_hash: common.CanHash
    ) -> None:
        # region Fix for AASd-131
        if that.global_asset_id is None and that.specific_asset_ids is None:
            that.global_asset_id = primitiving.generate_str(
                common.hash_path(path_hash, "global_asset_id")
            )

        if that.global_asset_id is not None and that.specific_asset_ids is not None:
            that.specific_asset_ids = None

        # endregion

    def _fix_basic_event_element(
        self, that: aas_types.BasicEventElement, path_hash: common.CanHash
    ) -> None:
        # Fix that the observed is a proper model reference
        if that.observed is not None:
            that.observed = generate_model_reference(
                common.hash_path(path_hash, "observed"),
                expected_type=aas_types.KeyTypes.REFERABLE,
            )

        # Override that the direction is output so that we can always set
        # the max interval
        if that.direction is not None:
            that.direction = aas_types.Direction.OUTPUT

        # Fix that the message broker is a proper model reference
        if that.message_broker is not None:
            that.message_broker = generate_model_reference(
                common.hash_path(path_hash, "message_broker"),
                expected_type=aas_types.KeyTypes.REFERABLE,
            )

    def _fix_concept_description(
        self, that: aas_types.ConceptDescription, path_hash: common.CanHash
    ) -> None:
        # Fix AASc-3a-008
        if that.embedded_data_specifications is not None:
            if not aas_verification.data_specification_iec_61360s_have_definition_at_least_in_english(
                that.embedded_data_specifications
            ) and not (
                aas_verification.data_specification_iec_61360s_have_value(
                    that.embedded_data_specifications
                )
            ):
                for i, ebd in enumerate(that.embedded_data_specifications):
                    if isinstance(ebd, aas_types.DataSpecificationIEC61360):
                        ebd.definition = (
                            [] if ebd.definition is None else ebd.definition
                        )

                        _extend_lang_string_set_to_have_an_entry_at_least_in_english(
                            path_hash=common.hash_path(
                                path_hash,
                                ["embedded_data_specifications", i, "definition"],
                            ),
                            lang_string_set=ebd.definition,
                            lang_string_class=aas_types.LangStringDefinitionTypeIEC61360,
                        )

    def _fix_data_specification_iec_61360(
        self, that: aas_types.DataSpecificationIEC61360, path_hash: common.CanHash
    ) -> None:
        # Constraint AASc-3a-010: If value and value_list, pick value
        if that.value is not None and that.value_list is not None:
            that.value_list = None

        # Constraint AASc-3a-010: If neither value nor value_list, set value
        if that.value is None and that.value_list is None:
            that.value = primitiving.generate_str(common.hash_path(path_hash, "value"))

        # Constraint AASc-3a-009: unit or unit ID must be set if data type requires it
        if (
            that.data_type is not None
            and that.data_type in aas_constants.IEC_61360_DATA_TYPES_WITH_UNIT
        ):
            that.unit = primitiving.generate_str(common.hash_path(path_hash, "unit"))

        # Constraint AASc-002: preferred name at least in English
        _extend_lang_string_set_to_have_an_entry_at_least_in_english(
            path_hash=common.hash_path(path_hash, "preferred_name"),
            lang_string_set=that.preferred_name,
            lang_string_class=aas_types.LangStringPreferredNameTypeIEC61360,
        )

    def _fix_entity(self, that: aas_types.Entity, path_hash: common.CanHash) -> None:
        # Fix for AASd-117
        if that.statements is not None:
            for i, statement in enumerate(that.statements):
                if statement.id_short is None:
                    statement.id_short = primitiving.generate_str(
                        common.hash_path(path_hash, ["statements", i, "id_short"])
                    )

        # Fix AASd-014: Either the attribute global asset ID or specific asset ID
        # must be set if entity type is set to 'SelfManagedEntity'. They are not
        # existing otherwise.
        if that.entity_type is aas_types.EntityType.SELF_MANAGED_ENTITY:
            if that.global_asset_id is not None and that.specific_asset_ids is not None:
                that.specific_asset_ids = None

            elif that.global_asset_id is None and that.specific_asset_ids is None:
                that.global_asset_id = generate_urn(
                    common.hash_path(path_hash, ["global_asset_id"])
                )
            else:
                pass

        else:
            that.global_asset_id = None
            that.specific_asset_ids = None

    def _fix_event_payload(
        self, that: aas_types.EventPayload, path_hash: common.CanHash
    ) -> None:
        if not aas_verification.is_model_reference_to(
            that.source, aas_types.KeyTypes.EVENT_ELEMENT
        ) and not aas_verification.is_model_reference_to(
            that.source, aas_types.KeyTypes.BASIC_EVENT_ELEMENT
        ):
            that.source = generate_model_reference(
                path_hash=common.hash_path(path_hash, "source"),
                expected_type=aas_types.KeyTypes.EVENT_ELEMENT,
            )

        if not aas_verification.is_model_reference_to_referable(
            that.observable_reference
        ):
            that.observable_reference = generate_model_reference(
                path_hash=common.hash_path(path_hash, "source"),
                expected_type=aas_types.KeyTypes.REFERABLE,
            )

    def _fix_extension(
        self, that: aas_types.Extension, path_hash: common.CanHash
    ) -> None:
        # Fix: The value must match the value type.
        if that.value is not None:
            value_type = that.value_type_or_default()
            if not aas_verification.value_consistent_with_xsd_type(
                that.value, value_type
            ):
                that.value = generate_xs_value(
                    common.hash_path(path_hash, "value"), value_type
                )

    def _fix_operation(
        self, that: aas_types.Operation, path_hash: common.CanHash
    ) -> None:
        # Fix for AASd-117
        if that.input_variables is not None:
            for i, input_variable in enumerate(that.input_variables):
                if input_variable.value.id_short is None:
                    input_variable.value.id_short = primitiving.generate_str(
                        common.hash_path(
                            path_hash, ["input_variables", i, "value", "id_short"]
                        )
                    )

        # Fix for AASd-117
        if that.output_variables is not None:
            for i, output_variable in enumerate(that.output_variables):
                if output_variable.value.id_short is None:
                    output_variable.value.id_short = primitiving.generate_str(
                        common.hash_path(
                            path_hash, ["output_variables", i, "value", "id_short"]
                        )
                    )

        # Fix for AASd-117
        if that.inoutput_variables is not None:
            for i, inoutput_variable in enumerate(that.inoutput_variables):
                if inoutput_variable.value.id_short is None:
                    inoutput_variable.value.id_short = primitiving.generate_str(
                        common.hash_path(
                            path_hash, ["inoutput_variables", i, "value", "id_short"]
                        )
                    )

    def _fix_property(
        self, that: aas_types.Property, path_hash: common.CanHash
    ) -> None:
        if (
            that.value is not None
            and not aas_verification.value_consistent_with_xsd_type(
                that.value, that.value_type
            )
        ):
            that.value = generate_xs_value(
                common.hash_path(path_hash, "value"), that.value_type
            )

    def _fix_qualifier(
        self, that: aas_types.Qualifier, path_hash: common.CanHash
    ) -> None:
        if (
            that.value is not None
            and not aas_verification.value_consistent_with_xsd_type(
                that.value, that.value_type
            )
        ):
            that.value = generate_xs_value(
                common.hash_path(path_hash, "value"), that.value_type
            )

    def _fix_range(self, that: aas_types.Range, path_hash: common.CanHash) -> None:
        if that.min is not None and that.max is not None:
            # We unset the min so that we never have a semantically invalid range.
            that.min = None

        assert (that.min is None) or (that.max is None)

        if that.min is not None:
            that.min = generate_xs_value(
                common.hash_path(path_hash, "min"), that.value_type
            )

        if that.max is not None:
            that.max = generate_xs_value(
                common.hash_path(path_hash, "max"), that.value_type
            )

    def _fix_reference(
        self, that: aas_types.Reference, path_hash: common.CanHash
    ) -> None:
        # NOTE (mristin, 2023-03-11):
        # We first check if this instance needs fixing at all. It could be
        # that the previous function higher up in the stack already fixed
        # the reference, so we do not want to undo the changes.
        #
        # We do not check before fixing in all the ``_fix_*`` methods as that is
        # computationally prohibitive.
        errors = list(aas_verification.verify(that))
        if len(errors) == 0:
            return

        # Simply overwrite the keys to satisfy the reference type
        if that.type is aas_types.ReferenceTypes.EXTERNAL_REFERENCE:
            that.keys = [
                aas_types.Key(
                    type=aas_types.KeyTypes.GLOBAL_REFERENCE,
                    value=generate_urn(
                        common.hash_path(path_hash, ["keys", 0, "value"])
                    ),
                )
            ]
        elif that.type is aas_types.ReferenceTypes.MODEL_REFERENCE:
            that.keys = [
                aas_types.Key(
                    type=aas_types.KeyTypes.SUBMODEL,
                    value=generate_urn(
                        common.hash_path(path_hash, ["keys", 0, "value"])
                    ),
                )
            ]
        else:
            assert_never(that.type)

    def _fix_submodel(
        self, that: aas_types.Submodel, path_hash: common.CanHash
    ) -> None:
        # ID shorts must be defined for all submodel elements
        if that.submodel_elements is not None:
            for i, submodel_element in enumerate(that.submodel_elements):
                if submodel_element.id_short is None:
                    submodel_element.id_short = generate_id_short(
                        common.hash_path(
                            path_hash, ["submodel_elements", i, "id_short"]
                        )
                    )

        # region Fix AASd-119 and AASd-129

        # Check for AASd-119
        must_be_template = False
        if that.qualifiers is not None:
            if any(
                qualifier.kind_or_default()
                is aas_types.QualifierKind.TEMPLATE_QUALIFIER
                for qualifier in that.qualifiers
            ):
                must_be_template = True

        # Check for AASd-129
        if that.submodel_elements is not None:
            for submodel_element in that.submodel_elements:
                if submodel_element.qualifiers is not None:
                    for qualifier in submodel_element.qualifiers:
                        if (
                            qualifier.kind_or_default()
                            is aas_types.QualifierKind.TEMPLATE_QUALIFIER
                        ):
                            must_be_template = True
                            break

                if must_be_template:
                    break

        if must_be_template:
            that.kind = aas_types.ModellingKind.TEMPLATE

        # endregion

    def _fix_submodel_element_collection(
        self, that: aas_types.SubmodelElementCollection, path_hash: common.CanHash
    ) -> None:
        # Fix: ID-shorts need to be defined for all the elements.
        if that.value is not None:
            for i, item in enumerate(that.value):
                if item.id_short is None:
                    item.id_short = generate_id_short(
                        common.hash_path(path_hash, ["value", i, "id_short"])
                    )

    def _fix_submodel_element_list(
        self, that: aas_types.SubmodelElementList, path_hash: common.CanHash
    ) -> None:
        if that.value is not None:
            # Fix AASd-107
            if that.semantic_id_list_element is not None:
                for item in that.value:
                    if item.semantic_id is not None:
                        item.semantic_id = that.semantic_id_list_element
            else:
                # Fix AASd-114
                semantic_id = None  # type: Optional[aas_types.Reference]
                for item in that.value:
                    if item.semantic_id is not None:
                        semantic_id = item.semantic_id
                        break

                if semantic_id is not None:
                    for item in that.value:
                        if item.semantic_id is not None:
                            item.semantic_id = semantic_id

            # Fix AASd-108
            if that.type_value_list_element is not None:
                new_value = []  # type: List[aas_types.SubmodelElement]
                for i, item in enumerate(that.value):
                    if aas_verification.submodel_element_is_of_type(
                        item, that.type_value_list_element
                    ):
                        new_value.append(item)
                        continue

                    item = generate_minimal_submodel_element(
                        submodel_element_type=that.type_value_list_element,
                        path_hash=common.hash_path(path_hash, ["value", i]),
                    )

                    new_value.append(item)

                that.value = new_value

            # Fix AASd-109
            if that.type_value_list_element in (
                aas_types.AASSubmodelElements.PROPERTY,
                aas_types.AASSubmodelElements.RANGE,
            ):
                if that.value_type_list_element is None:
                    that.value_type_list_element = aas_types.DataTypeDefXSD.INT

                for item in that.value:
                    assert isinstance(item, (aas_types.Property, aas_types.Range)), (
                        f"We should have fixed the item "
                        f"to {that.type_value_list_element=} "
                        f"before, but got here: {item=}"
                    )

                    item.value_type = that.value_type_list_element


def _assert_fix_methods_sorted_in_handyman() -> None:
    """Assert that we alphabetically sorted methods in :py:class:`_Handyman`."""
    handyman_cls = _Handyman
    source_code = inspect.getsource(handyman_cls)
    root = ast.parse(source_code)
    assert isinstance(root, ast.Module)
    assert len(root.body) == 1

    handyman_cls_ast = root.body[0]
    assert isinstance(handyman_cls_ast, ast.ClassDef)

    method_names = [
        node.name
        for node in handyman_cls_ast.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_fix_")
    ]

    assert method_names == sorted(method_names), (
        f"The ``_fix_*`` methods in {_Handyman.__name__} must be sorted "
        f"for readability."
    )


_assert_fix_methods_sorted_in_handyman()


def assert_instance_at_path_in_environment(
    environment: aas_types.Environment,
    instance: aas_types.Class,
    path: Sequence[Union[str, int]],
) -> None:
    """Assert that the ``instance`` still resides in ``environment`` at ``path``."""
    something, error = common.dereference_instance(container=environment, path=path)

    if error is not None:
        path_str = common.instance_path_as_posix(path)
        raise AssertionError(
            f"Expected to find an instance "
            f"in the environment {environment} at path {path_str}, "
            f"but there was no instance: {error}"
        )
    assert something is not None

    if instance is not something:
        path_str = common.instance_path_as_posix(path)
        raise AssertionError(
            f"Expected to find instance {instance} at path {path_str}, "
            f"but got: {something}"
        )


_HANDYMAN = _Handyman()


def fix(root: aas_types.Class) -> None:
    """
    Fix recursively the ``root`` instance.

    Usually, the ``root`` is either an Environment, or a self-contained instance.
    """
    path_hash = common.hash_path(prefix_hash=None, segment_or_segments=[])
    _HANDYMAN.visit_with_context(root, path_hash)

    errors = list(aas_verification.verify(root))
    if len(errors) > 0:
        errors_joined = "\n".join(f"* {error.path}: {error.cause}" for error in errors)

        preserialized_root, _ = preserialization.preserialize(root)

        preserialized_dump = preserialization.dump(preserialized_root)

        raise AssertionError(
            f"Expected no errors after fixing the instance {root}, "
            f"but got errors:\n"
            f"{errors_joined}\n\n"
            f"The dump of the preserialized instance:\n"
            f"{preserialized_dump}"
        )
