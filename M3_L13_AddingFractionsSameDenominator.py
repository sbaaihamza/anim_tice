from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Dict

import numpy as np
from manim import *


# ============================================================
# CONFIG / STYLES
# ============================================================

@dataclass
class AddFracStyle:
    # Bar geometry
    whole_width: float = 7.0
    whole_height: float = 1.15
    corner_radius: float = 0.20
    stroke_width: float = 4.0
    fill_opacity: float = 0.22

    # Text sizes
    font_size_title: int = 38
    font_size_main: int = 34
    font_size_small: int = 28

    # Animation pacing
    pause: float = 0.45
    rt_fast: float = 0.7
    rt_norm: float = 1.0
    rt_slow: float = 1.25

    # Toggles / extensions
    show_arabic: bool = False          # enable only if Arabic fonts render correctly
    show_why_same_denominator: bool = True
    show_number_line_optional: bool = False
    show_mixed_form_if_ge_1: bool = True  # gentle, only if sum >= 1

    # Visual affordances
    show_counter_ticks: bool = True
    counter_scale: float = 0.8


@dataclass
class AddFractionsExample:
    """
    Example: a/n + b/n
    """
    a: int = 1
    b: int = 2
    n: int = 4  # denominator


@dataclass
class LessonConfigM3_L13:
    title_en: str = "Adding fractions"
    title_ar: str = "جمع الأعداد الكسرية"
    language: str = "en"  # "en" | "ar"

    # Prompts (verbal scaffolding)
    prompt_model_en: str = "Model both fractions on the SAME whole."
    prompt_model_ar: str = "مثّل الكسرين على نفس الكل."

    prompt_partition_en: str = "We lock the partition: same denominator = same-size parts."
    prompt_partition_ar: str = "نثبت التقسيم: نفس المقام = أجزاء متساوية الحجم."

    prompt_shade1_en: str = "Shade the first fraction."
    prompt_shade1_ar: str = "ظلّل الكسر الأول."

    prompt_shade2_en: str = "Shade the second fraction using the SAME partition."
    prompt_shade2_ar: str = "ظلّل الكسر الثاني باستعمال نفس التقسيم."

    prompt_combine_en: str = "Combine the shaded parts and count."
    prompt_combine_ar: str = "ادمج الأجزاء المظللة ثم عدّها."

    prompt_symbol_en: str = "Now we write it as a fraction addition:"
    prompt_symbol_ar: str = "الآن نكتب الجمع بالكسر:"

    prompt_wholecheck_en: str = "Does the sum make a whole (1) or more?"
    prompt_wholecheck_ar: str = "هل المجموع يساوي كلاً (1) أو أكثر؟"

    # Default examples (extend list)
    examples: List[AddFractionsExample] = field(default_factory=lambda: [
        AddFractionsExample(a=1, b=2, n=4),  # 1/4 + 2/4 = 3/4
        AddFractionsExample(a=3, b=2, n=5),  # 3/5 + 2/5 = 5/5 = 1
        AddFractionsExample(a=3, b=4, n=6),  # 3/6 + 4/6 = 7/6 (>=1)
    ])


# ============================================================
# REUSABLE PRIMITIVES
# ============================================================

