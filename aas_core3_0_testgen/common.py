"""Provide common methods for generation of data in different formats."""
import collections.abc
import hashlib
import io
import pathlib
from typing import (
    MutableMapping,
    Tuple,
    Union,
    Protocol,
    TypeVar,
    Optional,
    Sequence,
    Any,
)

import aas_core_codegen.common
import aas_core_codegen.parse
import aas_core_codegen.run
from aas_core_codegen import intermediate, infer_for_schema
from icontract import ensure
from typing_extensions import assert_never

import aas_core3.types as aas_types


def load_symbol_table_and_infer_constraints_for_schema(
    model_path: pathlib.Path,
) -> Tuple[
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


CanHashT = TypeVar("CanHashT", bound="CanHash")


class CanHash(Protocol):
    """Represent an incremental hash."""

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
    lambda prefix_hash, segment_or_segments, result: not (
        isinstance(segment_or_segments, collections.abc.Sized)
        and len(segment_or_segments) > 0
    )
    or (prefix_hash is not result),
    "Hash is always copied unless there were no segments to hash",
)
@ensure(
    lambda prefix_hash, segment_or_segments, result: not isinstance(
        segment_or_segments, (int, str)
    )
    or (prefix_hash is not result),
    "Hash is always copied when there is a segment given",
)
def hash_path(
    prefix_hash: Optional[CanHash],
    segment_or_segments: Union[int, str, Sequence[Union[int, str]]],
) -> CanHash:
    """
    Hash a path extended with a segment and pre-hashed prefix.

    Hashing a single segment in a list is equal to hashing that segment directly:

    >>> prefix = hash_path(None, 'something')
    >>> (
    ...     hash_path(prefix, ['something-more']).hexdigest()
    ...         == hash_path(prefix, 'something-more').hexdigest()
    ... )
    True
    """
    if isinstance(segment_or_segments, (int, str)):
        segment_bytes = f"/{repr(segment_or_segments)}".encode("utf-8")
        hsh = prefix_hash.copy() if prefix_hash is not None else hashlib.md5()
        hsh.update(segment_bytes)
        return hsh

    elif isinstance(segment_or_segments, collections.abc.Iterable) and isinstance(
        segment_or_segments, collections.abc.Sized
    ):
        if len(segment_or_segments) == 0:
            return prefix_hash if prefix_hash is not None else hashlib.md5()

        hsh = prefix_hash.copy() if prefix_hash is not None else hashlib.md5()
        # noinspection PyTypeChecker
        for segment in segment_or_segments:
            segment_bytes = f"/{repr(segment)}".encode("utf-8")
            hsh.update(segment_bytes)

        return hsh

    else:
        assert_never(segment_or_segments)
        raise AssertionError("Unexpected execution path")


def instance_path_as_posix(path: Sequence[Union[str, int]]) -> str:
    """Create a string representation as a POSIX-like path."""
    return "/" + "/".join(str(segment) for segment in path)


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def dereference_instance(
    container: aas_types.Class, path: Sequence[Union[str, int]]
) -> Tuple[Optional[aas_types.Class], Optional[str]]:
    """
    Follow the path, and assert that the target is of ``expected_type``.

    The segments of ``path`` should be either indices in the lists or property names
    of the meta-model instances.

    The property names are expected as Python names, and *not* as aas-meta-model names
    (``semantic_ids`` instead of ``semantic_IDs``).
    """
    something = container  # type: Any
    for i, segment in enumerate(path):
        if isinstance(segment, int):
            if not isinstance(something, collections.abc.Sequence):
                subpath_str = instance_path_as_posix(path[:i])
                path_str = instance_path_as_posix(path)
                return None, (
                    f"Expected a sequence at {subpath_str}, "
                    f"but got: {something} on path {path_str}"
                )

            if len(something) <= segment:
                subpath_str = instance_path_as_posix(path[:i])
                path_str = instance_path_as_posix(path)

                return None, (
                    f"The sequence at {subpath_str} has "
                    f"only {len(something)} element(s), "
                    f"but we want to access index {segment} on path {path_str}"
                )

            something = something[segment]

        elif isinstance(segment, str):
            if not isinstance(something, aas_types.Class):
                subpath_str = instance_path_as_posix(path[:i])
                path_str = instance_path_as_posix(path)
                return None, (
                    f"Expected an instance at {subpath_str}, "
                    f"but got: {something} on path {path_str}"
                )

            if not hasattr(something, segment):
                subpath_str = instance_path_as_posix(path[:i])
                path_str = instance_path_as_posix(path)
                return None, (
                    f"The instance at {subpath_str} does not have "
                    f"the attribute {segment!r} on path {path_str}"
                )

            something = getattr(something, segment)

        else:
            aas_core_codegen.common.assert_never(segment)

    if not isinstance(something, aas_types.Class):
        path_str = instance_path_as_posix(path)
        return None, (
            f"Expected an instance "
            f"of {aas_types.__name__}.{aas_types.Class.__name__}, "
            f"but got: {something} on path {path_str}"
        )

    return something, None


def must_dereference_instance(
    container: aas_types.Class, path: Sequence[Union[str, int]]
) -> aas_types.Class:
    """
    Follow the path, and assert that the target is of ``expected_type``.

    The segments of ``path`` should be either indices in the lists or property names
    of the meta-model instances.

    The property names are expected as Python names, and *not* as aas-meta-model names
    (``semantic_ids`` instead of ``semantic_IDs``).
    """
    something, error = dereference_instance(container, path)
    if error is not None:
        raise ValueError(error)

    assert something is not None
    return something
