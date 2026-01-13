from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Dict, Literal

import numpy as np
from manim import *


# ============================================================
# STYLE / CONFIG
# ============================================================

@dataclass
class ShapePropsStyle:
    # geometry visuals
    stroke_width: float = 5.0
    fill_opacity: float = 0.10
    marker_stroke: float = 6.0
    vertex_radius: float = 0.10

    # text
    font_size_title: int = 38
    font_size_main: int = 34
    font_size_small: int = 28

    # pacing
    pause: float = 0.45
    rt_fast: float = 0.7
    rt_norm: float = 1.0
    rt_slow: float = 1.25

    # toggles
    show_angle_markers: bool = True
    show_side_markers: bool = True
    show_vertex_markers: bool = True
    show_comparison_panel: bool = True
    show_classification_step: bool = True

    # layout
    title_y_shift: float = -0.9
    main_shape_pos: np.ndarray = field(default_factory=lambda: np.array([-2.8, 0.2, 0]))
    compare_row_y: float = -2.2
    panel_pos: np.ndarray = field(default_factory=lambda: np.array([4.1, 0.1, 0]))


@dataclass
class ShapeSpec:
    sid: str
    name_en: str
    name_ar: str
    vertices: List[np.ndarray]  # in local coordinates
    fill: bool = True


@dataclass
class LessonConfigM3_G07:
    title_en: str = "Properties of standard geometric shapes"
    title_ar: str = "خاصيات الأشكال الهندسية الاعتيادية"
    domain_en: str = "Geometry"
    domain_ar: str = "الهندسة"
    language: str = "en"

    # prompts (property language)
    p_display_en: str = "Look at the shape."
    p_display_ar: str = "نلاحظ الشكل."

    p_sides_en: str = "Count the sides."
    p_sides_ar: str = "نعد الأضلاع."

    p_vertices_en: str = "Count the vertices."
    p_vertices_ar: str = "نعد الرؤوس."

    p_angles_en: str = "Highlight the angles (corners)."
    p_angles_ar: str = "نبرز الزوايا (الأركان)."

    p_compare_en: str = "Compare shapes by properties."
    p_compare_ar: str = "نقارن الأشكال حسب الخاصيات."

    p_classify_en: str = "Classify: same properties → same family."
    p_classify_ar: str = "نصنف: نفس الخاصيات → نفس العائلة."

    shapes: List[ShapeSpec] = field(default_factory=lambda: [
        ShapeSpec(
            sid="triangle",
            name_en="Triangle",
            name_ar="مثلث",
            vertices=[
                np.array([0.0, 1.6, 0]),
                np.array([-1.4, -1.0, 0]),
                np.array([1.4, -1.0, 0]),
            ],
        ),
        ShapeSpec(
            sid="square",
            name_en="Square",
            name_ar="مربع",
            vertices=[
                np.array([-1.2, 1.2, 0]),
                np.array([1.2, 1.2, 0]),
                np.array([1.2, -1.2, 0]),
                np.array([-1.2, -1.2, 0]),
            ],
        ),
        ShapeSpec(
            sid="rectangle",
            name_en="Rectangle",
            name_ar="مستطيل",
            vertices=[
                np.array([-1.8, 1.1, 0]),
                np.array([1.8, 1.1, 0]),
                np.array([1.8, -1.1, 0]),
                np.array([-1.8, -1.1, 0]),
            ],
        ),
        ShapeSpec(
            sid="pentagon",
            name_en="Pentagon",
            name_ar="خماسي",
            vertices=[
                np.array([0.0, 1.7, 0]),
                np.array([-1.6, 0.5, 0]),
                np.array([-1.0, -1.4, 0]),
                np.array([1.0, -1.4, 0]),
                np.array([1.6, 0.5, 0]),
            ],
        ),
    ])


# ============================================================
# HELPERS
# ============================================================

