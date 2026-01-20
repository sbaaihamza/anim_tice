from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

import numpy as np
from manim import *

from anim_tice.core import AnimTiceScene, LessonConfig, StyleConfig


# ============================================================
# CONFIG / STYLES
# ============================================================

@dataclass
class BaseTenStyle(StyleConfig):
    # block sizing
    unit_size: float = 0.42
    stroke_width: float = 3.0
    fill_opacity: float = 0.12

    # text sizes
    font_size_small: int = 28

    # pacing
    rt_slow: float = 1.2

    # toggles
    show_number_line: bool = True
    show_digit_cards: bool = True
    show_arabic: bool = False  # enable only if Arabic fonts render correctly

    # number line parameters
    nl_min: int = 0
    nl_max: int = 1000
    nl_step: int = 100
    nl_length: float = 11.5


@dataclass
class LessonConfigM3_L01(LessonConfig):
    # Example numbers for prerequisite review
    examples: List[int] = field(default_factory=lambda: [275, 509, 903, 118])
    # scene title
    title_en: str = "Numbers 0 to 999 — Prerequisite review"
    title_ar: str = "الأعداد من 0 إلى 999 — مراجعة المستلزمات"

    # guided questioning (verbal layer)
    prompt_observe_en: str = "Observe: what do you notice about this number?"
    prompt_observe_ar: str = "لاحظ: ماذا تلاحظ في هذا العدد؟"

    prompt_compare_en: str = "Compare: which digit is the most important here?"
    prompt_compare_ar: str = "قارن: أي رقم أهم هنا؟"

    prompt_hypothesize_en: str = "Hypothesize: what happens if we change the tens digit?"
    prompt_hypothesize_ar: str = "افترض: ماذا يحدث إذا غيّرنا رقم العشرات؟"


# ============================================================
# REUSABLE PRIMITIVES
# ============================================================

class DigitCard(VGroup):
    """
    A 'digit card' used to represent hundreds/tens/ones digits.
    """
    def __init__(self, digit: int, label: str = "", width: float = 1.2, height: float = 1.5, **kwargs):
        super().__init__(**kwargs)
        rect = RoundedRectangle(width=width, height=height, corner_radius=0.18).set_stroke(width=3)
        txt = Text(str(digit), font_size=46)
        txt.move_to(rect.get_center())
        self.add(rect, txt)

        if label:
            lab = Text(label, font_size=22).next_to(rect, DOWN, buff=0.12)
            self.add(lab)

        self.rect = rect
        self.txt = txt


class BaseTenBlocks(VGroup):
    """
    Simple base-ten blocks:
      - unit: small square
      - ten: rod of 10 units
      - hundred: flat of 10 rods (100 units)
    This is visually clear and easy to manipulate in Manim.
    """
    def __init__(self, style: BaseTenStyle, **kwargs):
        super().__init__(**kwargs)
        self.s = style

    def make_unit(self) -> Square:
        sq = Square(side_length=self.s.unit_size).set_stroke(width=self.s.stroke_width)
        sq.set_fill(opacity=self.s.fill_opacity)
        return sq

    def make_ten(self) -> VGroup:
        # 10 units in a row
        row = VGroup(*[self.make_unit() for _ in range(10)]).arrange(RIGHT, buff=0)
        return row

    def make_hundred(self) -> VGroup:
        # 10 tens stacked
        tens = VGroup(*[self.make_ten() for _ in range(10)]).arrange(DOWN, buff=0)
        return tens

    def build_number(self, n: int) -> Tuple[VGroup, Dict[str, int]]:
        """
        Build a base-ten representation for n (0..999).
        Returns (mobject_group, decomposition_dict).
        """
        assert 0 <= n <= 999
        h = n // 100
        t = (n % 100) // 10
        u = n % 10

        blocks = VGroup()

        # Hundreds flats
        hundreds_group = VGroup()
        for _ in range(h):
            hundreds_group.add(self.make_hundred())
        if h > 0:
            hundreds_group.arrange(RIGHT, buff=self.s.unit_size * 0.35)
            blocks.add(hundreds_group)

        # Tens rods
        tens_group = VGroup()
        for _ in range(t):
            tens_group.add(self.make_ten())
        if t > 0:
            tens_group.arrange(DOWN, buff=self.s.unit_size * 0.25)
            blocks.add(tens_group)

        # Units
        units_group = VGroup()
        for _ in range(u):
            units_group.add(self.make_unit())
        if u > 0:
            units_group.arrange(RIGHT, buff=self.s.unit_size * 0.05)
            blocks.add(units_group)

        # Layout: hundreds on left, tens in middle, units on right
        if len(blocks) == 0:
            # n = 0
            zero = Text("0", font_size=48)
            blocks.add(zero)
        else:
            # Place each group visually
            # hundreds largest → left
            x = -4.8
            if h > 0:
                hundreds_group.move_to(np.array([x, 0.0, 0.0]))
                x += 4.4
            if t > 0:
                tens_group.move_to(np.array([x, 0.0, 0.0]))
                x += 3.0
            if u > 0:
                units_group.move_to(np.array([x, 0.0, 0.0]))

        return blocks, {"hundreds": h, "tens": t, "ones": u}


