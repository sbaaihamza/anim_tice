from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Literal

import numpy as np
from manim import *

from anim_tice.core import AnimTiceScene, LessonConfig, StyleConfig


# ============================================================
# STYLE / CONFIG
# ============================================================

@dataclass
class LinesRelStyle(StyleConfig):
    # line look
    line_stroke: float = 7.0
    aux_stroke: float = 4.0
    marker_stroke: float = 7.0

    # right-angle marker
    right_angle_size: float = 0.35

    # text
    font_size_small: int = 28

    # pacing
    rt_slow: float = 1.25

    # toggles
    show_symbols: bool = True
    show_labels: bool = True
    show_real_world_hints: bool = True  # simple icons/mini-scenes (rails, plus sign)
    show_classifier: bool = True        # quick classify at end
    show_grid: bool = False

    # geometry / layout
    title_y_shift: float = -0.9
    left_anchor: np.ndarray = field(default_factory=lambda: np.array([-4.6, 0.2, 0]))
    right_anchor: np.ndarray = field(default_factory=lambda: np.array([3.8, 0.2, 0]))
    demo_y_top: float = 1.4
    demo_y_mid: float = 0.1
    demo_y_bot: float = -1.4


@dataclass
class LessonConfigM3_G06(LessonConfig):
    title_en: str = "Identifying line positions – parallelism and perpendicularity"
    title_ar: str = "تعرف أوضاع المستقيمات – التوازي والتعامد"
    domain_en: str = "Geometry"
    domain_ar: str = "الهندسة"

    # prompts
    p_explore_en: str = "Exploration: observe line behaviors when we extend them."
    p_explore_ar: str = "استكشاف: نلاحظ سلوك المستقيمات عند تمديدها."

    p_parallel_en: str = "Parallel: extend both lines… they never meet."
    p_parallel_ar: str = "التوازي: نمدّ المستقيمين… لا يلتقيان أبداً."

    p_intersect_en: str = "Not parallel: extend… they meet at a point."
    p_intersect_ar: str = "غير متوازيين: نمدّ… يلتقيان في نقطة."

    p_perp_en: str = "Perpendicular: they meet and form a right angle."
    p_perp_ar: str = "التعامد: يلتقيان ويشكلان زاوية قائمة."

    p_institution_en: str = "Institutionalization: name, symbol, and how to recognize."
    p_institution_ar: str = "التثبيت: الاسم، الرمز، وكيف نتعرف."

    p_classify_en: str = "Classify each pair: ∥ , ⟂ , or just intersecting."
    p_classify_ar: str = "صنّف كل زوج: ∥ أو ⟂ أو تقاطع فقط."

    # symbols
    sym_parallel: str = "∥"
    sym_perp: str = "⊥"


# ============================================================
# HELPERS
# ============================================================

def make_infinite_like_line(p1: np.ndarray, p2: np.ndarray, length: float = 10.0) -> Line:
    """
    Build a long line passing through points p1->p2 (direction).
    """
    v = p2 - p1
    v = v / (np.linalg.norm(v) + 1e-9)
    mid = (p1 + p2) / 2
    a = mid - v * (length / 2)
    b = mid + v * (length / 2)
    return Line(a, b)


def extend_line_animation(line: Line, factor: float = 1.75) -> Line:
    """
    Return a new line that is a scaled version around its center (longer).
    """
    new_line = line.copy()
    new_line.scale(factor, about_point=line.get_center())
    return new_line


def intersection_point(l1: Line, l2: Line) -> Optional[np.ndarray]:
    """
    Compute intersection of two lines (infinite), returns point if not parallel.
    """
    p = l1.get_start()[:2]
    r = (l1.get_end() - l1.get_start())[:2]
    q = l2.get_start()[:2]
    s = (l2.get_end() - l2.get_start())[:2]

    rxs = r[0]*s[1] - r[1]*s[0]
    if abs(rxs) < 1e-8:
        return None

    q_p = q - p
    t = (q_p[0]*s[1] - q_p[1]*s[0]) / rxs
    inter = p + t*r
    return np.array([inter[0], inter[1], 0])