def T(cfg: LessonConfigM3_L13, s: AddFracStyle, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
    txt = en if cfg.language == "en" else (ar or en)
    return Text(txt, font_size=s.font_size_main).scale(scale)


def frac_tex(n: int, d: int, scale: float = 1.25) -> Mobject:
    return MathTex(rf"\frac{{{n}}}{{{d}}}").scale(scale)


def add_expr_tex(a: int, b: int, n: int, scale: float = 1.15) -> Mobject:
    return MathTex(rf"\frac{{{a}}}{{{n}}} + \frac{{{b}}}{{{n}}} = \frac{{{a+b}}}{{{n}}}").scale(scale)


def mixed_tex(num: int, den: int, scale: float = 1.1) -> Mobject:
    whole = num // den
    rem = num % den
    if rem == 0:
        return MathTex(rf"{whole}").scale(scale)
    return MathTex(rf"{whole}\ \frac{{{rem}}}{{{den}}}").scale(scale)


class FractionBar(VGroup):
    """
    A bar partitioned into n equal parts.
    Can shade specified indices or first k parts.
    """
    def __init__(self, n: int, style: AddFracStyle, **kwargs):
        super().__init__(**kwargs)
        self.n = n
        self.s = style

        outer = RoundedRectangle(
            width=style.whole_width,
            height=style.whole_height,
            corner_radius=style.corner_radius
        ).set_stroke(width=style.stroke_width).set_fill(opacity=0.0)

        lines = VGroup()
        x0 = -style.whole_width / 2
        for i in range(1, n):
            x = x0 + i * style.whole_width / n
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
        part_w = w / self.n
        x0 = -w / 2
        for i in range(self.n):
            box = Rectangle(width=part_w, height=h).set_stroke(width=0).set_fill(opacity=0.0)
            box.move_to([x0 + part_w * (i + 0.5), 0, 0])
            boxes.add(box)
        return boxes

    def shade_parts(self, indices: List[int]) -> VGroup:
        boxes = self.part_boxes()
        shaded = VGroup()
        for i in indices:
            if 0 <= i < len(boxes):
                b = boxes[i].copy().set_fill(opacity=self.s.fill_opacity).set_stroke(width=0)
                shaded.add(b)
        return shaded

    def shade_first_k(self, k: int) -> VGroup:
        return self.shade_parts(list(range(max(0, min(k, self.n)))))


def counter_above_bar(style: AddFracStyle, bar: FractionBar, count: int) -> VGroup:
    """
    Draw little tick labels over the first `count` parts to show counting.
    """
    if not style.show_counter_ticks:
        return VGroup()

    parts = bar.part_boxes()
    ticks = VGroup()
    for i in range(min(count, len(parts))):
        center = parts[i].get_center()
        lbl = Text(str(i + 1), font_size=style.font_size_small).scale(style.counter_scale)
        lbl.move_to(center + UP * (style.whole_height * 0.65))
        ticks.add(lbl)
    return ticks


# ============================================================
# LESSON SCENE (Reusable / Adjustable / Extensible)
# ============================================================

class M3_L13_AddingFractionsSameDenominator(Scene):
    """
    M3_L13 — Adding fractions (same denominator focus)

    Engine recipe:
      show_one_whole
      partition_into_n_equal_parts (denominator fixed)
      shade_a_parts for first fraction
      shade_b_parts for second fraction on same partition
      merge/count shaded parts
      reveal symbolic operation: a/n + b/n = (a+b)/n
      optional: if >= 1, show whole / mixed (gentle)
    """

    def __init__(
        self,
        cfg: LessonConfigM3_L13 = LessonConfigM3_L13(),
        style: AddFracStyle = AddFracStyle(),
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
            ("collective_discussion_why_denominator", self.step_collective_discussion_why_denominator),
            ("institutionalization_rule", self.step_institutionalization_rule),
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
            "Combine equal parts of the SAME whole",
            "نجمع أجزاء متساوية من نفس الكل",
            scale=0.52
        ).next_to(title, DOWN, buff=0.18)

        self.play(Write(title), FadeIn(subtitle, shift=DOWN * 0.15), run_time=self.s.rt_norm)
        self.wait(0.2)
        self.play(FadeOut(subtitle, shift=UP * 0.1), run_time=self.s.rt_fast)

        self.title = title

    # ------------------------------------------------------------
    # Core demo per example
    # ------------------------------------------------------------

    def run_example(self, ex: AddFractionsExample) -> VGroup:
        a, b, n = ex.a, ex.b, ex.n
        total = a + b

        # Prompt: model on same whole
        p = T(self.cfg, self.s, self.cfg.prompt_model_en, self.cfg.prompt_model_ar, scale=0.55)
        p = self.banner(p).shift(DOWN * 0.9)
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        # Build two aligned bars (same partition)
        bar1 = FractionBar(n, self.s).move_to(UP * 0.4)
        bar2 = FractionBar(n, self.s).move_to(DOWN * 0.9)

        self.play(Create(bar1), Create(bar2), run_time=self.s.rt_norm)

        # Lock partition (visual emphasis)
        p_lock = T(self.cfg, self.s, self.cfg.prompt_partition_en, self.cfg.prompt_partition_ar, scale=0.55)
        p_lock = self.banner(p_lock).shift(DOWN * 0.9)
        self.play(Transform(self.title, p_lock), run_time=self.s.rt_fast)
        lock_box1 = SurroundingRectangle(bar1, buff=0.08)
        lock_box2 = SurroundingRectangle(bar2, buff=0.08)
        self.play(Create(lock_box1), Create(lock_box2), run_time=self.s.rt_fast)
        self.play(FadeOut(lock_box1), FadeOut(lock_box2), run_time=self.s.rt_fast)

        # Shade first fraction
        p1 = T(self.cfg, self.s, self.cfg.prompt_shade1_en, self.cfg.prompt_shade1_ar, scale=0.55)
        p1 = self.banner(p1).shift(DOWN * 0.9)
        self.play(Transform(self.title, p1), run_time=self.s.rt_fast)

        shade1 = bar1.shade_first_k(a).move_to(bar1.get_center())
        lab1 = frac_tex(a, n, scale=1.25).next_to(bar1, LEFT, buff=0.6)
        self.play(FadeIn(shade1), Write(lab1), run_time=self.s.rt_norm)

        # Shade second fraction (same partition)
        p2 = T(self.cfg, self.s, self.cfg.prompt_shade2_en, self.cfg.prompt_shade2_ar, scale=0.55)
        p2 = self.banner(p2).shift(DOWN * 0.9)
        self.play(Transform(self.title, p2), run_time=self.s.rt_fast)

        shade2 = bar2.shade_first_k(b).move_to(bar2.get_center())
        lab2 = frac_tex(b, n, scale=1.25).next_to(bar2, LEFT, buff=0.6)
        self.play(FadeIn(shade2), Write(lab2), run_time=self.s.rt_norm)

        # Combine into one bar (merge filled parts)
        p3 = T(self.cfg, self.s, self.cfg.prompt_combine_en, self.cfg.prompt_combine_ar, scale=0.55)
        p3 = self.banner(p3).shift(DOWN * 0.9)
        self.play(Transform(self.title, p3), run_time=self.s.rt_fast)

        # Create a result bar (same partition) in the middle
        result_bar = FractionBar(n, self.s).move_to(DOWN * 0.25)
        self.play(Transform(bar2, result_bar.copy().move_to(bar2.get_center())), run_time=self.s.rt_fast)

        # Visually "move" shaded parts up into result:
        # We'll transform shade2 into a partial shading overlay added after shade1.
        result_shade = result_bar.shade_first_k(total).move_to(result_bar.get_center())

        # counter shows counting of parts (a+b)
        ticks = counter_above_bar(self.s, result_bar, total)

        # Merge: fade out the two bars into a single result
        self.play(
            Transform(bar1, result_bar),
            Transform(shade1, result_shade),
            FadeOut(bar2),
            FadeOut(shade2),
            FadeOut(lab2),
            run_time=self.s.rt_slow
        )

        self.play(FadeIn(ticks, shift=UP * 0.1), run_time=self.s.rt_norm)

        # Reveal symbolic operation last
        p4 = T(self.cfg, self.s, self.cfg.prompt_symbol_en, self.cfg.prompt_symbol_ar, scale=0.55)
        p4 = self.banner(p4).shift(DOWN * 0.9)
        self.play(Transform(self.title, p4), run_time=self.s.rt_fast)

        expr = add_expr_tex(a, b, n, scale=1.15).to_edge(DOWN)
        self.play(Write(expr), run_time=self.s.rt_norm)

        # Whole / exceed check
        check_group = VGroup()
        if self.s.show_mixed_form_if_ge_1:
            p5 = T(self.cfg, self.s, self.cfg.prompt_wholecheck_en, self.cfg.prompt_wholecheck_ar, scale=0.55)
            p5 = self.banner(p5).shift(DOWN * 0.9)
            self.play(Transform(self.title, p5), run_time=self.s.rt_fast)

            if total == n:
                tag = T(self.cfg, self.s, "It makes exactly 1 whole.", "يساوي كلاً واحداً تماماً.", scale=0.55)
                tag.next_to(expr, UP, buff=0.2)
                self.play(FadeIn(tag, shift=UP * 0.1), run_time=self.s.rt_fast)
                check_group = VGroup(tag)
            elif total > n:
                tag = T(self.cfg, self.s, "It is more than 1 whole.", "أكبر من 1.", scale=0.55)
                tag.next_to(expr, UP, buff=0.2)

                mix = mixed_tex(total, n, scale=1.15).next_to(tag, UP, buff=0.15)
                self.play(FadeIn(tag, shift=UP * 0.1), Write(mix), run_time=self.s.rt_norm)
                check_group = VGroup(tag, mix)

        # keep lab1 for reference but update to result label
        res_lab = frac_tex(total, n, scale=1.25).next_to(result_bar, LEFT, buff=0.6)
        self.play(Transform(lab1, res_lab), run_time=self.s.rt_fast)

        return VGroup(result_bar, shade1, lab1, ticks, expr, check_group)

    # ============================================================
    # Steps
    # ============================================================

    def step_exploration_examples(self):
        """
        Exploration: start from concrete/visual, shade and combine.
        """
        for ex in self.cfg.examples[:2]:
            group = self.run_example(ex)
            self.wait(0.4)
            self.play(FadeOut(group), run_time=self.s.rt_fast)

        # show one "sum >= 1" example if present
        for ex in self.cfg.examples[2:]:
            group = self.run_example(ex)
            self.wait(0.4)
            self.play(FadeOut(group), run_time=self.s.rt_fast)
            break

    def step_collective_discussion_why_denominator(self):
        """
        Students justify why denominator must be same (equal-sized parts).
        We optionally show a quick 'impossible to count together' moment.
        """
        prompt = T(
            self.cfg, self.s,
            "Discussion: Why must the denominator be the same?",
            "نقاش: لماذا يجب أن يكون المقام نفسه؟",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        # language scaffold card
        box = RoundedRectangle(width=11.6, height=2.8, corner_radius=0.25).to_edge(DOWN).shift(UP * 0.2)
        box.set_fill(opacity=0.06).set_stroke(width=3)

        l1 = T(self.cfg, self.s, "• Parts must be equal-sized to be counted together.", "• يجب أن تكون الأجزاء متساوية الحجم لنعدّها معاً.", scale=0.52)
        l2 = T(self.cfg, self.s, "• Same denominator = same partition.", "• نفس المقام = نفس التقسيم.", scale=0.52)
        l3 = T(self.cfg, self.s, "• Then we can combine shaded parts.", "• عندها يمكن دمج الأجزاء المظللة.", scale=0.52)
        scaff = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(box.get_center())

        self.play(Create(box), FadeIn(scaff, shift=UP * 0.1), run_time=self.s.rt_norm)

        if self.s.show_why_same_denominator:
            # quick visual contrast: 1/2 vs 1/3 cannot be “counted” directly
            a = FractionBar(2, self.s).scale(0.8).to_edge(LEFT).shift(UP * 0.7 + RIGHT * 0.9)
            b = FractionBar(3, self.s).scale(0.8).to_edge(LEFT).shift(DOWN * 0.5 + RIGHT * 0.9)
            sa = a.shade_first_k(1).move_to(a.get_center()).scale(0.8)
            sb = b.shade_first_k(1).move_to(b.get_center()).scale(0.8)

            msg = T(
                self.cfg, self.s,
                "Different partitions → parts are not the same size.",
                "تقسيم مختلف → الأجزاء ليست بنفس الحجم.",
                scale=0.50
            ).to_edge(RIGHT).shift(DOWN * 0.1 + LEFT * 0.2)

            self.play(Create(a), FadeIn(sa), Create(b), FadeIn(sb), FadeIn(msg, shift=LEFT * 0.1), run_time=self.s.rt_norm)
            self.wait(0.4)
            self.play(FadeOut(VGroup(a, sa, b, sb, msg)), run_time=self.s.rt_fast)

        self.wait(0.4)
        self.play(FadeOut(VGroup(box, scaff)), run_time=self.s.rt_fast)

    def step_institutionalization_rule(self):
        """
        Formalize the rule for same denominator cases, connected back to the model.
        """
        prompt = T(
            self.cfg, self.s,
            "Institutionalization: keep denominator, add numerators",
            "التثبيت: نحافظ على المقام ونجمع البسطين",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        rule = MathTex(r"\frac{a}{n} + \frac{b}{n} = \frac{a+b}{n}").scale(1.35).move_to(ORIGIN + UP * 0.2)
        note = T(
            self.cfg, self.s,
            "Because we are counting the same-size parts.",
            "لأننا نعدّ أجزاءً متساوية الحجم.",
            scale=0.52
        ).next_to(rule, DOWN, buff=0.3)

        self.play(Write(rule), run_time=self.s.rt_norm)
        self.play(FadeIn(note, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.5)
        self.play(FadeOut(VGroup(rule, note)), run_time=self.s.rt_fast)

    def step_mini_assessment(self):
        """
        Formative: quick exercise with reveal.
        """
        prompt = T(
            self.cfg, self.s,
            "Mini-check: Add the shaded parts.",
            "تحقق صغير: اجمع الأجزاء المظللة.",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        ex = AddFractionsExample(a=2, b=3, n=7)
        # show two bars and ask; then reveal
        bar1 = FractionBar(ex.n, self.s).move_to(UP * 0.4)
        bar2 = FractionBar(ex.n, self.s).move_to(DOWN * 0.9)
        s1 = bar1.shade_first_k(ex.a).move_to(bar1.get_center())
        s2 = bar2.shade_first_k(ex.b).move_to(bar2.get_center())

        self.play(Create(bar1), FadeIn(s1), Create(bar2), FadeIn(s2), run_time=self.s.rt_norm)

        q = T(self.cfg, self.s, "What is the sum?", "ما هو المجموع؟", scale=0.62).to_edge(RIGHT).shift(UP * 0.0)
        self.play(FadeIn(q, shift=LEFT * 0.1), run_time=self.s.rt_fast)

        # reveal
        res = add_expr_tex(ex.a, ex.b, ex.n, scale=1.15).to_edge(DOWN)
        self.play(Write(res), run_time=self.s.rt_norm)

        self.wait(0.5)
        self.play(FadeOut(VGroup(bar1, bar2, s1, s2, q, res)), run_time=self.s.rt_fast)

    def step_outro(self):
        recap = VGroup(
            T(self.cfg, self.s, "Recap:", "الخلاصة:", scale=0.6),
            T(self.cfg, self.s, "• Same denominator → same-size parts", "• نفس المقام → أجزاء بنفس الحجم", scale=0.50),
            T(self.cfg, self.s, "• Combine shaded parts (count them)", "• نجمع الأجزاء المظللة (ونعدّها)", scale=0.50),
            T(self.cfg, self.s, "• Keep denominator, add numerators", "• نحافظ على المقام ونجمع البسطين", scale=0.50),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        recap.to_edge(RIGHT).shift(DOWN * 0.2)
        self.play(FadeIn(recap, shift=LEFT * 0.2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(recap, shift=RIGHT * 0.2), FadeOut(self.title), run_time=self.s.rt_fast)


# ============================================================
# RUN:
#   manim -pqh your_file.py M3_L13_AddingFractionsSameDenominator
#
# CUSTOMIZE:
#   cfg = LessonConfigM3_L13(
#       examples=[AddFractionsExample(a=1,b=1,n=3)],
#       language="ar"
#   )
# ============================================================