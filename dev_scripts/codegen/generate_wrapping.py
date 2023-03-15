"""Generate the code to wrap instances in an environment."""

import argparse
import os
import pathlib
import sys
from typing import List, Optional, Sequence, Tuple, MutableMapping

from aas_core_codegen import intermediate
from aas_core_codegen.common import (
    Stripped,
    indent_but_first_line,
    Identifier,
    assert_never,
)
from aas_core_codegen.python import common as python_common, naming as python_naming
from aas_core_codegen.python.common import INDENT as I, INDENT2 as II, INDENT3 as III
from icontract import ensure, require

import aas_core3_0_testgen.common
import dev_scripts.codegen.common
import dev_scripts.codegen.ontology

_REPO_DIR = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent


def _determine_concrete_minimal_function(cls: intermediate.ConcreteClass) -> str:
    """
    Determine the concrete minimal function for the given ``cls``.

    This function is necessary as concrete classes without descendants are created with
    ``minimal_*`` functions, while concrete classes with descendants are semi-randomly
    dispatched to either itself (``concrete_minimal_``) or one of the concrete
    descendants.
    """
    if len(cls.concrete_descendants) > 0:
        function_name = python_naming.function_name(
            Identifier(f"concrete_minimal_{cls.name}")
        )
    else:
        function_name = python_naming.function_name(Identifier(f"minimal_{cls.name}"))

    return f"creation.{function_name}"


def _determine_concrete_maximal_function(cls: intermediate.ConcreteClass) -> str:
    """
    Determine the concrete maximal function for the given ``cls``.

    This function is necessary as concrete classes without descendants are created with
    ``maximal_*`` functions, while concrete classes with descendants are semi-randomly
    dispatched to either itself (``concrete_maximal_``) or one of the concrete
    descendants.
    """
    if len(cls.concrete_descendants) > 0:
        function_name = python_naming.function_name(
            Identifier(f"concrete_maximal_{cls.name}")
        )
    else:
        function_name = python_naming.function_name(Identifier(f"maximal_{cls.name}"))

    return f"creation.{function_name}"


