from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal

import numpy as np
from manim import *

from anim_tice.core import AnimTiceScene, LessonConfig, StyleConfig


# ============================================================
# STYLE / CONFIG
# ============================================================

@dataclass
class RulerLessonStyle(StyleConfig):
    # ruler visuals
    ruler_length: float = 7.0
    ruler_height: float = 0.75
    ruler_corner: float = 0.18
    ruler_stroke: float = 5.0
    tick_stroke: float = 3.0
    tick_step: float = 0.35  # spacing between ticks in scene-units (visual only)

    # drawing
    line_stroke: float = 7.0
    helper_stroke: float = 4.0
    point_radius: float = 0.10

    # text
    font_size_small: int = 28

    # pacing
    rt_slow: float = 1.25

    # toggles
    show_freehand_contrast: bool = True
    show_ticks: bool = True
    show_labels: bool = True
    show_notation: bool = True
    show_verification: bool = True

    # layout
    title_y_shift: float = -0.9
    work_y: float = 0.1
    left_x: float = -4.8
    right_x: float = 4.8
    bottom_y: float = -3.0


@dataclass
class LessonConfigM3_G05(LessonConfig):
    title_en: str = "Using a ruler to construct line segments and lines"
    title_ar: str = "استعمال المسطرة لإنشاء قطع ومستقيمات"
    domain_en: str = "Geometry"
    domain_ar: str = "الهندسة"

    # prompts
    p_explore_en: str = "Exploration: freehand vs ruler."
    p_explore_ar: str = "استكشاف: الرسم الحر مقابل المسطرة."

    p_align_en: str = "Align the ruler with the two points."
    p_align_ar: str = "نحاذي المسطرة مع النقطتين."

    p_trace_en: str = "Trace the segment along the ruler edge."
    p_trace_ar: str = "نرسم القطعة على حافة المسطرة."

    p_highlight_en: str = "Highlight endpoints and name the segment."
    p_highlight_ar: str = "نبرز النهايتين ونسمي القطعة."

    p_line_en: str = "Extend to a full line (goes both ways)."
    p_line_ar: str = "نمدّها لتصبح مستقيماً (يمتد في الاتجاهين)."

    p_institution_en: str = "Institutionalization: segment vs line + precision."
    p_institution_ar: str = "التثبيت: قطعة مقابل مستقيم + الدقة."

    # names
    A_name: str = "A"
    B_name: str = "B"


# ============================================================
# REUSABLE BUILDING BLOCK: RULER
# ============================================================

class Ruler(VGroup):
    """
    Reusable, adjustable ruler object (visual ruler, not real unit scaling).
    - length/height configurable
    - optional ticks
    - you can align it to two points and slide/rotate it
    """

    def __init__(self, style: RulerLessonStyle, with_ticks: bool = True):
        super().__init__()
        self.s = style

        body = RoundedRectangle(
            width=style.ruler_length,
            height=style.ruler_height,
            corner_radius=style.ruler_corner
        ).set_stroke(width=style.ruler_stroke).set_fill(opacity=0.08)

        self.body = body

        ticks = VGroup()
        if with_ticks:
            n = int(style.ruler_length / style.tick_step)
            x0 = -style.ruler_length / 2
            for i in range(n + 1):
                x = x0 + i * style.tick_step
                long = (i % 5 == 0)
                h = style.ruler_height * (0.45 if long else 0.28)
                t = Line(
                    np.array([x, -style.ruler_height / 2, 0]),
                    np.array([x, -style.ruler_height / 2 + h, 0]),
                    stroke_width=style.tick_stroke
                ).set_opacity(0.75)
                ticks.add(t)

        self.ticks = ticks
        self.add(body, ticks)

        # two reference edges (top and bottom) for tracing
        self.top_edge = Line(body.get_corner(UL), body.get_corner(UR)).set_opacity(0)
        self.bottom_edge = Line(body.get_corner(DL), body.get_corner(DR)).set_opacity(0)

    def align_to_points(self, p1: np.ndarray, p2: np.ndarray, edge: Literal["top", "bottom"] = "top"):
        """
        Rotate and move ruler so its selected edge goes through p1→p2 direction.
        """
        v = p2 - p1
        ang = np.arctan2(v[1], v[0])
        self.rotate(ang - self.get_angle(), about_point=self.get_center())

        # shift so that chosen edge is near the segment line
        edge_line = self.top_edge if edge == "top" else self.bottom_edge
        # edge_line is invisible; but its center provides alignment reference
        target_mid = (p1 + p2) / 2
        self.move_to(target_mid)

        # small perpendicular offset so points sit on the edge (feels like contact)
        # compute perpendicular direction to v
        d = v / (np.linalg.norm(v) + 1e-9)
        perp = np.array([-d[1], d[0], 0])
        # choose direction so the edge sits "on" the segment
        offset = (-perp) * (self.s.ruler_height * 0.35) if edge == "top" else (perp) * (self.s.ruler_height * 0.35)
        self.shift(offset)
        return self

    def get_angle(self) -> float:
        """
        Current rotation angle estimate based on body top edge.
        """
        a = self.body.get_corner(UL)
        b = self.body.get_corner(UR)
        v = b - a
        return float(np.arctan2(v[1], v[0]))

    def tracing_edge_line(self, edge: Literal["top", "bottom"] = "top") -> Line:
        body = self.body
        if edge == "top":
            return Line(body.get_corner(UL), body.get_corner(UR))
        return Line(body.get_corner(DL), body.get_corner(DR))


