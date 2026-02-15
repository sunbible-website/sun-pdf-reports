from pathlib import Path
from svglib.svglib import svg2rlg
from reportlab.platypus import Spacer
from pathlib import Path
from reportlab.lib.units import inch
import os

def load_svg(svg_path: Path, max_height=None, max_width=None):
    """
    Load and optionally scale an SVG drawing.
    """
    if not Path(svg_path).exists():
        raise FileNotFoundError(f"{svg_path} does not exist")

    drawing = svg2rlg(str(svg_path))  # convert Path to string for svglib
    if max_height is not None:
        # scale proportionally
        scale = max_height / drawing.height
        drawing.width *= scale
        drawing.height *= scale
        for obj in drawing.contents:
            obj.scale(scale, scale)
    
    return drawing

def boost_strokes(drawing, min_stroke=1.2):
    """
    Ensure SVG strokes are thick enough for printing.
    """
    for elem in drawing.contents:
        if hasattr(elem, "strokeWidth") and elem.strokeWidth:
            elem.strokeWidth = max(elem.strokeWidth, min_stroke)
        if hasattr(elem, "contents"):
            boost_strokes(elem, min_stroke)

def small_svg_for_word(word, word_to_svg, svg_folder, size=0.25 * inch):
    svg_filename = word_to_svg.get(word.lower())
    if not svg_filename:
        return Spacer(1, size)

    svg_path = os.path.join(svg_folder, svg_filename)
    if not os.path.exists(svg_path):
        return Spacer(1, size)

    drawing = svg2rlg(svg_path)
    scale = min(size / drawing.width, size / drawing.height)
    drawing.scale(scale, scale)
    drawing.width *= scale
    drawing.height *= scale
    return drawing