def right_angle_marker_at(vertex: np.ndarray, dir1: np.ndarray, dir2: np.ndarray, size: float, stroke: float) -> VGroup:
    """
    Draw a small square marker for a right angle at 'vertex', given two ray directions dir1, dir2.
    Directions are assumed non-zero and roughly perpendicular.
    """
    d1 = dir1 / (np.linalg.norm(dir1) + 1e-9)
    d2 = dir2 / (np.linalg.norm(dir2) + 1e-9)
    a = vertex + d1 * size
    b = a + d2 * size
    c = vertex + d2 * size
    marker = VGroup(
        Line(vertex, a, stroke_width=stroke),
        Line(a, b, stroke_width=stroke),
        Line(b, c, stroke_width=stroke),
    )
    marker.set_opacity(0.85)
    return marker


def mini_real_world_hint(kind: Literal["rails", "cross"], s: LinesRelStyle) -> VGroup:
    """
    Simple icon-like hints:
      - rails: two parallel segments + sleepers
      - cross: plus sign
    """
    if kind == "rails":
        l1 = Line(LEFT*1.5, RIGHT*1.5).rotate(15*DEGREES).shift(UP*0.2)
        l2 = l1.copy().shift(DOWN*0.6)
        sleepers = VGroup()
        for x in np.linspace(-1.2, 1.2, 5):
            sleepers.add(Line(np.array([x, -0.15, 0]), np.array([x, -0.35, 0]), stroke_width=s.aux_stroke))
        g = VGroup(l1, l2, sleepers)
        g.scale(0.6)
        return g
    else:  # "cross"
        a = Line(LEFT*1.0, RIGHT*1.0, stroke_width=s.aux_stroke)
        b = Line(DOWN*1.0, UP*1.0, stroke_width=s.aux_stroke)
        g = VGroup(a, b).scale(0.55)
        return g


# ============================================================
# MAIN SCENE
# ============================================================

