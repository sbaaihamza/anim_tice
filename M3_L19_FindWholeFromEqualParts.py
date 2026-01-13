from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable

import numpy as np
from manim import *


# ============================================================
# CONFIG / STYLES
# ============================================================

@dataclass
class EqualPartsStyle:
    stroke_width: float = 4.0
    fill_opacity: float = 0.16

    # bars
    unit_width: float = 0.5       # visual width per 1 unit of value
    bar_height: float = 0.62
    bar_corner_radius: float = 0.18
    gap_between_parts: float = 0.14

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
    show_repeated_addition: bool = True
    show_implicit_multiplication: bool = True   # appears only after repetition
    show_grouping_braces: bool = True
    show_verify_step: bool = True

    # layout
    left_anchor_x: float = -5.2
    part_row_y: float = 0.4
    whole_row_y: float = -1.0


@dataclass
class EqualPartsProblem:
    """
    Find the whole from equal parts.
      - part_value: value of one part
      - n_parts: number of equal parts
      - whole = part_value * n_parts
    """
    part_value: int = 4
    n_parts: int = 5
    context: str = "Each bag has 4 candies. There are 5 bags. How many candies in total?"
    label_part: str = "one part"
    label_whole: str = "whole"
    answer: Optional[int] = None  # if None => computed


@dataclass
class LessonConfigM3_L19:
    title_en: str = "Finding the whole from equal parts"
    title_ar: str = "حل مسائل البحث عن الكل – أجزاء متساوية"
    language: str = "en"  # "en" | "ar"

    # prompts
    prompt_part_en: str = "We know ONE part."
    prompt_part_ar: str = "نعرف قيمة جزء واحد."

    prompt_repeat_en: str = "Repeat the same part the required number of times."
    prompt_repeat_ar: str = "نكرر نفس الجزء العدد المطلوب من المرات."

    prompt_merge_en: str = "Put parts end-to-end to build the whole."
    prompt_merge_ar: str = "نضع الأجزاء متجاورة لبناء الكل."

    prompt_calc_en: str = "Now write the calculation."
    prompt_calc_ar: str = "الآن نكتب الحساب."

    prompt_verify_en: str = "Check: does the model match the total?"
    prompt_verify_ar: str = "تحقق: هل النموذج يطابق المجموع؟"

    problems: List[EqualPartsProblem] = field(default_factory=lambda: [
        EqualPartsProblem(part_value=4, n_parts=5,
                          context="Each bag has 4 candies. There are 5 bags. How many candies in total?",
                          label_part="bag", label_whole="candies"),
        EqualPartsProblem(part_value=3, n_parts=6,
                          context="Each box has 3 pencils. There are 6 boxes. How many pencils altogether?",
                          label_part="box", label_whole="pencils"),
    ])


# ============================================================
# REUSABLE PRIMITIVES
# ============================================================