def number_to_digits(n: int) -> Tuple[int, int, int]:
    return (n // 100, (n % 100) // 10, n % 10)


# ============================================================
# LESSON SCENE (Reusable / Adjustable / Extensible)
# ============================================================

class M3_L01_Numbers0to999_PrereqReview(AnimTiceScene):
    """
    M3_L01 — Numbers from 0 to 999 — prerequisite review

    Covers your animation guideline flow:
      - start_with_concrete_objects (base-ten blocks)
      - transition_to_symbols (numerical notation + digit cards)
      - freeze_on_key_rule (decomposition rule)

    Didactic situation: problem_situation (observe, compare, hypothesize)
    """

    def __init__(
        self,
        lesson_config: LessonConfigM3_L01 = LessonConfigM3_L01(),
        style_config: BaseTenStyle = BaseTenStyle(),
        **kwargs
    ):
        super().__init__(
            lesson_config=lesson_config,
            style_config=style_config,
            **kwargs
        )
        self.blocks_factory = BaseTenBlocks(style=self.s)

    def build_steps(self):
        self.steps = [
            ("intro", self.step_intro),
            ("exploration_concrete", self.step_exploration_concrete),
            ("collective_discussion", self.step_collective_discussion),
            ("transition_to_symbols", self.step_transition_to_symbols),
            ("institutionalization_rule", self.step_institutionalization_rule),
            ("mini_assessment", self.step_mini_assessment),
            ("outro", self.step_outro),
        ]

    def show_number_line(self):
        if not self.s.show_number_line:
            return None
        nl = NumberLine(
            x_range=[self.s.nl_min, self.s.nl_max, self.s.nl_step],
            length=self.s.nl_length,
            include_numbers=True,
            label_direction=DOWN,
            font_size=24,
        )
        nl.to_edge(DOWN).shift(UP * 0.35)
        return nl

    def step_intro(self):
        didactic = self.t(
            "Observe • Compare • Hypothesize",
            "لاحظ • قارن • افترض",
            scale=0.52,
        ).next_to(self.title, DOWN, buff=0.18)

        self.play(FadeIn(didactic, shift=DOWN * 0.15), run_time=self.s.rt_norm)
        self.wait(0.2)
        self.play(FadeOut(didactic, shift=UP * 0.1), run_time=self.s.rt_fast)

        nl = self.show_number_line()
        if nl:
            self.play(Create(nl), run_time=self.s.rt_norm)
        self.number_line = nl

    def step_exploration_concrete(self):
        # Pick first example as the anchor
        n = self.cfg.examples[0]
        prompt = self.t(self.cfg.prompt_observe_en, self.cfg.prompt_observe_ar, scale=0.52).to_edge(UP).shift(DOWN * 0.9)

        num = Text(str(n), font_size=72).to_edge(UP).shift(DOWN * 1.6)

        blocks, decomp = self.blocks_factory.build_number(n)
        blocks.shift(DOWN * 0.2)

        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)
        self.play(FadeIn(num, shift=DOWN * 0.2), run_time=self.s.rt_norm)
        self.play(FadeIn(blocks, shift=UP * 0.1), run_time=self.s.rt_norm)

        # highlight (hundreds, tens, ones) progressively
        h, t, u = decomp["hundreds"], decomp["tens"], decomp["ones"]

        labels = VGroup()
        if h > 0:
            labels.add(self.t(f"{h} hundreds", f"{h} مئات", scale=0.5))
        if t > 0:
            labels.add(self.t(f"{t} tens", f"{t} عشرات", scale=0.5))
        if u > 0:
            labels.add(self.t(f"{u} ones", f"{u} وحدات", scale=0.5))

        if len(labels) > 0:
            labels.arrange(DOWN, aligned_edge=LEFT, buff=0.18).to_edge(LEFT).shift(UP * 0.3)
            self.play(FadeIn(labels, shift=RIGHT * 0.15), run_time=self.s.rt_norm)

        self.n_current = n
        self.blocks_current = blocks
        self.num_text = num
        self.decomp_current = decomp
        self.labels_current = labels

    def step_collective_discussion(self):
        # Compare with another number to activate place value intuition
        n2 = self.cfg.examples[1]
        prompt = self.t(self.cfg.prompt_compare_en, self.cfg.prompt_compare_ar, scale=0.52).to_edge(UP).shift(DOWN * 0.9)

        num2 = Text(str(n2), font_size=72).to_edge(UP).shift(DOWN * 1.6)

        blocks2, decomp2 = self.blocks_factory.build_number(n2)
        blocks2.shift(DOWN * 0.2)

        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)
        self.play(Transform(self.num_text, num2), run_time=self.s.rt_norm)

        # swap blocks
        self.play(Transform(self.blocks_current, blocks2), run_time=self.s.rt_slow)

        # update labels
        self.play(FadeOut(self.labels_current, shift=LEFT * 0.1), run_time=self.s.rt_fast)
        labels2 = VGroup()
        if decomp2["hundreds"] > 0:
            labels2.add(self.t(f'{decomp2["hundreds"]} hundreds', f'{decomp2["hundreds"]} مئات', scale=0.5))
        if decomp2["tens"] > 0:
            labels2.add(self.t(f'{decomp2["tens"]} tens', f'{decomp2["tens"]} عشرات', scale=0.5))
        if decomp2["ones"] > 0:
            labels2.add(self.t(f'{decomp2["ones"]} ones', f'{decomp2["ones"]} وحدات', scale=0.5))
        labels2.arrange(DOWN, aligned_edge=LEFT, buff=0.18).to_edge(LEFT).shift(UP * 0.3)

        self.play(FadeIn(labels2, shift=RIGHT * 0.15), run_time=self.s.rt_norm)

        self.n_current = n2
        self.decomp_current = decomp2
        self.labels_current = labels2

    def step_transition_to_symbols(self):
        if not self.s.show_digit_cards:
            return

        # Show digit cards for the current number
        h, t, u = number_to_digits(self.n_current)

        cards = VGroup(
            DigitCard(h, label="H" if self.cfg.language == "en" else "مئات"),
            DigitCard(t, label="T" if self.cfg.language == "en" else "عشرات"),
            DigitCard(u, label="O" if self.cfg.language == "en" else "وحدات"),
        ).arrange(RIGHT, buff=0.45)

        cards.to_edge(RIGHT).shift(DOWN * 0.4)

        arrow = Arrow(self.num_text.get_bottom(), cards.get_top(), buff=0.25)

        prompt = self.t(
            "Transition: digits tell us place value",
            "انتقال: الأرقام تُظهر القيمة المكانية",
            scale=0.52,
        ).to_edge(UP).shift(DOWN * 0.9)

        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)
        self.play(GrowArrow(arrow), FadeIn(cards, shift=LEFT * 0.15), run_time=self.s.rt_norm)

        # highlight each card in order
        for c in cards:
            self.play(c.animate.scale(1.15), run_time=0.35)
            self.play(c.animate.scale(1 / 1.15), run_time=0.25)

        self.cards = cards
        self.arrow = arrow

    def step_institutionalization_rule(self):
        # Freeze on key rule: decomposition
        h, t, u = number_to_digits(self.n_current)

        rule = MathTex(
            rf"{self.n_current} = {h}\times 100 + {t}\times 10 + {u}",
        ).scale(0.95)

        box = RoundedRectangle(width=11.5, height=1.9, corner_radius=0.25).to_edge(DOWN).shift(UP * 0.6)
        box.set_fill(opacity=0.06).set_stroke(width=3)

        prompt = self.t(
            "Key rule: read and decompose using place value",
            "قاعدة: نقرأ ونفكك حسب القيمة المكانية",
            scale=0.52,
        ).to_edge(UP).shift(DOWN * 0.9)

        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)
        self.play(Create(box), run_time=self.s.rt_norm)
        self.play(Write(rule.move_to(box.get_center())), run_time=self.s.rt_norm)

        self.rule_box = VGroup(box, rule)

    def step_mini_assessment(self):
        # quick formative: ask to decompose a new number (no direct formula at first)
        n3 = self.cfg.examples[2]
        prompt = self.t(
            self.cfg.prompt_hypothesize_en,
            self.cfg.prompt_hypothesize_ar,
            scale=0.52,
        ).to_edge(UP).shift(DOWN * 0.9)

        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        test_num = Text(str(n3), font_size=72).to_edge(UP).shift(DOWN * 1.6)

        self.play(Transform(self.num_text, test_num), run_time=self.s.rt_norm)

        # show only blocks first (object manipulation), then reveal digit cards update
        blocks3, decomp3 = self.blocks_factory.build_number(n3)
        blocks3.shift(DOWN * 0.2)

        self.play(Transform(self.blocks_current, blocks3), run_time=self.s.rt_slow)

        if self.s.show_digit_cards and hasattr(self, "cards"):
            h3, t3, u3 = number_to_digits(n3)
            new_cards = VGroup(
                DigitCard(h3, label="H" if self.cfg.language == "en" else "مئات"),
                DigitCard(t3, label="T" if self.cfg.language == "en" else "عشرات"),
                DigitCard(u3, label="O" if self.cfg.language == "en" else "وحدات"),
            ).arrange(RIGHT, buff=0.45)
            new_cards.move_to(self.cards.get_center())
            self.play(Transform(self.cards, new_cards), run_time=self.s.rt_norm)

        # Finally: reveal decomposition line (briefly)
        h3, t3, u3 = number_to_digits(n3)
        ans = MathTex(rf"{n3} = {h3}\times 100 + {t3}\times 10 + {u3}").scale(0.95)
        ans.next_to(self.rule_box, UP, buff=0.25)

        self.play(FadeIn(ans, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.35)
        self.play(FadeOut(ans, shift=DOWN * 0.1), run_time=self.s.rt_fast)

    def step_outro(self):
        recap = VGroup(
            self.t("Recap:", "الخلاصة:", scale=0.6),
            self.t("• Place value: hundreds, tens, ones", "• القيمة المكانية: مئات، عشرات، وحدات", scale=0.50),
            self.t("• Read numbers correctly", "• قراءة الأعداد بشكل صحيح", scale=0.50),
            self.t("• Decompose numbers", "• تفكيك الأعداد", scale=0.50),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        recap.to_edge(RIGHT).shift(DOWN * 0.2)
        self.play(FadeIn(recap, shift=LEFT * 0.2), run_time=self.s.rt_norm)
        self.wait(0.6)

        # clean end
        self.play(
            FadeOut(recap, shift=RIGHT * 0.2),
            FadeOut(self.rule_box),
            FadeOut(self.blocks_current),
            FadeOut(self.num_text),
            FadeOut(self.labels_current) if hasattr(self, "labels_current") else AnimationGroup(),
            FadeOut(self.cards) if hasattr(self, "cards") else AnimationGroup(),
            FadeOut(self.arrow) if hasattr(self, "arrow") else AnimationGroup(),
            FadeOut(self.number_line) if self.number_line else AnimationGroup(),
            run_time=self.s.rt_fast,
        )


# ============================================================
# RUN:
#   manim -pqh M3_L01_Numbers0to999_PrereqReview.py M3_L01_Numbers0to999_PrereqReview
#
# CUSTOMIZE:
#   cfg = LessonConfigM3_L01(examples=[342, 507, 980], language="ar")
#   style = BaseTenStyle(show_arabic=True, show_number_line=False)
#   scene = M3_L01_Numbers0to999_PrereqReview(cfg, style)
# ============================================================
