#!/usr/bin/env python3
"""
Polygon Prism Net Generator

Generates 3D prism nets from SVG polygon patterns for paper craft models.
"""

import typer
from pathlib import Path
from typing import Optional, Dict
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.svg_parser import SVGParser
from src.geometry import GeometryProcessor
from src.color_mapping import ColorMapper
from src.net_generator import NetGenerator

app = typer.Typer(help="Generate 3D prism nets from SVG polygon patterns")
console = Console()


def parse_color_mapping(colors_str: str) -> Dict[str, float]:
    """Parse color-height mapping from CLI string format."""
    color_map = {}
    for pair in colors_str.split(','):
        color, height = pair.strip().split(':')
        color_map[color.strip()] = float(height.strip())
    return color_map


@app.command()
def generate(
    input_file: Path = typer.Argument(..., help="Input SVG file path"),
    colors: str = typer.Option(..., help="Color-height mapping (e.g., 'red:1,blue:2,green:1.5')"),
    output_dir: Optional[Path] = typer.Option("nets", help="Output directory for generated nets"),
    tolerance: float = typer.Option(0.1, help="Intersection detection tolerance"),
) -> None:
    """Generate prism nets from SVG polygon patterns."""
    
    if not input_file.exists():
        console.print(f"[red]Error: Input file {input_file} does not exist[/red]")
        raise typer.Exit(1)
    
    if not input_file.suffix.lower() == '.svg':
        console.print(f"[red]Error: Input file must be an SVG file[/red]")
        raise typer.Exit(1)
    
    try:
        color_mapping = parse_color_mapping(colors)
    except ValueError as e:
        console.print(f"[red]Error parsing color mapping: {e}[/red]")
        console.print("[yellow]Expected format: 'red:1,blue:2,green:1.5'[/yellow]")
        raise typer.Exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Parse SVG
        task = progress.add_task("Parsing SVG file...", total=None)
        parser = SVGParser(tolerance=tolerance)
        line_segments = parser.parse_svg(input_file)
        progress.update(task, description=f"Found {len(line_segments)} line segments")
        
        # Detect polygons
        task = progress.add_task("Detecting polygons...", total=None)
        geometry_processor = GeometryProcessor(tolerance=tolerance)
        polygons = geometry_processor.find_polygons(line_segments)
        progress.update(task, description=f"Detected {len(polygons)} polygons")
        
        # Map colors to heights
        task = progress.add_task("Mapping colors to heights...", total=None)
        color_mapper = ColorMapper(color_mapping)
        polygon_heights = color_mapper.map_polygon_heights(polygons, input_file)
        progress.update(task, description=f"Mapped heights for {len(polygon_heights)} polygons")
        
        # Generate nets
        task = progress.add_task("Generating prism nets...", total=None)
        net_generator = NetGenerator()
        generated_count = 0
        
        for i, (polygon, height) in enumerate(polygon_heights):
            net_svg = net_generator.generate_net(polygon, height)
            output_file = output_dir / f"prism_net_{i+1}.svg"
            
            with open(output_file, 'w') as f:
                f.write(net_svg)
            
            generated_count += 1
        
        progress.update(task, description=f"Generated {generated_count} prism nets")
    
    console.print(f"[green]✓ Successfully generated {generated_count} prism nets in {output_dir}[/green]")


if __name__ == "__main__":
    app()