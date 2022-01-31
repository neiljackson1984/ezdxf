#  Copyright (c) 2022, Manfred Moitzi
#  License: MIT License
# Immutable spatial search tree based on the SsTree implementation of the book
# "Advanced Algorithms and Data Structures"
# - JS SsTree implementation: https://github.com/mlarocca/AlgorithmsAndDataStructuresInAction/tree/master/JavaScript/src/ss_tree
# - Research paper of Antonin Guttman: http://www-db.deis.unibo.it/courses/SI-LS/papers/Gut84.pdf

from typing import List, Optional, Iterator, Tuple, Callable, Sequence, Iterable
import abc
import math

from ezdxf.math import BoundingBox, AnyVec, Vec3

__all__ = ["RTree"]

INF = float("inf")


class Node:
    __slots__ = ("bbox",)

    def __init__(self, bbox: BoundingBox):
        self.bbox = bbox

    @abc.abstractmethod
    def __len__(self):
        ...

    @abc.abstractmethod
    def contains(self, point: AnyVec) -> bool:
        ...

    @abc.abstractmethod
    def _nearest_neighbor(
        self, target: AnyVec, nn: AnyVec = None, nn_dist: float = INF
    ) -> Tuple[Optional[AnyVec], float]:
        ...

    @abc.abstractmethod
    def points_in_sphere(
        self, center: AnyVec, radius: float
    ) -> Iterator[AnyVec]:
        ...

    @abc.abstractmethod
    def points_in_bbox(self, bbox: BoundingBox) -> Iterator[AnyVec]:
        ...

    def nearest_neighbor(self, target: AnyVec) -> AnyVec:
        nn = self._nearest_neighbor(target)[0]
        assert (
            nn is not None
        ), "empty tree should be prevented by tree constructor"
        return nn


class LeafNode(Node):
    __slots__ = ("points", "bbox")

    def __init__(self, points: List[AnyVec]):
        self.points = tuple(points)
        super().__init__(BoundingBox(self.points))

    def __len__(self):
        return len(self.points)

    def contains(self, point: AnyVec) -> bool:
        return any(point.isclose(p) for p in self.points)

    def _nearest_neighbor(
        self, target: AnyVec, nn: AnyVec = None, nn_dist: float = INF
    ) -> Tuple[Optional[AnyVec], float]:

        distance, point = min((target.distance(p), p) for p in self.points)
        if distance < nn_dist:
            nn, nn_dist = point, distance
        return nn, nn_dist

    def points_in_sphere(
        self, center: AnyVec, radius: float
    ) -> Iterator[AnyVec]:
        return (p for p in self.points if center.distance(p) <= radius)

    def points_in_bbox(self, bbox: BoundingBox) -> Iterator[AnyVec]:
        return (p for p in self.points if bbox.inside(p))


class InnerNode(Node):
    __slots__ = ("children", "bbox")

    def __init__(self, children: Sequence[Node]):
        super().__init__(BoundingBox())
        self.children = tuple(children)
        for child in self.children:
            # build union of all child bounding boxes
            self.bbox.extend([child.bbox.extmin, child.bbox.extmax])

    def __len__(self):
        return sum(len(c) for c in self.children)

    def contains(self, point: AnyVec) -> bool:
        for child in self.children:
            if child.bbox.inside(point) and child.contains(point):
                return True
        return False

    def _nearest_neighbor(
        self, target: AnyVec, nn: AnyVec = None, nn_dist: float = INF
    ) -> Tuple[Optional[AnyVec], float]:
        closest_child = find_closest_child(self.children, target)
        nn, nn_dist = closest_child._nearest_neighbor(target, nn, nn_dist)
        for child in self.children:
            if child is closest_child:
                continue
            # is target inside the child bounding box + nn_dist in all directions
            if grow_box(child.bbox, nn_dist).inside(target):
                point, distance = child._nearest_neighbor(target, nn, nn_dist)
                if distance < nn_dist:
                    nn = point
                    nn_dist = distance
        return nn, nn_dist

    def points_in_sphere(
        self, center: AnyVec, radius: float
    ) -> Iterator[AnyVec]:
        for child in self.children:
            if is_sphere_intersecting_bbox(
                center, radius, child.bbox.center, child.bbox.size
            ):
                yield from child.points_in_sphere(center, radius)

    def points_in_bbox(self, bbox: BoundingBox) -> Iterator[AnyVec]:
        for child in self.children:
            if bbox.has_overlap(child.bbox):
                yield from child.points_in_bbox(bbox)


