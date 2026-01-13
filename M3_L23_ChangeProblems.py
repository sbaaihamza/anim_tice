from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Literal

import numpy as np
from manim import *


# ============================================================
# CONFIG / STYLES
# ============================================================

@dataclass
class ChangePSStyle:
    stroke_width: float = 4.0
    fill_opacity: float = 0.14

    unit_width: float = 0.5
    bar_height: float = 0.62
    bar_corner_radius: float = 0.18

    # bar segment styles
    before_opacity: float = 0.18
    change_opacity: float = 0.25
    after_opacity: float = 0.18

    # text
    font_size_title: int = 38
    font_size_main: int = 34
    font_size_small: int = 28
    font_size_problem: int = 26

    # timeline
    timeline_y: float = -1.45
    timeline_w: float = 10.8
    timeline_h: float = 0.0

    # pacing
    pause: float = 0.45
    rt_fast: float = 0.7
    rt_norm: float = 1.0
    rt_slow: float = 1.25

    # toggles
    show_problem_text: bool = True
    show_timeline: bool = True
    show_model_to_operation: bool = True
    show_context_answer: bool = True
    show_verify: bool = True

    # layout
    left_anchor_x: float = -5.2
    before_y: float = 0.75
    change_y: float = 0.0
    after_y: float = -0.75


@dataclass
class ChangeProblem:
    """
    Change / transformation problem.

    kind:
      - "increase": final = initial + change
      - "decrease": final = initial - change

    unknown:
      - "final": initial and change known
      - "initial": final and change known
      - "change": initial and final known
    """
    pid: str
    kind: Literal["increase", "decrease"]

    initial: Optional[int] = None
    change: Optional[int] = None
    final: Optional[int] = None

    unknown: Literal["final", "initial", "change"] = "final"

    item: str = "stickers"
    context_subject: str = "Sara"
    verb_gain: str = "gets"
    verb_lose: str = "gives away"

    question: str = ""
    answer: Optional[int] = None  # computed if None


@dataclass
class LessonConfigM3_L23:
    title_en: str = "Solving change (transformation) problems"
    title_ar: str = "حل مسائل البحث عن التحول"
    language: str = "en"

    prompt_before_en: str = "Before: identify the initial state."
    prompt_before_ar: str = "قبل: نحدد الحالة الأولى."

    prompt_change_en: str = "Change: what is added or removed?"
    prompt_change_ar: str = "التحول: ماذا نضيف أو نحذف؟"

    prompt_after_en: str = "After: identify the final state."
    prompt_after_ar: str = "بعد: نحدد الحالة النهائية."

    prompt_unknown_en: str = "Which part is unknown?"
    prompt_unknown_ar: str = "ما الذي نبحث عنه؟"

    prompt_link_en: str = "Link the model to an operation."
    prompt_link_ar: str = "نربط النموذج بعملية حسابية."

    problems: List[ChangeProblem] = field(default_factory=lambda: [
        ChangeProblem(
            pid="C1",
            kind="increase",
            initial=8,
            change=5,
            final=None,
            unknown="final",
            item="marbles",
            context_subject="Omar",
            verb_gain="finds",
            question="Omar has 8 marbles. He finds 5 more. How many marbles does he have now?"
        ),
        ChangeProblem(
            pid="C2",
            kind="decrease",
            initial=14,
            change=6,
            final=None,
            unknown="final",
            item="stickers",
            context_subject="Lina",
            verb_lose="gives away",
            question="Lina has 14 stickers. She gives away 6. How many stickers does she have now?"
        ),
        ChangeProblem(
            pid="C3",
            kind="increase",
            initial=None,
            change=7,
            final=15,
            unknown="initial",
            item="coins",
            context_subject="Yassine",
            verb_gain="receives",
            question="Yassine has some coins. He receives 7 more and now has 15. How many did he have before?"
        ),
    ])


# ============================================================
# REUSABLE PRIMITIVES
# ============================================================

