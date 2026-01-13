from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Dict

import numpy as np
from manim import *


# ============================================================
# CONFIG / STYLES
# ============================================================

@dataclass
class PerimeterStyle:
    stroke_width: float = 4.0
    fill_opacity: float = 0.10

    # tracing
    tracer_radius: float = 0.08
    trace_run_time: float = 1.0
    highlight_run_time: float = 0.45

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
    show_arabic: bool = False  # enable only if Arabic fonts render correctly
    show_string_metaphor: bool = True  # “wrap string around shape”
    show_area_contrast: bool = True    # clarify perimeter vs area
    show_units: str = "cm"             # unit label for side lengths, "cm" or "m"

    # layout
    show_sum_panel: bool = True
    sum_panel_width: float = 6.0
    sum_panel_height: float = 2.6


@dataclass
class ShapeSpec:
    """
    Standard shapes with known side lengths (in chosen units).
    For grade 3: keep it simple and explicit.
    """
    kind: str  # "square" | "rectangle" | "triangle"
    # side lengths (in units): square uses a; rectangle uses w,h; triangle uses a,b,c
    a: float = 4.0
    b: float = 0.0
    c: float = 0.0
    label: str = ""


@dataclass
class LessonConfigM3_L15:
    title_en: str = "Identifying perimeters of standard geometric shapes"
    title_ar: str = "تعرف محيطات الأشكال الهندسية الاعتيادية"
    language: str = "en"  # "en" | "ar"

    # prompts
    prompt_trace_en: str = "Perimeter is the length around the shape."
    prompt_trace_ar: str = "المحيط هو الطول حول الشكل."

    prompt_follow_en: str = "Let’s trace the contour side by side."
    prompt_follow_ar: str = "لنَتْبَعْ حدود الشكل ضلعاً ضلعاً."

    prompt_add_en: str = "We add the side lengths."
    prompt_add_ar: str = "نجمع أطوال الأضلاع."

    prompt_total_en: str = "Total perimeter:"
    prompt_total_ar: str = "المحيط الكلي:"

    prompt_not_area_en: str = "Perimeter is NOT the filled area."
    prompt_not_area_ar: str = "المحيط ليس هو المساحة المظللة."

    # default shapes
    shapes: List[ShapeSpec] = field(default_factory=lambda: [
        ShapeSpec(kind="square", a=4, label="Square (4,4,4,4)"),
        ShapeSpec(kind="rectangle", a=6, b=3, label="Rectangle (6,3)"),
        ShapeSpec(kind="triangle", a=3, b=4, c=5, label="Triangle (3,4,5)"),
    ])


# ============================================================
# REUSABLE PRIMITIVES
# ============================================================

