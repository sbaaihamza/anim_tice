from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Dict

import numpy as np
from manim import *


# ============================================================
# CONFIG / STYLES
# ============================================================

@dataclass
class EqFracStyle:
    # Visual sizing
    whole_width: float = 6.6
    whole_height: float = 1.2
    corner_radius: float = 0.20
    stroke_width: float = 4.0
    fill_opacity: float = 0.22

    # Text
    font_size_title: int = 38
    font_size_main: int = 34
    font_size_small: int = 28

    # Animation pacing
    pause: float = 0.45
    rt_fast: float = 0.7
    rt_norm: float = 1.0
    rt_slow: float = 1.25

    # Toggles
    show_circle_variant: bool = True
    show_segment_variant: bool = False
    show_arabic: bool = False  # enable only if Arabic fonts render correctly

    # “Gentle simplify back” at the end
    show_simplify_back: bool = True


@dataclass
class EqFracExample:
    """
    Start fraction a/b, then subdivide each part by factor k → (a*k)/(b*k)
    Typical: 1/2 -> subdivide by 2 -> 2/4
    """
    numerator: int = 1
    denominator: int = 2
    subdiv_factor: int = 2
    # shape: "bar" | "circle" | "segment"
    shape_type: str = "bar"
    label: str = "bar"


@dataclass
class LessonConfigM3_L07:
    title_en: str = "Identifying equivalent fractions"
    title_ar: str = "تعرف الأعداد الكسرية المتكافئة"
    language: str = "en"  # "en" | "ar"

    # Guided prompts (verbal)
    prompt_start_en: str = "Start with one representation."
    prompt_start_ar: str = "نبدأ بتمثيل واحد."

    prompt_duplicate_en: str = "Same whole… duplicated."
    prompt_duplicate_ar: str = "نفس الكل… ننسخه."

    prompt_subdivide_en: str = "Now subdivide each equal part into smaller equal parts."
    prompt_subdivide_ar: str = "الآن نقسم كل جزء إلى أجزاء أصغر متساوية."

    prompt_same_quantity_en: str = "The shaded quantity stays the same."
    prompt_same_quantity_ar: str = "الكمية المظللة تبقى نفسها."

    prompt_reveal_label_en: str = "So we can label it with a new fraction:"
    prompt_reveal_label_ar: str = "إذن يمكن تسميتها بكسر جديد:"

    prompt_simplify_en: str = "Simplify back (اختزال): same value, simpler form."
    prompt_simplify_ar: str = "اختزال: نفس القيمة، شكل أبسط."

    # Default examples (extend list easily)
    examples: List[EqFracExample] = field(default_factory=lambda: [
        EqFracExample(numerator=1, denominator=2, subdiv_factor=2, shape_type="bar", label="1/2 → 2/4"),
        EqFracExample(numerator=2, denominator=3, subdiv_factor=2, shape_type="bar", label="2/3 → 4/6"),
    ])


# ============================================================
# REUSABLE PRIMITIVES
# ============================================================