def T(cfg: LessonConfigM3_L23, s: ChangePSStyle, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
    txt = en if cfg.language == "en" else (ar or en)
    return Text(txt, font_size=s.font_size_main).scale(scale)


def problem_box(text: str, s: ChangePSStyle) -> VGroup:
    box = RoundedRectangle(width=11.6, height=2.1, corner_radius=0.25).set_stroke(width=3).set_fill(opacity=0.06)
    t = Paragraph(*text.split("\n"), alignment="left", font_size=s.font_size_problem).scale(0.95)
    t.move_to(box.get_center())
    return VGroup(box, t).to_edge(UP).shift(DOWN * 1.25)


def bar_segment(value: int, s: ChangePSStyle, label: str = "", opacity: float = 0.18) -> VGroup:
    w = max(0.9, value * s.unit_width)
    rect = RoundedRectangle(width=w, height=s.bar_height, corner_radius=s.bar_corner_radius)
    rect.set_stroke(width=s.stroke_width).set_fill(opacity=opacity)

    txt = Text(str(value), font_size=s.font_size_small).scale(0.72).move_to(rect.get_center())
    lab = Text(label, font_size=s.font_size_small).scale(0.62).next_to(rect, UP, buff=0.1) if label else VGroup()
    return VGroup(rect, txt, lab)


def op_tex(kind: str, unknown: str, initial: int, change: int, final: int) -> MathTex:
    # returns the matching operation expression, but ONLY after the modeling
    if unknown == "final":
        # final = initial ± change
        sign = "+" if kind == "increase" else "-"
        return MathTex(rf"{initial} {sign} {change} = {final}").scale(1.25)
    if unknown == "initial":
        # initial = final ∓ change
        sign = "-" if kind == "increase" else "+"
        return MathTex(rf"{final} {sign} {change} = {initial}").scale(1.25)
    # unknown == "change"
    # change = final - initial (or initial - final) depending on increase/decrease
    # keep it consistent as absolute difference:
    return MathTex(rf"{final} - {initial} = {change}").scale(1.25)


# ============================================================
# LESSON SCENE
# ============================================================

class M3_L23_ChangeProblems(Scene):
    """
    M3_L23 — Change / Transformation problems

    Visual flow:
      display initial state (before)
      label "before"
      animate change (add or remove segment)
      display final state (after)
      highlight unknown state (initial OR change OR final)
      only then translate to operation
      reveal result
    """

    def __init__(
        self,
        cfg: LessonConfigM3_L23 = LessonConfigM3_L23(),
        style: ChangePSStyle = ChangePSStyle(),
        **kwargs
    ):
        super().__init__(**kwargs)
        self.cfg = cfg
        self.s = style
        self.steps: List[Tuple[str, Callable[[], None]]] = []

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
        title = T(self.cfg, self.s, self.cfg.title_en, self.cfg.title_ar, scale=0.60)
        title = self.banner(title)

        subtitle = T(
            self.cfg, self.s,
            "Before → Change → After",
            "قبل → تحول → بعد",
            scale=0.62
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
            "Discussion: Sometimes the unknown is BEFORE, sometimes AFTER.",
            "نقاش: أحياناً المجهول قبل التحول وأحياناً بعده.",
            scale=0.50
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        box = RoundedRectangle(width=11.6, height=2.9, corner_radius=0.25).to_edge(DOWN).shift(UP * 0.2)
        box.set_stroke(width=3).set_fill(opacity=0.06)

        l1 = T(self.cfg, self.s, "• Identify what happens first.", "• نحدد ما يحدث أولاً.", scale=0.52)
        l2 = T(self.cfg, self.s, "• Identify the change (gain / loss).", "• نحدد التحول (زيادة / نقصان).", scale=0.52)
        l3 = T(self.cfg, self.s, "• Then locate the unknown on the timeline.", "• ثم نحدد مكان المجهول على الخط الزمني.", scale=0.52)

        scaff = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(box.get_center())
        self.play(Create(box), FadeIn(scaff, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.5)
        self.play(FadeOut(VGroup(box, scaff)), run_time=self.s.rt_fast)

    def step_institutionalization(self):
        prompt = T(
            self.cfg, self.s,
            "Institutionalization: Initial → Transformation → Final",
            "التثبيت: الحالة الأولى → التحول → الحالة النهائية",
            scale=0.52
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        r1 = MathTex(r"\text{Final} = \text{Initial} \pm \text{Change}").scale(1.1)
        r2 = MathTex(r"\text{Initial} = \text{Final} \mp \text{Change}").scale(1.1).next_to(r1, DOWN, buff=0.25)

        self.play(Write(r1), run_time=self.s.rt_norm)
        self.play(Write(r2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(VGroup(r1, r2)), run_time=self.s.rt_fast)

    def step_mini_assessment(self):
        prompt = T(
            self.cfg, self.s,
            "Mini-check: Salma had some pencils. She loses 4 and has 9 left. How many before?",
            "تحقق صغير: سلمة كان عندها أقلام. ضاعت منها 4 وبقي 9. كم كان عندها قبل؟",
            scale=0.44
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        p = ChangeProblem(
            pid="C4",
            kind="decrease",
            initial=None,
            change=4,
            final=9,
            unknown="initial",
            item="pencils",
            context_subject="Salma",
            verb_lose="loses",
            question="Salma had some pencils. She loses 4 and has 9 left. How many pencils did she have before?"
        )
        g = self.animate_problem(p)
        self.wait(0.35)
        self.play(FadeOut(g), run_time=self.s.rt_fast)

    def step_outro(self):
        recap = VGroup(
            T(self.cfg, self.s, "Recap:", "الخلاصة:", scale=0.6),
            T(self.cfg, self.s, "• Before (initial) — what we start with", "• قبل (البداية) — ما نبدأ به", scale=0.50),
            T(self.cfg, self.s, "• Change — added or removed", "• التحول — زيادة أو نقصان", scale=0.50),
            T(self.cfg, self.s, "• After (final) — what we end with", "• بعد (النهاية) — ما ننتهي إليه", scale=0.50),
            T(self.cfg, self.s, "• Put the unknown in the right place, then choose the operation", "• نحدد مكان المجهول ثم نختار العملية", scale=0.44),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        recap.to_edge(RIGHT).shift(DOWN * 0.15)
        self.play(FadeIn(recap, shift=LEFT * 0.2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(recap, shift=RIGHT * 0.2), FadeOut(self.title), run_time=self.s.rt_fast)

    # ============================================================
    # Core animation per problem
    # ============================================================

    def animate_problem(self, prob: ChangeProblem) -> VGroup:
        # compute missing based on kind + unknown
        kind = prob.kind
        unknown = prob.unknown

        initial = prob.initial
        change = prob.change
        final = prob.final

        if unknown == "final":
            assert initial is not None and change is not None
            final = prob.answer if prob.answer is not None else (initial + change if kind == "increase" else initial - change)
        elif unknown == "initial":
            assert final is not None and change is not None
            initial = prob.answer if prob.answer is not None else (final - change if kind == "increase" else final + change)
        else:  # unknown == "change"
            assert initial is not None and final is not None
            change = prob.answer if prob.answer is not None else (final - initial if kind == "increase" else initial - final)

        assert initial is not None and change is not None and final is not None

        pb = VGroup()
        if self.s.show_problem_text:
            pb = problem_box(prob.question, self.s)
            self.play(FadeIn(pb, shift=DOWN * 0.1), run_time=self.s.rt_norm)

        # timeline
        tl = VGroup()
        if self.s.show_timeline:
            line = Line(LEFT * (self.s.timeline_w / 2), RIGHT * (self.s.timeline_w / 2), stroke_width=self.s.stroke_width)
            line.move_to(np.array([0, self.s.timeline_y, 0]))
            arr = Arrow(line.get_left(), line.get_right(), buff=0, stroke_width=self.s.stroke_width)
            before_txt = Text("before", font_size=self.s.font_size_small).scale(0.65).next_to(arr.get_left(), UP, buff=0.12)
            after_txt = Text("after", font_size=self.s.font_size_small).scale(0.65).next_to(arr.get_right(), UP, buff=0.12)
            tl = VGroup(arr, before_txt, after_txt)
            self.play(FadeIn(tl, shift=UP * 0.05), run_time=self.s.rt_fast)

        # BEFORE (initial)
        p1 = T(self.cfg, self.s, self.cfg.prompt_before_en, self.cfg.prompt_before_ar, scale=0.56)
        p1 = self.banner(p1).shift(DOWN * 0.9)
        self.play(Transform(self.title, p1), run_time=self.s.rt_fast)

        before_label = "Before" if self.cfg.language == "en" else "قبل"
        before_bar = bar_segment(initial, self.s, label=f"{before_label}: {initial} {prob.item}", opacity=self.s.before_opacity)
        before_bar.move_to(np.array([0, self.s.before_y, 0]))
        before_bar.shift(np.array([self.s.left_anchor_x, 0, 0]) - before_bar[0].get_left())

        self.play(Create(before_bar[0]), FadeIn(before_bar[1]), FadeIn(before_bar[2], shift=UP * 0.05), run_time=self.s.rt_norm)

        # CHANGE (add or remove)
        p2 = T(self.cfg, self.s, self.cfg.prompt_change_en, self.cfg.prompt_change_ar, scale=0.56)
        p2 = self.banner(p2).shift(DOWN * 0.9)
        self.play(Transform(self.title, p2), run_time=self.s.rt_fast)

        change_label = "+ change" if kind == "increase" else "- change"
        ch = bar_segment(change, self.s, label=f"{change_label}: {change}", opacity=self.s.change_opacity)
        ch.move_to(np.array([0, self.s.change_y, 0]))
        ch.shift(np.array([self.s.left_anchor_x, 0, 0]) - ch[0].get_left())
        self.play(Create(ch[0]), FadeIn(ch[1]), FadeIn(ch[2], shift=UP * 0.05), run_time=self.s.rt_norm)

        # animate transformation into AFTER bar:
        p3 = T(self.cfg, self.s, self.cfg.prompt_after_en, self.cfg.prompt_after_ar, scale=0.56)
        p3 = self.banner(p3).shift(DOWN * 0.9)
        self.play(Transform(self.title, p3), run_time=self.s.rt_fast)

        after_label = "After" if self.cfg.language == "en" else "بعد"
        after_bar = bar_segment(final, self.s, label=f"{after_label}: {final} {prob.item}", opacity=self.s.after_opacity)
        after_bar.move_to(np.array([0, self.s.after_y, 0]))
        after_bar.shift(np.array([self.s.left_anchor_x, 0, 0]) - after_bar[0].get_left())

        # build AFTER visually from BEFORE + CHANGE (or remove)
        if kind == "increase":
            # move BEFORE down to become the start of AFTER, then attach CHANGE to the right
            before_copy = before_bar[0].copy()
            self.play(Transform(before_copy, Rectangle(width=before_bar[0].width, height=before_bar[0].height).move_to(after_bar[0].get_center()).shift(LEFT*(after_bar[0].width - before_bar[0].width)/2)),
                      run_time=self.s.rt_fast)
            # move CHANGE into position at the end of BEFORE inside AFTER
            target_x = after_bar[0].get_left()[0] + before_bar[0].width + ch[0].width / 2
            target = np.array([target_x, after_bar[0].get_center()[1], 0])
            self.play(ch[0].animate.move_to(target), FadeOut(ch[2]), run_time=self.s.rt_norm)
            # reveal AFTER bar
            self.play(Create(after_bar[0]), FadeIn(after_bar[1]), FadeIn(after_bar[2], shift=UP * 0.05), run_time=self.s.rt_norm)
            self.play(FadeOut(before_copy), run_time=self.s.rt_fast)
        else:
            # decrease: show AFTER as BEFORE with a removed segment
            self.play(Create(after_bar[0]), FadeIn(after_bar[1]), FadeIn(after_bar[2], shift=UP * 0.05), run_time=self.s.rt_norm)
            # animate "removal": move CHANGE over the right end of BEFORE then fade it
            target = before_bar[0].get_right() - RIGHT * (ch[0].width / 2)
            self.play(ch[0].animate.move_to(np.array([target[0], before_bar[0].get_center()[1], 0])),
                      FadeOut(ch[2]),
                      run_time=self.s.rt_norm)
            cut = Rectangle(width=ch[0].width, height=before_bar[0].height).set_stroke(width=0).set_fill(opacity=0.25)
            cut.move_to(np.array([target[0], before_bar[0].get_center()[1], 0]))
            self.play(FadeIn(cut), run_time=self.s.rt_fast)
            self.play(FadeOut(cut), FadeOut(ch[0]), run_time=self.s.rt_fast)

        # Highlight UNKNOWN
        p4 = T(self.cfg, self.s, self.cfg.prompt_unknown_en, self.cfg.prompt_unknown_ar, scale=0.56)
        p4 = self.banner(p4).shift(DOWN * 0.9)
        self.play(Transform(self.title, p4), run_time=self.s.rt_fast)

        unknown_hl = VGroup()
        if prob.unknown == "initial":
            unknown_hl = SurroundingRectangle(before_bar[0], buff=0.15).set_stroke(width=6)
        elif prob.unknown == "change":
            unknown_hl = SurroundingRectangle(ch[0], buff=0.15).set_stroke(width=6) if kind == "increase" else SurroundingRectangle(after_bar[0], buff=0.15).set_stroke(width=6)
        else:  # final
            unknown_hl = SurroundingRectangle(after_bar[0], buff=0.15).set_stroke(width=6)

        self.play(Create(unknown_hl), run_time=self.s.rt_fast)

        # Model -> Operation (only now)
        op = VGroup()
        if self.s.show_model_to_operation:
            p5 = T(self.cfg, self.s, self.cfg.prompt_link_en, self.cfg.prompt_link_ar, scale=0.56)
            p5 = self.banner(p5).shift(DOWN * 0.9)
            self.play(Transform(self.title, p5), run_time=self.s.rt_fast)

            expr = op_tex(kind, prob.unknown, initial, change, final).to_edge(DOWN)
            self.play(Write(expr), run_time=self.s.rt_norm)
            op.add(expr)

        # Context answer
        ctx = VGroup()
        if self.s.show_context_answer:
            if prob.unknown == "final":
                ans_txt = f"Now: {final} {prob.item}"
            elif prob.unknown == "initial":
                ans_txt = f"Before: {initial} {prob.item}"
            else:
                ans_txt = f"Change: {change} {prob.item}"

            ctx_t = Text("Answer: " + ans_txt, font_size=self.s.font_size_small).scale(0.7)
            if len(op):
                ctx_t.next_to(op[0], UP, buff=0.2)
            else:
                ctx_t.to_edge(DOWN)
            self.play(FadeIn(ctx_t, shift=UP * 0.05), run_time=self.s.rt_fast)
            ctx.add(ctx_t)

        if self.s.show_verify and len(op):
            check = Text("✓", font_size=self.s.font_size_main).scale(0.7).next_to(op[0], LEFT, buff=0.25)
            self.play(FadeIn(check, shift=UP * 0.05), run_time=self.s.rt_fast)
            ctx.add(check)

        return VGroup(pb, tl, before_bar, ch, after_bar, unknown_hl, op, ctx)
        

# ============================================================
# RUN:
#   manim -pqh your_file.py M3_L23_ChangeProblems
#
# CUSTOMIZE:
#   cfg = LessonConfigM3_L23(
#       problems=[ChangeProblem(pid="X", kind="increase", initial=10, change=3, unknown="final",
#                               item="books", context_subject="Aya", verb_gain="buys",
#                               question="Aya has 10 books. She buys 3 more...")],
#       language="en"
#   )
# ============================================================
