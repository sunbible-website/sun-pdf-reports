from reportlab.graphics import renderPDF
from reportlab.platypus import Flowable
import os
from svglib.svglib import svg2rlg
from reportlab.lib.units import inch

class SvgAndWordHeader(Flowable):
    """Flowable to display an SVG and a word (section + subsection) side by side"""
    def __init__(self, svg_path, word, max_height=0.4*inch):
        super().__init__()
        self.word = word
        self.max_height = max_height
        self.drawing = None
        if os.path.exists(svg_path):
            self.drawing = svg2rlg(svg_path)
            if self.drawing.height > 0:
                scale = min(max_height / self.drawing.height, 1)
                self.drawing.width *= scale
                self.drawing.height *= scale
                self.drawing.scale(scale, scale)

    def wrap(self, availWidth, availHeight):
        return availWidth, self.max_height

    def draw(self):
        x_offset = 0
        if self.drawing:
            renderPDF.draw(self.drawing, self.canv, 0, 0)
            x_offset = self.drawing.width + 5  # space between symbol and text
        self.canv.setFont("Helvetica-Bold", 12)
        self.canv.drawString(x_offset, 0, self.word)