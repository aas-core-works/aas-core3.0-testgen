"""
Fix instances in place to conform to the meta-model constraints.

.. note::

    We fix instances on the best-effort basis. It might be that something goes wrong.
    Please always verify the results.
"""
from typing import TypeVar, List, Type, Generic, Protocol

import typing_extensions

import aas_core3.types as aas_types
import aas_core3.constants as aas_constants

from aas_core3_0_testgen import common, primitiving
from aas_core3_0_testgen.codegened import abstract_fixing

LangStringT = TypeVar("LangStringT", bound=aas_types.AbstractLangString)


def _extend_lang_string_set_to_have_an_entry_at_least_in_english(
        path_hash: common.CanHash,
        lang_string_set: List[LangStringT],
        lang_string_class: Type[LangStringT]
) -> None:
    """Extend ``lang_string_set`` to contain at least one entry in English."""
    has_english = False
    for lang_string in lang_string_set:
        language_lower = lang_string.language.lower()
        if language_lower == "en" or language_lower.startswith("en-"):
            has_english = True
            break

    if not has_english:
        text_path_hash = common.hash_path(
            path_hash,
            [len(lang_string_set), "text"]
        )

        lang_string_set.append(
            lang_string_class(
                language="en-UK",
                text=f"Something random in English {text_path_hash.hexdigest()[:8]}"
            )
        )


def generate_url(
        path_hash: common.CanHash
) -> str:
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
            "yet-another-company.com"
        ]
    )

    return f"https://{domain}/{path_hash.hexdigest()[:8]}"


def generate_urn(
        path_hash: common.CanHash
) -> str:
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
            "urn:yet-another-company"
        ]
    )
    number = int(path_hash.hexdigest()[:8], base=16)
    random_id = f"{number % 20:02d}"

    return f"{prefix}{random_id}:{path_hash.hexdigest()[:8]}"


def generate_id_short(
        path_hash: common.CanHash
) -> str:
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
                value=generate_urn(common.hash_path(path_hash, ["keys", 0, "value"]))
            )
        ]
    elif expected_type in aas_constants.AAS_SUBMODEL_ELEMENTS_AS_KEYS:
        keys = [
            aas_types.Key(
                type=aas_types.KeyTypes.SUBMODEL,
                value=generate_urn(common.hash_path(path_hash, ["keys", 0, "value"]))
            ),
            aas_types.Key(
                type=expected_type,
                value=generate_id_short(
                    common.hash_path(path_hash, ["keys", 1, "value"])
                )
            )
        ]
    else:
        raise NotImplementedError(
            f"Unhandled {expected_type=}; when we developed this module there were "
            f"no other key types expected in the meta-model as a reference, "
            f"but this has obviously changed. Please contact the developers."
        )

    return aas_types.Reference(
        type=aas_types.ReferenceTypes.MODEL_REFERENCE,
        keys=keys
    )


def generate_external_reference(path_hash: common.CanHash) -> aas_types.Reference:
    """Generate a semi-random external reference."""
    keys = [
        aas_types.Key(
            type=aas_types.KeyTypes.GLOBAL_REFERENCE,
            value=generate_urn(common.hash_path(path_hash, ["keys", 0, "value"]))
        )
    ]

    return aas_types.Reference(
        type=aas_types.ReferenceTypes.EXTERNAL_REFERENCE,
        keys=keys
    )


class _Handyman(abstract_fixing):
    """Fix the instances recursively on the best-effort basis."""

    @typing_extensions.override
    def _fix_basic_event_element(
            self,
            that: aas_types.BasicEventElement,
            path_hash: common.CanHash
    ) -> None:
        # Fix that the observed is a proper model reference
        if that.observed is not None:
            that.observed = generate_model_reference(
                common.hash_path(path_hash, "observed"),
                expected_type=aas_types.KeyTypes.REFERABLE
            )

        # Override that the direction is output so that we can always set
        # the max interval
        if that.direction is not None:
            that.direction = aas_types.Direction.OUTPUT

        # Fix that the message broker is a proper model reference
        if that.message_broker is not None:
            that.message_broker = generate_model_reference(
                common.hash_path(path_hash, "message_broker"),
                expected_type=aas_types.KeyTypes.REFERABLE
            )

    @typing_extensions.override
    def _fix_asset_information(
            self,
            that: aas_types.AssetInformation,
            path_hash: common.CanHash
    ) -> None:
        # Fix for AASd-131: Either the global asset ID shall be defined or at least one
        # specific asset ID.
        if (
                that.global_asset_id is None
                and that.specific_asset_ids is None
        ):
            that.global_asset_id = primitiving.generate_str(
                common.hash_path(path_hash, "global_asset_id")
            )




# TODO (mristin, 2023-03-9): implement Handyman 🠒 use PassThrough visitor
# TODO (mristin, 2023-03-9): implement dereference function in common
# TODO (mristin, 2023-03-9): implement function to assert that the instance still exists in the wrapped environment after fixing
# TODO (mristin, 2023-03-9):  assert_instance_at_path_in_environment(environment, instance, path)

# TODO (mristin, 2023-03-9): fix(instance: Class)

# TODO (mristin, 2023-03-9): fix_wrapping(environment, instance, path)
# TODO (mristin, 2023-03-9):  🠒 call assert_instance_at_path_in_environment
