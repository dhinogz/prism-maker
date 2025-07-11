# Development Guidelines for Polygon Prism Net Generator

## Project Overview
This project generates 3D prism nets from SVG polygon patterns for paper craft models. The system detects polygons from intersecting line segments, maps colors to heights, and creates printable nets with flaps.

## Development Rules

### Environment Setup
- **Virtual Environment**: Use the existing `.venv` virtual environment
  - Activated with: `source .venv/bin/activate` (macOS/Linux) or `.venv\Scripts\activate` (Windows)
  - Created with: `python3 -m venv .venv`

### Required Libraries
- **CLI Framework**: Use Typer library for all command-line interface functionality
- **Core Dependencies**: 
  - `shapely` - Geometric operations and polygon handling
  - `svgpathtools` - SVG parsing and path manipulation
  - `typer` - CLI framework
  - Additional libraries as needed for computational geometry

### Code Quality Standards
- **Clean Code Practices**: Apply world-class engineering standards
- **Type Hints**: Use comprehensive type annotations
- **Error Handling**: Implement robust error handling and validation
- **Modular Design**: Create well-structured, reusable components
- **Documentation**: Clear docstrings and inline comments where necessary
- **Testing**: Include unit tests for core functionality

### CLI Interface Requirements
- Use Typer for all CLI functionality
- Accept color-height mapping as command-line arguments
- Example usage: `python polygon_prism_nets.py input.svg --colors "red:1,blue:2,green:1.5" --output nets/`

### Project Specifications
- **Input**: SVG files with paths/polylines representing line segments
- **Polygon Detection**: Find enclosed areas from intersecting line segments
- **Tolerance**: Use 0.1 units for intersection detection
- **Polygon Validation**: Maximum 6 sides per polygon, ignore nested polygons
- **Color Mapping**: Extract fill colors, map to heights using RGB interpolation
- **Flap Calculation**: Width = shortest distance from edge midpoint to polygon center ÷ 3
- **Flap Design**: 30° slopes, alternating pattern around perimeter
- **Net Layout**: All side faces connected, only one attached to base
- **Output**: Individual SVG files for each prism net

### File Structure
```
project/
├── .venv/                 # Virtual environment
├── AGENTS.md             # This file
├── TODO.md               # Task tracking
├── requirements.txt      # Dependencies
├── main.py              # CLI entry point
├── src/
│   ├── __init__.py
│   ├── svg_parser.py    # SVG parsing and line extraction
│   ├── geometry.py      # Intersection detection and polygon finding
│   ├── color_mapping.py # Color extraction and height mapping
│   ├── net_generator.py # Prism net generation with flaps
│   └── utils.py         # Utility functions
└── tests/               # Unit tests
```

### Git Workflow
- Commit frequently with descriptive messages
- Follow conventional commit format
- Test before committing

### Performance Considerations
- Optimize for large SVG files with many line segments
- Efficient intersection detection algorithms
- Memory-conscious polygon processing

## Notes for Future Sessions
- Reference this file for development standards
- Update TODO.md as tasks are completed
- Maintain clean, professional code quality throughout development