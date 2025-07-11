# TODO List - Polygon Prism Net Generator

## Project Status
**Current Phase**: Documentation and Setup  
**Last Updated**: July 11, 2025

## High Priority Tasks

### ✅ Documentation
- [x] Create AGENTS.md with development rules and guidelines
- [ ] Create TODO.md with current task list *(IN PROGRESS)*

### 🔧 Project Setup
- [ ] Update project setup to use Typer for CLI and .venv virtual environment
- [ ] Set up project structure and dependencies (shapely, svgpathtools, typer, etc.)

### 🎯 Core Implementation
- [ ] Implement SVG parser to extract line segments from paths/polylines
- [ ] Build intersection detection with tolerance (0.1 units)
- [ ] Implement polygon detection from intersecting line segments

## Medium Priority Tasks

### 🔍 Polygon Processing
- [ ] Add polygon validation (≤6 sides, ignore nested polygons)
- [ ] Extract fill colors from detected polygons
- [ ] Implement RGB color interpolation for height mapping

### 📐 Net Generation
- [ ] Calculate flap dimensions (shortest midpoint-to-center distance ÷ 3)
- [ ] Implement CLI interface with Typer and color-height mapping arguments
- [ ] Output final nets as SVG files

### 🏗️ Advanced Features
- [ ] Generate prism nets with alternating flap pattern and 30° slopes

## Low Priority Tasks

### 🧪 Quality Assurance
- [ ] Add testing and validation

## Technical Specifications

### Input Requirements
- SVG files with paths/polylines representing line segments
- Color-height mapping via CLI arguments
- Example: `python main.py input.svg --colors "red:1,blue:2,green:1.5" --output nets/`

### Processing Pipeline
1. **SVG Parsing** → Extract line segments from paths/polylines
2. **Intersection Detection** → Find intersection points with 0.1 unit tolerance
3. **Polygon Detection** → Identify enclosed areas from intersecting segments
4. **Color Extraction** → Get fill colors from original SVG polygons
5. **Height Mapping** → Map colors to Z values using RGB interpolation
6. **Net Generation** → Create unfolded prism nets with flaps

### Output Specifications
- Individual SVG files for each prism net
- Flap width: shortest distance from polygon edge midpoint to center ÷ 3
- Flap angle: 30° slopes for better gluing
- Flap pattern: alternating around perimeter
- Net layout: all side faces connected, only one attached to base

### Dependencies
- `typer` - CLI framework
- `shapely` - Geometric operations
- `svgpathtools` - SVG parsing
- `numpy` - Numerical computations
- Additional libraries as needed

## Development Notes
- Use existing `.venv` virtual environment
- Follow clean code practices with type hints
- Implement robust error handling
- Create modular, testable components
- Reference AGENTS.md for detailed development guidelines

## Completed Tasks
- ✅ Project planning and requirements gathering
- ✅ Development guidelines documentation