@require(lambda shortest_path_from_environment: len(shortest_path_from_environment) > 0)
def _generate_create_cls_in_environment(
    cls: intermediate.ConcreteClass,
    shortest_path_from_environment: Sequence[dev_scripts.codegen.ontology.Segment],
) -> Stripped:
    """Generate the function to create instances wrapped in an environment."""
    blocks = [
        Stripped("path_hash = common.hash_path(None, [])"),
        Stripped("path = []  # type: List[Union[int, str]]"),
    ]  # type: List[Stripped]

    variable_registry = dict()  # type: MutableMapping[Identifier, int]

    def next_variable(a_cls_name: Identifier) -> Identifier:
        """Generate the variable in the body corresponding to the given class name."""
        count = variable_registry.get(a_cls_name, None)
        if count is None:
            count = 0
        else:
            count += 1

        if count == 0:
            prefix = "the_"
        else:
            prefix = "yet_" * (count - 1) + "another_"

        variable_registry[a_cls_name] = count

        return python_naming.variable_name(Identifier(f"{prefix}{a_cls_name}"))

    first_source_variable = None  # type: Optional[Identifier]
    source_variable = None  # type: Optional[Identifier]
    target_variable = None  # type: Optional[Identifier]

    for i, segment in enumerate(shortest_path_from_environment):
        if first_source_variable is None:
            source_variable = next_variable(segment.source.name)

            minimal_source = _determine_concrete_minimal_function(segment.source)

            blocks.append(
                Stripped(
                    f"""\
{source_variable} = {minimal_source}(
{I}path_hash
)"""
                )
            )

            first_source_variable = source_variable

        assert source_variable is not None

        target_variable = next_variable(segment.target.name)

        if i == len(shortest_path_from_environment) - 1:
            target_creation = "creation_function"
        else:
            target_creation = _determine_concrete_minimal_function(segment.target)

        if isinstance(
            segment.relationship, dev_scripts.codegen.ontology.PropertyRelationship
        ):
            prop_name = python_naming.property_name(segment.relationship.property_name)
            prop_name_literal = python_common.string_literal(prop_name)
            blocks.append(
                Stripped(
                    f"""\
path.append(
{I}{prop_name_literal}
)
path_hash = common.hash_path(
{I}path_hash,
{I}{prop_name_literal}
)
{target_variable} = {target_creation}(
{I}path_hash
)
{source_variable}.{prop_name} = {target_variable}"""
                )
            )

            source_variable = target_variable

        elif isinstance(
            segment.relationship, dev_scripts.codegen.ontology.ListPropertyRelationship
        ):
            prop_name = python_naming.property_name(segment.relationship.property_name)
            prop_name_literal = python_common.string_literal(prop_name)

            blocks.append(
                Stripped(
                    f"""\
path.extend(
{I}[{prop_name_literal}, 0]
)
path_hash = common.hash_path(
{I}path_hash,
{I}[{prop_name_literal}, 0]
)
{target_variable} = {target_creation}(
{I}path_hash
)
{source_variable}.{prop_name} = [
{I}{target_variable}
]"""
                )
            )

            source_variable = target_variable
        else:
            assert_never(segment)

    blocks.append(
        Stripped(
            f"""\
return (
{I}{first_source_variable},
{I}{target_variable},
{I}path
)"""
        )
    )

    body = "\n\n".join(blocks)

    function_name = python_naming.function_name(
        Identifier(f"_{cls.name}_in_environment")
    )
    cls_name = python_naming.class_name(cls.name)

    return Stripped(
        f"""\
def {function_name}(
{I}creation_function: Callable[
{II}[common.CanHash],
{II}aas_types.{cls_name}
{I}]
) -> Tuple[
{I}aas_types.Environment,
{I}aas_types.{cls_name},
{I}List[Union[str, int]]
]:
{I}\"\"\"
{I}Generate an instance wrapped in an Environment.

{I}.. note::

{II}The generated Environment satisfies only the type constraints.
{II}That means it can be serialized as-is, but probably violates one or
{II}more meta-model constraints.
{I}\"\"\"
{I}{indent_but_first_line(body, I)}"""
    )


def _generate_minimal_cls_in_environment(
    cls: intermediate.ConcreteClass,
) -> Stripped:
    """Generate the function to create minimal instances wrapped in an environment."""
    cls_name = python_naming.class_name(cls.name)
    function_name = python_naming.function_name(
        Identifier(f"minimal_{cls.name}_in_environment")
    )
    minimal_function = _determine_concrete_minimal_function(cls)
    generation_function = python_naming.function_name(
        Identifier(f"_{cls.name}_in_environment")
    )

    return Stripped(
        f"""\
def {function_name}() -> Tuple[
{I}aas_types.Environment,
{I}aas_types.{cls_name},
{I}List[Union[str, int]]
]:
{I}\"\"\"
{I}Generate a minimal instance wrapped in an Environment.

{I}.. note::

{II}The generated Environment satisfies only the type constraints.
{II}That means it can be serialized as-is, but probably violates one or
{II}more meta-model constraints.
{I}\"\"\"
{I}return {generation_function}(
{II}creation_function={minimal_function}
{I})"""
    )


def _generate_class_name_to_minimal_in_environment(
    classes_in_environment: Sequence[intermediate.ConcreteClass],
) -> Stripped:
    """Generate the dispatch map from class names to creation function."""
    items = []  # type: List[Tuple[str, Identifier]]
    for cls in classes_in_environment:
        minimal_in_environment = python_naming.function_name(
            Identifier(f"minimal_{cls.name}_in_environment")
        )

        items.append((python_common.string_literal(cls.name), minimal_in_environment))

    items_joined = ",\n".join(
        f"""\
{key}:
{value}"""
        for key, value in items
    )

    return Stripped(
        f"""\
_CLASS_NAME_TO_MINIMAL_IN_ENVIRONMENT = {{
{I}{indent_but_first_line(items_joined, I)}
}}"""
    )


