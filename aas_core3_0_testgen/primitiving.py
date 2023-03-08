"""Generate primitive values based on the path."""
import hashlib
from typing import Optional, TypeVar, Sequence, List

from icontract import ensure

from aas_core3_0_testgen import common
from aas_core3_0_testgen.frozen_examples import (
    pattern as frozen_examples_pattern
)


def generate_bool(path_hash: common.CanHash) -> bool:
    """Return the hexadecimal digest transformed to a boolean."""
    number = int(path_hash.hexdigest()[:8], base=16)
    return number % 2 == 0


def generate_int(path_hash: common.CanHash) -> int:
    """Return the hexadecimal digest parsed as integer."""
    return int(path_hash.hexdigest()[:8], base=16)


def generate_int64(path_hash: common.CanHash) -> int:
    """Return the hexadecimal digest parsed as integer."""
    return int(path_hash.hexdigest()[:8], base=16) % (2 ** 63 - 1)


def generate_float(path_hash: common.CanHash) -> float:
    """Return the hexadecimal digest transformed to a float."""
    number = int(path_hash.hexdigest()[:8], base=16)
    return float(number) / 100


# fmt: off
@ensure(
    lambda count, result:
    not (count is not None)
    or (len(result) == count)
)
# fmt: on
def generate_str(
        path_hash: common.CanHash,
        count: Optional[int] = None
) -> str:
    """Transform the digest to a semi-meaningful string value."""
    hexdigest = path_hash.hexdigest()

    if count is None:
        return f"something_{hexdigest[:8]}"

    if len(hexdigest) > count:
        return hexdigest[:count]

    ruler = "1234567890"

    tens = count // 10
    remainder = count % 10
    return "".join(
        [hexdigest, ruler[len(hexdigest) : 10], ruler * (tens - 1), ruler[:remainder]]
    )

# fmt: off
@ensure(
    lambda count, result:
    not (count is not None)
    or (len(result) == count)
)
# fmt: on
def generate_str_satisfying_pattern(
        path_hash: common.CanHash,
        pattern: str
) -> str:
    """Transform the digest to one of the pattern examples."""
    examples = frozen_examples_pattern.BY_PATTERN.get(pattern, None)
    if examples is None:
        raise AssertionError(
            f"Unexpected pattern not covered in the frozen examples: {pattern!r}"
        )

    return choose_value(path_hash, list(examples.positives.values()))


# fmt: off
@ensure(
    lambda count, result:
    not (count is not None)
    or (len(result) == count)
)
# fmt: on
def generate_bytes(
        path_hash: common.CanHash,
        count: Optional[int] = None
) -> bytes:
    """Transform the digest to a meaningless byte array."""
    digest = path_hash.digest()

    if count is None:
        # NOTE (mristin, 2023-03-08):
        # We return here an arbitrary number of bytes to make it explicit
        # in the generated examples that there is no limit on 8 bytes or something
        # similar.
        return digest[:12]

    if count < len(digest):
        return digest[:count]

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

    return b"".join(parts)


T = TypeVar("T")


def choose_value(
        path_hash: common.CanHash,
        choice: Sequence[T]
) -> T:
    """Choose the value among ``choice`` based on the ``path_hash``."""
    number = int(path_hash.hexdigest()[:8], base=16)

    return choice[number % len(choice)]