def T(cfg: LessonConfigM3_L19, s: EqualPartsStyle, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
    txt = en if cfg.language == "en" else (ar or en)
    return Text(txt, font_size=s.font_size_main).scale(scale)


def boxed_problem(text: str, s: EqualPartsStyle) -> VGroup:
    box = RoundedRectangle(width=11.6, height=2.1, corner_radius=0.25).set_stroke(width=3).set_fill(opacity=0.06)
    t = Paragraph(*text.split("\n"), alignment="left", font_size=26).scale(0.92)
    t.move_to(box.get_center())
    grp = VGroup(box, t).to_edge(UP).shift(DOWN * 1.25)
    return grp


class PartBar(VGroup):
    def __init__(self, value_units: int, s: EqualPartsStyle, label: str = "", **kwargs):
        super().__init__(**kwargs)
        w = max(0.8, value_units * s.unit_width)
        rect = RoundedRectangle(width=w, height=s.bar_height, corner_radius=s.bar_corner_radius)
        rect.set_stroke(width=s.stroke_width).set_fill(opacity=s.fill_opacity)
        self.rect = rect
        self.value_units = value_units

        value_txt = Text(str(value_units), font_size=s.font_size_small).scale(0.75).move_to(rect.get_center())
        self.value_txt = value_txt

        lab = Text(label, font_size=s.font_size_small).scale(0.65) if label else VGroup()
        if label:
            lab.next_to(rect, UP, buff=0.1)
        self.lab = lab

        self.add(rect, value_txt, lab)

    def left(self):
        return self.rect.get_left()

    def right(self):
        return self.rect.get_right()


def op_repeated_add(part: int, n: int) -> Mobject:
    # e.g., 4+4+4+4+4 = 20
    expr = "+".join([str(part)] * n)
    return MathTex(rf"{expr} = {part*n}").scale(1.2)


def op_mult(part: int, n: int) -> Mobject:
    return MathTex(rf"{n}\times {part} = {part*n}").scale(1.25)


# ============================================================
# LESSON SCENE (Reusable / Adjustable / Extensible)
# ============================================================

class M3_L19_FindWholeFromEqualParts(Scene):
    """
    M3_L19 — Find the whole from equal parts

    Visual flow:
      display single part with its value
      duplicate part visually (n times)
      align parts end-to-end
      merge into one whole bar
      highlight whole
      reveal total value
      (optional) show repeated addition then implicit multiplication

    Avoid:
      starting with multiplication symbol; skipping repetition.
    """

    def __init__(
        self,
        cfg: LessonConfigM3_L19 = LessonConfigM3_L19(),
        style: EqualPartsStyle = EqualPartsStyle(),
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
            "Whole = several equal parts put together",
            "الكل = عدة أجزاء متساوية مجتمعة",
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
            "Discussion: Why do we get the same total?",
            "نقاش: لماذا نحصل على نفس المجموع؟",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        box = RoundedRectangle(width=11.6, height=2.9, corner_radius=0.25).to_edge(DOWN).shift(UP * 0.2)
        box.set_stroke(width=3).set_fill(opacity=0.06)

        l1 = T(self.cfg, self.s, "• Each part has the same value.", "• كل جزء له نفس القيمة.", scale=0.52)
        l2 = T(self.cfg, self.s, "• Repeating parts adds the same amount each time.", "• تكرار الأجزاء يعني جمع نفس المقدار.", scale=0.52)
        l3 = T(self.cfg, self.s, "• The whole is the sum of all parts.", "• الكل هو مجموع الأجزاء.", scale=0.52)

        scaff = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(box.get_center())
        self.play(Create(box), FadeIn(scaff, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.5)
        self.play(FadeOut(VGroup(box, scaff)), run_time=self.s.rt_fast)

    def step_institutionalization(self):
        prompt = T(
            self.cfg, self.s,
            "Institutionalization: Whole from equal parts",
            "التثبيت: الكل من أجزاء متساوية",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        rule1 = MathTex(r"\text{Whole} = \underbrace{\text{part} + \text{part} + \cdots + \text{part}}_{\text{n times}}").scale(1.0)
        rule2 = MathTex(r"\text{Whole} = n \times \text{part}").scale(1.15).next_to(rule1, DOWN, buff=0.25)

        self.play(Write(rule1), run_time=self.s.rt_norm)
        self.play(Write(rule2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(VGroup(rule1, rule2)), run_time=self.s.rt_fast)

    def step_mini_assessment(self):
        prompt = T(
            self.cfg, self.s,
            "Mini-check: One part = 7. Number of equal parts = 4. Find the whole.",
            "تحقق صغير: جزء واحد = 7، وعدد الأجزاء = 4. أوجد الكل.",
            scale=0.50
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        p = EqualPartsProblem(
            part_value=7,
            n_parts=4,
            context="One part is 7. There are 4 equal parts. What is the whole?",
            label_part="part",
            label_whole="whole"
        )
        g = self.animate_problem(p)
        self.wait(0.35)
        self.play(FadeOut(g), run_time=self.s.rt_fast)

    def step_outro(self):
        recap = VGroup(
            T(self.cfg, self.s, "Recap:", "الخلاصة:", scale=0.6),
            T(self.cfg, self.s, "• Identify one part value", "• نحدد قيمة جزء واحد", scale=0.50),
            T(self.cfg, self.s, "• Identify number of equal parts", "• نحدد عدد الأجزاء المتساوية", scale=0.50),
            T(self.cfg, self.s, "• Repeat and assemble to build the whole", "• نكرر ونجمع لبناء الكل", scale=0.50),
            T(self.cfg, self.s, "• Then write the calculation", "• ثم نكتب الحساب", scale=0.50),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        recap.to_edge(RIGHT).shift(DOWN * 0.15)
        self.play(FadeIn(recap, shift=LEFT * 0.2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(recap, shift=RIGHT * 0.2), FadeOut(self.title), run_time=self.s.rt_fast)

    # ============================================================
    # Core animation for one problem
    # ============================================================

    def animate_problem(self, prob: EqualPartsProblem) -> VGroup:
        part = prob.part_value
        n = prob.n_parts
        total = prob.answer if prob.answer is not None else part * n

        # show problem text
        pb = boxed_problem(prob.context, self.s).set_opacity(1.0)
        self.play(FadeIn(pb, shift=DOWN * 0.1), run_time=self.s.rt_norm)

        # prompt: we know one part
        p1 = T(self.cfg, self.s, self.cfg.prompt_part_en, self.cfg.prompt_part_ar, scale=0.56)
        p1 = self.banner(p1).shift(DOWN * 0.9)
        self.play(Transform(self.title, p1), run_time=self.s.rt_fast)

        part_bar = PartBar(part, self.s, label=f"{prob.label_part} = {part}")
        part_bar.move_to(np.array([-2.0, self.s.part_row_y, 0]))
        part_bar.shift(np.array([self.s.left_anchor_x, 0, 0]) - part_bar.left())
        self.play(Create(part_bar.rect), FadeIn(part_bar.value_txt), FadeIn(part_bar.lab, shift=UP * 0.05), run_time=self.s.rt_norm)

        # duplicate part visually n times
        p2 = T(self.cfg, self.s, self.cfg.prompt_repeat_en, self.cfg.prompt_repeat_ar, scale=0.56)
        p2 = self.banner(p2).shift(DOWN * 0.9)
        self.play(Transform(self.title, p2), run_time=self.s.rt_fast)

        parts = VGroup(part_bar)
        for i in range(2, n + 1):
            clone = PartBar(part, self.s, label="")
            # position next to last
            clone.move_to(parts[-1].get_center())
            clone.shift((parts[-1].right() + RIGHT * self.s.gap_between_parts) - clone.left())
            # animate appearance
            self.play(FadeIn(clone, shift=RIGHT * 0.1), run_time=self.s.rt_fast)
            parts.add(clone)

        # braces/group label
        braces = VGroup()
        if self.s.show_grouping_braces:
            br = Brace(parts, direction=UP)
            br_lab = Text(f"{n} equal parts", font_size=self.s.font_size_small).scale(0.7).next_to(br, UP, buff=0.08)
            braces = VGroup(br, br_lab)
            self.play(GrowFromCenter(br), FadeIn(br_lab, shift=UP * 0.05), run_time=self.s.rt_fast)

        # merge into one whole bar
        p3 = T(self.cfg, self.s, self.cfg.prompt_merge_en, self.cfg.prompt_merge_ar, scale=0.56)
        p3 = self.banner(p3).shift(DOWN * 0.9)
        self.play(Transform(self.title, p3), run_time=self.s.rt_fast)

        whole_bar = PartBar(total, self.s, label=f"{prob.label_whole} = ?")
        whole_bar.move_to(np.array([0, self.s.whole_row_y, 0]))
        whole_bar.shift((parts[0].left() - whole_bar.left()))  # same start
        whole_q = Text("?", font_size=self.s.font_size_title).scale(0.85).move_to(whole_bar.rect.get_center())

        self.play(Create(whole_bar.rect), FadeIn(whole_bar.lab, shift=UP * 0.05), FadeIn(whole_q, shift=UP * 0.05), run_time=self.s.rt_norm)

        # highlight complete whole + reveal total
        highlight = SurroundingRectangle(whole_bar.rect, buff=0.12).set_stroke(width=5)
        self.play(Create(highlight), run_time=self.s.rt_fast)

        total_txt = Text(str(total), font_size=self.s.font_size_title).scale(0.75).move_to(whole_bar.rect.get_center())
        self.play(Transform(whole_q, total_txt), run_time=self.s.rt_norm)
        whole_bar.lab.become(Text(f"{prob.label_whole} = {total}", font_size=self.s.font_size_small).scale(0.65).next_to(whole_bar.rect, UP, buff=0.1))

        # reveal calculation only after construction
        p4 = T(self.cfg, self.s, self.cfg.prompt_calc_en, self.cfg.prompt_calc_ar, scale=0.56)
        p4 = self.banner(p4).shift(DOWN * 0.9)
        self.play(Transform(self.title, p4), run_time=self.s.rt_fast)

        ops = VGroup()
        if self.s.show_repeated_addition:
            add = op_repeated_add(part, n).to_edge(DOWN)
            self.play(Write(add), run_time=self.s.rt_norm)
            ops.add(add)

        if self.s.show_implicit_multiplication:
            mult = op_mult(part, n).to_edge(DOWN)
            if len(ops) > 0:
                self.play(Transform(ops[0], mult), run_time=self.s.rt_norm)
                ops = VGroup(mult)
            else:
                self.play(Write(mult), run_time=self.s.rt_norm)
                ops.add(mult)

        # verify step (map back)
        verify = VGroup()
        if self.s.show_verify_step:
            p5 = T(self.cfg, self.s, self.cfg.prompt_verify_en, self.cfg.prompt_verify_ar, scale=0.56)
            p5 = self.banner(p5).shift(DOWN * 0.9)
            self.play(Transform(self.title, p5), run_time=self.s.rt_fast)

            check = Text("✓", font_size=self.s.font_size_title).scale(0.75).next_to(ops, LEFT, buff=0.3) if len(ops) else Text("✓", font_size=self.s.font_size_title).scale(0.75).to_edge(DOWN)
            verify = VGroup(check)
            self.play(FadeIn(check, shift=UP * 0.05), run_time=self.s.rt_fast)

        return VGroup(pb, parts, braces, whole_bar, whole_q, highlight, ops, verify)


# ============================================================
# RUN:
#   manim -pqh your_file.py M3_L19_FindWholeFromEqualParts
#
# CUSTOMIZE:
#   cfg = LessonConfigM3_L19(
#       problems=[EqualPartsProblem(part_value=6, n_parts=7, context="7 groups, each has 6...")],
#       language="ar"
#   )
# ============================================================

