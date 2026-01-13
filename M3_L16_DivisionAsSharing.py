from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Dict

import numpy as np
from manim import *


# ============================================================
# CONFIG / STYLES
# ============================================================

@dataclass
class ShareStyle:
    stroke_width: float = 4.0
    fill_opacity: float = 0.14

    # objects (tokens)
    token_radius: float = 0.14
    token_spacing: float = 0.42

    # group containers
    container_radius: float = 1.05
    container_stroke: float = 4.0

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
    show_equality_check: bool = True
    show_division_expression: bool = True
    show_round_robin_pointer: bool = True  # highlight current target group

    # layout
    max_tokens_per_row: int = 6
    token_row_gap: float = 0.35


@dataclass
class SharingExample:
    total: int = 12
    groups: int = 3
    label: str = "12 objects shared among 3 groups"


@dataclass
class LessonConfigM3_L16:
    title_en: str = "Concept of division: sharing (distribution)"
    title_ar: str = "مفهوم القسمة: التوزيع"
    language: str = "en"  # "en" | "ar"

    # prompts
    prompt_setup_en: str = "We want to share fairly: same number in each group."
    prompt_setup_ar: str = "نريد توزيعاً عادلاً: نفس العدد في كل مجموعة."

    prompt_one_by_one_en: str = "Distribute one by one, round-robin."
    prompt_one_by_one_ar: str = "نوزّع واحداً واحداً بالتناوب."

    prompt_compare_en: str = "Pause and compare: are the shares equal?"
    prompt_compare_ar: str = "نتوقف ونقارن: هل الحصص متساوية؟"

    prompt_result_en: str = "Each group gets:"
    prompt_result_ar: str = "كل مجموعة تحصل على:"

    prompt_symbol_en: str = "We can write it as a division:"
    prompt_symbol_ar: str = "يمكن كتابة ذلك كعملية قسمة:"

    # default examples (extend list)
    examples: List[SharingExample] = field(default_factory=lambda: [
        SharingExample(total=12, groups=3, label="12 shared among 3"),
        SharingExample(total=15, groups=5, label="15 shared among 5"),
        SharingExample(total=14, groups=4, label="14 shared among 4 (shows remainder idea gently)"),
    ])


# ============================================================
# REUSABLE PRIMITIVES
# ============================================================

