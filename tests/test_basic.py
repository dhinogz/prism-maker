"""
Basic tests for the polygon prism net generator.
"""

import pytest
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon

from src.svg_parser import SVGParser
from src.geometry import GeometryProcessor
from src.color_mapping import ColorMapper
from src.net_generator import NetGenerator


def create_test_svg(content: str) -> Path:
    """Create a temporary SVG file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write(content)
        return Path(f.name)


def test_svg_parser_basic():
    """Test basic SVG parsing functionality."""
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
        <line x1="0" y1="0" x2="50" y2="0" stroke="black"/>
        <line x1="50" y1="0" x2="50" y2="50" stroke="black"/>
        <line x1="50" y1="50" x2="0" y2="50" stroke="black"/>
        <line x1="0" y1="50" x2="0" y2="0" stroke="black"/>
    </svg>'''
    
    svg_file = create_test_svg(svg_content)
    
    try:
        parser = SVGParser(tolerance=0.1)
        segments = parser.parse_svg(svg_file)
        
        assert len(segments) == 4
        assert all(isinstance(seg, tuple) and len(seg) == 2 for seg in segments)
        
    finally:
        svg_file.unlink()


def test_geometry_processor_square():
    """Test polygon detection with a simple square."""
    # Create line segments for a square
    segments = [
        (complex(0, 0), complex(10, 0)),
        (complex(10, 0), complex(10, 10)),
        (complex(10, 10), complex(0, 10)),
        (complex(0, 10), complex(0, 0))
    ]
    
    processor = GeometryProcessor(tolerance=0.1)
    polygons = processor.find_polygons(segments)
    
    assert len(polygons) >= 1
    assert all(isinstance(poly, Polygon) for poly in polygons)


def test_color_mapper_basic():
    """Test basic color mapping functionality."""
    color_mapping = {'red': 1.0, 'blue': 2.0}
    mapper = ColorMapper(color_mapping)
    
    # Test color name to RGB conversion
    red_rgb = mapper._color_name_to_rgb('red')
    assert red_rgb == (255, 0, 0)
    
    blue_rgb = mapper._color_name_to_rgb('blue')
    assert blue_rgb == (0, 0, 255)
    
    # Test hex color conversion
    hex_rgb = mapper._hex_to_rgb('#FF0000')
    assert hex_rgb == (255, 0, 0)


def test_net_generator_basic():
    """Test basic net generation functionality."""
    # Create a simple square polygon
    square = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    height = 5.0
    
    generator = NetGenerator()
    
    # Test flap width calculation
    flap_width = generator._calculate_flap_width(square)
    assert flap_width > 0
    
    # Test side face generation
    vertices = list(square.exterior.coords)[:-1]
    side_faces = generator._generate_side_faces(vertices, height)
    assert len(side_faces) == 4
    
    # Test SVG generation
    svg_content = generator.generate_net(square, height)
    assert isinstance(svg_content, str)
    assert '<svg' in svg_content
    assert '</svg>' in svg_content


def test_integration_simple():
    """Test integration with a simple SVG."""
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
        <rect x="10" y="10" width="30" height="30" fill="red"/>
        <line x1="10" y1="10" x2="40" y2="10" stroke="black"/>
        <line x1="40" y1="10" x2="40" y2="40" stroke="black"/>
        <line x1="40" y1="40" x2="10" y2="40" stroke="black"/>
        <line x1="10" y1="40" x2="10" y2="10" stroke="black"/>
    </svg>'''
    
    svg_file = create_test_svg(svg_content)
    
    try:
        # Parse SVG
        parser = SVGParser(tolerance=0.1)
        segments = parser.parse_svg(svg_file)
        assert len(segments) > 0
        
        # Detect polygons
        processor = GeometryProcessor(tolerance=0.1)
        polygons = processor.find_polygons(segments)
        
        if polygons:  # Only test if polygons were detected
            # Map colors
            color_mapping = {'red': 1.0, 'blue': 2.0}
            mapper = ColorMapper(color_mapping)
            polygon_heights = mapper.map_polygon_heights(polygons, svg_file)
            
            assert len(polygon_heights) > 0
            
            # Generate net
            generator = NetGenerator()
            for polygon, height in polygon_heights:
                svg_net = generator.generate_net(polygon, height)
                assert isinstance(svg_net, str)
                assert len(svg_net) > 0
    
    finally:
        svg_file.unlink()


if __name__ == "__main__":
    pytest.main([__file__])