# ============================================================
# MAIN SCENE
# ============================================================

class M3_G05_Ruler_Construct_Segments_And_Lines(AnimTiceScene):
    """
    M3_G05 — Using a ruler to construct line segments and lines:
      - contrast freehand vs ruler
      - place ruler
      - align with two points
      - trace segment
      - highlight endpoints + notation [AB]
      - extend to full line (line goes both ways)
      - verify straightness / precision
    """

    def __init__(
        self,
        lesson_config: LessonConfigM3_G05 = LessonConfigM3_G05(),
        style_config: RulerLessonStyle = RulerLessonStyle(),
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
        ]
        if self.s.show_freehand_contrast:
            self.steps.append(("freehand_vs_ruler", self.step_freehand_vs_ruler))

        self.steps.extend([
            ("construct_segment", self.step_construct_segment),
            ("extend_to_line", self.step_extend_to_line),
            ("institutionalization", self.step_institutionalization),
        ])

    def step_intro(self):
        # The base class handles the title, so this can be a placeholder or for additional intro animations.
        pass

    def step_freehand_vs_ruler(self):
        p = self._prompt(self.cfg.p_explore_en, self.cfg.p_explore_ar)
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        # two points
        A = np.array([self.s.left_x + 1.6, self.s.work_y + 0.8, 0])
        B = np.array([self.s.left_x + 4.2, self.s.work_y - 0.6, 0])

        dA = Dot(A, radius=self.s.point_radius)
        dB = Dot(B, radius=self.s.point_radius)
        lA = Text(self.cfg.A_name, font_size=self.s.font_size_small).scale(0.6).next_to(dA, UP, buff=0.12)
        lB = Text(self.cfg.B_name, font_size=self.s.font_size_small).scale(0.6).next_to(dB, DOWN, buff=0.12)

        # “freehand” (wavy-ish) line as contrast
        pts = [
            A,
            (A + B) / 2 + np.array([0.0, 0.45, 0]),
            (A + B) / 2 + np.array([0.25, -0.35, 0]),
            B
        ]
        freehand = VMobject().set_stroke(width=self.s.line_stroke)
        freehand.set_points_smoothly(pts)

        # ruler straight segment placeholder (thin)
        straight = Line(A, B).set_stroke(width=self.s.helper_stroke).set_opacity(0.6)

        cap1 = Text("freehand", font_size=self.s.font_size_small).scale(0.55).next_to(freehand, UP, buff=0.18)
        cap2 = Text("with ruler", font_size=self.s.font_size_small).scale(0.55).next_to(straight, DOWN, buff=0.18)

        self.play(FadeIn(dA), FadeIn(dB), FadeIn(lA), FadeIn(lB), run_time=self.s.rt_fast)
        self.play(Create(freehand), FadeIn(cap1, shift=UP * 0.05), run_time=self.s.rt_norm)
        self.play(Create(straight), FadeIn(cap2, shift=UP * 0.05), run_time=self.s.rt_norm)

        # emphasize "precision"
        self.play(freehand.animate.set_opacity(0.35), run_time=self.s.rt_fast)
        self.play(straight.animate.set_opacity(1.0), run_time=self.s.rt_fast)

        self.wait(0.25)
        self.play(FadeOut(VGroup(freehand, straight, cap1, cap2, dA, dB, lA, lB)), run_time=self.s.rt_fast)

    def step_construct_segment(self) -> Dict[str, Mobject]:
        p = self._prompt(self.cfg.p_align_en, self.cfg.p_align_ar)
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        # points A, B (centered)
        A = np.array([-2.4, self.s.work_y + 0.8, 0])
        B = np.array([1.8, self.s.work_y - 0.6, 0])

        dA = Dot(A, radius=self.s.point_radius)
        dB = Dot(B, radius=self.s.point_radius)
        lA = Text(self.cfg.A_name, font_size=self.s.font_size_small).scale(0.6).next_to(dA, UP, buff=0.12)
        lB = Text(self.cfg.B_name, font_size=self.s.font_size_small).scale(0.6).next_to(dB, DOWN, buff=0.12)
        self.play(FadeIn(dA), FadeIn(dB), FadeIn(lA), FadeIn(lB), run_time=self.s.rt_fast)

        # ruler enters
        ruler = Ruler(self.s, with_ticks=self.s.show_ticks)
        ruler.move_to(np.array([0, self.s.work_y + 1.7, 0]))
        self.play(FadeIn(ruler, shift=DOWN * 0.12), run_time=self.s.rt_norm)

        # align ruler to A-B
        ruler_target = ruler.copy().align_to_points(A, B, edge="bottom")
        self.play(Transform(ruler, ruler_target), run_time=self.s.rt_norm)

        # trace segment
        p2 = self._prompt(self.cfg.p_trace_en, self.cfg.p_trace_ar)
        self.play(Transform(self.title, p2), run_time=self.s.rt_fast)

        seg = Line(A, B).set_stroke(width=self.s.line_stroke)
        # “guided tracing”: draw along the ruler edge
        self.play(Create(seg), run_time=self.s.rt_norm)

        # highlight endpoints & notation
        p3 = self._prompt(self.cfg.p_highlight_en, self.cfg.p_highlight_ar)
        self.play(Transform(self.title, p3), run_time=self.s.rt_fast)

        glowA = Circle(radius=0.22).move_to(A).set_stroke(width=self.s.helper_stroke).set_opacity(0.75)
        glowB = Circle(radius=0.22).move_to(B).set_stroke(width=self.s.helper_stroke).set_opacity(0.75)
        self.play(FadeIn(glowA), FadeIn(glowB), run_time=self.s.rt_fast)

        notation = VGroup()
        if self.s.show_notation:
            # segment notation: [AB] or \overline{AB}
            expr = MathTex(r"\overline{%s%s}" % (self.cfg.A_name, self.cfg.B_name)).scale(1.0)
            expr.next_to(seg, DOWN, buff=0.35)
            notation = expr
            self.play(FadeIn(notation, shift=UP * 0.05), run_time=self.s.rt_fast)

        # verification: show edge contact
        verify_pack = VGroup()
        if self.s.show_verification:
            verify = Text("Aligned edge → straight segment", font_size=self.s.font_size_small).scale(0.52)
            verify.to_edge(DOWN).shift(UP * 0.2)
            # show faint edge line overlay
            edge_line = ruler.tracing_edge_line("bottom").set_stroke(width=self.s.helper_stroke).set_opacity(0.35)
            verify_pack = VGroup(edge_line, verify)
            self.play(FadeIn(edge_line), FadeIn(verify), run_time=self.s.rt_fast)

        self.wait(0.35)
        self.segment_pack = {
            "ruler": ruler,
            "A": dA, "B": dB, "lA": lA, "lB": lB,
            "segment": seg,
            "glowA": glowA, "glowB": glowB,
            "notation": notation,
            "verify_pack": verify_pack
        }

    def step_extend_to_line(self):
        pack = self.segment_pack
        p = self._prompt(self.cfg.p_line_en, self.cfg.p_line_ar)
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        seg: Line = pack["segment"]  # type: ignore
        A = seg.get_start()
        B = seg.get_end()

        # create a longer line through A-B to show "line" concept
        v = B - A
        v = v / (np.linalg.norm(v) + 1e-9)
        mid = (A + B) / 2
        long_line = Line(mid - v * 6.0, mid + v * 6.0).set_stroke(width=self.s.line_stroke).set_opacity(0.8)

        # keep segment emphasized, then swap to long line (segment remains visible as thick overlay)
        seg_emph = seg.copy().set_stroke(width=self.s.line_stroke + 2)
        self.play(Transform(seg, seg_emph), run_time=self.s.rt_fast)
        self.play(Transform(seg, long_line), run_time=self.s.rt_norm)

        # add arrows to suggest extension both ways
        arrL = Arrow(long_line.get_center(), long_line.get_start(), buff=0.0,
                     stroke_width=self.s.helper_stroke).set_opacity(0.5)
        arrR = Arrow(long_line.get_center(), long_line.get_end(), buff=0.0,
                     stroke_width=self.s.helper_stroke).set_opacity(0.5)
        self.play(FadeIn(arrL), FadeIn(arrR), run_time=self.s.rt_fast)

        # optional: line notation
        if self.s.show_notation:
            line_note = Text("line: extends both directions", font_size=self.s.font_size_small).scale(0.5)
            line_note.next_to(long_line, UP, buff=0.25)
            self.play(FadeIn(line_note, shift=UP * 0.05), run_time=self.s.rt_fast)
            self.wait(0.25)
            self.play(FadeOut(line_note), run_time=self.s.rt_fast)

        self.wait(0.25)

        # cleanup arrows (keep everything else for summary fade later)
        self.play(FadeOut(VGroup(arrL, arrR)), run_time=self.s.rt_fast)

        # now fade the construction objects except maybe the ruler
        self.play(
            FadeOut(VGroup(
                pack["verify_pack"],
                pack["notation"],
                pack["glowA"], pack["glowB"],
            )),
            run_time=self.s.rt_fast
        )

        # keep line and points briefly then fade
        self.wait(0.15)
        self.play(
            FadeOut(VGroup(pack["ruler"], pack["A"], pack["B"], pack["lA"], pack["lB"], pack["segment"])),
            run_time=self.s.rt_fast
        )

    def step_institutionalization(self):
        p = self._prompt("Institutionalization: segment vs line.", "التثبيت: القطعة والمستقيم.")
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        box = RoundedRectangle(width=11.4, height=2.7, corner_radius=0.25).set_stroke(width=3).set_fill(opacity=0.06)
        box.to_edge(DOWN).shift(UP * 0.25)

        if self.cfg.language == "en":
            lines = [
                "Segment: has two endpoints (A and B).",
                "Line: extends infinitely in both directions.",
                "Ruler use: align → trace → verify (precision).",
            ]
        else:
            lines = [
                "القطعة: لها نهايتان (A و B).",
                "المستقيم: يمتد بلا نهاية في الاتجاهين.",
                "استعمال المسطرة: محاذاة → رسم → تحقق (دقة).",
            ]

        txt = VGroup(*[Text(l, font_size=self.s.font_size_small).scale(0.55) for l in lines]) \
            .arrange(DOWN, aligned_edge=LEFT, buff=0.14) \
            .move_to(box.get_center())

        self.play(FadeIn(VGroup(box, txt), shift=UP * 0.08), run_time=self.s.rt_norm)
        self.wait(0.55)
        self.play(FadeOut(VGroup(box, txt)), run_time=self.s.rt_fast)

    def _prompt(self, en: str, ar: str) -> Mobject:
        prompt = self.t(en, ar, scale=0.52)
        prompt = self.banner(prompt).shift(DOWN * self.s.title_y_shift)
        return prompt


# ============================================================
# RUN:
#   manim -pqh M3_G05_Ruler_Construct_Segments_And_Lines.py M3_G05_Ruler_Construct_Segments_And_Lines
#
# EXTEND IDEAS:
#   - Add "given length" segment: show a tick-scale on ruler and a target length label.
#   - Add "misalignment error": slightly rotate ruler, trace, then show it misses point B.
#   - Add exercises: show 3 point pairs and ask learner to choose correct alignment.
# ============================================================
