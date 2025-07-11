"""
Geometry Processing Module

Handles intersection detection and polygon formation from line segments.
"""

from typing import List, Tuple, Set, Optional
import numpy as np
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union
import itertools


class GeometryProcessor:
    """Processes line segments to detect intersections and form polygons."""
    
    def __init__(self, tolerance: float = 0.1):
        """
        Initialize geometry processor.
        
        Args:
            tolerance: Tolerance for intersection detection and point matching
        """
        self.tolerance = tolerance
        self.intersections: Set[complex] = set()
        self.segments: List[Tuple[complex, complex]] = []
    
    def find_polygons(self, line_segments: List[Tuple[complex, complex]]) -> List[Polygon]:
        """
        Find all polygons formed by intersecting line segments.
        
        Args:
            line_segments: List of line segments as (start, end) complex number pairs
            
        Returns:
            List of Shapely Polygon objects
        """
        self.segments = line_segments
        self.intersections = set()
        
        # Find all intersection points
        self._find_intersections()
        
        # Split segments at intersection points
        split_segments = self._split_segments_at_intersections()
        
        # Build graph of connected segments
        graph = self._build_segment_graph(split_segments)
        
        # Find cycles (polygons) in the graph
        polygons = self._find_cycles_in_graph(graph)
        
        # Validate and filter polygons
        valid_polygons = self._validate_polygons(polygons)
        
        return valid_polygons
    
    def _find_intersections(self) -> None:
        """Find all intersection points between line segments."""
        for i, seg1 in enumerate(self.segments):
            for j, seg2 in enumerate(self.segments[i + 1:], i + 1):
                intersection = self._line_intersection(seg1, seg2)
                if intersection is not None:
                    self.intersections.add(intersection)
    
    def _line_intersection(self, seg1: Tuple[complex, complex], 
                          seg2: Tuple[complex, complex]) -> Optional[complex]:
        """
        Find intersection point between two line segments.
        
        Args:
            seg1: First line segment (start, end)
            seg2: Second line segment (start, end)
            
        Returns:
            Intersection point as complex number, or None if no intersection
        """
        p1, p2 = seg1
        p3, p4 = seg2
        
        # Convert to real coordinates for calculation
        x1, y1 = p1.real, p1.imag
        x2, y2 = p2.real, p2.imag
        x3, y3 = p3.real, p3.imag
        x4, y4 = p4.real, p4.imag
        
        # Calculate intersection using parametric form
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        
        if abs(denom) < self.tolerance:
            # Lines are parallel
            return None
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
        
        # Check if intersection is within both segments
        if 0 <= t <= 1 and 0 <= u <= 1:
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            return complex(x, y)
        
        return None
    
    def _split_segments_at_intersections(self) -> List[Tuple[complex, complex]]:
        """Split line segments at intersection points."""
        split_segments = []
        
        for segment in self.segments:
            start, end = segment
            
            # Find intersections on this segment
            intersections_on_segment = []
            for intersection in self.intersections:
                if self._point_on_segment(intersection, segment):
                    intersections_on_segment.append(intersection)
            
            # Add segment endpoints
            intersections_on_segment.extend([start, end])
            
            # Sort points along the segment
            intersections_on_segment = self._sort_points_along_segment(
                intersections_on_segment, start, end
            )
            
            # Create sub-segments
            for i in range(len(intersections_on_segment) - 1):
                p1 = intersections_on_segment[i]
                p2 = intersections_on_segment[i + 1]
                
                if abs(p2 - p1) > self.tolerance:
                    split_segments.append((p1, p2))
        
        return split_segments
    
    def _point_on_segment(self, point: complex, segment: Tuple[complex, complex]) -> bool:
        """Check if a point lies on a line segment."""
        start, end = segment
        
        # Check if point is collinear with segment
        cross_product = ((point.imag - start.imag) * (end.real - start.real) - 
                        (point.real - start.real) * (end.imag - start.imag))
        
        if abs(cross_product) > self.tolerance:
            return False
        
        # Check if point is within segment bounds
        min_x, max_x = min(start.real, end.real), max(start.real, end.real)
        min_y, max_y = min(start.imag, end.imag), max(start.imag, end.imag)
        
        return (min_x - self.tolerance <= point.real <= max_x + self.tolerance and
                min_y - self.tolerance <= point.imag <= max_y + self.tolerance)
    
    def _sort_points_along_segment(self, points: List[complex], 
                                  start: complex, end: complex) -> List[complex]:
        """Sort points along a line segment from start to end."""
        def distance_from_start(point: complex) -> float:
            return abs(point - start)
        
        return sorted(set(points), key=distance_from_start)
    
    def _build_segment_graph(self, segments: List[Tuple[complex, complex]]) -> dict:
        """Build a graph representation of connected segments."""
        graph = {}
        
        for start, end in segments:
            # Round coordinates to handle floating point precision
            start_key = self._round_point(start)
            end_key = self._round_point(end)
            
            if start_key not in graph:
                graph[start_key] = []
            if end_key not in graph:
                graph[end_key] = []
            
            graph[start_key].append(end_key)
            graph[end_key].append(start_key)
        
        return graph
    
    def _round_point(self, point: complex) -> complex:
        """Round point coordinates to handle floating point precision."""
        precision = int(-np.log10(self.tolerance))
        return complex(round(point.real, precision), round(point.imag, precision))
    
    def _find_cycles_in_graph(self, graph: dict) -> List[List[complex]]:
        """Find all cycles (potential polygons) in the segment graph."""
        cycles = []
        visited_edges = set()
        
        for start_node in graph:
            for neighbor in graph[start_node]:
                edge = tuple(sorted([start_node, neighbor], key=lambda x: (x.real, x.imag)))
                if edge in visited_edges:
                    continue
                
                # Try to find cycles starting from this edge
                cycle = self._find_cycle_from_edge(graph, start_node, neighbor, visited_edges)
                if cycle and len(cycle) >= 3:
                    cycles.append(cycle)
        
        return cycles
    
    def _find_cycle_from_edge(self, graph: dict, start: complex, current: complex,
                             visited_edges: set) -> Optional[List[complex]]:
        """Find a cycle starting from a specific edge using DFS."""
        path = [start, current]
        visited_nodes = {start, current}
        
        while True:
            # Get unvisited neighbors of current node
            neighbors = []
            for neighbor in graph[current]:
                edge = tuple(sorted([current, neighbor], key=lambda x: (x.real, x.imag)))
                if edge not in visited_edges and neighbor not in visited_nodes:
                    neighbors.append(neighbor)
            
            # Also check if we can return to start
            if start in graph[current]:
                edge = tuple(sorted([current, start], key=lambda x: (x.real, x.imag)))
                if edge not in visited_edges and len(path) >= 3:
                    # Found a cycle
                    for i in range(len(path) - 1):
                        edge = tuple(sorted([path[i], path[i + 1]], key=lambda x: (x.real, x.imag)))
                        visited_edges.add(edge)
                    edge = tuple(sorted([current, start], key=lambda x: (x.real, x.imag)))
                    visited_edges.add(edge)
                    return path
            
            if not neighbors:
                break
            
            # Choose the neighbor that makes the smallest angle (rightmost turn)
            if len(neighbors) == 1:
                next_node = neighbors[0]
            else:
                next_node = self._choose_rightmost_neighbor(current, path[-2], neighbors)
            
            path.append(next_node)
            visited_nodes.add(next_node)
            current = next_node
        
        return None
    
    def _choose_rightmost_neighbor(self, current: complex, previous: complex,
                                  neighbors: List[complex]) -> complex:
        """Choose the neighbor that makes the smallest clockwise angle."""
        incoming_vector = current - previous
        incoming_angle = np.angle(incoming_vector)
        
        best_neighbor = neighbors[0]
        best_angle = float('inf')
        
        for neighbor in neighbors:
            outgoing_vector = neighbor - current
            outgoing_angle = np.angle(outgoing_vector)
            
            # Calculate clockwise angle difference
            angle_diff = (outgoing_angle - incoming_angle) % (2 * np.pi)
            
            if angle_diff < best_angle:
                best_angle = angle_diff
                best_neighbor = neighbor
        
        return best_neighbor
    
    def _validate_polygons(self, cycles: List[List[complex]]) -> List[Polygon]:
        """Validate and convert cycles to Shapely polygons."""
        valid_polygons = []
        
        for cycle in cycles:
            try:
                # Convert to coordinate pairs
                coords = [(p.real, p.imag) for p in cycle]
                
                # Create Shapely polygon
                polygon = Polygon(coords)
                
                # Validate polygon
                if (polygon.is_valid and 
                    not polygon.is_empty and 
                    polygon.area > self.tolerance and
                    len(coords) <= 6):  # Max 6 sides as specified
                    
                    valid_polygons.append(polygon)
                    
            except Exception:
                # Skip invalid polygons
                continue
        
        # Remove nested polygons
        return self._remove_nested_polygons(valid_polygons)
    
    def _remove_nested_polygons(self, polygons: List[Polygon]) -> List[Polygon]:
        """Remove polygons that are nested inside other polygons."""
        filtered_polygons = []
        
        for i, poly1 in enumerate(polygons):
            is_nested = False
            
            for j, poly2 in enumerate(polygons):
                if i != j and poly2.contains(poly1):
                    is_nested = True
                    break
            
            if not is_nested:
                filtered_polygons.append(poly1)
        
        return filtered_polygons