def _generate_minimal_in_environment() -> Stripped:
    """Generate the function that dispatches on class name."""
    return Stripped(
        f"""\
def minimal_in_environment(
{I}class_name: str
) -> Tuple[
{I}aas_types.Environment,
{I}aas_types.Class,
{I}List[Union[str, int]]
]:
{I}\"\"\"
{I}Generate a minimal instance wrapped in an Environment based on ``class_name``.

{I}.. note::

{II}The generated Environment satisfies only the type constraints.
{II}That means it can be serialized as-is, but probably violates one or
{II}more meta-model constraints.
{I}\"\"\"
{I}dispatch = _CLASS_NAME_TO_MINIMAL_IN_ENVIRONMENT.get(class_name, None)
{I}if dispatch is None:
{II}raise KeyError(
{III}f"The class name {{class_name!r}} is invalid. We expect "
{III}f"the class names as provided in aas-core-meta, "
{III}f"and *not* the Python class names."
{II})
{I}return dispatch()"""
    )


def _generate_maximal_cls_in_environment(
    cls: intermediate.ConcreteClass,
) -> Stripped:
    """Generate the function to create maximal instances wrapped in an environment."""
    cls_name = python_naming.class_name(cls.name)
    function_name = python_naming.function_name(
        Identifier(f"maximal_{cls.name}_in_environment")
    )
    maximal_function = _determine_concrete_maximal_function(cls)
    generation_function = python_naming.function_name(
        Identifier(f"_{cls.name}_in_environment")
    )

    return Stripped(
        f"""\
def {function_name}() -> Tuple[
{I}aas_types.Environment,
{I}aas_types.{cls_name},
{I}List[Union[str, int]]
]:
{I}\"\"\"
{I}Generate a maximal instance wrapped in an Environment.

{I}.. note::

{II}The generated Environment satisfies only the type constraints.
{II}That means it can be serialized as-is, but probably violates one or
{II}more meta-model constraints.
{I}\"\"\"
{I}return {generation_function}(
{II}creation_function={maximal_function}
{I})"""
    )


def _generate_class_name_to_maximal_in_environment(
    classes_in_environment: Sequence[intermediate.ConcreteClass],
) -> Stripped:
    """Generate the dispatch map from class names to creation function."""
    items = []  # type: List[Tuple[str, Identifier]]
    for cls in classes_in_environment:
        maximal_in_environment = python_naming.function_name(
            Identifier(f"maximal_{cls.name}_in_environment")
        )

        items.append((python_common.string_literal(cls.name), maximal_in_environment))

    items_joined = ",\n".join(
        f"""\
{key}:
{value}"""
        for key, value in items
    )

    return Stripped(
        f"""\
_CLASS_NAME_TO_MAXIMAL_IN_ENVIRONMENT = {{
{I}{indent_but_first_line(items_joined, I)}
}}"""
    )