def T(cfg: LessonConfigM3_L16, s: ShareStyle, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
    txt = en if cfg.language == "en" else (ar or en)
    return Text(txt, font_size=s.font_size_main).scale(scale)


def div_tex(total: int, groups: int, q: Optional[int] = None, r: Optional[int] = None, scale: float = 1.15) -> Mobject:
    if q is None:
        return MathTex(rf"{total}\div {groups} = \ ?").scale(scale)
    if r is None or r == 0:
        return MathTex(rf"{total}\div {groups} = {q}").scale(scale)
    # gentle remainder notation
    return MathTex(rf"{total}\div {groups} = {q}\ \text{{R}}\ {r}").scale(scale)


class Token(VGroup):
    def __init__(self, idx: int, style: ShareStyle, **kwargs):
        super().__init__(**kwargs)
        dot = Circle(radius=style.token_radius).set_stroke(width=0).set_fill(opacity=0.30)
        lab = Text(str(idx), font_size=style.font_size_small).scale(0.55)
        lab.move_to(dot.get_center())
        self.dot = dot
        self.lab = lab
        self.add(dot, lab)


class GroupContainer(VGroup):
    def __init__(self, gid: int, style: ShareStyle, **kwargs):
        super().__init__(**kwargs)
        circle = Circle(radius=style.container_radius).set_stroke(width=style.container_stroke).set_fill(opacity=0.0)
        label = Text(f"G{gid}", font_size=style.font_size_small).scale(0.75).next_to(circle, UP, buff=0.12)
        self.circle = circle
        self.label = label
        self.tokens = VGroup()
        self.add(circle, label, self.tokens)

    def add_token(self, token: Token, style: ShareStyle):
        """
        Place token inside container in rows.
        """
        n = len(self.tokens)
        row = n // style.max_tokens_per_row
        col = n % style.max_tokens_per_row

        # compute local position inside the circle
        x0 = - (style.max_tokens_per_row - 1) * style.token_spacing / 2
        x = x0 + col * style.token_spacing
        y = 0.4 - row * style.token_row_gap

        token.move_to(self.circle.get_center() + np.array([x, y, 0.0]))
        self.tokens.add(token)
        return token

    def count(self) -> int:
        return len(self.tokens)


def make_token_pool(total: int, style: ShareStyle) -> VGroup:
    """
    Tokens laid out in a pool on the left.
    """
    pool = VGroup()
    for i in range(1, total + 1):
        pool.add(Token(i, style))

    # arrange in rows
    rows = int(np.ceil(total / style.max_tokens_per_row))
    for idx, tok in enumerate(pool):
        r = idx // style.max_tokens_per_row
        c = idx % style.max_tokens_per_row
        x0 = - (style.max_tokens_per_row - 1) * style.token_spacing / 2
        x = x0 + c * style.token_spacing
        y = (rows - 1) * style.token_row_gap / 2 - r * style.token_row_gap
        tok.move_to(np.array([x, y, 0.0]))

    # wrap box
    box = RoundedRectangle(width=3.5, height=max(2.0, rows * style.token_row_gap + 0.8), corner_radius=0.2)
    box.set_stroke(width=3).set_fill(opacity=0.06)
    box.move_to(pool.get_center())

    title = Text("Total", font_size=style.font_size_small).scale(0.75).next_to(box, UP, buff=0.1)
    return VGroup(box, title, pool)


def equality_check_marks(counts: List[int], style: ShareStyle) -> VGroup:
    """
    Show a simple visual: if all equal -> check mark; else -> not equal sign.
    """
    ok = all(c == counts[0] for c in counts) if counts else True
    text = "✓ equal" if ok else "≠ not equal"
    mob = Text(text, font_size=style.font_size_main).scale(0.55)
    bubble = RoundedRectangle(width=3.2, height=1.0, corner_radius=0.2).set_stroke(width=3).set_fill(opacity=0.06)
    grp = VGroup(bubble, mob)
    mob.move_to(bubble.get_center())
    grp.to_edge(DOWN)
    return grp


# ============================================================
# LESSON SCENE (Reusable / Adjustable / Extensible)
# ============================================================

class M3_L16_DivisionAsSharing(Scene):
    """
    M3_L16 — Division as fair sharing (distribution)

    Flow:
      display_total_objects
      display_empty_groups
      distribute one-by-one to each group (round-robin)
      pause & compare groups
      confirm equal shares
      reveal number per group
      optionally show division expression (12 ÷ 3 = 4)
    """

    def __init__(
        self,
        cfg: LessonConfigM3_L16 = LessonConfigM3_L16(),
        style: ShareStyle = ShareStyle(),
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
            ("collective_discussion_strategy", self.step_collective_discussion_strategy),
            ("institutionalization_symbol", self.step_institutionalization_symbol),
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
            "Division = fair sharing into equal groups",
            "القسمة = توزيع عادل إلى مجموعات متساوية",
            scale=0.52
        ).next_to(title, DOWN, buff=0.18)

        self.play(Write(title), FadeIn(subtitle, shift=DOWN * 0.15), run_time=self.s.rt_norm)
        self.wait(0.2)
        self.play(FadeOut(subtitle, shift=UP * 0.1), run_time=self.s.rt_fast)
        self.title = title

    # ------------------------------------------------------------
    # Core sharing demo
    # ------------------------------------------------------------

    def run_sharing_example(self, ex: SharingExample) -> VGroup:
        total, g = ex.total, ex.groups

        # prompt
        p = T(self.cfg, self.s, self.cfg.prompt_setup_en, self.cfg.prompt_setup_ar, scale=0.56)
        p = self.banner(p).shift(DOWN * 0.9)
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        # token pool (left)
        pool = make_token_pool(total, self.s).to_edge(LEFT).shift(RIGHT * 0.35 + DOWN * 0.1)
        self.play(FadeIn(pool, shift=RIGHT * 0.15), run_time=self.s.rt_norm)

        # empty groups (right)
        groups = VGroup(*[GroupContainer(i + 1, self.s) for i in range(g)])
        groups.arrange(RIGHT, buff=0.55)
        groups.to_edge(RIGHT).shift(LEFT * 0.35 + DOWN * 0.1)
        self.play(FadeIn(groups, shift=LEFT * 0.15), run_time=self.s.rt_norm)

        # pointer to show round-robin target
        pointer = VGroup()
        if self.s.show_round_robin_pointer:
            pointer = Triangle().scale(0.18)
            pointer.rotate(PI)  # pointing down
            pointer.set_fill(opacity=0.35).set_stroke(width=0)
            pointer.move_to(groups[0].circle.get_top() + UP * 0.25)
            self.play(FadeIn(pointer, shift=UP * 0.05), run_time=self.s.rt_fast)

        # distribute one by one
        p2 = T(self.cfg, self.s, self.cfg.prompt_one_by_one_en, self.cfg.prompt_one_by_one_ar, scale=0.56)
        p2 = self.banner(p2).shift(DOWN * 0.9)
        self.play(Transform(self.title, p2), run_time=self.s.rt_fast)

        tokens: VGroup = pool[2]  # box,title,pool
        tokens_list = list(tokens)

        # animation: round robin allocation
        for idx, tok in enumerate(tokens_list):
            target = groups[idx % g]
            if self.s.show_round_robin_pointer:
                self.play(pointer.animate.move_to(target.circle.get_top() + UP * 0.25), run_time=0.18)
            # move token into container
            new_tok = tok.copy()
            target.add_token(new_tok, self.s)
            self.play(Transform(tok, new_tok), run_time=0.35)

            # occasional pause and compare
            if idx in {g - 1, 2 * g - 1, 3 * g - 1}:
                if self.s.show_equality_check:
                    p3 = T(self.cfg, self.s, self.cfg.prompt_compare_en, self.cfg.prompt_compare_ar, scale=0.56)
                    p3 = self.banner(p3).shift(DOWN * 0.9)
                    self.play(Transform(self.title, p3), run_time=self.s.rt_fast)

                    counts = [c.count() for c in groups]
                    check = equality_check_marks(counts, self.s)
                    self.play(FadeIn(check, shift=UP * 0.1), run_time=self.s.rt_fast)
                    self.wait(0.2)
                    self.play(FadeOut(check), run_time=self.s.rt_fast)

        # final compare + confirm
        counts = [c.count() for c in groups]
        q = min(counts) if counts else 0
        r = total - q * g

        if self.s.show_equality_check:
            final_check = equality_check_marks(counts, self.s)
            self.play(FadeIn(final_check, shift=UP * 0.1), run_time=self.s.rt_fast)
            self.wait(0.3)
            self.play(FadeOut(final_check), run_time=self.s.rt_fast)

        # reveal number per group
        p4 = T(self.cfg, self.s, self.cfg.prompt_result_en, self.cfg.prompt_result_ar, scale=0.56)
        p4 = self.banner(p4).shift(DOWN * 0.9)
        self.play(Transform(self.title, p4), run_time=self.s.rt_fast)

        # label on each group
        labels = VGroup()
        for c in groups:
            txt = Text(str(c.count()), font_size=self.s.font_size_title).scale(0.55)
            txt.move_to(c.circle.get_center() + DOWN * 1.05)
            labels.add(txt)
        self.play(FadeIn(labels, shift=UP * 0.1), run_time=self.s.rt_norm)

        # optional division expression
        expr = VGroup()
        if self.s.show_division_expression:
            p5 = T(self.cfg, self.s, self.cfg.prompt_symbol_en, self.cfg.prompt_symbol_ar, scale=0.56)
            p5 = self.banner(p5).shift(DOWN * 0.9)
            self.play(Transform(self.title, p5), run_time=self.s.rt_fast)

            expr = div_tex(total, g, q=q, r=r if r > 0 else 0, scale=1.25).to_edge(DOWN)
            self.play(Write(expr), run_time=self.s.rt_norm)

            # gentle remainder note if needed
            if r > 0:
                note = T(
                    self.cfg, self.s,
                    "Some objects remain. (Remainder) We will study it later.",
                    "تبقى بعض الأشياء. (باقٍ) سندرسها لاحقاً.",
                    scale=0.50
                ).next_to(expr, UP, buff=0.15)
                self.play(FadeIn(note, shift=UP * 0.05), run_time=self.s.rt_fast)
                expr = VGroup(expr, note)

        return VGroup(pool, groups, pointer, labels, expr)

    # ============================================================
    # Steps
    # ============================================================

    def step_exploration_examples(self):
        # main “clean” examples (no remainder)
        for ex in self.cfg.examples[:2]:
            g = self.run_sharing_example(ex)
            self.wait(0.4)
            self.play(FadeOut(g), run_time=self.s.rt_fast)

        # optional remainder example
        ex = self.cfg.examples[2]
        g = self.run_sharing_example(ex)
        self.wait(0.4)
        self.play(FadeOut(g), run_time=self.s.rt_fast)

    def step_collective_discussion_strategy(self):
        prompt = T(
            self.cfg, self.s,
            "Discussion: How do we know it is fair?",
            "نقاش: كيف نعرف أن التوزيع عادل؟",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        box = RoundedRectangle(width=11.6, height=2.8, corner_radius=0.25).to_edge(DOWN).shift(UP * 0.2)
        box.set_stroke(width=3).set_fill(opacity=0.06)

        l1 = T(self.cfg, self.s, "• We distribute one by one.", "• نوزّع واحداً واحداً.", scale=0.52)
        l2 = T(self.cfg, self.s, "• We compare group counts.", "• نقارن أعداد كل مجموعة.", scale=0.52)
        l3 = T(self.cfg, self.s, "• Fair sharing → equal counts.", "• التوزيع العادل → نفس العدد.", scale=0.52)

        scaff = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(box.get_center())
        self.play(Create(box), FadeIn(scaff, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.5)
        self.play(FadeOut(VGroup(box, scaff)), run_time=self.s.rt_fast)

    def step_institutionalization_symbol(self):
        prompt = T(
            self.cfg, self.s,
            "Institutionalization: Division notation",
            "التثبيت: كتابة القسمة",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        rule = MathTex(r"\text{total} \div \text{groups} = \text{objects per group}").scale(1.1).move_to(UP * 0.2)
        ex = MathTex(r"12 \div 3 = 4").scale(1.35).next_to(rule, DOWN, buff=0.35)

        self.play(Write(rule), run_time=self.s.rt_norm)
        self.play(Write(ex), run_time=self.s.rt_norm)
        self.wait(0.5)
        self.play(FadeOut(VGroup(rule, ex)), run_time=self.s.rt_fast)

    def step_mini_assessment(self):
        prompt = T(
            self.cfg, self.s,
            "Mini-check: Share 16 objects among 4 groups. How many per group?",
            "تحقق صغير: وزّع 16 شيئاً على 4 مجموعات. كم لكل مجموعة؟",
            scale=0.52
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        g = self.run_sharing_example(SharingExample(total=16, groups=4, label="16 among 4"))
        self.wait(0.4)
        self.play(FadeOut(g), run_time=self.s.rt_fast)

    def step_outro(self):
        recap = VGroup(
            T(self.cfg, self.s, "Recap:", "الخلاصة:", scale=0.6),
            T(self.cfg, self.s, "• Division = fair sharing", "• القسمة = توزيع عادل", scale=0.50),
            T(self.cfg, self.s, "• Distribute one by one to stay fair", "• نوزع واحداً واحداً لضمان العدل", scale=0.50),
            T(self.cfg, self.s, "• Same number in each group", "• نفس العدد في كل مجموعة", scale=0.50),
            T(self.cfg, self.s, "• Write: total ÷ groups = per group", "• نكتب: المجموع ÷ المجموعات = لكل مجموعة", scale=0.50),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        recap.to_edge(RIGHT).shift(DOWN * 0.15)
        self.play(FadeIn(recap, shift=LEFT * 0.2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(recap, shift=RIGHT * 0.2), FadeOut(self.title), run_time=self.s.rt_fast)


# ============================================================
# RUN:
#   manim -pqh your_file.py M3_L16_DivisionAsSharing
#
# CUSTOMIZE:
#   cfg = LessonConfigM3_L16(
#       examples=[SharingExample(total=18, groups=6)],
#       language="ar"
#   )
# ============================================================
