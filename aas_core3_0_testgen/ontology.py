"""Iterate over the class ontology of the meta-model."""
import collections
import itertools
from typing import Union, Mapping, Tuple, Sequence, Final, OrderedDict, List

import networkx
from aas_core_codegen import intermediate
from aas_core_codegen.common import Identifier
import aas_core_codegen.common


class PropertyRelationship:
    """
    Model a relationship between two classes as a property.

    Namely, instances of the target class appear as a property of the source class.
    """

    def __init__(self, property_name: Identifier) -> None:
        """Initialize with the given values."""
        self.property_name = property_name


class ListPropertyRelationship:
    """
    Model a relationship between two classes as an item of a list property.

    Namely, instances of the target class appear as items in a list property of
    the source class.
    """

    def __init__(self, property_name: Identifier) -> None:
        """Initialize with the given values."""
        self.property_name = property_name


RelationshipUnion = Union[PropertyRelationship, ListPropertyRelationship]

RelationshipMap = Mapping[Tuple[Identifier, Identifier], RelationshipUnion]


class Segment:
    """Represent a segment from the class ``Environment`` to a concrete class."""

    def __init__(
        self,
        source: intermediate.ConcreteClass,
        target: intermediate.ConcreteClass,
        relationship: RelationshipUnion,
    ) -> None:
        """Initialize with the given values."""
        self.source = source
        self.target = target
        self.relationship = relationship


ShortestPathMap = Mapping[Identifier, Sequence[Segment]]


class ClassGraph:
    """Model how classes of the meta-model are related to each other."""

    relationship_map: Final[RelationshipMap]
    shortest_paths: Final[ShortestPathMap]

    def __init__(
        self, relationship_map: RelationshipMap, shortest_paths: ShortestPathMap
    ) -> None:
        """Initialize with the given values."""
        self.relationship_map = relationship_map
        self.shortest_paths = shortest_paths


def _compute_relationship_map(
    symbol_table: intermediate.SymbolTable,
) -> RelationshipMap:
    """Compute the relationships between the classes as edges in the class graph."""
    rel_map: OrderedDict[
        Tuple[Identifier, Identifier], RelationshipUnion
    ] = collections.OrderedDict()

    for our_type in symbol_table.our_types:
        if isinstance(our_type, intermediate.ConcreteClass):
            for prop in our_type.properties:
                type_anno = intermediate.beneath_optional(prop.type_annotation)

                if isinstance(type_anno, intermediate.ListTypeAnnotation):
                    assert isinstance(
                        type_anno.items, intermediate.OurTypeAnnotation
                    ), (
                        "Expected only lists of enums or classes in the meta-model, "
                        f"but got: {type_anno}"
                    )

                    if isinstance(type_anno.items.our_type, intermediate.AbstractClass):
                        for (
                            concrete_cls
                        ) in type_anno.items.our_type.concrete_descendants:
                            source_target = (our_type.name, concrete_cls.name)

                            rel = rel_map.get(source_target, None)
                            if rel is None:
                                rel_map[source_target] = ListPropertyRelationship(
                                    property_name=prop.name
                                )
                    elif isinstance(
                        type_anno.items.our_type, intermediate.ConcreteClass
                    ):
                        for concrete_cls in itertools.chain(
                            [type_anno.items.our_type],
                            type_anno.items.our_type.concrete_descendants,
                        ):
                            source_target = (our_type.name, concrete_cls.name)

                            rel = rel_map.get(source_target, None)
                            if rel is None:
                                rel_map[source_target] = ListPropertyRelationship(
                                    property_name=prop.name
                                )
                    else:
                        pass

                elif isinstance(type_anno, intermediate.OurTypeAnnotation):
                    if isinstance(type_anno.our_type, intermediate.AbstractClass):
                        for concrete_cls in type_anno.our_type.concrete_descendants:
                            source_target = (our_type.name, concrete_cls.name)

                            rel = rel_map.get(source_target, None)

                            # NOTE (mristin, 2022-05-07):
                            # Property edges have smaller distance than list-property
                            # edges. Hence, we keep only the shortest edges.
                            #
                            # See: https://groups.google.com/g/networkx-discuss/c/87uC9F0ug8Y
                            if rel is None or isinstance(rel, ListPropertyRelationship):
                                rel_map[source_target] = PropertyRelationship(
                                    property_name=prop.name
                                )

                    elif isinstance(type_anno.our_type, intermediate.ConcreteClass):
                        for concrete_cls in itertools.chain(
                            [type_anno.our_type],
                            type_anno.our_type.concrete_descendants,
                        ):
                            source_target = (our_type.name, concrete_cls.name)

                            rel = rel_map.get(source_target, None)

                            # NOTE (mristin, 2022-05-07):
                            # See the note above re property edge *versus* list-property
                            # edge.
                            if rel is None or isinstance(rel, ListPropertyRelationship):
                                rel_map[source_target] = PropertyRelationship(
                                    property_name=prop.name
                                )
                    else:
                        pass

    return rel_map


