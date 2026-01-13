from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable

import numpy as np
from manim import *


# ============================================================
# CONFIG / STYLES
# ============================================================

@dataclass
class PartValueDivStyle:
    stroke_width: float = 4.0
    fill_opacity: float = 0.14

    # bar model
    unit_width: float = 0.5
    bar_height: float = 0.62
    bar_corner_radius: float = 0.18
    partition_tick_h: float = 0.28

    # focus / highlight
    focus_buff: float = 0.12
    glow_width: float = 6.0

    # objects model (optional)
    dot_radius: float = 0.085
    dot_spacing: float = 0.18

    # text
    font_size_title: int = 38
    font_size_main: int = 34
    font_size_small: int = 28
    font_size_problem: int = 26

    # pacing
    pause: float = 0.45
    rt_fast: float = 0.7
    rt_norm: float = 1.0
    rt_slow: float = 1.25

    # toggles
    show_problem_text: bool = True
    show_bar_model: bool = True             # main model recommended
    show_objects_model: bool = False        # optional secondary view
    show_zoom_focus: bool = True            # zoom-ish focus by scaling/spotlight
    show_symbolic_link: bool = True
    show_context_answer: bool = True
    show_verify: bool = True

    # layout
    left_anchor_x: float = -5.2
    bar_y: float = 0.2
    focus_y: float = -1.3


@dataclass
class PartValueDivisionProblem:
    """
    Division where the unknown is: value of one equal part.

    Known:
      - total
      - n_parts
    Unknown:
      - part_value = total / n_parts
    """
    pid: str
    total: int
    n_parts: int
    item: str = "candies"
    container: str = "bags"  # parts are "bags", "kids", "plates", etc.
    question: str = ""
    answer: Optional[int] = None  # computed if None


@dataclass
class LessonConfigM3_L21:
    title_en: str = "Division: find the value of one part"
    title_ar: str = "حل مسائل قسمة للبحث عن قيمة الجزء"
    language: str = "en"  # "en" | "ar"

    prompt_total_en: str = "Step 1: Identify the TOTAL."
    prompt_total_ar: str = "الخطوة 1: نحدد المجموع."

    prompt_parts_en: str = "Step 2: Identify the NUMBER of equal parts."
    prompt_parts_ar: str = "الخطوة 2: نحدد عدد الأجزاء المتساوية."

    prompt_partition_en: str = "Step 3: Partition the whole into equal parts."
    prompt_partition_ar: str = "الخطوة 3: نقسم الكل إلى أجزاء متساوية."

    prompt_focus_en: str = "Step 4: Focus on ONE part: that's the quotient meaning."
    prompt_focus_ar: str = "الخطوة 4: نركز على جزء واحد: هذا معنى خارج القسمة."

    prompt_link_en: str = "Step 5: Link the part value to the division expression."
    prompt_link_ar: str = "الخطوة 5: نربط قيمة الجزء بعملية القسمة."

    problems: List[PartValueDivisionProblem] = field(default_factory=lambda: [
        PartValueDivisionProblem(
            pid="PV1",
            total=12,
            n_parts=3,
            item="apples",
            container="kids",
            question="12 apples are shared equally among 3 kids. How many apples does each kid get?"
        ),
        PartValueDivisionProblem(
            pid="PV2",
            total=20,
            n_parts=5,
            item="stickers",
            container="envelopes",
            question="20 stickers are divided equally into 5 envelopes. How many stickers are in one envelope?"
        ),
    ])


# ============================================================
# REUSABLE PRIMITIVES
# ============================================================

