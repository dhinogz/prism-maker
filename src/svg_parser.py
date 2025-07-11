"""
SVG Parser Module

Extracts line segments from SVG paths and polylines for polygon detection.
"""

from typing import List, Tuple, Optional
from pathlib import Path
import xml.etree.ElementTree as ET
from svgpathtools import parse_path, Line, Path as SVGPath
import numpy as np


class SVGParser:
    """Parses SVG files to extract line segments from paths and polylines."""
    
    def __init__(self, tolerance: float = 0.1):
        """
        Initialize SVG parser.
        
        Args:
            tolerance: Tolerance for line segment approximation
        """
        self.tolerance = tolerance
        self.line_segments: List[Tuple[complex, complex]] = []
    
    def parse_svg(self, svg_file: Path) -> List[Tuple[complex, complex]]:
        """
        Parse SVG file and extract all line segments.
        
        Args:
            svg_file: Path to SVG file
            
        Returns:
            List of line segments as (start_point, end_point) tuples
        """
        self.line_segments = []
        
        try:
            tree = ET.parse(svg_file)
            root = tree.getroot()
            
            # Handle SVG namespace
            namespace = {'svg': 'http://www.w3.org/2000/svg'}
            if root.tag.startswith('{'):
                namespace_uri = root.tag.split('}')[0][1:]
                namespace = {'svg': namespace_uri}
            
            # Extract line segments from different SVG elements
            self._extract_from_paths(root, namespace)
            self._extract_from_polylines(root, namespace)
            self._extract_from_lines(root, namespace)
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid SVG file: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing SVG file: {e}")
        
        return self.line_segments
    
    def _extract_from_paths(self, root: ET.Element, namespace: dict) -> None:
        """Extract line segments from SVG path elements."""
        path_elements = root.findall('.//svg:path', namespace) + root.findall('.//path')
        
        for path_elem in path_elements:
            d_attr = path_elem.get('d')
            if d_attr:
                try:
                    path = parse_path(d_attr)
                    self._convert_path_to_segments(path)
                except Exception:
                    # Skip invalid paths
                    continue
    
    def _extract_from_polylines(self, root: ET.Element, namespace: dict) -> None:
        """Extract line segments from SVG polyline elements."""
        polyline_elements = root.findall('.//svg:polyline', namespace) + root.findall('.//polyline')
        
        for polyline_elem in polyline_elements:
            points_attr = polyline_elem.get('points')
            if points_attr:
                try:
                    points = self._parse_points(points_attr)
                    self._convert_points_to_segments(points)
                except Exception:
                    # Skip invalid polylines
                    continue
    
    def _extract_from_lines(self, root: ET.Element, namespace: dict) -> None:
        """Extract line segments from SVG line elements."""
        line_elements = root.findall('.//svg:line', namespace) + root.findall('.//line')
        
        for line_elem in line_elements:
            try:
                x1 = float(line_elem.get('x1', 0))
                y1 = float(line_elem.get('y1', 0))
                x2 = float(line_elem.get('x2', 0))
                y2 = float(line_elem.get('y2', 0))
                
                start = complex(x1, y1)
                end = complex(x2, y2)
                
                if abs(end - start) > self.tolerance:
                    self.line_segments.append((start, end))
                    
            except (ValueError, TypeError):
                # Skip invalid lines
                continue
    
    def _convert_path_to_segments(self, path: SVGPath) -> None:
        """Convert SVG path to line segments."""
        for segment in path:
            if isinstance(segment, Line):
                # Direct line segment
                start = segment.start
                end = segment.end
                if abs(end - start) > self.tolerance:
                    self.line_segments.append((start, end))
            else:
                # Approximate curves with line segments
                self._approximate_curve_with_lines(segment)
    
    def _approximate_curve_with_lines(self, curve) -> None:
        """Approximate a curve with line segments."""
        # Sample points along the curve
        num_samples = max(10, int(curve.length() / self.tolerance))
        
        prev_point = curve.start
        for i in range(1, num_samples + 1):
            t = i / num_samples
            current_point = curve.point(t)
            
            if abs(current_point - prev_point) > self.tolerance:
                self.line_segments.append((prev_point, current_point))
            
            prev_point = current_point
    
    def _parse_points(self, points_str: str) -> List[complex]:
        """Parse points string from polyline/polygon."""
        points = []
        coords = points_str.replace(',', ' ').split()
        
        for i in range(0, len(coords) - 1, 2):
            try:
                x = float(coords[i])
                y = float(coords[i + 1])
                points.append(complex(x, y))
            except (ValueError, IndexError):
                continue
        
        return points
    
    def _convert_points_to_segments(self, points: List[complex]) -> None:
        """Convert list of points to line segments."""
        for i in range(len(points) - 1):
            start = points[i]
            end = points[i + 1]
            
            if abs(end - start) > self.tolerance:
                self.line_segments.append((start, end))
    
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        """
        Get bounding box of all line segments.
        
        Returns:
            Tuple of (min_x, min_y, max_x, max_y)
        """
        if not self.line_segments:
            return (0, 0, 0, 0)
        
        all_points = []
        for start, end in self.line_segments:
            all_points.extend([start, end])
        
        x_coords = [p.real for p in all_points]
        y_coords = [p.imag for p in all_points]
        
        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))