def T(cfg: LessonConfigM3_L15, s: PerimeterStyle, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
    txt = en if cfg.language == "en" else (ar or en)
    return Text(txt, font_size=s.font_size_main).scale(scale)


def perimeter_tex(symbol: str = "P", expr: str = "", scale: float = 1.1) -> Mobject:
    if expr:
        return MathTex(rf"{symbol} = {expr}").scale(scale)
    return MathTex(rf"{symbol} = \ ?").scale(scale)


def add_chain_tex(values: List[float], unit: str, scale: float = 1.1) -> Mobject:
    # show: a + b + c = total (unit)
    expr = " + ".join(str(int(v)) if float(v).is_integer() else str(v) for v in values)
    total = sum(values)
    total_str = str(int(total)) if float(total).is_integer() else str(total)
    return MathTex(rf"{expr} = {total_str}\ \text{{{unit}}}").scale(scale)


class SumPanel(VGroup):
    def __init__(self, style: PerimeterStyle, **kwargs):
        super().__init__(**kwargs)
        box = RoundedRectangle(width=style.sum_panel_width, height=style.sum_panel_height, corner_radius=0.25)
        box.set_stroke(width=3).set_fill(opacity=0.06)
        self.box = box
        self.add(box)

    def place(self) -> "SumPanel":
        self.to_edge(RIGHT).shift(DOWN * 0.1)
        return self


class PerimeterTracer(VGroup):
    """
    A dot moving along edges + a path.
    """
    def __init__(self, style: PerimeterStyle, **kwargs):
        super().__init__(**kwargs)
        dot = Dot(radius=style.tracer_radius)
        self.dot = dot
        self.add(dot)

    def move_to_point(self, p: np.ndarray):
        self.dot.move_to(p)
        return self


def make_shape(spec: ShapeSpec, style: PerimeterStyle) -> Mobject:
    """
    Create a standard shape using Polygon so we can get edges precisely.
    Coordinates are in "manim units" (not cm). We keep lengths proportional,
    and display side lengths as labels (cm/m).
    """
    if spec.kind == "square":
        a = spec.a
        # scale down to fit screen: map length a -> visual a*0.4
        k = 0.45
        A = a * k
        pts = [
            np.array([-A/2, -A/2, 0]),
            np.array([ A/2, -A/2, 0]),
            np.array([ A/2,  A/2, 0]),
            np.array([-A/2,  A/2, 0]),
        ]
        poly = Polygon(*pts).set_stroke(width=style.stroke_width).set_fill(opacity=0.0)
        return poly

    if spec.kind == "rectangle":
        w, h = spec.a, spec.b
        k = 0.42
        W = w * k
        H = h * k
        rect = Rectangle(width=W, height=H).set_stroke(width=style.stroke_width).set_fill(opacity=0.0)
        return rect

    # triangle
    a, b, c = spec.a, spec.b, spec.c
    # build a simple triangle (not geometrically exact by sides, but stable for tracing);
    # we still DISPLAY the given side lengths as labels and sum them.
    k = 0.42
    base = c * k
    height = b * k  # just a visually reasonable height
    pts = [
        np.array([-base/2, -height/2, 0]),
        np.array([ base/2, -height/2, 0]),
        np.array([ 0,       height/2, 0]),
    ]
    tri = Polygon(*pts).set_stroke(width=style.stroke_width).set_fill(opacity=0.0)
    return tri


def edges_of_polygon(shape: Mobject) -> List[Line]:
    """
    Extract edges as Lines for Polygon/Rectangle.
    """
    if isinstance(shape, Rectangle):
        # rectangle points are in shape.get_vertices()
        verts = shape.get_vertices()
    else:
        # Polygon has get_vertices
        verts = shape.get_vertices()

    lines: List[Line] = []
    for i in range(len(verts)):
        a = verts[i]
        b = verts[(i + 1) % len(verts)]
        lines.append(Line(a, b))
    return lines


def side_length_labels(edges: List[Line], values: List[float], unit: str, style: PerimeterStyle) -> VGroup:
    """
    Put length labels near each edge (with small offset outward).
    """
    labels = VGroup()
    for edge, val in zip(edges, values):
        mid = edge.get_center()
        # offset outward: rotate edge direction and normalize
        v = edge.get_end() - edge.get_start()
        perp = np.array([-v[1], v[0], 0.0])
        if np.linalg.norm(perp) > 1e-6:
            perp = perp / np.linalg.norm(perp)
        offset = perp * 0.28

        txt = Text(f"{int(val) if float(val).is_integer() else val} {unit}", font_size=style.font_size_small).scale(0.7)
        txt.move_to(mid + offset)
        labels.add(txt)
    return labels


# ============================================================
# LESSON SCENE (Reusable / Adjustable / Extensible)
# ============================================================

class M3_L15_PerimeterOfStandardShapes(Scene):
    """
    M3_L15 — Perimeter of standard shapes

    Flow:
      display_shape
      animate_tracing_along_each_side (one after another)
      highlight_each_side_when_traced
      display_length_of_each_side
      accumulate_lengths progressively
      reveal total perimeter at the end

    Avoid:
      formula-first, confusing area with perimeter, numbers w/out tracing motion
    """

    def __init__(
        self,
        cfg: LessonConfigM3_L15 = LessonConfigM3_L15(),
        style: PerimeterStyle = PerimeterStyle(),
        **kwargs
    ):
        super().__init__(**kwargs)
        self.cfg = cfg
        self.s = style
        self.steps: List[Tuple[str, Callable[[], None]]] = []

    # ----------------------------
    # Orchestrator
    # ----------------------------

    def construct(self):
        self.build_steps()
        for _, fn in self.steps:
            fn()
            self.wait(self.s.pause)

    def build_steps(self):
        self.steps = [
            ("intro", self.step_intro),
            ("exploration_trace", self.step_exploration_trace),
            ("collective_discussion_perimeter_vs_area", self.step_collective_discussion_perimeter_vs_area),
            ("institutionalization_notation", self.step_institutionalization_notation),
            ("mini_assessment", self.step_mini_assessment),
            ("outro", self.step_outro),
        ]

    # ----------------------------
    # Helpers
    # ----------------------------

    def banner(self, mob: Mobject) -> Mobject:
        mob.to_edge(UP)
        return mob

    def step_intro(self):
        title = T(self.cfg, self.s, self.cfg.title_en, self.cfg.title_ar, scale=0.62)
        title = self.banner(title)

        subtitle = T(
            self.cfg, self.s,
            "We measure the boundary (around), not the inside.",
            "نقيس الحدود (حول الشكل)، وليس الداخل.",
            scale=0.52
        ).next_to(title, DOWN, buff=0.18)

        self.play(Write(title), FadeIn(subtitle, shift=DOWN * 0.15), run_time=self.s.rt_norm)
        self.wait(0.2)
        self.play(FadeOut(subtitle, shift=UP * 0.1), run_time=self.s.rt_fast)
        self.title = title

    # ------------------------------------------------------------
    # Core perimeter demo for one shape
    # ------------------------------------------------------------

    def get_side_values(self, spec: ShapeSpec, n_edges: int) -> List[float]:
        if spec.kind == "square":
            return [spec.a] * n_edges
        if spec.kind == "rectangle":
            # rectangle edges order: w, h, w, h
            return [spec.a, spec.b, spec.a, spec.b]
        # triangle
        return [spec.a, spec.b, spec.c]

    def trace_shape_and_sum(self, spec: ShapeSpec) -> VGroup:
        """
        Display shape, trace each edge sequentially, accumulate sum, reveal perimeter.
        """
        unit = self.s.show_units

        # prompts
        p = T(self.cfg, self.s, self.cfg.prompt_trace_en, self.cfg.prompt_trace_ar, scale=0.56)
        p = self.banner(p).shift(DOWN * 0.9)
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        shape = make_shape(spec, self.s).move_to(LEFT * 2.8 + DOWN * 0.1)
        name = Text(spec.label or spec.kind.title(), font_size=self.s.font_size_small).scale(0.75)
        name.next_to(shape, UP, buff=0.35)

        self.play(Create(shape), FadeIn(name, shift=UP * 0.1), run_time=self.s.rt_norm)

        edges = edges_of_polygon(shape)
        vals = self.get_side_values(spec, len(edges))
        labels = side_length_labels(edges, vals, unit, self.s)

        # Sum panel
        panel = SumPanel(self.s).place() if self.s.show_sum_panel else VGroup()
        self.play(FadeIn(panel, shift=LEFT * 0.1), run_time=self.s.rt_fast)

        # optional "string" metaphor: show a path hugging the boundary
        string_hint = VGroup()
        if self.s.show_string_metaphor:
            string = VMobject().set_stroke(width=6, opacity=0.20)
            string.set_points_as_corners([edges[0].get_start(), edges[0].get_end()])
            string_hint = Text("string", font_size=self.s.font_size_small).scale(0.65).next_to(shape, DOWN, buff=0.35)
            self.play(FadeIn(string_hint, shift=UP * 0.1), run_time=self.s.rt_fast)

        # Show side labels (but not the sum yet)
        self.play(FadeIn(labels, shift=UP * 0.05), run_time=self.s.rt_norm)

        # Follow contour step by step
        p2 = T(self.cfg, self.s, self.cfg.prompt_follow_en, self.cfg.prompt_follow_ar, scale=0.56)
        p2 = self.banner(p2).shift(DOWN * 0.9)
        self.play(Transform(self.title, p2), run_time=self.s.rt_fast)

        tracer = PerimeterTracer(self.s).move_to_point(edges[0].get_start())
        self.play(FadeIn(tracer, shift=UP * 0.05), run_time=self.s.rt_fast)

        # Accumulation text inside panel
        running_vals: List[float] = []
        running_tex: Optional[Mobject] = None

        for i, (edge, v) in enumerate(zip(edges, vals)):
            # highlight current side
            hi = edge.copy().set_stroke(width=self.s.stroke_width + 3, opacity=1.0)
            self.play(Create(hi), run_time=self.s.highlight_run_time)

            # animate tracing along the edge
            path = edge.copy()
            self.play(MoveAlongPath(tracer.dot, path), run_time=self.s.trace_run_time, rate_func=linear)

            # update running sum
            running_vals.append(v)
            new_tex = add_chain_tex(running_vals, unit, scale=1.0)
            new_tex.move_to(panel.get_center())

            if running_tex is None:
                running_tex = new_tex
                self.play(Write(running_tex), run_time=self.s.rt_fast)
            else:
                self.play(Transform(running_tex, new_tex), run_time=self.s.rt_fast)

            self.play(FadeOut(hi), run_time=self.s.rt_fast)

        # reveal total perimeter label
        p3 = T(self.cfg, self.s, self.cfg.prompt_total_en, self.cfg.prompt_total_ar, scale=0.56)
        p3 = self.banner(p3).shift(DOWN * 0.9)
        self.play(Transform(self.title, p3), run_time=self.s.rt_fast)

        total = sum(vals)
        total_str = str(int(total)) if float(total).is_integer() else str(total)
        total_label = MathTex(rf"P = {total_str}\ \text{{{unit}}}").scale(1.25)
        total_label.next_to(panel, DOWN, buff=0.25).align_to(panel, LEFT)

        self.play(Write(total_label), run_time=self.s.rt_norm)

        group = VGroup(shape, name, labels, tracer, panel, running_tex, total_label, string_hint)
        return group

    # ============================================================
    # Steps
    # ============================================================

    def step_exploration_trace(self):
        """
        Exploration: trace boundary with motion; discover measurable length.
        """
        for spec in self.cfg.shapes[:2]:
            g = self.trace_shape_and_sum(spec)
            self.wait(0.4)
            self.play(FadeOut(g), run_time=self.s.rt_fast)

    def step_collective_discussion_perimeter_vs_area(self):
        """
        Discussion: perimeter vs area; perimeter depends on side lengths, not filled surface.
        """
        prompt = T(
            self.cfg, self.s,
            "Discussion: Perimeter vs Area",
            "نقاش: المحيط والمساحة",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        box = RoundedRectangle(width=11.6, height=2.9, corner_radius=0.25).to_edge(DOWN).shift(UP * 0.2)
        box.set_fill(opacity=0.06).set_stroke(width=3)

        l1 = T(self.cfg, self.s, "• Perimeter = length around (boundary).", "• المحيط = الطول حول الشكل (الحدود).", scale=0.52)
        l2 = T(self.cfg, self.s, "• Area = surface inside.", "• المساحة = السطح داخل الشكل.", scale=0.52)
        l3 = T(self.cfg, self.s, "• A big area can still have smaller perimeter (and vice versa).", "• قد تكون المساحة كبيرة لكن المحيط أصغر (والعكس).", scale=0.52)
        scaff = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(box.get_center())

        self.play(Create(box), FadeIn(scaff, shift=UP * 0.1), run_time=self.s.rt_norm)

        if self.s.show_area_contrast:
            # quick contrast: same perimeter-ish, different area (purely visual reminder)
            r1 = Rectangle(width=3.2, height=1.6).set_stroke(width=4).set_fill(opacity=0.18)
            r2 = Rectangle(width=2.4, height=2.2).set_stroke(width=4).set_fill(opacity=0.18)
            demo = VGroup(r1, r2).arrange(RIGHT, buff=0.6).move_to(LEFT * 2.8 + UP * 0.2)
            tag = T(self.cfg, self.s, self.cfg.prompt_not_area_en, self.cfg.prompt_not_area_ar, scale=0.52)
            tag.next_to(demo, DOWN, buff=0.25)

            self.play(FadeIn(demo, shift=UP * 0.05), FadeIn(tag, shift=UP * 0.05), run_time=self.s.rt_norm)
            self.wait(0.5)
            self.play(FadeOut(VGroup(demo, tag)), run_time=self.s.rt_fast)

        self.play(FadeOut(VGroup(box, scaff)), run_time=self.s.rt_fast)

    def step_institutionalization_notation(self):
        """
        Institutionalization: introduce term 'perimeter' and notation P = ...
        """
        prompt = T(
            self.cfg, self.s,
            "Institutionalization: Perimeter (P)",
            "التثبيت: المحيط (P)",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        rule = MathTex(r"P = \text{sum of side lengths}").scale(1.25).move_to(UP * 0.3)
        ex = MathTex(r"\text{Example: } P = 4 + 4 + 4 + 4").scale(1.05).next_to(rule, DOWN, buff=0.3)

        self.play(Write(rule), run_time=self.s.rt_norm)
        self.play(Write(ex), run_time=self.s.rt_norm)
        self.wait(0.5)
        self.play(FadeOut(VGroup(rule, ex)), run_time=self.s.rt_fast)

    def step_mini_assessment(self):
        """
        Formative: trace and compute perimeter of a triangle (3,4,5).
        """
        prompt = T(
            self.cfg, self.s,
            "Mini-check: Find the perimeter.",
            "تحقق صغير: أوجد المحيط.",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        tri = ShapeSpec(kind="triangle", a=3, b=4, c=5, label="Triangle (3,4,5)")
        g = self.trace_shape_and_sum(tri)

        # highlight final answer
        ans = MathTex(r"P = 3 + 4 + 5 = 12").scale(1.25).to_edge(DOWN)
        self.play(Write(ans), run_time=self.s.rt_norm)
        self.wait(0.5)

        self.play(FadeOut(VGroup(g, ans)), run_time=self.s.rt_fast)

    def step_outro(self):
        recap = VGroup(
            T(self.cfg, self.s, "Recap:", "الخلاصة:", scale=0.6),
            T(self.cfg, self.s, "• Perimeter = length around the shape", "• المحيط = الطول حول الشكل", scale=0.50),
            T(self.cfg, self.s, "• Trace all sides (don’t skip!)", "• نتبع كل الأضلاع (بدون إهمال)", scale=0.50),
            T(self.cfg, self.s, "• Add side lengths: P = ...", "• نجمع أطوال الأضلاع: P = ...", scale=0.50),
            T(self.cfg, self.s, f"• Use units ({self.s.show_units})", f"• نستعمل الوحدة ({self.s.show_units})", scale=0.50),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        recap.to_edge(RIGHT).shift(DOWN * 0.15)
        self.play(FadeIn(recap, shift=LEFT * 0.2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(recap, shift=RIGHT * 0.2), FadeOut(self.title), run_time=self.s.rt_fast)


# ============================================================
# RUN:
#   manim -pqh your_file.py M3_L15_PerimeterOfStandardShapes
#
# CUSTOMIZE:
#   cfg = LessonConfigM3_L15(
#       shapes=[ShapeSpec("rectangle", a=8, b=2, label="Rectangle (8,2)")],
#       language="ar"
#   )
# ============================================================
