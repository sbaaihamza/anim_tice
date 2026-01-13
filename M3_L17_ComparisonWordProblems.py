from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable

import numpy as np
from manim import *


# ============================================================
# CONFIG / STYLES
# ============================================================

@dataclass
class CompareStyle:
    stroke_width: float = 4.0
    fill_opacity: float = 0.18

    # bars
    bar_height: float = 0.55
    bar_corner_radius: float = 0.18
    unit_width: float = 0.45  # visual width per "1 unit"

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
    show_objects_view: bool = True     # dots/items view before bars
    show_operation_translate: bool = True
    show_question_variants: bool = True  # difference vs find larger vs find smaller

    # layout
    left_anchor_x: float = -5.0
    bar_y_top: float = 0.7
    bar_y_bottom: float = -0.7


@dataclass
class ComparisonCase:
    """
    Comparison word-problem core parameters:
      A and B quantities; unknown can be difference, larger, or smaller.
    """
    a_name: str = "Amina"
    b_name: str = "Youssef"
    a_qty: int = 9
    b_qty: int = 6

    # question types:
    #   "difference": How many more/less?
    #   "find_larger": If B has ..., and B has ... more than A -> find B (addition)
    #   "find_smaller": If B has ..., and B has ... less than A -> find A (addition)
    question_type: str = "difference"

    context_item: str = "stickers"  # or apples, marbles...


@dataclass
class LessonConfigM3_L17:
    title_en: str = "Solving comparison word problems"
    title_ar: str = "حل مسائل وضعيات المقارنة"
    language: str = "en"  # "en" | "ar"

    # prompts (scaffolding)
    prompt_read_en: str = "Read the situation: who has more? who has less?"
    prompt_read_ar: str = "اقرأ الوضعية: من لديه أكثر؟ من لديه أقل؟"

    prompt_align_en: str = "Align both quantities from the same start."
    prompt_align_ar: str = "نحاذي الكميتين من نفس نقطة البداية."

    prompt_common_en: str = "This common part is the same for both."
    prompt_common_ar: str = "هذا الجزء المشترك متساوٍ عندهما."

    prompt_diff_en: str = "The extra part is the difference."
    prompt_diff_ar: str = "الجزء الزائد هو الفرق."

    prompt_translate_en: str = "Translate the model into an operation."
    prompt_translate_ar: str = "نحوّل النموذج إلى عملية حسابية."

    # default case(s)
    cases: List[ComparisonCase] = field(default_factory=lambda: [
        ComparisonCase(a_name="Amina", b_name="Youssef", a_qty=9, b_qty=6, question_type="difference", context_item="stickers"),
        # optional variants:
        ComparisonCase(a_name="Sara", b_name="Omar", a_qty=7, b_qty=10, question_type="difference", context_item="apples"),
    ])


# ============================================================
# REUSABLE PRIMITIVES
# ============================================================