def _compute_shortest_paths_from_environment(
    symbol_table: intermediate.SymbolTable, relationship_map: RelationshipMap
) -> ShortestPathMap:
    """Compute the shortest path from the environment to the concrete classes."""
    graph = networkx.DiGraph()
    for our_type in symbol_table.our_types:
        if isinstance(our_type, intermediate.ConcreteClass):
            graph.add_node(our_type.name)

    for (source, target), relationship in relationship_map.items():
        if isinstance(relationship, PropertyRelationship):
            graph.add_edge(source, target, weight=1)
        elif isinstance(relationship, ListPropertyRelationship):
            # NOTE (mristin, 2022-05-07):
            # Creating a list and adding an item is more work than creating an instance.
            # Thus, we pay two coins for the list-property creation.
            graph.add_edge(source, target, weight=2)
        else:
            aas_core_codegen.common.assert_never(relationship)

    _, raw_path_map = networkx.single_source_dijkstra(G=graph, source="Environment")

    path_map: OrderedDict[Identifier, Sequence[Segment]] = collections.OrderedDict()

    path_map[Identifier("Environment")] = []

    for our_type in symbol_table.our_types:
        if our_type.name == "Environment":
            continue

        raw_path = raw_path_map.get(our_type.name, None)
        if raw_path is None:
            continue

        assert len(raw_path) >= 2
        cursor = iter(raw_path)
        current = next(cursor, None)

        assert current is None or isinstance(current, str)

        path: List[Segment] = []

        while True:
            prev = current
            current = next(cursor, None)
            assert current is None or isinstance(current, str)

            if current is None:
                break

            assert prev is not None
            source_symbol = symbol_table.must_find_our_type(Identifier(prev))
            assert isinstance(
                source_symbol, intermediate.ConcreteClass
            ), "Only edges between concrete classes expected in the graph"

            assert current is not None
            target_symbol = symbol_table.must_find_our_type(Identifier(current))
            assert isinstance(
                target_symbol, intermediate.ConcreteClass
            ), "Only edges between concrete classes expected in the graph"

            relationship = relationship_map[(source_symbol.name, target_symbol.name)]
            path.append(
                Segment(
                    source=source_symbol,
                    target=target_symbol,
                    relationship=relationship,
                )
            )

        path_map[our_type.name] = path

    return path_map


def compute_class_graph(symbol_table: intermediate.SymbolTable) -> ClassGraph:
    """Compute the relationship between the classes."""
    relationship_map = _compute_relationship_map(symbol_table=symbol_table)

    return ClassGraph(
        relationship_map=relationship_map,
        shortest_paths=_compute_shortest_paths_from_environment(
            symbol_table=symbol_table,
            relationship_map=relationship_map,
        ),
    )
