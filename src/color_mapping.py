"""
Color Mapping Module

Extracts colors from SVG polygons and maps them to heights using RGB interpolation.
"""

from typing import List, Tuple, Dict, Optional
from pathlib import Path
import xml.etree.ElementTree as ET
import re
import numpy as np
from shapely.geometry import Polygon, Point


class ColorMapper:
    """Maps polygon colors to heights using RGB interpolation."""
    
    def __init__(self, color_height_mapping: Dict[str, float]):
        """
        Initialize color mapper.
        
        Args:
            color_height_mapping: Dictionary mapping color names to height values
        """
        self.color_height_mapping = color_height_mapping
        self.color_rgb_cache = {}
        
        # Convert color names to RGB values
        self._build_rgb_cache()
    
    def map_polygon_heights(self, polygons: List[Polygon], 
                           svg_file: Path) -> List[Tuple[Polygon, float]]:
        """
        Map polygons to their corresponding heights based on colors.
        
        Args:
            polygons: List of detected polygons
            svg_file: Original SVG file to extract colors from
            
        Returns:
            List of (polygon, height) tuples
        """
        polygon_heights = []
        
        # Parse SVG to extract color information
        svg_colors = self._extract_svg_colors(svg_file)
        
        for polygon in polygons:
            # Find the color for this polygon
            color = self._find_polygon_color(polygon, svg_colors)
            
            # Map color to height
            height = self._color_to_height(color)
            
            polygon_heights.append((polygon, height))
        
        return polygon_heights
    
    def _build_rgb_cache(self) -> None:
        """Build cache of RGB values for defined colors."""
        for color_name in self.color_height_mapping.keys():
            rgb = self._color_name_to_rgb(color_name)
            if rgb:
                self.color_rgb_cache[color_name] = rgb
    
    def _color_name_to_rgb(self, color_name: str) -> Optional[Tuple[int, int, int]]:
        """Convert color name to RGB tuple."""
        # Basic color name mapping
        color_map = {
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'cyan': (0, 255, 255),
            'magenta': (255, 0, 255),
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'gray': (128, 128, 128),
            'grey': (128, 128, 128),
            'orange': (255, 165, 0),
            'purple': (128, 0, 128),
            'brown': (165, 42, 42),
            'pink': (255, 192, 203),
        }
        
        color_lower = color_name.lower()
        
        # Check if it's a hex color
        if color_name.startswith('#'):
            return self._hex_to_rgb(color_name)
        
        # Check if it's an RGB function
        if color_name.startswith('rgb'):
            return self._parse_rgb_function(color_name)
        
        # Check basic color names
        if color_lower in color_map:
            return color_map[color_lower]
        
        return None
    
    def _hex_to_rgb(self, hex_color: str) -> Optional[Tuple[int, int, int]]:
        """Convert hex color to RGB tuple."""
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 3:
                hex_color = ''.join([c*2 for c in hex_color])
            if len(hex_color) == 6:
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            pass
        return None
    
    def _parse_rgb_function(self, rgb_str: str) -> Optional[Tuple[int, int, int]]:
        """Parse RGB function string to RGB tuple."""
        match = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', rgb_str)
        if match:
            return tuple(int(x) for x in match.groups())
        return None
    
    def _extract_svg_colors(self, svg_file: Path) -> List[Dict]:
        """Extract color information from SVG elements."""
        colors = []
        
        try:
            tree = ET.parse(svg_file)
            root = tree.getroot()
            
            # Handle SVG namespace
            namespace = {'svg': 'http://www.w3.org/2000/svg'}
            if root.tag.startswith('{'):
                namespace_uri = root.tag.split('}')[0][1:]
                namespace = {'svg': namespace_uri}
            
            # Extract colors from various SVG elements
            elements = (root.findall('.//svg:*[@fill]', namespace) + 
                       root.findall('.//*[@fill]'))
            
            for elem in elements:
                fill_color = elem.get('fill')
                if fill_color and fill_color != 'none':
                    # Try to extract geometry information
                    geometry = self._extract_element_geometry(elem)
                    if geometry:
                        colors.append({
                            'color': fill_color,
                            'geometry': geometry,
                            'element': elem.tag
                        })
            
        except ET.ParseError:
            pass
        
        return colors
    
    def _extract_element_geometry(self, elem: ET.Element) -> Optional[Polygon]:
        """Extract geometry from SVG element."""
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        
        try:
            if tag == 'rect':
                return self._rect_to_polygon(elem)
            elif tag == 'circle':
                return self._circle_to_polygon(elem)
            elif tag == 'polygon':
                return self._svg_polygon_to_shapely(elem)
            elif tag == 'path':
                return self._path_to_polygon(elem)
        except Exception:
            pass
        
        return None
    
    def _rect_to_polygon(self, rect_elem: ET.Element) -> Optional[Polygon]:
        """Convert SVG rect to Shapely polygon."""
        try:
            x = float(rect_elem.get('x', 0))
            y = float(rect_elem.get('y', 0))
            width = float(rect_elem.get('width', 0))
            height = float(rect_elem.get('height', 0))
            
            coords = [
                (x, y),
                (x + width, y),
                (x + width, y + height),
                (x, y + height)
            ]
            
            return Polygon(coords)
        except (ValueError, TypeError):
            return None
    
    def _circle_to_polygon(self, circle_elem: ET.Element) -> Optional[Polygon]:
        """Convert SVG circle to approximate Shapely polygon."""
        try:
            cx = float(circle_elem.get('cx', 0))
            cy = float(circle_elem.get('cy', 0))
            r = float(circle_elem.get('r', 0))
            
            # Create approximate polygon with 16 sides
            angles = np.linspace(0, 2*np.pi, 17)[:-1]
            coords = [(cx + r*np.cos(a), cy + r*np.sin(a)) for a in angles]
            
            return Polygon(coords)
        except (ValueError, TypeError):
            return None
    
    def _svg_polygon_to_shapely(self, polygon_elem: ET.Element) -> Optional[Polygon]:
        """Convert SVG polygon to Shapely polygon."""
        try:
            points_str = polygon_elem.get('points', '')
            coords = []
            
            points = points_str.replace(',', ' ').split()
            for i in range(0, len(points) - 1, 2):
                x = float(points[i])
                y = float(points[i + 1])
                coords.append((x, y))
            
            if len(coords) >= 3:
                return Polygon(coords)
        except (ValueError, IndexError):
            pass
        
        return None
    
    def _path_to_polygon(self, path_elem: ET.Element) -> Optional[Polygon]:
        """Convert simple SVG path to Shapely polygon (basic implementation)."""
        # This is a simplified implementation
        # For complex paths, you might want to use svgpathtools
        return None
    
    def _find_polygon_color(self, polygon: Polygon, svg_colors: List[Dict]) -> str:
        """Find the color associated with a detected polygon."""
        polygon_centroid = polygon.centroid
        
        # Find SVG elements that contain this polygon's centroid
        for color_info in svg_colors:
            svg_geometry = color_info['geometry']
            if svg_geometry and svg_geometry.contains(polygon_centroid):
                return color_info['color']
        
        # If no exact match, find the closest SVG element
        min_distance = float('inf')
        closest_color = 'black'  # Default color
        
        for color_info in svg_colors:
            svg_geometry = color_info['geometry']
            if svg_geometry:
                distance = polygon_centroid.distance(svg_geometry)
                if distance < min_distance:
                    min_distance = distance
                    closest_color = color_info['color']
        
        return closest_color
    
    def _color_to_height(self, color: str) -> float:
        """Map a color to height using RGB interpolation."""
        color_rgb = self._color_name_to_rgb(color)
        
        if not color_rgb:
            # Default height if color can't be parsed
            return 1.0
        
        # If exact color match exists
        for color_name, height in self.color_height_mapping.items():
            if color.lower() == color_name.lower():
                return height
        
        # Find closest color using RGB distance
        min_distance = float('inf')
        closest_height = 1.0
        
        for color_name, height in self.color_height_mapping.items():
            mapped_rgb = self.color_rgb_cache.get(color_name)
            if mapped_rgb:
                distance = self._rgb_distance(color_rgb, mapped_rgb)
                if distance < min_distance:
                    min_distance = distance
                    closest_height = height
        
        # If we have multiple close colors, interpolate
        if min_distance > 50:  # If no close match, try interpolation
            return self._interpolate_height(color_rgb)
        
        return closest_height
    
    def _rgb_distance(self, rgb1: Tuple[int, int, int], 
                     rgb2: Tuple[int, int, int]) -> float:
        """Calculate Euclidean distance between two RGB colors."""
        return np.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))
    
    def _interpolate_height(self, target_rgb: Tuple[int, int, int]) -> float:
        """Interpolate height based on RGB values of nearby colors."""
        if len(self.color_rgb_cache) < 2:
            return 1.0
        
        # Find the two closest colors
        distances = []
        for color_name, rgb in self.color_rgb_cache.items():
            distance = self._rgb_distance(target_rgb, rgb)
            height = self.color_height_mapping[color_name]
            distances.append((distance, height, rgb))
        
        distances.sort()
        
        if len(distances) >= 2:
            d1, h1, rgb1 = distances[0]
            d2, h2, rgb2 = distances[1]
            
            # Weighted interpolation based on distance
            if d1 + d2 > 0:
                weight1 = d2 / (d1 + d2)
                weight2 = d1 / (d1 + d2)
                return weight1 * h1 + weight2 * h2
        
        return distances[0][1] if distances else 1.0