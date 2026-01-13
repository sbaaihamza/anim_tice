from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Callable

import numpy as np
from manim import *


# ============================================================
# Config / Styles
# ============================================================

@dataclass
class BarModelStyle:
    total_units: int = 12            # total quantity (e.g., 12 items)
    part_size: int = 3               # size of one part (for case B) OR number of parts (for case A)
    # Visual sizing
    unit_width: float = 0.55
    bar_height: float = 0.55
    bar_stroke_width: float = 3.5
    unit_stroke_width: float = 2.0
    corner_radius: float = 0.12

    # Labels
    font_size_main: int = 34
    font_size_small: int = 28
    show_arabic: bool = False  # turn ON if Arabic renders well in your environment

    # Animation pacing
    pause: float = 0.45
    rt_fast: float = 0.7
    rt_norm: float = 1.0
    rt_slow: float = 1.2

    # Presentation toggles
    show_division_expression: bool = True
    show_reset_between_cases: bool = True


@dataclass
class LessonConfigM3_L22:
    """
    Use the same numbers, change only the question (semantic switch).
    Example defaults:
      total = 12
      case A (find value of one part): 12 ÷ 4 = 3  (4 equal parts, find each part)
      case B (find number of parts):   12 ÷ 3 = 4  (parts of size 3, find how many parts)
    """
    total: int = 12
    parts_count: int = 4       # for case A: number of equal parts is known
    part_value: int = 3        # for case B: value of one part is known

    # Titles
    title_en: str = "Division problems: find a part or the number of parts"
    title_ar: str = "حل مسائل القسمة للبحث عن الجزء أو عدد الأجزاء"

    # Questions (verbal layer)
    question_A_en: str = "We share 12 items equally among 4 groups. How many items in 1 group?"
    question_A_ar: str = "نقسم 12 بالتساوي على 4 مجموعات. كم عنصرًا في مجموعة واحدة؟"

    question_B_en: str = "We make groups of 3 from 12 items. How many groups can we make?"
    question_B_ar: str = "نكوّن مجموعات من 3 عناصر من أصل 12. كم مجموعة يمكن تكوينها؟"

    # Labels for meanings
    meaning_A_en: str = "Quotient = value of one part"
    meaning_A_ar: str = "خارج القسمة = قيمة الجزء"

    meaning_B_en: str = "Quotient = number of parts"
    meaning_B_ar: str = "خارج القسمة = عدد الأجزاء"

    # Layout
    language: str = "en"  # "en" or "ar"


# ============================================================
# Reusable primitives (Bar / Groups)
# ============================================================

class UnitBar(VGroup):
    """
    A bar subdivided into 'total_units' equal unit cells.
    You can also highlight groups (chunks) to represent equal parts.
    """
    def __init__(self, total_units: int, style: BarModelStyle, **kwargs):
        super().__init__(**kwargs)
        self.total_units = total_units
        self.style = style

        W = total_units * style.unit_width
        H = style.bar_height

        outer = RoundedRectangle(
            width=W,
            height=H,
            corner_radius=style.corner_radius,
            stroke_width=style.bar_stroke_width
        ).set_fill(opacity=0.05)

        # unit separators
        separators = VGroup()
        x0 = -W / 2
        for i in range(1, total_units):
            x = x0 + i * style.unit_width
            separators.add(
                Line(
                    start=np.array([x, -H / 2, 0]),
                    end=np.array([x, H / 2, 0]),
                    stroke_width=style.unit_stroke_width,
                ).set_stroke(opacity=0.5)
            )

        self.outer = outer
        self.separators = separators
        self.add(outer, separators)

    def group_boxes_by_count(self, parts_count: int) -> VGroup:
        """
        Partition the bar into `parts_count` equal groups.
        Returns boxes (one per group).
        Assumes total_units divisible by parts_count.
        """
        units_per_part = self.total_units // parts_count
        return self.group_boxes_by_size(units_per_part)

    def group_boxes_by_size(self, part_size: int) -> VGroup:
        """
        Partition the bar into groups of `part_size` units.
        Returns boxes (one per group).
        Assumes total_units divisible by part_size.
        """
        style = self.style
        W = self.total_units * style.unit_width
        H = style.bar_height
        x0 = -W / 2

        n_groups = self.total_units // part_size
        boxes = VGroup()
        for g in range(n_groups):
            start_unit = g * part_size
            x_start = x0 + start_unit * style.unit_width
            box_w = part_size * style.unit_width
            box = RoundedRectangle(
                width=box_w,
                height=H,
                corner_radius=style.corner_radius * 0.7,
                stroke_width=style.bar_stroke_width,
            ).set_fill(opacity=0.10)
            box.move_to(np.array([x_start + box_w / 2, 0.0, 0.0]))
            boxes.add(box)
        return boxes