class RTree:
    """Immutable spatial search tree loosely based on RTrees.

    The search tree is buildup once at initialization and immutable afterwards,
    because rebuilding the tree after inserting or deleting nodes is very costly
    and also keeps the implementation very simple. Without the ability to
    alter the content the restrictions which forces the tree balance at growing
    and shrinking of the original RTree, could be ignored, like the fixed
    minimum and maximum node size.

    This class uses internally only 3D bounding boxes, but also supports
    :class:`Vec2` as well as :class:`Vec3` objects as input data, but point
    types should not be mixed in a single search tree.

    The point objects keep their type and identity and the returned points of
    queries can be compared by the ``is`` operator for identity to the input
    points.

    """

    __slots__ = ("_root",)

    def __init__(self, points: Iterable[AnyVec], max_node_size: int = 5):
        if max_node_size < 2:
            raise ValueError("max node size must be > 1")
        _points = list(points)
        if len(_points) == 0:
            raise ValueError("no points given")
        self._root = make_node(_points, max_node_size, box_split)

    def __len__(self):
        """Returns the count of points in the search tree."""
        return len(self._root)

    def contains(self, point: AnyVec) -> bool:
        """Returns ``True`` if `point` exists, the comparison is done by the
        :meth:`isclose` method and not by th identity operator ``is``.
        """
        return self._root.contains(point)

    def nearest_neighbor(self, target: AnyVec) -> AnyVec:
        """Returns the closest point to the `target` point. """
        return self._root.nearest_neighbor(target)

    def points_in_sphere(
        self, center: AnyVec, radius: float
    ) -> Iterator[AnyVec]:
        """Returns all points in the range of the given sphere including the
        points at the boundary.
        """
        return self._root.points_in_sphere(center, radius)

    def points_in_bbox(self, bbox: BoundingBox) -> Iterator[AnyVec]:
        """Returns all points in the range of the given bounding box including
        the points at the boundary.
        """
        return self._root.points_in_bbox(bbox)


def make_node(
    points: List[AnyVec],
    max_size: int,
    split_strategy: Callable[[List[AnyVec], int], Sequence[Node]],
) -> Node:
    if len(points) > max_size:
        return InnerNode(split_strategy(points, max_size))
    else:
        return LeafNode(points)


def box_split(points: List[AnyVec], max_size: int) -> Sequence[Node]:
    n = len(points)
    size = BoundingBox(points).size.xyz
    dim = size.index(max(size))
    points.sort(key=lambda vec: vec[dim])
    k = math.ceil(n / max_size)
    return tuple(
        make_node(points[i : i + k], max_size, box_split)
        for i in range(0, n, k)
    )


def is_sphere_intersecting_bbox(
    centroid: AnyVec, radius: float, center: AnyVec, size: AnyVec
) -> bool:
    distance = centroid - center
    intersection_distance = size * 0.5 + Vec3(radius, radius, radius)
    # non-intersection is more often likely:
    if abs(distance.x) > intersection_distance.x:
        return False
    if abs(distance.y) > intersection_distance.y:
        return False
    if abs(distance.z) > intersection_distance.z:
        return False
    return True


def find_closest_child(children: Sequence[Node], point: AnyVec) -> Node:
    assert len(children) > 0
    _, node = min(
        (point.distance(child.bbox.center), child) for child in children
    )
    return node


def grow_box(box: BoundingBox, dist: float) -> BoundingBox:
    bbox = box.copy()
    bbox.grow(dist)
    return bbox