class M3_G06_Parallelism_Perpendicularity(AnimTiceScene):
    """
    M3_G06 — Identify line positions:
      - Parallel lines: extend → never meet
      - Intersecting (not parallel): extend → meet at a point
      - Perpendicular: intersect + right angle marker
    Reusable:
      - adjust anchors, angles, extension factors, labels, symbols
      - add more demos by calling demo_parallel/demo_intersect/demo_perpendicular
    """

    def __init__(
        self,
        lesson_config: LessonConfigM3_G06 = LessonConfigM3_G06(),
        style_config: LinesRelStyle = LinesRelStyle(),
        **kwargs
    ):
        super().__init__(
            lesson_config=lesson_config,
            style_config=style_config,
            **kwargs
        )

    def build_steps(self):
        self.steps = [
            ("intro", self.step_intro),
            ("parallel_demo", lambda: self.demo_parallel(y=self.s.demo_y_top)),
            ("intersect_demo", lambda: self.demo_intersect(y=self.s.demo_y_mid)),
            ("perpendicular_demo", lambda: self.demo_perpendicular(y=self.s.demo_y_bot)),
            ("institutionalization", self.institutionalization_panel),
        ]
        if self.s.show_classifier:
            self.steps.append(("classifier_check", self.classifier_check))

    def step_intro(self):
        if self.s.show_grid:
            grid = NumberPlane().set_opacity(0.15)
            self.add(grid)

        prompt = self.t(self.cfg.p_explore_en, self.cfg.p_explore_ar, scale=0.48)
        prompt = self.banner(prompt).shift(DOWN * self.s.title_y_shift)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

    def demo_parallel(self, y: float = 1.4) -> VGroup:
        # prompt
        p = self.t(self.cfg.p_parallel_en, self.cfg.p_parallel_ar, scale=0.52)
        p = self.banner(p).shift(DOWN * self.s.title_y_shift)
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        # base short segments (then extend)
        center = np.array([0.0, y, 0.0])
        l1 = Line(center + LEFT*2.0 + UP*0.25, center + RIGHT*2.0 + UP*0.25, stroke_width=self.s.line_stroke)
        l2 = Line(center + LEFT*2.0 + DOWN*0.25, center + RIGHT*2.0 + DOWN*0.25, stroke_width=self.s.line_stroke)

        label = VGroup()
        if self.s.show_labels:
            label = Text("parallel", font_size=self.s.font_size_small).scale(0.55)
            label.next_to(l2, DOWN, buff=0.18)

        sym = VGroup()
        if self.s.show_symbols:
            sym = Text(self.cfg.sym_parallel, font_size=self.s.font_size_title).scale(0.7)
            sym.next_to(label if label else l2, RIGHT, buff=0.25)

        hint = VGroup()
        if self.s.show_real_world_hints:
            hint = mini_real_world_hint("rails", self.s).next_to(l1, LEFT, buff=0.4)

        self.play(Create(l1), Create(l2), FadeIn(hint, shift=LEFT*0.05), run_time=self.s.rt_norm)
        self.play(FadeIn(label, shift=UP*0.05), FadeIn(sym, shift=UP*0.05), run_time=self.s.rt_fast)

        # extend both lines
        l1_long = extend_line_animation(l1, factor=2.3)
        l2_long = extend_line_animation(l2, factor=2.3)
        self.play(Transform(l1, l1_long), Transform(l2, l2_long), run_time=self.s.rt_norm)

        # show "no meeting" by placing fading dots far away (optional)
        dot_far = Dot(point=center + RIGHT*5.4, radius=0.06).set_opacity(0.25)
        self.play(FadeIn(dot_far), run_time=self.s.rt_fast)
        self.play(FadeOut(dot_far), run_time=self.s.rt_fast)
        self.g1 = VGroup(l1, l2, label, sym, hint)

    def demo_intersect(self, y: float = 0.1) -> VGroup:
        p = self.t(self.cfg.p_intersect_en, self.cfg.p_intersect_ar, scale=0.52)
        p = self.banner(p).shift(DOWN * self.s.title_y_shift)
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        center = np.array([0.0, y, 0.0])
        l1 = Line(center + LEFT*2.0 + DOWN*0.2, center + RIGHT*2.0 + UP*0.2, stroke_width=self.s.line_stroke)
        l2 = Line(center + LEFT*2.0 + UP*0.7, center + RIGHT*2.0 + DOWN*0.7, stroke_width=self.s.line_stroke)

        label = VGroup()
        if self.s.show_labels:
            label = Text("intersecting", font_size=self.s.font_size_small).scale(0.55)
            label.next_to(l2, DOWN, buff=0.18)

        self.play(Create(l1), Create(l2), run_time=self.s.rt_norm)

        # extend lines and reveal intersection point
        l1_long = extend_line_animation(l1, factor=2.2)
        l2_long = extend_line_animation(l2, factor=2.2)
        self.play(Transform(l1, l1_long), Transform(l2, l2_long), run_time=self.s.rt_norm)

        ip = intersection_point(l1, l2)
        meet = VGroup()
        if ip is not None:
            dot = Dot(ip, radius=0.09)
            ring = Circle(radius=0.18).move_to(ip).set_stroke(width=self.s.aux_stroke).set_opacity(0.75)
            meet = VGroup(dot, ring)
            self.play(FadeIn(meet, shift=UP*0.03), run_time=self.s.rt_fast)

        self.play(FadeIn(label, shift=UP*0.05), run_time=self.s.rt_fast)
        self.g2 = VGroup(l1, l2, meet, label)

    def demo_perpendicular(self, y: float = -1.4) -> VGroup:
        p = self.t(self.cfg.p_perp_en, self.cfg.p_perp_ar, scale=0.52)
        p = self.banner(p).shift(DOWN * self.s.title_y_shift)
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        center = np.array([0.0, y, 0.0])

        # make one horizontal, one rotating toward 90 degrees
        base_line = Line(center + LEFT*2.4, center + RIGHT*2.4, stroke_width=self.s.line_stroke)

        pivot = center + np.array([0.2, 0.0, 0.0])  # slight offset for better visibility
        rot_line = Line(pivot + DOWN*2.0, pivot + UP*2.0, stroke_width=self.s.line_stroke).rotate(25*DEGREES, about_point=pivot)

        hint = VGroup()
        if self.s.show_real_world_hints:
            hint = mini_real_world_hint("cross", self.s).next_to(base_line, LEFT, buff=0.4)

        sym = VGroup()
        if self.s.show_symbols:
            sym = Text(self.cfg.sym_perp, font_size=self.s.font_size_title).scale(0.7)

        label = VGroup()
        if self.s.show_labels:
            label = Text("perpendicular", font_size=self.s.font_size_small).scale(0.55)

        self.play(Create(base_line), Create(rot_line), FadeIn(hint, shift=LEFT*0.05), run_time=self.s.rt_norm)

        # rotate into perfect perpendicular (90)
        target_line = Line(pivot + DOWN*2.2, pivot + UP*2.2, stroke_width=self.s.line_stroke)
        self.play(Transform(rot_line, target_line), run_time=self.s.rt_norm)

        # right angle marker
        marker = right_angle_marker_at(
            vertex=pivot,
            dir1=base_line.get_end() - base_line.get_start(),
            dir2=rot_line.get_end() - rot_line.get_start(),
            size=self.s.right_angle_size,
            stroke=self.s.marker_stroke,
        )
        self.play(FadeIn(marker), run_time=self.s.rt_fast)

        # place label & symbol
        if label:
            label.next_to(base_line, DOWN, buff=0.18)
        if sym:
            sym.next_to(label if label else base_line, RIGHT, buff=0.25)
        self.play(FadeIn(label, shift=UP*0.05), FadeIn(sym, shift=UP*0.05), run_time=self.s.rt_fast)
        self.g3 = VGroup(base_line, rot_line, marker, label, sym, hint)

    def institutionalization_panel(self) -> VGroup:
        p = self.t(self.cfg.p_institution_en, self.cfg.p_institution_ar, scale=0.50)
        p = self.banner(p).shift(DOWN * self.s.title_y_shift)
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        box = RoundedRectangle(width=11.4, height=2.6, corner_radius=0.25).set_stroke(width=3).set_fill(opacity=0.06)
        box.to_edge(DOWN).shift(UP*0.25)

        lines = [
            f"Parallel: lines never meet when extended  ({self.cfg.sym_parallel})",
            f"Perpendicular: meet and form a right angle ({self.cfg.sym_perp})",
            "Intersecting: meet but not at a right angle",
        ]
        if self.cfg.language != "en":
            lines = [
                f"متوازيان: لا يلتقيان عند التمديد  ({self.cfg.sym_parallel})",
                f"متعامدان: يلتقيان بزاوية قائمة ({self.cfg.sym_perp})",
                "متقاطعان: يلتقيان لكن ليست زاوية قائمة",
            ]

        txt = VGroup(*[Text(l, font_size=self.s.font_size_small).scale(0.55) for l in lines]) \
            .arrange(DOWN, aligned_edge=LEFT, buff=0.14) \
            .move_to(box.get_center())

        inst = VGroup(box, txt)
        self.play(FadeIn(inst, shift=UP * 0.08), run_time=self.s.rt_norm)
        self.wait(0.45)
        self.play(FadeOut(inst), run_time=self.s.rt_fast)

    def classifier_check(self):
        p = self.t(self.cfg.p_classify_en, self.cfg.p_classify_ar, scale=0.52)
        p = self.banner(p).shift(DOWN * self.s.title_y_shift)
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        # A tiny prompt with 3 “cards”
        cards = VGroup()
        labels = [
            ("A", "∥"),
            ("B", "×"),  # intersecting (generic)
            ("C", "⊥"),
        ]
        for i, (k, sym) in enumerate(labels):
            r = RoundedRectangle(width=2.3, height=1.2, corner_radius=0.2).set_stroke(width=3).set_fill(opacity=0.06)
            t = Text(f"{k}: {sym}", font_size=self.s.font_size_small).scale(0.65).move_to(r.get_center())
            cards.add(VGroup(r, t))
        cards.arrange(RIGHT, buff=0.5).move_to(np.array([0, -2.9, 0]))

        self.play(FadeIn(cards, shift=UP*0.06), run_time=self.s.rt_norm)

        # quick “reveal” mapping (A->parallel demo, B->intersect demo, C->perp demo)
        # we just flash each demo and then flash the corresponding card.
        def flash(m: Mobject):
            self.play(m.animate.set_opacity(0.35), run_time=0.15)
            self.play(m.animate.set_opacity(1.0), run_time=0.15)

        flash(self.g1); flash(cards[0])
        flash(self.g2); flash(cards[1])
        flash(self.g3); flash(cards[2])

        self.wait(0.25)
        self.play(FadeOut(cards), run_time=self.s.rt_fast)
        self.play(FadeOut(VGroup(self.g1, self.g2, self.g3)), run_time=self.s.rt_fast)


# ============================================================
# RUN:
#   manim -pqh M3_G06_Parallelism_Perpendicularity.py M3_G06_Parallelism_Perpendicularity
#
# EXTEND IDEAS:
#   - Add a "near-parallel" case that intersects far away, to reinforce "extend" idea.
#   - Add a “right angle finder” animation: rotate line until marker appears at 90°.
#   - Add a real-world photo placeholder frame (no external assets needed).
# ============================================================