def question_mark(style: BarModelStyle) -> Mobject:
    return Text("?", font_size=style.font_size_main).set_stroke(width=0)


# ============================================================
# Lesson Scene (Reusable / Adjustable / Extensible)
# ============================================================

class M3_L22_DivisionSemanticSwitch(Scene):
    """
    M3_L22 — Division problems to find a part or the number of parts

    Key idea:
      Same operation family (division) answers different questions.
      We keep the TOTAL constant, and keep a consistent model,
      but we switch *what is unknown*:
        Case A: unknown = value of one part
        Case B: unknown = number of parts

    Extensibility:
      - Add new pairs of problems with same total.
      - Swap bar model to containers/circles.
      - Add "student justification" overlays and formative checks.
    """

    def __init__(
        self,
        cfg: LessonConfigM3_L22 = LessonConfigM3_L22(),
        style: BarModelStyle = BarModelStyle(),
        **kwargs
    ):
        super().__init__(**kwargs)
        self.cfg = cfg
        self.style = style
        self.steps: List[Tuple[str, Callable[[], None]]] = []

    # ----------------------------
    # Orchestrator
    # ----------------------------

    def construct(self):
        self.build_steps()
        for _, fn in self.steps:
            fn()
            self.wait(self.style.pause)

    def build_steps(self):
        self.steps = [
            ("intro", self.step_intro),
            ("exploration_pair_problems", self.step_exploration_pair_problems),
            ("case_A_find_part_value", self.step_case_A_find_part_value),
            ("reset", self.step_reset_visual),
            ("case_B_find_number_of_parts", self.step_case_B_find_number_of_parts),
            ("institutionalization", self.step_institutionalization),
            ("outro", self.step_outro),
        ]

    # ----------------------------
    # Text helpers
    # ----------------------------

    def t(self, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
        text = en if self.cfg.language == "en" else (ar or en)
        return Text(text, font_size=38).scale(scale)

    def m(self, latex: str, scale: float = 1.0) -> Mobject:
        return MathTex(latex).scale(scale)

    def top_banner(self, text: Mobject) -> Mobject:
        text.to_edge(UP)
        return text

    # ----------------------------
    # Visual helpers
    # ----------------------------

    def build_model(self) -> UnitBar:
        bar = UnitBar(total_units=self.cfg.total, style=self.style)
        bar.move_to(ORIGIN + DOWN * 0.2)
        return bar

    def build_div_expr(self, a: int, b: int) -> Mobject:
        # Keep expression visible and "constant" in layout (same place)
        expr = self.m(fr"{a} \div {b} = \ ?").scale(1.0)
        expr.to_edge(UP).shift(DOWN * 1.0)
        return expr

    # ============================================================
    # Steps (match your guideline flow)
    # ============================================================

    def step_intro(self):
        title = self.t(self.cfg.title_en, self.cfg.title_ar, scale=0.62)
        title = self.top_banner(title)
        subtitle = self.t(
            "Same numbers, different question → different meaning",
            "نفس الأعداد، سؤال مختلف → معنى مختلف",
            scale=0.52,
        ).next_to(title, DOWN, buff=0.18)

        self.play(Write(title), FadeIn(subtitle, shift=DOWN * 0.15), run_time=self.style.rt_norm)
        self.wait(0.2)
        self.play(FadeOut(subtitle, shift=UP * 0.1), run_time=self.style.rt_fast)

        self.title = title

    def step_exploration_pair_problems(self):
        # display total quantity visually
        bar = self.build_model()
        total_label = self.t(f"Total = {self.cfg.total}", f"المجموع = {self.cfg.total}", scale=0.55)
        total_label.next_to(bar, UP, buff=0.25)

        self.play(Create(bar), FadeIn(total_label, shift=UP * 0.1), run_time=self.style.rt_norm)

        # two question cards (A and B) with same total but different question
        qA = self.t(self.cfg.question_A_en, self.cfg.question_A_ar, scale=0.48)
        qB = self.t(self.cfg.question_B_en, self.cfg.question_B_ar, scale=0.48)
        cardA = SurroundingRectangle(qA, buff=0.2)
        cardB = SurroundingRectangle(qB, buff=0.2)
        VGroup(VGroup(qA, cardA), VGroup(qB, cardB)).arrange(DOWN, buff=0.25).to_edge(RIGHT).shift(DOWN * 0.1)

        self.play(FadeIn(qA), Create(cardA), run_time=self.style.rt_norm)
        self.play(FadeIn(qB), Create(cardB), run_time=self.style.rt_norm)

        hint = self.t(
            "Look carefully: what is the unknown?",
            "انتبه: ما المجهول؟",
            scale=0.52,
        ).to_edge(DOWN)

        self.play(FadeIn(hint, shift=UP * 0.1), run_time=self.style.rt_fast)

        self.bar = bar
        self.total_label = total_label
        self.q_cards = VGroup(qA, cardA, qB, cardB)
        self.hint = hint

    def step_case_A_find_part_value(self):
        """
        Case A: Known number of parts (groups). Unknown is the value of one part.
        Keep the model: same total bar. Partition by parts_count.
        """
        # highlight question A
        qA, cardA, qB, cardB = self.q_cards
        self.play(cardA.animate.set_stroke(width=6), cardB.animate.set_stroke(width=2), run_time=self.style.rt_fast)

        # keep division expression "constant"
        if self.style.show_division_expression:
            expr = self.build_div_expr(self.cfg.total, self.cfg.parts_count)
            self.play(Write(expr), run_time=self.style.rt_norm)
        else:
            expr = None

        # show equal parts structure
        boxes = self.bar.group_boxes_by_count(self.cfg.parts_count)
        boxes.set_stroke(opacity=1.0)
        self.play(LaggedStartMap(FadeIn, boxes, shift=UP * 0.05, lag_ratio=0.07), run_time=self.style.rt_norm)

        # Unknown marker on ONE part (value of one part unknown)
        one_box = boxes[0].copy()
        one_box.set_fill(opacity=0.20)
        qm = question_mark(self.style).move_to(one_box.get_center())
        self.play(one_box.animate.set_stroke(width=6), FadeIn(qm, scale=0.9), run_time=self.style.rt_fast)

        # Reveal value of the part
        part_value = self.cfg.total // self.cfg.parts_count
        reveal = self.t(f"One part = {part_value}", f"قيمة الجزء = {part_value}", scale=0.55)
        reveal.to_edge(DOWN)

        meaning = self.t(self.cfg.meaning_A_en, self.cfg.meaning_A_ar, scale=0.52).next_to(reveal, UP, buff=0.18)

        if expr:
            new_expr = self.m(fr"{self.cfg.total} \div {self.cfg.parts_count} = {part_value}").scale(1.0)
            new_expr.move_to(expr.get_center())
            self.play(Transform(expr, new_expr), run_time=self.style.rt_norm)

        self.play(FadeOut(qm), FadeIn(reveal, shift=UP * 0.1), FadeIn(meaning, shift=UP * 0.1), run_time=self.style.rt_norm)

        self.caseA_boxes = boxes
        self.caseA_focus = VGroup(one_box, reveal, meaning, expr) if expr else VGroup(one_box, reveal, meaning)

    def step_reset_visual(self):
        if not self.style.show_reset_between_cases:
            return

        # Fade out case A overlays but keep total bar & question cards
        if hasattr(self, "caseA_boxes"):
            self.play(FadeOut(self.caseA_boxes), run_time=self.style.rt_fast)
        if hasattr(self, "caseA_focus"):
            self.play(FadeOut(self.caseA_focus), run_time=self.style.rt_fast)

        reset_msg = self.t("Same total… now a different question.", "نفس المجموع... لكن سؤال مختلف.", scale=0.55)
        reset_msg.to_edge(DOWN)
        self.play(Transform(self.hint, reset_msg), run_time=self.style.rt_norm)
        self.wait(0.2)
        self.play(FadeOut(self.hint), run_time=self.style.rt_fast)

    def step_case_B_find_number_of_parts(self):
        """
        Case B: Known part value (group size). Unknown is how many parts.
        Keep the model: same total bar. Partition by part_value.
        """
        # highlight question B
        qA, cardA, qB, cardB = self.q_cards
        self.play(cardB.animate.set_stroke(width=6), cardA.animate.set_stroke(width=2), run_time=self.style.rt_fast)

        # keep division expression "constant"
        if self.style.show_division_expression:
            expr = self.build_div_expr(self.cfg.total, self.cfg.part_value)
            self.play(Write(expr), run_time=self.style.rt_norm)
        else:
            expr = None

        # show equal parts structure: groups of size = part_value
        boxes = self.bar.group_boxes_by_size(self.cfg.part_value)
        self.play(LaggedStartMap(FadeIn, boxes, shift=UP * 0.05, lag_ratio=0.07), run_time=self.style.rt_norm)

        # Unknown marker on NUMBER OF PARTS (a brace with ?)
        n_parts = self.cfg.total // self.cfg.part_value
        brace = Brace(boxes, DOWN, buff=0.15)
        qm = question_mark(self.style).next_to(brace, DOWN, buff=0.1)

        self.play(GrowFromCenter(brace), FadeIn(qm, scale=0.9), run_time=self.style.rt_norm)

        # Reveal: count parts
        count_labels = VGroup()
        for i, b in enumerate(boxes):
            lbl = Text(str(i + 1), font_size=self.style.font_size_small).scale(0.8)
            lbl.move_to(b.get_center())
            count_labels.add(lbl)

        self.play(LaggedStartMap(FadeIn, count_labels, lag_ratio=0.05), run_time=self.style.rt_norm)

        reveal = self.t(f"Number of parts = {n_parts}", f"عدد الأجزاء = {n_parts}", scale=0.55).to_edge(DOWN)
        meaning = self.t(self.cfg.meaning_B_en, self.cfg.meaning_B_ar, scale=0.52).next_to(reveal, UP, buff=0.18)

        if expr:
            new_expr = self.m(fr"{self.cfg.total} \div {self.cfg.part_value} = {n_parts}").scale(1.0)
            new_expr.move_to(expr.get_center())
            self.play(Transform(expr, new_expr), run_time=self.style.rt_norm)

        self.play(FadeOut(qm), FadeIn(reveal, shift=UP * 0.1), FadeIn(meaning, shift=UP * 0.1), run_time=self.style.rt_norm)

        self.caseB_group = VGroup(boxes, brace, count_labels, reveal, meaning, expr) if expr else VGroup(
            boxes, brace, count_labels, reveal, meaning
        )

    def step_institutionalization(self):
        """
        Formalize the distinction: same division family, different unknown → different meaning.
        """
        rule_title = self.t("Institutionalization", "التثبيت", scale=0.6).to_edge(UP)

        box = RoundedRectangle(width=11.5, height=2.5, corner_radius=0.25).to_edge(DOWN).shift(UP * 0.2)
        box.set_fill(opacity=0.06).set_stroke(width=3)

        line1 = self.t("Find the value of one part → quotient = part value", "البحث عن قيمة الجزء → خارج القسمة = قيمة الجزء", scale=0.50)
        line2 = self.t("Find the number of parts → quotient = number of parts", "البحث عن عدد الأجزاء → خارج القسمة = عدد الأجزاء", scale=0.50)
        rules = VGroup(line1, line2).arrange(DOWN, buff=0.22).move_to(box.get_center())

        self.play(Transform(self.title, rule_title), run_time=self.style.rt_fast)
        self.play(Create(box), FadeIn(rules, shift=UP * 0.1), run_time=self.style.rt_norm)

        self.rules_box = VGroup(box, rules)

    def step_outro(self):
        # quick formative signals list
        signals = VGroup(
            self.t("Formative check:", "تقويم مرحلي:", scale=0.58),
            self.t("• Did you identify what is known / unknown?", "• هل حدّدت المعطى والمجهول؟", scale=0.50),
            self.t("• Did you choose a model matching the unknown?", "• هل اخترت نموذجاً يناسب المجهول؟", scale=0.50),
            self.t("• Can you explain what the quotient represents?", "• هل تفسّر ماذا يمثل خارج القسمة؟", scale=0.50),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        signals.to_edge(RIGHT).shift(DOWN * 0.2)

        self.play(FadeIn(signals, shift=LEFT * 0.2), run_time=self.style.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(signals, shift=RIGHT * 0.2), FadeOut(self.rules_box), run_time=self.style.rt_fast)
        self.play(FadeOut(self.q_cards), FadeOut(self.total_label), FadeOut(self.bar), run_time=self.style.rt_fast)
        self.play(FadeOut(self.title), run_time=self.style.rt_fast)


# ============================================================
# Easy customization patterns
# ============================================================
#
# 1) Change the numbers but keep the semantic switch:
#    - total = 18
#    - parts_count = 6  -> 18 ÷ 6 = 3 (find part value)
#    - part_value  = 3  -> 18 ÷ 3 = 6 (find number of parts)
#
# 2) Add “containers” representation:
#    - Replace bar model with circles/boxes and move dots into containers.
#
# Run:
#   manim -pqh your_file.py M3_L22_DivisionSemanticSwitch
#
