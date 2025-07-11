"""
Net Generator Module

Generates printable prism nets with flaps from polygons and heights.
"""

from typing import List, Tuple, Dict
import numpy as np
import math
from shapely.geometry import Polygon, Point, LineString
from shapely.affinity import translate, rotate
import svgwrite


class NetGenerator:
    """Generates printable prism nets with flaps."""
    
    def __init__(self):
        """Initialize net generator."""
        self.flap_angle = 30  # degrees
        self.margin = 20  # SVG margin in units
    
    def generate_net(self, polygon: Polygon, height: float) -> str:
        """
        Generate a printable net for a prism.
        
        Args:
            polygon: Base polygon of the prism
            height: Height of the prism
            
        Returns:
            SVG string of the net
        """
        # Calculate flap dimensions
        flap_width = self._calculate_flap_width(polygon)
        
        # Get polygon vertices
        vertices = list(polygon.exterior.coords)[:-1]  # Remove duplicate last point
        
        # Generate side faces
        side_faces = self._generate_side_faces(vertices, height)
        
        # Generate flaps with alternating pattern
        flaps = self._generate_flaps(vertices, height, flap_width)
        
        # Layout the net
        net_layout = self._layout_net(polygon, side_faces, flaps)
        
        # Create SVG
        svg_content = self._create_svg(net_layout)
        
        return svg_content
    
    def _calculate_flap_width(self, polygon: Polygon) -> float:
        """Calculate flap width as shortest distance from edge midpoint to center ÷ 3."""
        centroid = polygon.centroid
        vertices = list(polygon.exterior.coords)[:-1]
        
        min_distance = float('inf')
        
        for i in range(len(vertices)):
            # Get edge midpoint
            p1 = Point(vertices[i])
            p2 = Point(vertices[(i + 1) % len(vertices)])
            midpoint = Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
            
            # Calculate distance to centroid
            distance = midpoint.distance(centroid)
            min_distance = min(min_distance, distance)
        
        return min_distance / 3
    
    def _generate_side_faces(self, vertices: List[Tuple[float, float]], 
                           height: float) -> List[Polygon]:
        """Generate side face rectangles for the prism."""
        side_faces = []
        
        for i in range(len(vertices)):
            p1 = vertices[i]
            p2 = vertices[(i + 1) % len(vertices)]
            
            # Calculate edge length
            edge_length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            
            # Create rectangle for this side face
            face_coords = [
                (0, 0),
                (edge_length, 0),
                (edge_length, height),
                (0, height)
            ]
            
            side_face = Polygon(face_coords)
            side_faces.append(side_face)
        
        return side_faces
    
    def _generate_flaps(self, vertices: List[Tuple[float, float]], 
                       height: float, flap_width: float) -> List[List[Polygon]]:
        """Generate flaps for each side face with alternating pattern."""
        flaps = []
        
        for i in range(len(vertices)):
            face_flaps = []
            
            p1 = vertices[i]
            p2 = vertices[(i + 1) % len(vertices)]
            edge_length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            
            # Alternating flap pattern: even indices get flaps on top and bottom
            # odd indices get flaps on left and right
            if i % 2 == 0:
                # Top flap
                top_flap = self._create_flap(edge_length, flap_width, 'top')
                face_flaps.append(top_flap)
                
                # Bottom flap
                bottom_flap = self._create_flap(edge_length, flap_width, 'bottom')
                face_flaps.append(bottom_flap)
            else:
                # Left flap
                left_flap = self._create_flap(height, flap_width, 'left')
                face_flaps.append(left_flap)
                
                # Right flap
                right_flap = self._create_flap(height, flap_width, 'right')
                face_flaps.append(right_flap)
            
            flaps.append(face_flaps)
        
        return flaps
    
    def _create_flap(self, edge_length: float, flap_width: float, 
                    position: str) -> Polygon:
        """Create a flap with 30° slopes."""
        slope_offset = flap_width * math.tan(math.radians(self.flap_angle))
        
        if position == 'top':
            coords = [
                (slope_offset, 0),
                (edge_length - slope_offset, 0),
                (edge_length, -flap_width),
                (0, -flap_width)
            ]
        elif position == 'bottom':
            coords = [
                (0, flap_width),
                (edge_length, flap_width),
                (edge_length - slope_offset, 0),
                (slope_offset, 0)
            ]
        elif position == 'left':
            coords = [
                (0, slope_offset),
                (0, edge_length - slope_offset),
                (-flap_width, edge_length),
                (-flap_width, 0)
            ]
        elif position == 'right':
            coords = [
                (flap_width, 0),
                (flap_width, edge_length),
                (0, edge_length - slope_offset),
                (0, slope_offset)
            ]
        else:
            raise ValueError(f"Invalid flap position: {position}")
        
        return Polygon(coords)
    
    def _layout_net(self, base_polygon: Polygon, side_faces: List[Polygon], 
                   flaps: List[List[Polygon]]) -> Dict:
        """Layout the net with base and connected side faces."""
        layout = {
            'base': base_polygon,
            'sides': [],
            'flaps': []
        }
        
        vertices = list(base_polygon.exterior.coords)[:-1]
        current_x = 0
        current_y = 0
        
        # Position base polygon
        base_bounds = base_polygon.bounds
        base_width = base_bounds[2] - base_bounds[0]
        base_height = base_bounds[3] - base_bounds[1]
        
        # Center the base
        base_x = self.margin
        base_y = self.margin + max(face.bounds[3] - face.bounds[1] for face in side_faces)
        
        positioned_base = translate(base_polygon, base_x, base_y)
        layout['base'] = positioned_base
        
        # Position side faces around the base
        for i, (side_face, face_flaps) in enumerate(zip(side_faces, flaps)):
            # Calculate position for this side face
            edge_start = vertices[i]
            edge_end = vertices[(i + 1) % len(vertices)]
            
            # Calculate edge vector and perpendicular
            edge_vector = np.array([edge_end[0] - edge_start[0], 
                                  edge_end[1] - edge_start[1]])
            edge_length = np.linalg.norm(edge_vector)
            edge_unit = edge_vector / edge_length if edge_length > 0 else np.array([1, 0])
            
            # Position side face
            if i == 0:
                # First side face attached to base
                side_x = base_x + edge_start[0]
                side_y = base_y - (side_face.bounds[3] - side_face.bounds[1])
                
                # Rotate to align with edge
                angle = math.degrees(math.atan2(edge_unit[1], edge_unit[0]))
                positioned_side = rotate(side_face, angle, origin=(0, 0))
                positioned_side = translate(positioned_side, side_x, side_y)
            else:
                # Other side faces connected to previous side face
                prev_side = layout['sides'][i-1]
                prev_bounds = prev_side.bounds
                
                side_x = prev_bounds[2]  # Right edge of previous side
                side_y = prev_bounds[1]  # Bottom edge of previous side
                
                positioned_side = translate(side_face, side_x, side_y)
            
            layout['sides'].append(positioned_side)
            
            # Position flaps for this side face
            positioned_flaps = []
            side_bounds = positioned_side.bounds
            
            for j, flap in enumerate(face_flaps):
                if i % 2 == 0:  # Top/bottom flaps
                    if j == 0:  # Top flap
                        flap_x = side_bounds[0]
                        flap_y = side_bounds[3]
                    else:  # Bottom flap
                        flap_x = side_bounds[0]
                        flap_y = side_bounds[1] - (flap.bounds[3] - flap.bounds[1])
                else:  # Left/right flaps
                    if j == 0:  # Left flap
                        flap_x = side_bounds[0] - (flap.bounds[2] - flap.bounds[0])
                        flap_y = side_bounds[1]
                    else:  # Right flap
                        flap_x = side_bounds[2]
                        flap_y = side_bounds[1]
                
                positioned_flap = translate(flap, flap_x, flap_y)
                positioned_flaps.append(positioned_flap)
            
            layout['flaps'].extend(positioned_flaps)
        
        return layout
    
    def _create_svg(self, layout: Dict) -> str:
        """Create SVG string from the net layout."""
        # Calculate total bounds
        all_shapes = [layout['base']] + layout['sides'] + layout['flaps']
        
        min_x = min(shape.bounds[0] for shape in all_shapes)
        min_y = min(shape.bounds[1] for shape in all_shapes)
        max_x = max(shape.bounds[2] for shape in all_shapes)
        max_y = max(shape.bounds[3] for shape in all_shapes)
        
        width = max_x - min_x + 2 * self.margin
        height = max_y - min_y + 2 * self.margin
        
        # Create SVG
        dwg = svgwrite.Drawing(size=(f'{width}px', f'{height}px'))
        
        # Add base polygon
        base_coords = list(layout['base'].exterior.coords)
        dwg.add(dwg.polygon(
            points=base_coords,
            fill='lightblue',
            stroke='black',
            stroke_width=1
        ))
        
        # Add side faces
        for side in layout['sides']:
            side_coords = list(side.exterior.coords)
            dwg.add(dwg.polygon(
                points=side_coords,
                fill='lightgreen',
                stroke='black',
                stroke_width=1
            ))
        
        # Add flaps
        for flap in layout['flaps']:
            flap_coords = list(flap.exterior.coords)
            dwg.add(dwg.polygon(
                points=flap_coords,
                fill='lightyellow',
                stroke='black',
                stroke_width=1,
                stroke_dasharray='2,2'
            ))
        
        return dwg.tostring()