def T(cfg: LessonConfigM3_L21, s: PartValueDivStyle, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
    txt = en if cfg.language == "en" else (ar or en)
    return Text(txt, font_size=s.font_size_main).scale(scale)


def problem_box(text: str, s: PartValueDivStyle) -> VGroup:
    box = RoundedRectangle(width=11.6, height=2.1, corner_radius=0.25).set_stroke(width=3).set_fill(opacity=0.06)
    t = Paragraph(*text.split("\n"), alignment="left", font_size=s.font_size_problem).scale(0.95)
    t.move_to(box.get_center())
    return VGroup(box, t).to_edge(UP).shift(DOWN * 1.25)


class WholeBar(VGroup):
    def __init__(self, total_units: int, s: PartValueDivStyle, label: str = "", **kwargs):
        super().__init__(**kwargs)
        w = max(1.0, total_units * s.unit_width)
        rect = RoundedRectangle(width=w, height=s.bar_height, corner_radius=s.bar_corner_radius)
        rect.set_stroke(width=s.stroke_width).set_fill(opacity=s.fill_opacity)
        self.rect = rect
        self.total_units = total_units

        lab = Text(label, font_size=s.font_size_small).scale(0.65) if label else VGroup()
        if label:
            lab.next_to(rect, UP, buff=0.12)
        self.lab = lab
        self.add(rect, lab)

    def left(self):
        return self.rect.get_left()

    def right(self):
        return self.rect.get_right()


def partition_ticks(bar_rect: RoundedRectangle, n_parts: int, s: PartValueDivStyle) -> VGroup:
    # ticks at internal boundaries
    ticks = VGroup()
    left = bar_rect.get_left()
    width = bar_rect.width
    for i in range(1, n_parts):
        x = left[0] + width * i / n_parts
        t = Line(
            start=np.array([x, bar_rect.get_center()[1] - s.partition_tick_h / 2, 0]),
            end=np.array([x, bar_rect.get_center()[1] + s.partition_tick_h / 2, 0]),
            stroke_width=s.stroke_width
        )
        ticks.add(t)
    return ticks


def part_rect_from_partition(bar_rect: RoundedRectangle, n_parts: int, idx: int) -> Rectangle:
    # idx in [0..n_parts-1]
    left_x = bar_rect.get_left()[0] + bar_rect.width * idx / n_parts
    right_x = bar_rect.get_left()[0] + bar_rect.width * (idx + 1) / n_parts
    w = right_x - left_x
    r = Rectangle(width=w, height=bar_rect.height).set_stroke(width=0).set_fill(opacity=0.22)
    r.move_to(np.array([(left_x + right_x) / 2, bar_rect.get_center()[1], 0]))
    return r


def div_expr(total: int, n_parts: int, quotient: int, scale: float = 1.25) -> Mobject:
    return MathTex(rf"{total}\div {n_parts} = {quotient}").scale(scale)


# ============================================================
# LESSON SCENE
# ============================================================

class M3_L21_DivisionFindPartValue(Scene):
    """
    M3_L21 — Division problems to find the value of one part

    Key constraint:
      The quotient must be shown as ONE highlighted part (not number of parts).

    Visual flow:
      display total
      divide into known number of equal parts
      show all parts briefly
      highlight ONE part
      reveal its value
      link to division expression
    """

    def __init__(
        self,
        cfg: LessonConfigM3_L21 = LessonConfigM3_L21(),
        style: PartValueDivStyle = PartValueDivStyle(),
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
            ("exploration", self.step_exploration),
            ("collective_discussion", self.step_collective_discussion),
            ("institutionalization", self.step_institutionalization),
            ("mini_assessment", self.step_mini_assessment),
            ("outro", self.step_outro),
        ]

    def banner(self, mob: Mobject) -> Mobject:
        mob.to_edge(UP)
        return mob

    # ============================================================
    # Steps
    # ============================================================

    def step_intro(self):
        title = T(self.cfg, self.s, self.cfg.title_en, self.cfg.title_ar, scale=0.62)
        title = self.banner(title)

        subtitle = T(
            self.cfg, self.s,
            "Quotient = value of ONE equal part",
            "خارج القسمة = قيمة جزء واحد متساوٍ",
            scale=0.55
        ).next_to(title, DOWN, buff=0.18)

        self.play(Write(title), FadeIn(subtitle, shift=DOWN * 0.15), run_time=self.s.rt_norm)
        self.wait(0.2)
        self.play(FadeOut(subtitle, shift=UP * 0.1), run_time=self.s.rt_fast)
        self.title = title

    def step_exploration(self):
        for p in self.cfg.problems:
            g = self.animate_problem(p)
            self.wait(0.35)
            self.play(FadeOut(g), run_time=self.s.rt_fast)

    def step_collective_discussion(self):
        prompt = T(
            self.cfg, self.s,
            "Discussion: Why is the answer the value of ONE part?",
            "نقاش: لماذا الجواب هو قيمة جزء واحد؟",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        box = RoundedRectangle(width=11.6, height=2.9, corner_radius=0.25).to_edge(DOWN).shift(UP * 0.2)
        box.set_stroke(width=3).set_fill(opacity=0.06)

        l1 = T(self.cfg, self.s, "• Total is split into equal parts.", "• نقسم المجموع إلى أجزاء متساوية.", scale=0.52)
        l2 = T(self.cfg, self.s, "• Each part has the same value.", "• كل جزء له نفس القيمة.", scale=0.52)
        l3 = T(self.cfg, self.s, "• The quotient tells the value of one share.", "• الخارج يعطينا قيمة حصة واحدة.", scale=0.52)

        scaff = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(box.get_center())
        self.play(Create(box), FadeIn(scaff, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.5)
        self.play(FadeOut(VGroup(box, scaff)), run_time=self.s.rt_fast)

    def step_institutionalization(self):
        prompt = T(
            self.cfg, self.s,
            "Institutionalization: total ÷ number of parts = value of one part",
            "التثبيت: المجموع ÷ عدد الأجزاء = قيمة الجزء",
            scale=0.50
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        r = MathTex(r"\text{part value} = \frac{\text{total}}{\text{number of equal parts}}").scale(1.1)
        self.play(Write(r), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(r), run_time=self.s.rt_fast)

    def step_mini_assessment(self):
        prompt = T(
            self.cfg, self.s,
            "Mini-check: 18 flowers shared among 6 vases. Value of one part?",
            "تحقق صغير: 18 زهرة توزع على 6 مزهريات. ما قيمة جزء واحد؟",
            scale=0.50
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        p = PartValueDivisionProblem(
            pid="PV3",
            total=18,
            n_parts=6,
            item="flowers",
            container="vases",
            question="18 flowers are shared equally among 6 vases. How many flowers in one vase?"
        )
        g = self.animate_problem(p)
        self.wait(0.35)
        self.play(FadeOut(g), run_time=self.s.rt_fast)

    def step_outro(self):
        recap = VGroup(
            T(self.cfg, self.s, "Recap:", "الخلاصة:", scale=0.6),
            T(self.cfg, self.s, "• Known: total + number of equal parts", "• المعطيات: المجموع + عدد الأجزاء", scale=0.50),
            T(self.cfg, self.s, "• Unknown: value of ONE part", "• المجهول: قيمة جزء واحد", scale=0.50),
            T(self.cfg, self.s, "• Always highlight one part to interpret the quotient", "• نُبرز جزءاً واحداً لفهم معنى الخارج", scale=0.50),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        recap.to_edge(RIGHT).shift(DOWN * 0.15)
        self.play(FadeIn(recap, shift=LEFT * 0.2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(recap, shift=RIGHT * 0.2), FadeOut(self.title), run_time=self.s.rt_fast)

    # ============================================================
    # Core animation
    # ============================================================

    def animate_problem(self, prob: PartValueDivisionProblem) -> VGroup:
        total = prob.total
        n = prob.n_parts
        q = prob.answer if prob.answer is not None else total // n

        # problem text
        pb = VGroup()
        if self.s.show_problem_text:
            pb = problem_box(prob.question, self.s)
            self.play(FadeIn(pb, shift=DOWN * 0.1), run_time=self.s.rt_norm)

        # Step 1: total
        p1 = T(self.cfg, self.s, self.cfg.prompt_total_en, self.cfg.prompt_total_ar, scale=0.56)
        p1 = self.banner(p1).shift(DOWN * 0.9)
        self.play(Transform(self.title, p1), run_time=self.s.rt_fast)

        whole = WholeBar(total_units=total, s=self.s, label=f"Total = {total} {prob.item}")
        whole.move_to(np.array([0, self.s.bar_y, 0]))
        whole.shift(np.array([self.s.left_anchor_x, 0, 0]) - whole.left())
        self.play(Create(whole.rect), FadeIn(whole.lab, shift=UP * 0.05), run_time=self.s.rt_norm)

        # Step 2: number of parts
        p2 = T(self.cfg, self.s, self.cfg.prompt_parts_en, self.cfg.prompt_parts_ar, scale=0.56)
        p2 = self.banner(p2).shift(DOWN * 0.9)
        self.play(Transform(self.title, p2), run_time=self.s.rt_fast)

        parts_label = Text(f"{n} equal parts", font_size=self.s.font_size_small).scale(0.7)
        parts_label.next_to(whole.rect, DOWN, buff=0.25)
        self.play(FadeIn(parts_label, shift=UP * 0.05), run_time=self.s.rt_fast)

        # Step 3: partition the whole
        p3 = T(self.cfg, self.s, self.cfg.prompt_partition_en, self.cfg.prompt_partition_ar, scale=0.56)
        p3 = self.banner(p3).shift(DOWN * 0.9)
        self.play(Transform(self.title, p3), run_time=self.s.rt_fast)

        ticks = partition_ticks(whole.rect, n, self.s)
        self.play(Create(ticks), run_time=self.s.rt_norm)

        # show all parts briefly by flashing a light fill across segments
        segs = VGroup(*[part_rect_from_partition(whole.rect, n, i) for i in range(n)])
        self.play(FadeIn(segs, shift=UP * 0.03), run_time=self.s.rt_fast)
        self.wait(0.15)
        self.play(FadeOut(segs, shift=DOWN * 0.03), run_time=self.s.rt_fast)

        # Step 4: focus on ONE part
        p4 = T(self.cfg, self.s, self.cfg.prompt_focus_en, self.cfg.prompt_focus_ar, scale=0.50)
        p4 = self.banner(p4).shift(DOWN * 0.9)
        self.play(Transform(self.title, p4), run_time=self.s.rt_fast)

        focus_idx = 0  # you can change to pick any segment
        one_part = part_rect_from_partition(whole.rect, n, focus_idx)
        one_outline = SurroundingRectangle(one_part, buff=self.s.focus_buff).set_stroke(width=self.s.glow_width)
        one_q = Text("?", font_size=self.s.font_size_title).scale(0.85).move_to(one_part.get_center())

        self.play(FadeIn(one_part), Create(one_outline), FadeIn(one_q, shift=UP * 0.05), run_time=self.s.rt_norm)

        # reveal its value (the quotient)
        one_val = Text(str(q), font_size=self.s.font_size_title).scale(0.78).move_to(one_part.get_center())
        self.play(Transform(one_q, one_val), run_time=self.s.rt_norm)

        part_value_caption = Text(
            f"One {prob.container[:-1] if prob.container.endswith('s') else prob.container} = {q} {prob.item}",
            font_size=self.s.font_size_small
        ).scale(0.65).to_edge(DOWN).shift(UP * 1.0)

        if self.s.show_context_answer:
            self.play(FadeIn(part_value_caption, shift=UP * 0.05), run_time=self.s.rt_fast)

        # Step 5: link to division expression
        op = VGroup()
        if self.s.show_symbolic_link:
            p5 = T(self.cfg, self.s, self.cfg.prompt_link_en, self.cfg.prompt_link_ar, scale=0.56)
            p5 = self.banner(p5).shift(DOWN * 0.9)
            self.play(Transform(self.title, p5), run_time=self.s.rt_fast)

            expr = div_expr(total, n, q).to_edge(DOWN)
            self.play(Write(expr), run_time=self.s.rt_norm)
            op.add(expr)

        # verify (optional quick check by showing n parts * q = total)
        verify = VGroup()
        if self.s.show_verify:
            check = Text("✓", font_size=self.s.font_size_main).scale(0.7)
            if len(op):
                check.next_to(op[0], LEFT, buff=0.25)
            else:
                check.to_edge(DOWN)
            self.play(FadeIn(check, shift=UP * 0.05), run_time=self.s.rt_fast)
            verify.add(check)

        return VGroup(pb, whole, parts_label, ticks, one_part, one_outline, one_q, part_value_caption, op, verify)


# ============================================================
# RUN:
#   manim -pqh your_file.py M3_L21_DivisionFindPartValue
#
# CUSTOMIZE:
#   cfg = LessonConfigM3_L21(
#       problems=[PartValueDivisionProblem(pid="X", total=24, n_parts=6, item="balls", container="teams",
#                                          question="24 balls shared among 6 teams...")],
#       language="en"
#   )
# ============================================================