def T(cfg: LessonConfigM3_L17, s: CompareStyle, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
    txt = en if cfg.language == "en" else (ar or en)
    return Text(txt, font_size=s.font_size_main).scale(scale)


class QuantityBar(VGroup):
    """
    A quantity bar with a "common" segment and optional "extra" segment.
    """
    def __init__(self, qty: int, style: CompareStyle, label: str = "", **kwargs):
        super().__init__(**kwargs)
        self.qty = qty
        self.s = style

        width = qty * style.unit_width
        bar = RoundedRectangle(
            width=width,
            height=style.bar_height,
            corner_radius=style.bar_corner_radius
        ).set_stroke(width=style.stroke_width).set_fill(opacity=style.fill_opacity)

        name = Text(label, font_size=style.font_size_small).scale(0.75).next_to(bar, LEFT, buff=0.3)

        self.bar = bar
        self.name = name
        self.add(bar, name)

    def left(self) -> np.ndarray:
        return self.bar.get_left()

    def right(self) -> np.ndarray:
        return self.bar.get_right()

    def subsegment(self, start_units: int, length_units: int) -> RoundedRectangle:
        """
        Return a rectangle overlay segment inside the bar from start_units for length_units.
        """
        w = self.qty * self.s.unit_width
        part_w = length_units * self.s.unit_width
        x0 = -w / 2 + (start_units * self.s.unit_width) + part_w / 2
        seg = RoundedRectangle(
            width=part_w,
            height=self.s.bar_height,
            corner_radius=max(0.01, self.s.bar_corner_radius * 0.55),
        ).set_stroke(width=0).set_fill(opacity=0.30)
        seg.move_to(self.bar.get_center() + np.array([x0, 0, 0]))
        return seg


def dots_for_quantity(qty: int, style: CompareStyle, label: str) -> VGroup:
    """
    Discrete object representation: dots/items in a row.
    """
    dots = VGroup()
    for i in range(qty):
        d = Dot(radius=0.09)
        dots.add(d)
    dots.arrange(RIGHT, buff=0.18)
    tag = Text(f"{label}: {qty}", font_size=style.font_size_small).scale(0.75).next_to(dots, LEFT, buff=0.35)
    return VGroup(tag, dots)


def op_tex_difference(big: int, small: int, scale: float = 1.2) -> Mobject:
    return MathTex(rf"{big} - {small} = {big-small}").scale(scale)


def op_tex_add(base: int, diff: int, scale: float = 1.2) -> Mobject:
    return MathTex(rf"{base} + {diff} = {base+diff}").scale(scale)


# ============================================================
# LESSON SCENE (Reusable / Adjustable / Extensible)
# ============================================================

class M3_L17_ComparisonWordProblems(Scene):
    """
    M3_L17 — Comparison problems

    Visual flow:
      display_two_quantities separately
      align from same start
      highlight common part
      highlight extra part (difference)
      label difference
      translate visual to operation

    Avoids:
      jump straight to subtraction; keeps relational language.
    """

    def __init__(
        self,
        cfg: LessonConfigM3_L17 = LessonConfigM3_L17(),
        style: CompareStyle = CompareStyle(),
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
            ("exploration_cases", self.step_exploration_cases),
            ("collective_discussion_structure", self.step_collective_discussion_structure),
            ("institutionalization_template", self.step_institutionalization_template),
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
            "More / Less / Difference → choose the operation from the question",
            "أكثر / أقل / الفرق → نختار العملية حسب السؤال",
            scale=0.52
        ).next_to(title, DOWN, buff=0.18)

        self.play(Write(title), FadeIn(subtitle, shift=DOWN * 0.15), run_time=self.s.rt_norm)
        self.wait(0.2)
        self.play(FadeOut(subtitle, shift=UP * 0.1), run_time=self.s.rt_fast)
        self.title = title

    # ------------------------------------------------------------
    # Core visualization for one case
    # ------------------------------------------------------------

    def run_case(self, case: ComparisonCase) -> VGroup:
        # Decide which is bigger
        a_qty, b_qty = case.a_qty, case.b_qty
        a_big = a_qty >= b_qty
        big_name = case.a_name if a_big else case.b_name
        small_name = case.b_name if a_big else case.a_name
        big = max(a_qty, b_qty)
        small = min(a_qty, b_qty)
        diff = big - small

        # Prompt: read who has more/less
        p = T(self.cfg, self.s, self.cfg.prompt_read_en, self.cfg.prompt_read_ar, scale=0.56)
        p = self.banner(p).shift(DOWN * 0.9)
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        # Discrete objects view first (optional)
        objs = VGroup()
        if self.s.show_objects_view:
            row1 = dots_for_quantity(a_qty, self.s, case.a_name).move_to(LEFT * 2.3 + UP * 0.8)
            row2 = dots_for_quantity(b_qty, self.s, case.b_name).move_to(LEFT * 2.3 + DOWN * 0.2)
            objs = VGroup(row1, row2)
            self.play(FadeIn(objs, shift=UP * 0.1), run_time=self.s.rt_norm)

            hint = T(
                self.cfg, self.s,
                f"Context: {case.context_item}",
                f"السياق: {case.context_item}",
                scale=0.50
            ).to_edge(DOWN)
            self.play(FadeIn(hint, shift=UP * 0.05), run_time=self.s.rt_fast)
            self.wait(0.2)
            self.play(FadeOut(hint), run_time=self.s.rt_fast)

        # Transition to aligned bars (the core model)
        p2 = T(self.cfg, self.s, self.cfg.prompt_align_en, self.cfg.prompt_align_ar, scale=0.56)
        p2 = self.banner(p2).shift(DOWN * 0.9)
        self.play(Transform(self.title, p2), run_time=self.s.rt_fast)

        barA = QuantityBar(a_qty, self.s, label=case.a_name).move_to(np.array([0, self.s.bar_y_top, 0]))
        barB = QuantityBar(b_qty, self.s, label=case.b_name).move_to(np.array([0, self.s.bar_y_bottom, 0]))

        # align left edges to same anchor point
        anchor = np.array([self.s.left_anchor_x, 0, 0])
        barA.shift(anchor - barA.left())
        barB.shift(anchor - barB.left())

        if self.s.show_objects_view:
            self.play(FadeOut(objs, run_time=self.s.rt_fast))

        self.play(Create(barA.bar), FadeIn(barA.name), Create(barB.bar), FadeIn(barB.name), run_time=self.s.rt_norm)

        # Highlight common part
        p3 = T(self.cfg, self.s, self.cfg.prompt_common_en, self.cfg.prompt_common_ar, scale=0.56)
        p3 = self.banner(p3).shift(DOWN * 0.9)
        self.play(Transform(self.title, p3), run_time=self.s.rt_fast)

        commonA = barA.subsegment(0, min(a_qty, b_qty))
        commonB = barB.subsegment(0, min(a_qty, b_qty))
        self.play(FadeIn(commonA), FadeIn(commonB), run_time=self.s.rt_norm)

        # Highlight difference (extra segment on the bigger bar)
        p4 = T(self.cfg, self.s, self.cfg.prompt_diff_en, self.cfg.prompt_diff_ar, scale=0.56)
        p4 = self.banner(p4).shift(DOWN * 0.9)
        self.play(Transform(self.title, p4), run_time=self.s.rt_fast)

        extra = VGroup()
        if a_big:
            extra = barA.subsegment(small, diff)
        else:
            extra = barB.subsegment(small, diff)

        # difference label
        diff_lab = Text(f"Difference = {diff}", font_size=self.s.font_size_small).scale(0.75)
        diff_lab.next_to(extra, UP, buff=0.18)

        self.play(FadeIn(extra), FadeIn(diff_lab, shift=UP * 0.05), run_time=self.s.rt_norm)

        # Translate to operation (contextual)
        op_group = VGroup()
        if self.s.show_operation_translate:
            p5 = T(self.cfg, self.s, self.cfg.prompt_translate_en, self.cfg.prompt_translate_ar, scale=0.56)
            p5 = self.banner(p5).shift(DOWN * 0.9)
            self.play(Transform(self.title, p5), run_time=self.s.rt_fast)

            # Most common: find difference -> subtraction
            if case.question_type == "difference":
                op = op_tex_difference(big, small, scale=1.25).to_edge(DOWN)
                explain = T(
                    self.cfg, self.s,
                    f"{big_name} has {diff} more {case.context_item} than {small_name}.",
                    f"{big_name} لديه {diff} أكثر من {case.context_item} من {small_name}.",
                    scale=0.50
                ).next_to(op, UP, buff=0.18)
                op_group = VGroup(explain, op)
                self.play(Write(op), FadeIn(explain, shift=UP * 0.05), run_time=self.s.rt_norm)

            else:
                # extension: cases that lead to addition (find larger/smaller from base + diff)
                # Here we interpret "unknown" as one quantity given the other + difference
                # We show: base + diff = unknown
                # base is the smaller, unknown is the bigger
                op = op_tex_add(small, diff, scale=1.25).to_edge(DOWN)
                explain = T(
                    self.cfg, self.s,
                    f"If {small_name} has {small}, and the difference is {diff}, then {big_name} has:",
                    f"إذا كان {small_name} لديه {small} والفرق {diff} فإن {big_name} لديه:",
                    scale=0.48
                ).next_to(op, UP, buff=0.18)
                op_group = VGroup(explain, op)
                self.play(Write(op), FadeIn(explain, shift=UP * 0.05), run_time=self.s.rt_norm)

        return VGroup(barA, barB, commonA, commonB, extra, diff_lab, op_group)

    # ============================================================
    # Steps
    # ============================================================

    def step_exploration_cases(self):
        # Main: difference cases
        for case in self.cfg.cases:
            g = self.run_case(case)
            self.wait(0.4)
            self.play(FadeOut(g), run_time=self.s.rt_fast)

        # Optional: show question variants using the SAME model
        if self.s.show_question_variants:
            case = ComparisonCase(a_name="Lina", b_name="Adil", a_qty=5, b_qty=8, question_type="difference", context_item="marbles")
            g = self.run_case(case)
            self.wait(0.3)

            # change only the question: find larger from smaller + diff
            # (we keep the same aligned-bar model idea)
            q = T(
                self.cfg, self.s,
                "Variant question: Lina has 5. Adil has 3 more. How many does Adil have?",
                "سؤال مختلف: لينا لديها 5. عادل لديه 3 أكثر. كم لدى عادل؟",
                scale=0.44
            ).to_edge(DOWN)
            self.play(FadeIn(q, shift=UP * 0.05), run_time=self.s.rt_fast)

            op = op_tex_add(5, 3, scale=1.25).to_edge(DOWN)
            self.play(Transform(q, op), run_time=self.s.rt_norm)

            self.wait(0.4)
            self.play(FadeOut(VGroup(g, q)), run_time=self.s.rt_fast)

    def step_collective_discussion_structure(self):
        prompt = T(
            self.cfg, self.s,
            "Discussion: What are the 3 key parts?",
            "نقاش: ما هي الأجزاء الثلاثة الأساسية؟",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        box = RoundedRectangle(width=11.6, height=2.9, corner_radius=0.25).to_edge(DOWN).shift(UP * 0.2)
        box.set_stroke(width=3).set_fill(opacity=0.06)

        l1 = T(self.cfg, self.s, "• Quantity 1 (who/what)", "• الكمية 1 (من/ماذا)", scale=0.52)
        l2 = T(self.cfg, self.s, "• Quantity 2 (who/what)", "• الكمية 2 (من/ماذا)", scale=0.52)
        l3 = T(self.cfg, self.s, "• Relationship: more/less → difference", "• العلاقة: أكثر/أقل → الفرق", scale=0.52)

        scaff = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(box.get_center())
        self.play(Create(box), FadeIn(scaff, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.5)
        self.play(FadeOut(VGroup(box, scaff)), run_time=self.s.rt_fast)

    def step_institutionalization_template(self):
        prompt = T(
            self.cfg, self.s,
            "Institutionalization: Comparison template",
            "التثبيت: قالب وضعية المقارنة",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        tmpl = MathTex(r"\text{bigger} = \text{smaller} + \text{difference}").scale(1.25).move_to(UP * 0.2)
        ex = MathTex(r"8 = 5 + 3 \quad \Rightarrow \quad 8-5=3").scale(1.1).next_to(tmpl, DOWN, buff=0.3)
        self.play(Write(tmpl), run_time=self.s.rt_norm)
        self.play(Write(ex), run_time=self.s.rt_norm)
        self.wait(0.5)
        self.play(FadeOut(VGroup(tmpl, ex)), run_time=self.s.rt_fast)

    def step_mini_assessment(self):
        prompt = T(
            self.cfg, self.s,
            "Mini-check: Omar has 11, Rania has 7. How many more does Omar have?",
            "تحقق صغير: عمر لديه 11 ورانيا لديها 7. كم لدى عمر أكثر؟",
            scale=0.48
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        case = ComparisonCase(a_name="Omar", b_name="Rania", a_qty=11, b_qty=7, question_type="difference", context_item="books")
        g = self.run_case(case)
        self.wait(0.4)
        self.play(FadeOut(g), run_time=self.s.rt_fast)

    def step_outro(self):
        recap = VGroup(
            T(self.cfg, self.s, "Recap:", "الخلاصة:", scale=0.6),
            T(self.cfg, self.s, "• Identify bigger, smaller, and difference", "• نحدد الأكبر والأصغر والفرق", scale=0.50),
            T(self.cfg, self.s, "• Align from the same start point", "• نحاذي من نفس نقطة البداية", scale=0.50),
            T(self.cfg, self.s, "• Difference = extra part after the common part", "• الفرق = الجزء الزائد بعد المشترك", scale=0.50),
            T(self.cfg, self.s, "• Choose + or − from the question", "• نختار + أو − حسب السؤال", scale=0.50),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        recap.to_edge(RIGHT).shift(DOWN * 0.15)
        self.play(FadeIn(recap, shift=LEFT * 0.2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(recap, shift=RIGHT * 0.2), FadeOut(self.title), run_time=self.s.rt_fast)


# ============================================================
# RUN:
#   manim -pqh your_file.py M3_L17_ComparisonWordProblems
#
# CUSTOMIZE:
#   cfg = LessonConfigM3_L17(
#       cases=[ComparisonCase(a_name="Ali", b_name="Mona", a_qty=14, b_qty=9, context_item="coins")],
#       language="ar"
#   )
# ============================================================