def T(cfg: LessonConfigM3_L07, s: EqFracStyle, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
    txt = en if cfg.language == "en" else (ar or en)
    return Text(txt, font_size=s.font_size_main).scale(scale)


def frac_tex(n: int, d: int, scale: float = 1.2) -> Mobject:
    return MathTex(rf"\frac{{{n}}}{{{d}}}").scale(scale)


def eq_tex(left: Tuple[int, int], right: Tuple[int, int], scale: float = 1.2) -> Mobject:
    (a, b), (c, d) = left, right
    return MathTex(rf"\frac{{{a}}}{{{b}}} = \frac{{{c}}}{{{d}}}").scale(scale)


class FractionBar(VGroup):
    """
    A rounded rectangle partitioned into equal parts (denominator).
    We can shade a number of parts (numerator) and later subdivide each part visually.
    """
    def __init__(self, denominator: int, style: EqFracStyle, **kwargs):
        super().__init__(**kwargs)
        self.d = denominator
        self.s = style

        outer = RoundedRectangle(
            width=style.whole_width,
            height=style.whole_height,
            corner_radius=style.corner_radius
        ).set_stroke(width=style.stroke_width).set_fill(opacity=0.0)

        # partition lines
        lines = VGroup()
        x0 = -style.whole_width / 2
        for i in range(1, denominator):
            x = x0 + i * style.whole_width / denominator
            lines.add(
                Line([x, -style.whole_height/2, 0], [x, style.whole_height/2, 0]).set_stroke(
                    width=style.stroke_width * 0.75, opacity=0.75
                )
            )

        self.outer = outer
        self.lines = lines
        self.add(outer, lines)

    def part_boxes(self) -> VGroup:
        boxes = VGroup()
        w = self.s.whole_width
        h = self.s.whole_height
        part_w = w / self.d
        x0 = -w / 2
        for i in range(self.d):
            box = Rectangle(width=part_w, height=h).set_stroke(width=0).set_fill(opacity=0.0)
            box.move_to([x0 + part_w*(i+0.5), 0, 0])
            boxes.add(box)
        return boxes

    def shade_first_k(self, k: int) -> VGroup:
        parts = self.part_boxes()
        shaded = VGroup()
        for i in range(min(k, len(parts))):
            p = parts[i].copy().set_fill(opacity=self.s.fill_opacity).set_stroke(width=0)
            shaded.add(p)
        return shaded


def add_subdivision_lines_for_factor(
    bar: FractionBar,
    denominator: int,
    factor: int,
    style: EqFracStyle
) -> VGroup:
    """
    Add extra partition lines to go from denominator b to b*factor.
    We do NOT change the outer; we just add the finer lines.
    """
    new_d = denominator * factor
    lines = VGroup()
    x0 = -style.whole_width / 2
    for i in range(1, new_d):
        # skip old boundaries (multiples of factor) to avoid double lines
        if i % factor == 0:
            continue
        x = x0 + i * style.whole_width / new_d
        lines.add(
            Line([x, -style.whole_height/2, 0], [x, style.whole_height/2, 0]).set_stroke(
                width=style.stroke_width * 0.6, opacity=0.55
            )
        )
    return lines


def shaded_group_after_subdivision(
    style: EqFracStyle,
    new_denominator: int,
    shaded_length_fraction: float
) -> VGroup:
    """
    Build shading as a continuous region covering the same length fraction of the bar.
    We shade 'shaded_length_fraction' of the total width with fine parts.
    """
    w = style.whole_width
    h = style.whole_height
    part_w = w / new_denominator
    k_parts = int(round(shaded_length_fraction * new_denominator))

    x0 = -w / 2
    shaded = VGroup()
    for i in range(k_parts):
        box = Rectangle(width=part_w, height=h).set_stroke(width=0).set_fill(opacity=style.fill_opacity)
        box.move_to([x0 + part_w*(i+0.5), 0, 0])
        shaded.add(box)
    return shaded


class PartitionedCircleEq(VGroup):
    """
    Circle partitioned into equal sectors, for equivalence demo.
    """
    def __init__(self, denominator: int, style: EqFracStyle, radius: float = 1.55, **kwargs):
        super().__init__(**kwargs)
        self.d = denominator
        self.s = style
        self.radius = radius

        circle = Circle(radius=radius).set_stroke(width=style.stroke_width).set_fill(opacity=0.0)
        lines = VGroup()
        for i in range(denominator):
            ang = i * TAU / denominator
            p = np.array([np.cos(ang), np.sin(ang), 0.0]) * radius
            lines.add(Line(ORIGIN, p).set_stroke(width=style.stroke_width * 0.75, opacity=0.75))
        self.circle = circle
        self.lines = lines
        self.add(circle, lines)

    def sectors(self) -> VGroup:
        secs = VGroup()
        for i in range(self.d):
            start = i * TAU / self.d
            sec = Sector(outer_radius=self.radius, start_angle=start, angle=TAU / self.d)
            sec.set_stroke(width=0).set_fill(opacity=0.0)
            secs.add(sec)
        return secs


# ============================================================
# LESSON SCENE (Reusable / Adjustable / Extensible)
# ============================================================

class M3_L07_EquivalentFractions(Scene):
    """
    M3_L07 — Identifying equivalent fractions

    Gold-layer animation flow:
      1) start_with_one_representation (e.g., 1/2 shaded)
      2) duplicate_same_whole
      3) subdivide_each_part (halves -> quarters)
      4) show shaded quantity remains identical
      5) reveal new fraction label (2/4)
      6) optional simplify back visually (2/4 -> 1/2)

    Avoids rule-first arithmetic.
    """

    def __init__(
        self,
        cfg: LessonConfigM3_L07 = LessonConfigM3_L07(),
        style: EqFracStyle = EqFracStyle(),
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
            ("exploration_examples", self.step_exploration_examples),
            ("collective_discussion_why_equal", self.step_collective_discussion_why_equal),
            ("institutionalization_vocab_and_simplify", self.step_institutionalization_vocab_and_simplify),
            ("mini_assessment_match", self.step_mini_assessment_match),
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
            "Same whole, different partitions → same quantity",
            "نفس الكل، تقسيم مختلف → نفس الكمية",
            scale=0.52
        ).next_to(title, DOWN, buff=0.18)

        self.play(Write(title), FadeIn(subtitle, shift=DOWN * 0.15), run_time=self.s.rt_norm)
        self.wait(0.2)
        self.play(FadeOut(subtitle, shift=UP * 0.1), run_time=self.s.rt_fast)

        self.title = title

    # ============================================================
    # Core equivalence demonstration (BAR)
    # ============================================================

    def show_equivalence_bar(self, ex: EqFracExample) -> Dict[str, Mobject]:
        """
        Returns a dict of created objects (for later fadeout).
        """
        a, b, k = ex.numerator, ex.denominator, ex.subdiv_factor
        new_a, new_b = a * k, b * k

        # prompts
        p1 = T(self.cfg, self.s, self.cfg.prompt_start_en, self.cfg.prompt_start_ar, scale=0.55)
        p1 = self.banner(p1).shift(DOWN * 0.9)
        self.play(Transform(self.title, p1), run_time=self.s.rt_fast)

        # 1) start with one representation
        left_bar = FractionBar(b, self.s).move_to(LEFT * 3.3 + DOWN * 0.2)
        left_shade = left_bar.shade_first_k(a).move_to(left_bar.get_center())
        left_label = frac_tex(a, b, scale=1.3).next_to(left_bar, UP, buff=0.25)

        self.play(Create(left_bar), FadeIn(left_shade), Write(left_label), run_time=self.s.rt_norm)

        # 2) duplicate same whole
        p2 = T(self.cfg, self.s, self.cfg.prompt_duplicate_en, self.cfg.prompt_duplicate_ar, scale=0.55)
        p2 = self.banner(p2).shift(DOWN * 0.9)
        self.play(Transform(self.title, p2), run_time=self.s.rt_fast)

        right_bar = left_bar.copy().move_to(RIGHT * 3.3 + DOWN * 0.2)
        right_shade = left_shade.copy().move_to(right_bar.get_center())
        right_label_old = frac_tex(a, b, scale=1.3).next_to(right_bar, UP, buff=0.25)

        self.play(Create(right_bar), FadeIn(right_shade), Write(right_label_old), run_time=self.s.rt_norm)

        # 3) subdivide each part on the right bar
        p3 = T(self.cfg, self.s, self.cfg.prompt_subdivide_en, self.cfg.prompt_subdivide_ar, scale=0.55)
        p3 = self.banner(p3).shift(DOWN * 0.9)
        self.play(Transform(self.title, p3), run_time=self.s.rt_fast)

        finer_lines = add_subdivision_lines_for_factor(right_bar, b, k, self.s)
        self.play(LaggedStartMap(FadeIn, finer_lines, lag_ratio=0.05), run_time=self.s.rt_norm)

        # 4) shaded quantity remains identical, but now described as new_a/new_b
        p4 = T(self.cfg, self.s, self.cfg.prompt_same_quantity_en, self.cfg.prompt_same_quantity_ar, scale=0.55)
        p4 = self.banner(p4).shift(DOWN * 0.9)
        self.play(Transform(self.title, p4), run_time=self.s.rt_fast)

        shaded_fraction = a / b  # same length fraction
        new_shade = shaded_group_after_subdivision(self.s, new_b, shaded_fraction).move_to(right_bar.get_center())
        # replace old shade with fine-grained shade (still same area visually)
        self.play(Transform(right_shade, new_shade), run_time=self.s.rt_slow)

        # highlight same quantity (outline glow)
        glowL = SurroundingRectangle(left_shade, buff=0.06)
        glowR = SurroundingRectangle(right_shade, buff=0.06)
        self.play(Create(glowL), Create(glowR), run_time=self.s.rt_fast)
        self.play(FadeOut(glowL), FadeOut(glowR), run_time=self.s.rt_fast)

        # 5) reveal new fraction label last
        p5 = T(self.cfg, self.s, self.cfg.prompt_reveal_label_en, self.cfg.prompt_reveal_label_ar, scale=0.55)
        p5 = self.banner(p5).shift(DOWN * 0.9)
        self.play(Transform(self.title, p5), run_time=self.s.rt_fast)

        right_label_new = frac_tex(new_a, new_b, scale=1.3).next_to(right_bar, UP, buff=0.25)
        self.play(Transform(right_label_old, right_label_new), run_time=self.s.rt_norm)

        eq = eq_tex((a, b), (new_a, new_b), scale=1.3).to_edge(DOWN)
        self.play(Write(eq), run_time=self.s.rt_norm)

        # optional simplify back visually
        simplify_group = VGroup()
        if self.s.show_simplify_back:
            simp_prompt = T(self.cfg, self.s, self.cfg.prompt_simplify_en, self.cfg.prompt_simplify_ar, scale=0.52)
            simp_prompt.next_to(eq, UP, buff=0.18)
            self.play(FadeIn(simp_prompt, shift=UP * 0.1), run_time=self.s.rt_fast)

            # gentle “merge” highlight: show that 2 tiny parts combine into 1 bigger part
            # (visual cue only: fade finer lines slightly)
            self.play(finer_lines.animate.set_stroke(opacity=0.20), run_time=self.s.rt_norm)
            self.play(finer_lines.animate.set_stroke(opacity=0.55), run_time=self.s.rt_norm)
            simplify_group = VGroup(simp_prompt)

        return {
            "left_bar": left_bar,
            "left_shade": left_shade,
            "left_label": left_label,
            "right_bar": right_bar,
            "right_shade": right_shade,
            "right_label": right_label_old,
            "finer_lines": finer_lines,
            "eq": eq,
            "simplify_group": simplify_group,
        }

    # ============================================================
    # Optional circle variant (same idea)
    # ============================================================

    def show_equivalence_circle(self, a: int, b: int, k: int) -> VGroup:
        new_a, new_b = a * k, b * k

        left = PartitionedCircleEq(b, self.s).scale(0.95).move_to(LEFT * 3.2 + DOWN * 0.2)
        right = PartitionedCircleEq(b, self.s).scale(0.95).move_to(RIGHT * 3.2 + DOWN * 0.2)

        left_secs = left.sectors()
        right_secs = right.sectors()

        # shade a sectors
        shadeL = VGroup()
        for i in range(a):
            sec = left_secs[i].copy().set_fill(opacity=self.s.fill_opacity).set_stroke(width=0)
            shadeL.add(sec)
        shadeL.move_to(left.get_center())

        shadeR = VGroup()
        for i in range(a):
            sec = right_secs[i].copy().set_fill(opacity=self.s.fill_opacity).set_stroke(width=0)
            shadeR.add(sec)
        shadeR.move_to(right.get_center())

        labL = frac_tex(a, b, scale=1.2).next_to(left, UP, buff=0.2)
        labR = frac_tex(a, b, scale=1.2).next_to(right, UP, buff=0.2)

        self.play(Create(left), FadeIn(shadeL), Write(labL), run_time=self.s.rt_norm)
        self.play(Create(right), FadeIn(shadeR), Write(labR), run_time=self.s.rt_norm)

        # subdivide right: add extra radial lines by re-creating circle partition with new_b
        finer = PartitionedCircleEq(new_b, self.s).scale(0.95).move_to(right.get_center())
        finer_lines_only = finer.lines.copy().set_stroke(opacity=0.55)

        self.play(LaggedStartMap(FadeIn, finer_lines_only, lag_ratio=0.03), run_time=self.s.rt_norm)

        # replace shadeR with finer shading: shade new_a sectors out of new_b (same angle span)
        finer_secs = finer.sectors()
        shadeR2 = VGroup()
        for i in range(new_a):
            sec = finer_secs[i].copy().set_fill(opacity=self.s.fill_opacity).set_stroke(width=0)
            shadeR2.add(sec)
        shadeR2.move_to(right.get_center())

        self.play(Transform(shadeR, shadeR2), run_time=self.s.rt_slow)
        self.play(Transform(labR, frac_tex(new_a, new_b, scale=1.2).move_to(labR.get_center())), run_time=self.s.rt_norm)

        eq = eq_tex((a, b), (new_a, new_b), scale=1.2).to_edge(DOWN)
        self.play(Write(eq), run_time=self.s.rt_norm)

        return VGroup(left, shadeL, labL, right, shadeR, labR, finer_lines_only, eq)

    # ============================================================
    # Steps
    # ============================================================

    def step_exploration_examples(self):
        """
        Exploration: “see sameness” before any symbolic technique.
        """
        # run through configured examples (bar-based)
        for ex in self.cfg.examples:
            if ex.shape_type != "bar":
                continue
            objs = self.show_equivalence_bar(ex)
            self.wait(0.4)
            self.play(*[FadeOut(m) for m in objs.values() if isinstance(m, Mobject)], run_time=self.s.rt_fast)

        # Optional: circle variant (quick reinforcement)
        if self.s.show_circle_variant:
            prompt = T(
                self.cfg, self.s,
                "Same idea with a circle (pizza).",
                "نفس الفكرة مع دائرة (بيتزا).",
                scale=0.55
            )
            prompt = self.banner(prompt).shift(DOWN * 0.9)
            self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

            circle_group = self.show_equivalence_circle(a=1, b=2, k=2)
            self.wait(0.4)
            self.play(FadeOut(circle_group), run_time=self.s.rt_fast)

    def step_collective_discussion_why_equal(self):
        """
        Discussion: justify equivalence with visual reasoning.
        """
        prompt = T(
            self.cfg, self.s,
            "Discussion: Why are they equal?",
            "نقاش: لماذا هما متكافئان؟",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        # A simple “language scaffold” card
        box = RoundedRectangle(width=11.5, height=2.7, corner_radius=0.25).to_edge(DOWN).shift(UP * 0.25)
        box.set_fill(opacity=0.06).set_stroke(width=3)

        s1 = T(self.cfg, self.s, "• Same whole", "• نفس الكل", scale=0.52)
        s2 = T(self.cfg, self.s, "• Same shaded area/length", "• نفس المساحة/الطول المظلل", scale=0.52)
        s3 = T(self.cfg, self.s, "• Each part was split into equal smaller parts", "• قُسم كل جزء إلى أجزاء أصغر متساوية", scale=0.52)
        scaff = VGroup(s1, s2, s3).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(box.get_center())

        self.play(Create(box), FadeIn(scaff, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.5)
        self.play(FadeOut(VGroup(box, scaff)), run_time=self.s.rt_fast)

    def step_institutionalization_vocab_and_simplify(self):
        """
        Formal vocabulary: equivalent fractions + intro simplification (اختزال) as “same value, simpler form”.
        """
        prompt = T(
            self.cfg, self.s,
            "Institutionalization: equivalent fractions & simplification",
            "التثبيت: الكسور المتكافئة والاختزال",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        # Show a clean symbolic statement AFTER visuals
        eq = eq_tex((2, 4), (1, 2), scale=1.35)
        eq.move_to(ORIGIN + UP * 0.2)

        note1 = T(self.cfg, self.s, "Equivalent fractions: same quantity.", "كسور متكافئة: نفس الكمية.", scale=0.54)
        note2 = T(self.cfg, self.s, "Simplify (اختزال): keep value, use simpler form.", "اختزال: نحافظ على القيمة ونبسط الشكل.", scale=0.54)
        notes = VGroup(note1, note2).arrange(DOWN, buff=0.18).next_to(eq, DOWN, buff=0.35)

        self.play(Write(eq), run_time=self.s.rt_norm)
        self.play(FadeIn(notes, shift=UP * 0.1), run_time=self.s.rt_norm)

        self.wait(0.5)
        self.play(FadeOut(VGroup(eq, notes)), run_time=self.s.rt_fast)

    def step_mini_assessment_match(self):
        """
        Formative: match two representations that are equivalent.
        """
        prompt = T(
            self.cfg, self.s,
            "Mini-check: Which two fractions are equivalent?",
            "تحقق صغير: أي كسرين متكافئان؟",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        # Options
        a = frac_tex(1, 2, scale=1.2)
        b = frac_tex(2, 4, scale=1.2)  # equivalent
        c = frac_tex(3, 4, scale=1.2)
        opts = VGroup(a, b, c).arrange(DOWN, buff=0.35).to_edge(RIGHT).shift(DOWN * 0.2)

        # Visual: bar shaded 1/2
        bar = FractionBar(2, self.s).move_to(LEFT * 2.8 + DOWN * 0.2)
        shade = bar.shade_first_k(1).move_to(bar.get_center())
        self.play(Create(bar), FadeIn(shade), FadeIn(opts, shift=LEFT * 0.15), run_time=self.s.rt_norm)

        # Reveal: highlight correct pair
        box1 = SurroundingRectangle(a, buff=0.12)
        box2 = SurroundingRectangle(b, buff=0.12)
        ok = T(self.cfg, self.s, "They represent the same shaded quantity.", "يمثلان نفس الكمية المظللة.", scale=0.52)
        ok.to_edge(DOWN)

        self.play(Create(box1), Create(box2), FadeIn(ok, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.4)

        self.play(FadeOut(VGroup(bar, shade, opts, box1, box2, ok)), run_time=self.s.rt_fast)

    def step_outro(self):
        recap = VGroup(
            T(self.cfg, self.s, "Recap:", "الخلاصة:", scale=0.6),
            T(self.cfg, self.s, "• Equivalent fractions = same quantity", "• الكسور المتكافئة = نفس الكمية", scale=0.50),
            T(self.cfg, self.s, "• Subdivision creates finer parts (same shaded area)", "• التقسيم يعطي أجزاء أصغر (نفس المساحة)", scale=0.50),
            T(self.cfg, self.s, "• Simplification keeps the value (اختزال)", "• الاختزال يحافظ على القيمة", scale=0.50),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        recap.to_edge(RIGHT).shift(DOWN * 0.2)
        self.play(FadeIn(recap, shift=LEFT * 0.2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(recap, shift=RIGHT * 0.2), FadeOut(self.title), run_time=self.s.rt_fast)


# ============================================================
# RUN:
#   manim -pqh your_file.py M3_L07_EquivalentFractions
#
# CUSTOMIZE:
#   cfg = LessonConfigM3_L07(
#       examples=[EqFracExample(1,2,3,"bar","1/2 → 3/6")],
#       language="ar"
#   )
#   style = EqFracStyle(show_circle_variant=False, show_simplify_back=True)
# ============================================================