def T(cfg: LessonConfigM3_G07, s: ShapePropsStyle, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
    txt = en if cfg.language == "en" else (ar or en)
    return Text(txt, font_size=s.font_size_main).scale(scale)


def polygon_from_spec(spec: ShapeSpec, style: ShapePropsStyle) -> Polygon:
    poly = Polygon(*spec.vertices)
    poly.set_stroke(width=style.stroke_width)
    if spec.fill:
        poly.set_fill(opacity=style.fill_opacity)
    return poly


def side_segments(poly: Polygon) -> List[Line]:
    pts = poly.get_vertices()
    segs: List[Line] = []
    for i in range(len(pts)):
        a = pts[i]
        b = pts[(i + 1) % len(pts)]
        segs.append(Line(a, b))
    return segs


def vertex_dots(poly: Polygon, style: ShapePropsStyle) -> VGroup:
    dots = VGroup()
    for v in poly.get_vertices():
        dots.add(Dot(v, radius=style.vertex_radius))
    return dots


def side_markers(poly: Polygon, style: ShapePropsStyle) -> VGroup:
    """
    Put a small tick on each side (centered, perpendicular).
    """
    marks = VGroup()
    for seg in side_segments(poly):
        mid = seg.get_center()
        # perpendicular small tick
        d = seg.get_unit_vector()
        perp = np.array([-d[1], d[0], 0])
        tick = Line(mid - 0.12 * perp, mid + 0.12 * perp, stroke_width=style.marker_stroke)
        tick.set_opacity(0.7)
        marks.add(tick)
    return marks


def angle_markers(poly: Polygon, style: ShapePropsStyle) -> VGroup:
    """
    Use Angle mobject between consecutive edges at each vertex.
    """
    pts = poly.get_vertices()
    m = VGroup()
    n = len(pts)
    for i in range(n):
        prev = pts[(i - 1) % n]
        cur = pts[i]
        nxt = pts[(i + 1) % n]
        l1 = Line(cur, prev)
        l2 = Line(cur, nxt)
        ang = Angle(l1, l2, radius=0.35, other_angle=False, stroke_width=style.marker_stroke)
        ang.set_opacity(0.75)
        m.add(ang)
    return m


def property_panel(shape_name: str, sides: int, vertices: int) -> VGroup:
    box = RoundedRectangle(width=4.9, height=2.4, corner_radius=0.25).set_stroke(width=3).set_fill(opacity=0.06)
    t1 = Text(f"Name: {shape_name}", font_size=28).scale(0.55)
    t2 = Text(f"Sides: {sides}", font_size=28).scale(0.55)
    t3 = Text(f"Vertices: {vertices}", font_size=28).scale(0.55)
    col = VGroup(t1, t2, t3).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to(box.get_center())
    return VGroup(box, col)


def classification_strip(items: List[Tuple[str, int, int]], style: ShapePropsStyle) -> VGroup:
    """
    A tiny “table-like” strip: name | sides | vertices.
    """
    header = Text("Shape   | sides | vertices", font_size=style.font_size_small).scale(0.48)
    rows = VGroup()
    for name, s, v in items:
        rows.add(Text(f"{name:<8} |  {s:<2}   |   {v:<2}", font_size=style.font_size_small).scale(0.45))
    rows.arrange(DOWN, aligned_edge=LEFT, buff=0.10)
    group = VGroup(header, rows).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    box = RoundedRectangle(width=6.3, height=2.7, corner_radius=0.25).set_stroke(width=3).set_fill(opacity=0.06)
    group.move_to(box.get_center())
    return VGroup(box, group)


# ============================================================
# MAIN SCENE
# ============================================================

class M3_G07_StandardShapes_Properties(Scene):
    """
    M3_G07 — Properties of standard geometric shapes
      display shape → highlight sides → highlight angles → compare with others → classify by invariants
    """

    def __init__(
        self,
        cfg: LessonConfigM3_G07 = LessonConfigM3_G07(),
        style: ShapePropsStyle = ShapePropsStyle(),
        **kwargs
    ):
        super().__init__(**kwargs)
        self.cfg = cfg
        self.s = style

    def banner(self, mob: Mobject) -> Mobject:
        mob.to_edge(UP)
        return mob

    def construct(self):
        # intro
        title = T(self.cfg, self.s, self.cfg.title_en, self.cfg.title_ar, scale=0.58)
        title = self.banner(title)
        self.play(Write(title), run_time=self.s.rt_norm)
        self.title = title

        # cycle through shapes: observe → count sides/vertices → highlight angles
        summary: List[Tuple[str, int, int]] = []
        for spec in self.cfg.shapes:
            summary.append(self.show_shape_properties(spec))

        # comparison + classification
        self.compare_and_classify(summary)

        self.play(FadeOut(self.title), run_time=self.s.rt_fast)

    # ============================================================
    # Core steps per shape
    # ============================================================

    def show_shape_properties(self, spec: ShapeSpec) -> Tuple[str, int, int]:
        # prompt: display
        prompt = T(self.cfg, self.s, self.cfg.p_display_en, self.cfg.p_display_ar, scale=0.54)
        prompt = self.banner(prompt).shift(DOWN * self.s.title_y_shift)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        poly = polygon_from_spec(spec, self.s)
        poly.move_to(self.s.main_shape_pos)

        name = spec.name_en if self.cfg.language == "en" else spec.name_ar
        label = Text(name, font_size=self.s.font_size_small).scale(0.62).next_to(poly, UP, buff=0.25)

        self.play(Create(poly), FadeIn(label, shift=UP * 0.05), run_time=self.s.rt_norm)

        n_sides = len(poly.get_vertices())
        n_vertices = n_sides

        # highlight sides (counting)
        if self.s.show_side_markers:
            prompt2 = T(self.cfg, self.s, self.cfg.p_sides_en, self.cfg.p_sides_ar, scale=0.54)
            prompt2 = self.banner(prompt2).shift(DOWN * self.s.title_y_shift)
            self.play(Transform(self.title, prompt2), run_time=self.s.rt_fast)

            segs = VGroup(*[Line(sg.get_start(), sg.get_end()).set_stroke(width=self.s.stroke_width + 2) for sg in side_segments(poly)])
            # animate one by one: “count”
            counter = Text(f"0", font_size=self.s.font_size_main).scale(0.7).move_to(self.s.panel_pos + np.array([0, 1.4, 0]))
            self.play(FadeIn(counter), run_time=self.s.rt_fast)
            for i, seg in enumerate(segs, start=1):
                self.play(Create(seg), run_time=0.22)
                new_counter = Text(f"{i}", font_size=self.s.font_size_main).scale(0.7).move_to(counter.get_center())
                self.play(Transform(counter, new_counter), run_time=0.15)
            marks = side_markers(poly, self.s)
            self.play(FadeIn(marks, shift=UP * 0.03), run_time=self.s.rt_fast)
            self.wait(0.15)
        else:
            marks = VGroup()
            segs = VGroup()
            counter = VGroup()

        # vertices
        if self.s.show_vertex_markers:
            prompt3 = T(self.cfg, self.s, self.cfg.p_vertices_en, self.cfg.p_vertices_ar, scale=0.54)
            prompt3 = self.banner(prompt3).shift(DOWN * self.s.title_y_shift)
            self.play(Transform(self.title, prompt3), run_time=self.s.rt_fast)

            vdots = vertex_dots(poly, self.s)
            self.play(FadeIn(vdots, shift=UP * 0.03), run_time=self.s.rt_fast)
        else:
            vdots = VGroup()

        # angles
        if self.s.show_angle_markers:
            prompt4 = T(self.cfg, self.s, self.cfg.p_angles_en, self.cfg.p_angles_ar, scale=0.54)
            prompt4 = self.banner(prompt4).shift(DOWN * self.s.title_y_shift)
            self.play(Transform(self.title, prompt4), run_time=self.s.rt_fast)

            angs = angle_markers(poly, self.s)
            self.play(FadeIn(angs), run_time=self.s.rt_norm)
        else:
            angs = VGroup()

        # property panel
        panel = property_panel(shape_name=name, sides=n_sides, vertices=n_vertices)
        panel.move_to(self.s.panel_pos)
        self.play(FadeIn(panel, shift=UP * 0.08), run_time=self.s.rt_norm)

        self.wait(0.35)

        # cleanup current shape objects
        self.play(
            FadeOut(VGroup(panel, angs, vdots, marks, segs, counter, label)),
            FadeOut(poly),
            run_time=self.s.rt_fast
        )

        return (name, n_sides, n_vertices)

    # ============================================================
    # Comparison / classification
    # ============================================================

    def compare_and_classify(self, summary: List[Tuple[str, int, int]]):
        # prompt compare
        prompt = T(self.cfg, self.s, self.cfg.p_compare_en, self.cfg.p_compare_ar, scale=0.54)
        prompt = self.banner(prompt).shift(DOWN * self.s.title_y_shift)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        # show small shapes row
        minis = VGroup()
        for spec in self.cfg.shapes:
            poly = polygon_from_spec(spec, self.s).scale(0.32)
            nm = spec.name_en if self.cfg.language == "en" else spec.name_ar
            lbl = Text(nm, font_size=self.s.font_size_small).scale(0.40).next_to(poly, DOWN, buff=0.12)
            minis.add(VGroup(poly, lbl))

        minis.arrange(RIGHT, buff=0.7).move_to(np.array([0, self.s.compare_row_y, 0]))
        self.play(FadeIn(minis, shift=UP * 0.08), run_time=self.s.rt_norm)

        # classification strip (table-like)
        if self.s.show_classification_step:
            prompt2 = T(self.cfg, self.s, self.cfg.p_classify_en, self.cfg.p_classify_ar, scale=0.54)
            prompt2 = self.banner(prompt2).shift(DOWN * self.s.title_y_shift)
            self.play(Transform(self.title, prompt2), run_time=self.s.rt_fast)

            strip = classification_strip(summary, self.s)
            strip.move_to(np.array([0, 0.5, 0]))
            self.play(FadeIn(strip, shift=UP * 0.08), run_time=self.s.rt_norm)

            # highlight invariant idea: same #sides => family
            # quick glow around each row
            rows = strip[1][1]  # box -> group(header, rows) -> rows
            for i in range(len(summary)):
                self.play(rows[i].animate.set_opacity(0.35), run_time=0.2)
                self.play(rows[i].animate.set_opacity(1.0), run_time=0.2)

            self.wait(0.35)
            self.play(FadeOut(strip), run_time=self.s.rt_fast)

        self.play(FadeOut(minis), run_time=self.s.rt_fast)


# ============================================================
# RUN:
#   manim -pqh your_file.py M3_G07_StandardShapes_Properties
#
# EXTEND:
#   - Add more ShapeSpec entries (hexagon, rhombus, etc.).
#   - Add more properties (equal sides markers, right-angle markers) by extending
#     side_markers() and angle_markers(), then adding a "special property" step.
# ============================================================