def _generate_maximal_in_environment() -> Stripped:
    """Generate the function that dispatches on class name."""
    return Stripped(
        f"""\
def maximal_in_environment(
{I}class_name: str
) -> Tuple[
{I}aas_types.Environment,
{I}aas_types.Class,
{I}List[Union[str, int]]
]:
{I}\"\"\"
{I}Generate a maximal instance wrapped in an Environment based on ``class_name``.

{I}.. note::

{II}The generated Environment satisfies only the type constraints.
{II}That means it can be serialized as-is, but probably violates one or
{II}more meta-model constraints.
{I}\"\"\"
{I}dispatch = _CLASS_NAME_TO_MAXIMAL_IN_ENVIRONMENT.get(class_name, None)
{I}if dispatch is None:
{II}raise KeyError(
{III}f"The class name {{class_name!r}} is invalid. We expect "
{III}f"the class names as provided in aas-core-meta, "
{III}f"and *not* the Python class names."
{II})
{I}return dispatch()"""
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate(
    symbol_table: intermediate.SymbolTable,
) -> Tuple[Optional[Stripped], Optional[str]]:
    """Generate the module."""
    class_graph = dev_scripts.codegen.ontology.compute_class_graph(
        symbol_table=symbol_table
    )

    warning = dev_scripts.codegen.common.generate_warning(__file__)

    blocks = [
        Stripped(
            f"""\
\"\"\"
Create instances wrapped in environment.

.. note::

{I}The generated Environment satisfies only the type constraints.
{I}That means it can be serialized as-is, but probably violates one or
{I}more meta-model constraints.
\"\"\""""
        ),
        warning,
        Stripped(
            f"""\
from typing import (
{I}Callable,
{I}List,
{I}Tuple,
{I}Union
)

from aas_core3 import types as aas_types

from aas_core3_0_testgen import common
from aas_core3_0_testgen.codegened import creation"""
        ),
    ]

    classes_in_environment = []  # type: List[intermediate.ConcreteClass]

    for our_type in symbol_table.our_types:
        if not isinstance(our_type, intermediate.ConcreteClass):
            continue

        # fmt: off
        shortest_path_from_environment = (
            class_graph.shortest_paths_from_environment.get(
                our_type.name, None
            )
        )
        # fmt: on

        # NOTE (mristin, 2023-03-09):
        # There are classes which live outside the environment, so we can not
        # generate them in the environment.
        if shortest_path_from_environment is None:
            continue

        if len(shortest_path_from_environment) == 0:
            # NOTE (mristin, 2023-03-09):
            # The environment can not be generated in an environment.
            assert our_type.name == "Environment"
            continue

        classes_in_environment.append(our_type)

    # region General creation

    for cls in classes_in_environment:
        # fmt: off
        shortest_path_from_environment = (
            class_graph.shortest_paths_from_environment[cls.name]
        )
        # fmt: on

        blocks.append(
            _generate_create_cls_in_environment(
                cls=cls, shortest_path_from_environment=shortest_path_from_environment
            )
        )

    # endregion

    # region Minimal in environment

    for cls in classes_in_environment:
        blocks.append(_generate_minimal_cls_in_environment(cls=cls))

    blocks.append(
        _generate_class_name_to_minimal_in_environment(
            classes_in_environment=classes_in_environment
        )
    )

    blocks.append(_generate_minimal_in_environment())

    # endregion

    # Maximal in environment

    for cls in classes_in_environment:
        blocks.append(_generate_maximal_cls_in_environment(cls=cls))

    blocks.append(
        _generate_class_name_to_maximal_in_environment(
            classes_in_environment=classes_in_environment
        )
    )

    blocks.append(_generate_maximal_in_environment())

    # endregion

    blocks.append(
        Stripped(
            f"""\
def lives_in_environment(
{I}class_name: str
) -> bool:
{I}\"\"\"Check if the instance of the class lives in the Environment.\"\"\"
{I}return class_name in _CLASS_NAME_TO_MINIMAL_IN_ENVIRONMENT"""
        )
    )

    blocks.append(warning)

    return Stripped("\n\n\n".join(blocks)), None


def generate_and_write() -> Optional[str]:
    """Generate the code and write it to the pre-defined file."""
    # fmt: off
    symbol_table, _ = (
        aas_core3_0_testgen.common.load_symbol_table_and_infer_constraints_for_schema()
    )
    # fmt: on

    code, error = _generate(symbol_table)
    if error is not None:
        return error

    assert code is not None

    path = _REPO_DIR / "aas_core3_0_testgen" / "codegened" / "wrapping.py"
    path.write_text(code + "\n", encoding="utf-8")

    return None


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.parse_args()

    error = generate_and_write()
    if error is not None:
        print(error, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
