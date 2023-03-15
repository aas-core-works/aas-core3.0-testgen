"""Generate primitive values based on the path."""
import hashlib
from typing import Optional, TypeVar, Sequence, List

from icontract import ensure

from aas_core3_0_testgen import common
from aas_core3_0_testgen.frozen_examples import pattern as frozen_examples_pattern


def generate_bool(path_hash: common.CanHash) -> bool:
    """Return the hexadecimal digest transformed to a boolean."""
    number = int(path_hash.hexdigest()[:8], base=16)
    return number % 2 == 0


def generate_int(path_hash: common.CanHash) -> int:
    """Return the hexadecimal digest parsed as integer."""
    return int(path_hash.hexdigest()[:8], base=16)


def generate_int64(path_hash: common.CanHash) -> int:
    """Return the hexadecimal digest parsed as integer."""
    return int(path_hash.hexdigest()[:8], base=16) % (2**63 - 1)


def generate_float(path_hash: common.CanHash) -> float:
    """Return the hexadecimal digest transformed to a float."""
    number = int(path_hash.hexdigest()[:8], base=16)
    return float(number) / 100


_RULER_STR = "1234567890"


@ensure(lambda length, result: len(result) == length)
def generate_str_padding(length: int) -> str:
    """Generate a dummy string padding."""
    tens = length // 10
    remainder = length % 10
    return "".join([_RULER_STR * tens, _RULER_STR[:remainder]])


_RULER_BYTES = b"1234567890"


@ensure(lambda length, result: len(result) == length)
def generate_bytes_padding(length: int) -> bytes:
    """Generate a dummy string padding."""
    tens = length // 10
    remainder = length % 10
    return b"".join([_RULER_BYTES * tens, _RULER_BYTES[:remainder]])


# fmt: off
@ensure(
    lambda length, result:
    len(result) == length
)
# fmt: on
def generate_str_of_exact_len(hexdigest: str, length: int) -> str:
    """Generate a semi-random string of the exact given ``length``."""
    if length < 12:
        # NOTE (mristin, 2023-03-08):
        # Short strings look just as hexadecimal.
        return hexdigest[:length]

    if length <= 10 + len(hexdigest):
        len_hexdigest_part = length - 10
        return f"something_{hexdigest[:len_hexdigest_part]}"

    prefix = f"something_{hexdigest}"
    return prefix + generate_str_padding(length - len(prefix))


# fmt: off
@ensure(
    lambda min_len, result:
    not (min_len is not None)
    or (min_len <= len(result))
)
@ensure(
    lambda max_len, result:
    not (max_len is not None)
    or (len(result) <= max_len)
)
# fmt: on
def generate_str(
    path_hash: common.CanHash,
    min_len: Optional[int] = None,
    max_len: Optional[int] = None,
) -> str:
    """Transform the digest to a semi-meaningful string value."""
    hexdigest = path_hash.hexdigest()

    default = f"something_{hexdigest[:8]}"

    if min_len is None and max_len is None:
        return default

    elif min_len is not None and max_len is None:
        if min_len <= len(default):
            return default

        return generate_str_of_exact_len(hexdigest, min_len)

    elif min_len is None and max_len is not None:
        if len(default) < max_len:
            return default

        return generate_str_of_exact_len(hexdigest, max_len)

    elif min_len is not None and max_len is not None:
        if min_len <= len(default) <= max_len:
            return default

        return generate_str_of_exact_len(hexdigest, min_len)

    else:
        raise AssertionError(f"Unexpected case: {min_len=}, {max_len=}")


def generate_str_satisfying_pattern(path_hash: common.CanHash, pattern: str) -> str:
    """Transform the digest to one of the pattern examples."""
    examples = frozen_examples_pattern.BY_PATTERN.get(pattern, None)
    if examples is None:
        raise AssertionError(
            f"Unexpected pattern not covered in the frozen examples: {pattern!r}"
        )

    return choose_value(path_hash, list(examples.positives.values()))


# fmt: off
@ensure(
    lambda min_len, result:
    not (min_len is not None)
    or (min_len <= len(result))
)
@ensure(
    lambda max_len, result:
    not (max_len is not None)
    or (len(result) <= max_len)
)
# fmt: on
def generate_bytes(
    path_hash: common.CanHash,
    min_len: Optional[int] = None,
    max_len: Optional[int] = None,
) -> bytes:
    """Transform the digest to a meaningless byte array."""
    digest = path_hash.digest()

    # NOTE (mristin, 2023-03-08):
    # We return here an arbitrary number of bytes to make it explicit
    # in the generated examples that there is no limit on 8 bytes or something
    # similar.
    default_len = 11

    count = None  # type: Optional[int]

    if min_len is None and max_len is None:
        count = default_len
    elif min_len is not None and max_len is None:
        count = min_len
    elif min_len is None and max_len is not None:
        count = min(max_len, default_len)
    elif min_len is not None and max_len is not None:
        count = min_len
    else:
        raise AssertionError("Unhandled case")

    assert count is not None

    if count <= len(digest):
        result = digest[:count]
    else:
        parts = []  # type: List[bytes]
        length = 0

        current_digest = digest

        while length < count:
            remaining = length - count
            if len(current_digest) < remaining:
                parts.append(current_digest)
                length += len(current_digest)

                # NOTE (mristin, 2023-03-08):
                # Re-hash for a "random" effect. This works OK for examples.
                hasher = hashlib.md5()
                hasher.update(current_digest)
                current_digest = hasher.digest()

            else:
                parts.append(current_digest[:remaining])
                length += remaining

        result = b"".join(parts)

    assert len(result) == count
    return result


T = TypeVar("T")


def choose_value(path_hash: common.CanHash, choice: Sequence[T]) -> T:
    """Choose the value among ``choice`` based on the ``path_hash``."""
    number = int(path_hash.hexdigest()[:8], base=16)

    return choice[number % len(choice)]


def generate_time_of_day(path_hash: common.CanHash) -> str:
    """Generate a semi-random time of the day based on the ``path_hash``."""
    number = int(path_hash.hexdigest()[:8], base=16)

    remainder = number
    hours = (remainder // 3600) % 24
    remainder = remainder % 3600
    minutes = (remainder // 60) % 60
    seconds = remainder % 60

    fraction = number % 1000000

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{fraction}"
