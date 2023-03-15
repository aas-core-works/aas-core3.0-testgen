"""Generate examples for all the pattern verification functions."""
import pathlib
import re
import warnings
from typing import Set

import hypothesis
import hypothesis.errors
import hypothesis.strategies
from aas_core_codegen import intermediate
import aas_core_codegen.run
import aas_core_meta.v3

warnings.filterwarnings(
    "ignore", category=hypothesis.errors.NonInteractiveExampleWarning
)


def main() -> None:
    """Execute the main routine."""
    (
        symbol_table_atok,
        error,
    ) = aas_core_codegen.run.load_model(pathlib.Path(aas_core_meta.v3.__file__))
    if error is not None:
        raise RuntimeError(error)
    assert symbol_table_atok is not None
    symbol_table = symbol_table_atok[0]

    for verification_function in symbol_table.verification_functions:
        if not isinstance(verification_function, intermediate.PatternVerification):
            continue

        strategy = hypothesis.strategies.from_regex(
            verification_function.pattern, fullmatch=True
        )

        print(
            f"For verification function {verification_function.name} "
            f"with pattern {verification_function.pattern}:"
        )
        print("  positives = [")
        for i in range(10):
            text = strategy.example()
            print(f"    ('fuzzed_{(i + 1):02d}', {text!r}),")
        print("  ]")
        print()

        print("  negatives = [")

        strategy = hypothesis.strategies.text()
        pattern_re = re.compile(verification_function.pattern)
        observed = set()  # type: Set[str]

        count = 0
        for _ in range(1000):
            text = strategy.example()
            if text in observed:
                continue

            if pattern_re.match(text) is None:
                print(f"    ('negatively_fuzzed_{(count + 1):02d}', {text!r}),")
                count += 1
                observed.add(text)

            if count == 10:
                break

        print("  ]")
        print()


if __name__ == "__main__":
    main()
