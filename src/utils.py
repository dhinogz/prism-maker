"""
Utility functions for the polygon prism net generator.
"""

import math
from typing import Tuple, List
import numpy as np


def distance_2d(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate Euclidean distance between two 2D points."""
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


def angle_between_vectors(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
    """Calculate angle between two 2D vectors in radians."""
    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
    mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
    
    if mag1 == 0 or mag2 == 0:
        return 0
    
    cos_angle = dot_product / (mag1 * mag2)
    cos_angle = max(-1, min(1, cos_angle))  # Clamp to [-1, 1]
    
    return math.acos(cos_angle)


def normalize_vector(vector: Tuple[float, float]) -> Tuple[float, float]:
    """Normalize a 2D vector to unit length."""
    magnitude = math.sqrt(vector[0]**2 + vector[1]**2)
    if magnitude == 0:
        return (0, 0)
    return (vector[0] / magnitude, vector[1] / magnitude)


def rotate_point(point: Tuple[float, float], angle: float, 
                origin: Tuple[float, float] = (0, 0)) -> Tuple[float, float]:
    """Rotate a point around an origin by the given angle in radians."""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    
    # Translate to origin
    x = point[0] - origin[0]
    y = point[1] - origin[1]
    
    # Rotate
    new_x = x * cos_a - y * sin_a
    new_y = x * sin_a + y * cos_a
    
    # Translate back
    return (new_x + origin[0], new_y + origin[1])


def polygon_area(vertices: List[Tuple[float, float]]) -> float:
    """Calculate the area of a polygon using the shoelace formula."""
    if len(vertices) < 3:
        return 0
    
    area = 0
    n = len(vertices)
    
    for i in range(n):
        j = (i + 1) % n
        area += vertices[i][0] * vertices[j][1]
        area -= vertices[j][0] * vertices[i][1]
    
    return abs(area) / 2


def polygon_centroid(vertices: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Calculate the centroid of a polygon."""
    if len(vertices) < 3:
        return (0, 0)
    
    area = polygon_area(vertices)
    if area == 0:
        return (0, 0)
    
    cx = 0
    cy = 0
    n = len(vertices)
    
    for i in range(n):
        j = (i + 1) % n
        factor = vertices[i][0] * vertices[j][1] - vertices[j][0] * vertices[i][1]
        cx += (vertices[i][0] + vertices[j][0]) * factor
        cy += (vertices[i][1] + vertices[j][1]) * factor
    
    cx /= (6 * area)
    cy /= (6 * area)
    
    return (cx, cy)


def is_point_in_polygon(point: Tuple[float, float], 
                       vertices: List[Tuple[float, float]]) -> bool:
    """Check if a point is inside a polygon using ray casting algorithm."""
    x, y = point
    n = len(vertices)
    inside = False
    
    p1x, p1y = vertices[0]
    for i in range(1, n + 1):
        p2x, p2y = vertices[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


def simplify_polygon(vertices: List[Tuple[float, float]], 
                    tolerance: float = 0.1) -> List[Tuple[float, float]]:
    """Simplify a polygon by removing vertices that are too close together."""
    if len(vertices) < 3:
        return vertices
    
    simplified = [vertices[0]]
    
    for i in range(1, len(vertices)):
        if distance_2d(simplified[-1], vertices[i]) > tolerance:
            simplified.append(vertices[i])
    
    # Check if last point is too close to first
    if len(simplified) > 1 and distance_2d(simplified[-1], simplified[0]) <= tolerance:
        simplified.pop()
    
    return simplified if len(simplified) >= 3 else vertices