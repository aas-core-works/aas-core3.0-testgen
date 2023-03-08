"""Provide common methods for generation of data in different formats."""
import collections.abc
import hashlib
import io
import pathlib
from typing import MutableMapping, Tuple, Union, Iterable, Protocol, TypeVar

import aas_core_codegen.common
import aas_core_codegen.parse
import aas_core_codegen.run
import aas_core_meta.v3
import icontract
from aas_core_codegen import intermediate, infer_for_schema
from icontract import ensure


def load_symbol_table_and_infer_constraints_for_schema() -> Tuple[
    intermediate.SymbolTable,
    MutableMapping[intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty],
]:
    """
    Load the symbol table from the meta-model and infer the schema constraints.

    These constraints might not be sufficient to generate *some* of the instances.
    Further constraints in form of invariants might apply which are not represented
    in the schema constraints. However, this will help us cover *many* classes of the
    meta-model and spare us the work of manually writing many generators.
    """
    model_path = pathlib.Path(aas_core_meta.v3.__file__)
    assert model_path.exists() and model_path.is_file(), model_path

    text = model_path.read_text(encoding="utf-8")

    atok, parse_exception = aas_core_codegen.parse.source_to_atok(source=text)
    if parse_exception:
        if isinstance(parse_exception, SyntaxError):
            raise RuntimeError(
                f"Failed to parse the meta-model {model_path}: "
                f"invalid syntax at line {parse_exception.lineno}\n"
            )
        else:
            raise RuntimeError(
                f"Failed to parse the meta-model {model_path}: " f"{parse_exception}\n"
            )

    assert atok is not None

    import_errors = aas_core_codegen.parse.check_expected_imports(atok=atok)
    if import_errors:
        writer = io.StringIO()
        aas_core_codegen.run.write_error_report(
            message="One or more unexpected imports in the meta-model",
            errors=import_errors,
            stderr=writer,
        )

        raise RuntimeError(writer.getvalue())

    lineno_columner = aas_core_codegen.common.LinenoColumner(atok=atok)

    parsed_symbol_table, error = aas_core_codegen.parse.atok_to_symbol_table(atok=atok)
    if error is not None:
        writer = io.StringIO()
        aas_core_codegen.run.write_error_report(
            message=f"Failed to construct the symbol table from {model_path}",
            errors=[lineno_columner.error_message(error)],
            stderr=writer,
        )

        raise RuntimeError(writer.getvalue())

    assert parsed_symbol_table is not None

    ir_symbol_table, error = intermediate.translate(
        parsed_symbol_table=parsed_symbol_table,
        atok=atok,
    )
    if error is not None:
        writer = io.StringIO()
        aas_core_codegen.run.write_error_report(
            message=f"Failed to translate the parsed symbol table "
                    f"to intermediate symbol table "
                    f"based on {model_path}",
            errors=[lineno_columner.error_message(error)],
            stderr=writer,
        )

        raise RuntimeError(writer.getvalue())

    assert ir_symbol_table is not None

    (
        constraints_by_class,
        inference_errors,
    ) = aas_core_codegen.infer_for_schema.infer_constraints_by_class(
        symbol_table=ir_symbol_table
    )

    if inference_errors is not None:
        writer = io.StringIO()
        aas_core_codegen.run.write_error_report(
            message=f"Failed to infer the constraints for the schema "
                    f"based on {model_path}",
            errors=[lineno_columner.error_message(error) for error in inference_errors],
            stderr=writer,
        )

        raise RuntimeError(writer.getvalue())

    assert constraints_by_class is not None
    (
        constraints_by_class,
        merge_error,
    ) = aas_core_codegen.infer_for_schema.merge_constraints_with_ancestors(
        symbol_table=ir_symbol_table, constraints_by_class=constraints_by_class
    )

    if merge_error is not None:
        writer = io.StringIO()
        aas_core_codegen.run.write_error_report(
            message=f"Failed to infer the constraints for the schema "
                    f"based on {model_path}",
            errors=[lineno_columner.error_message(merge_error)],
            stderr=writer,
        )

        raise RuntimeError(writer.getvalue())

    assert constraints_by_class is not None

    return ir_symbol_table, constraints_by_class


CanHashT = TypeVar('CanHashT', bound='CanHash')


class CanHash(Protocol):
    def update(self, data: bytes) -> None:
        """Update the hasher with the given data."""
        raise NotImplementedError()

    def digest(self) -> bytes:
        """Return the hash digest as bytes."""
        raise NotImplementedError()

    def hexdigest(self) -> str:
        """Return the hexadecimal hash digest in hex."""
        raise NotImplementedError()

    def copy(self: CanHashT) -> CanHashT:
        """Copy the hasher state."""
        raise NotImplementedError()


@ensure(
    lambda prefix_hash, segment_or_segments, result:
    not (
            isinstance(segment_or_segments, collections.abc.Sized)
            and len(segment_or_segments) > 0)
    or (
            prefix_hash is not result
    ),
    "Hash is always copied unless there were no segments to hash"
)
@ensure(
    lambda prefix_hash, segment_or_segments, result:
    not isinstance(segment_or_segments, (int, str))
    or (prefix_hash is not result),
    "Hash is always copied when there is a segment given"
)
@ensure(
    lambda prefix_hash, segment_or_segments, result:
    not isinstance(segment_or_segments, (int, str))
    or result.hexdigest() == hash_path(prefix_hash, [segment_or_segments]),
    "Hashing a single segment in a list is equal to hashing that segment directly",
    enabled=icontract.SLOW
)
def hash_path(
        prefix_hash: CanHash,
        segment_or_segments: Union[int, str, Iterable[Union[int, str]]]
) -> CanHash:
    """Hash a path extended with a segment and pre-hashed prefix."""
    if isinstance(segment_or_segments, (int, str)):
        segment_bytes = f"/{repr(segment_or_segments)}".encode('utf-8')
        hsh = prefix_hash.copy()
        hsh.update(segment_bytes)
        return hsh

    elif (
            isinstance(segment_or_segments, collections.abc.Iterable)
            and isinstance(segment_or_segments, collections.abc.Sized)
    ):
        if len(segment_or_segments) == 0:
            return prefix_hash

        hsh = prefix_hash.copy()
        # noinspection PyTypeChecker
        for segment in segment_or_segments:
            segment_bytes = f"/{repr(segment)}".encode('utf-8')
            hsh.update(segment_bytes)

        return hsh
