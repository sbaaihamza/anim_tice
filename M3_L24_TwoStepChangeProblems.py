from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Literal

import numpy as np
from manim import *


# ============================================================
# CONFIG / STYLES
# ============================================================

@dataclass
class TwoStepChangeStyle:
    stroke_width: float = 4.0
    fill_opacity: float = 0.14

    unit_width: float = 0.5
    bar_height: float = 0.62
    bar_corner_radius: float = 0.18

    # opacities
    state_opacity: float = 0.18
    change_opacity: float = 0.25

    # text
    font_size_title: int = 38
    font_size_main: int = 34
    font_size_small: int = 28
    font_size_problem: int = 26

    # timeline
    timeline_y: float = -1.55
    timeline_w: float = 11.0

    # pacing
    pause: float = 0.45
    rt_fast: float = 0.7
    rt_norm: float = 1.0
    rt_slow: float = 1.25

    # toggles
    show_problem_text: bool = True
    show_timeline: bool = True
    show_model_to_operations: bool = True
    show_context_answer: bool = True
    show_verify: bool = True

    # layout
    left_anchor_x: float = -5.2
    y_initial: float = 1.05
    y_intermediate: float = 0.2
    y_final: float = -0.65


@dataclass
class TwoStepChangeProblem:
    """
    Two-step change:

      state0 --(change1)--> state1 --(change2)--> state2

    kind for each change:
      + (increase) or - (decrease)

    unknown can be:
      - "final" (state2)   : state0, change1, change2 known
      - "initial" (state0) : state2, change1, change2 known
      - "intermediate" (state1) : state0 & change1 known OR state2 & change2 known (choose one)
    """
    pid: str

    initial: Optional[int] = None
    change1: int = 0
    kind1: Literal["increase", "decrease"] = "increase"

    change2: int = 0
    kind2: Literal["increase", "decrease"] = "increase"

    intermediate: Optional[int] = None
    final: Optional[int] = None

    unknown: Literal["final", "initial", "intermediate"] = "final"

    item: str = "stickers"
    question: str = ""
    answer: Optional[int] = None  # computed if None


@dataclass
class LessonConfigM3_L24:
    title_en: str = "Solving two-step change problems"
    title_ar: str = "حل مسائل تحول من خطوتين"
    language: str = "en"

    prompt_initial_en: str = "Start: identify the initial state."
    prompt_initial_ar: str = "البداية: نحدد الحالة الأولى."

    prompt_change1_en: str = "Step 1: apply the first change."
    prompt_change1_ar: str = "الخطوة 1: نطبق التحول الأول."

    prompt_intermediate_en: str = "Pause: label the intermediate state."
    prompt_intermediate_ar: str = "توقف: نحدد الحالة الوسطية."

    prompt_change2_en: str = "Step 2: apply the second change."
    prompt_change2_ar: str = "الخطوة 2: نطبق التحول الثاني."

    prompt_final_en: str = "End: identify the final state."
    prompt_final_ar: str = "النهاية: نحدد الحالة النهائية."

    prompt_link_en: str = "Now reveal the combined operations."
    prompt_link_ar: str = "نُظهر الآن العمليات المرتبطة."

    problems: List[TwoStepChangeProblem] = field(default_factory=lambda: [
        TwoStepChangeProblem(
            pid="TS1",
            initial=10,
            change1=4,
            kind1="increase",
            change2=3,
            kind2="decrease",
            unknown="final",
            item="books",
            question="Aya has 10 books. She buys 4 more, then gives away 3. How many books does she have now?"
        ),
        TwoStepChangeProblem(
            pid="TS2",
            initial=18,
            change1=6,
            kind1="decrease",
            change2=5,
            kind2="increase",
            unknown="final",
            item="coins",
            question="Yassine has 18 coins. He loses 6, then receives 5. How many coins does he have now?"
        ),
        TwoStepChangeProblem(
            pid="TS3",
            initial=None,
            change1=7,
            kind1="increase",
            change2=2,
            kind2="increase",
            final=20,
            unknown="initial",
            item="stickers",
            question="Lina had some stickers. She gets 7, then gets 2 more, and now has 20. How many did she have at first?"
        ),
    ])


# ============================================================
# PRIMITIVES
# ============================================================

def T(cfg: LessonConfigM3_L24, s: TwoStepChangeStyle, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
    txt = en if cfg.language == "en" else (ar or en)
    return Text(txt, font_size=s.font_size_main).scale(scale)


def problem_box(text: str, s: TwoStepChangeStyle) -> VGroup:
    box = RoundedRectangle(width=11.6, height=2.1, corner_radius=0.25).set_stroke(width=3).set_fill(opacity=0.06)
    t = Paragraph(*text.split("\n"), alignment="left", font_size=s.font_size_problem).scale(0.95)
    t.move_to(box.get_center())
    return VGroup(box, t).to_edge(UP).shift(DOWN * 1.25)


def state_bar(value: int, s: TwoStepChangeStyle, label: str, opacity: float) -> VGroup:
    w = max(0.9, value * s.unit_width)
    rect = RoundedRectangle(width=w, height=s.bar_height, corner_radius=s.bar_corner_radius)
    rect.set_stroke(width=s.stroke_width).set_fill(opacity=opacity)
    txt = Text(str(value), font_size=s.font_size_small).scale(0.72).move_to(rect.get_center())
    lab = Text(label, font_size=s.font_size_small).scale(0.62).next_to(rect, UP, buff=0.1)
    return VGroup(rect, txt, lab)


def change_bar(value: int, s: TwoStepChangeStyle, label: str, opacity: float) -> VGroup:
    w = max(0.9, value * s.unit_width)
    rect = RoundedRectangle(width=w, height=s.bar_height, corner_radius=s.bar_corner_radius)
    rect.set_stroke(width=s.stroke_width).set_fill(opacity=opacity)
    txt = Text(str(value), font_size=s.font_size_small).scale(0.72).move_to(rect.get_center())
    lab = Text(label, font_size=s.font_size_small).scale(0.62).next_to(rect, UP, buff=0.1)
    return VGroup(rect, txt, lab)


def apply_change(value: int, delta: int, kind: str) -> int:
    return value + delta if kind == "increase" else value - delta


def op_chain_tex(initial: int, c1: int, k1: str, c2: int, k2: str, final: int) -> MathTex:
    s1 = "+" if k1 == "increase" else "-"
    s2 = "+" if k2 == "increase" else "-"
    return MathTex(rf"{initial} {s1} {c1} {s2} {c2} = {final}").scale(1.25)


# ============================================================
# LESSON SCENE
# ============================================================

class M3_L24_TwoStepChangeProblems(Scene):
    """
    M3_L24 — Two-step change problems

    Visual flow:
      initial state
      first change
      intermediate state (explicit pause + label)
      second change
      final state
      highlight target (unknown)
      reveal combined operations (after modeling)
    """

    def __init__(
        self,
        cfg: LessonConfigM3_L24 = LessonConfigM3_L24(),
        style: TwoStepChangeStyle = TwoStepChangeStyle(),
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
            "State → Change → Intermediate → Change → Final",
            "حالة → تحول → وسط → تحول → نهاية",
            scale=0.50
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
            "Discussion: Why does order matter?",
            "نقاش: لماذا الترتيب مهم؟",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        box = RoundedRectangle(width=11.6, height=2.9, corner_radius=0.25).to_edge(DOWN).shift(UP * 0.2)
        box.set_stroke(width=3).set_fill(opacity=0.06)

        l1 = T(self.cfg, self.s, "• Each change modifies the previous state.", "• كل تحول يغير الحالة السابقة.", scale=0.52)
        l2 = T(self.cfg, self.s, "• You must track the intermediate state.", "• يجب تتبع الحالة الوسطية.", scale=0.52)
        l3 = T(self.cfg, self.s, "• Swapping changes can lead to different results.", "• تغيير الترتيب قد يعطي نتيجة مختلفة.", scale=0.52)

        scaff = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(box.get_center())
        self.play(Create(box), FadeIn(scaff, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.5)
        self.play(FadeOut(VGroup(box, scaff)), run_time=self.s.rt_fast)

    def step_institutionalization(self):
        prompt = T(
            self.cfg, self.s,
            "Institutionalization: solve step by step",
            "التثبيت: نحل خطوة بخطوة",
            scale=0.56
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        r = VGroup(
            T(self.cfg, self.s, "1) Initial state", "1) الحالة الأولى", scale=0.52),
            T(self.cfg, self.s, "2) Apply change 1 → intermediate", "2) نطبق التحول 1 → وسط", scale=0.52),
            T(self.cfg, self.s, "3) Apply change 2 → final", "3) نطبق التحول 2 → نهاية", scale=0.52),
            T(self.cfg, self.s, "4) Then write the combined operations", "4) ثم نكتب العمليات", scale=0.52),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16).to_edge(RIGHT).shift(LEFT * 0.6)

        self.play(FadeIn(r, shift=LEFT * 0.2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(r, shift=RIGHT * 0.2), run_time=self.s.rt_fast)

    def step_mini_assessment(self):
        prompt = T(
            self.cfg, self.s,
            "Mini-check: 9 birds, +6 arrive, -4 fly away. Final?",
            "تحقق صغير: 9 عصافير، +6 تصل، -4 تطير. النهاية؟",
            scale=0.48
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        p = TwoStepChangeProblem(
            pid="TS4",
            initial=9,
            change1=6,
            kind1="increase",
            change2=4,
            kind2="decrease",
            unknown="final",
            item="birds",
            question="There are 9 birds. 6 arrive, then 4 fly away. How many birds are there now?"
        )
        g = self.animate_problem(p)
        self.wait(0.35)
        self.play(FadeOut(g), run_time=self.s.rt_fast)

    def step_outro(self):
        recap = VGroup(
            T(self.cfg, self.s, "Recap:", "الخلاصة:", scale=0.6),
            T(self.cfg, self.s, "• Two changes = two successive steps", "• تحولان = خطوتان متتاليتان", scale=0.50),
            T(self.cfg, self.s, "• Always write the intermediate state", "• دائماً نكتب الحالة الوسطية", scale=0.50),
            T(self.cfg, self.s, "• Then combine the operations", "• ثم نجمع العمليات", scale=0.50),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        recap.to_edge(RIGHT).shift(DOWN * 0.15)
        self.play(FadeIn(recap, shift=LEFT * 0.2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(recap, shift=RIGHT * 0.2), FadeOut(self.title), run_time=self.s.rt_fast)

    # ============================================================
    # Core animation per problem
    # ============================================================

    def animate_problem(self, prob: TwoStepChangeProblem) -> VGroup:
        # compute states
        if prob.unknown == "final":
            assert prob.initial is not None
            s0 = prob.initial
            s1 = apply_change(s0, prob.change1, prob.kind1)
            s2 = apply_change(s1, prob.change2, prob.kind2)
            ans = prob.answer if prob.answer is not None else s2
        elif prob.unknown == "initial":
            assert prob.final is not None
            s2 = prob.final
            # reverse step2 then step1
            s1 = apply_change(s2, prob.change2, "decrease" if prob.kind2 == "increase" else "increase")
            s0 = apply_change(s1, prob.change1, "decrease" if prob.kind1 == "increase" else "increase")
            ans = prob.answer if prob.answer is not None else s0
        else:  # intermediate unknown
            # choose: if initial known -> forward to intermediate; else if final known -> reverse
            if prob.initial is not None:
                s0 = prob.initial
                s1 = apply_change(s0, prob.change1, prob.kind1)
                s2 = apply_change(s1, prob.change2, prob.kind2) if prob.final is None else prob.final
            else:
                assert prob.final is not None
                s2 = prob.final
                s1 = apply_change(s2, prob.change2, "decrease" if prob.kind2 == "increase" else "increase")
                s0 = apply_change(s1, prob.change1, "decrease" if prob.kind1 == "increase" else "increase") if prob.initial is None else prob.initial
            ans = prob.answer if prob.answer is not None else s1

        pb = VGroup()
        if self.s.show_problem_text:
            pb = problem_box(prob.question, self.s)
            self.play(FadeIn(pb, shift=DOWN * 0.1), run_time=self.s.rt_norm)

        # timeline with two arrows
        tl = VGroup()
        if self.s.show_timeline:
            base = Line(LEFT * (self.s.timeline_w / 2), RIGHT * (self.s.timeline_w / 2), stroke_width=self.s.stroke_width)
            base.move_to(np.array([0, self.s.timeline_y, 0]))
            a1 = Arrow(base.get_left(), base.get_center(), buff=0, stroke_width=self.s.stroke_width)
            a2 = Arrow(base.get_center(), base.get_right(), buff=0, stroke_width=self.s.stroke_width)
            t0 = Text("before", font_size=self.s.font_size_small).scale(0.62).next_to(a1.get_left(), UP, buff=0.12)
            t1 = Text("middle", font_size=self.s.font_size_small).scale(0.62).next_to(base.get_center(), UP, buff=0.12)
            t2 = Text("after", font_size=self.s.font_size_small).scale(0.62).next_to(a2.get_right(), UP, buff=0.12)
            tl = VGroup(a1, a2, t0, t1, t2)
            self.play(FadeIn(tl, shift=UP * 0.05), run_time=self.s.rt_fast)

        # INITIAL
        p0 = T(self.cfg, self.s, self.cfg.prompt_initial_en, self.cfg.prompt_initial_ar, scale=0.56)
        p0 = self.banner(p0).shift(DOWN * 0.9)
        self.play(Transform(self.title, p0), run_time=self.s.rt_fast)

        initial_value = s0 if prob.unknown != "initial" else ans
        label0 = ("Initial" if self.cfg.language == "en" else "البداية") + f": {initial_value} {prob.item}"
        b0 = state_bar(initial_value, self.s, label0, opacity=self.s.state_opacity)
        b0.move_to(np.array([0, self.s.y_initial, 0]))
        b0.shift(np.array([self.s.left_anchor_x, 0, 0]) - b0[0].get_left())
        self.play(Create(b0[0]), FadeIn(b0[1]), FadeIn(b0[2], shift=UP * 0.05), run_time=self.s.rt_norm)

        # CHANGE 1
        p1 = T(self.cfg, self.s, self.cfg.prompt_change1_en, self.cfg.prompt_change1_ar, scale=0.56)
        p1 = self.banner(p1).shift(DOWN * 0.9)
        self.play(Transform(self.title, p1), run_time=self.s.rt_fast)

        sign1 = "+" if prob.kind1 == "increase" else "-"
        c1 = change_bar(prob.change1, self.s, label=f"Change 1: {sign1}{prob.change1}", opacity=self.s.change_opacity)
        c1.move_to(np.array([0, self.s.y_intermediate, 0]))
        c1.shift(np.array([self.s.left_anchor_x, 0, 0]) - c1[0].get_left())
        self.play(Create(c1[0]), FadeIn(c1[1]), FadeIn(c1[2], shift=UP * 0.05), run_time=self.s.rt_norm)

        # INTERMEDIATE (explicit pause + label)
        p2 = T(self.cfg, self.s, self.cfg.prompt_intermediate_en, self.cfg.prompt_intermediate_ar, scale=0.56)
        p2 = self.banner(p2).shift(DOWN * 0.9)
        self.play(Transform(self.title, p2), run_time=self.s.rt_fast)

        intermediate_value = s1 if prob.unknown != "intermediate" else ans
        label1 = ("Intermediate" if self.cfg.language == "en" else "وسط") + f": {intermediate_value} {prob.item}"
        b1 = state_bar(intermediate_value, self.s, label1, opacity=self.s.state_opacity)
        b1.move_to(np.array([0, self.s.y_intermediate, 0]))
        b1.shift(np.array([self.s.left_anchor_x, 0, 0]) - b1[0].get_left())

        # animate from b0 + c1 to b1 (show step as transformation)
        self.play(Create(b1[0]), FadeIn(b1[1]), FadeIn(b1[2], shift=UP * 0.05), run_time=self.s.rt_norm)

        glow1 = SurroundingRectangle(b1[0], buff=0.15).set_stroke(width=6)
        self.play(Create(glow1), run_time=self.s.rt_fast)
        self.wait(0.2)
        self.play(FadeOut(glow1), run_time=self.s.rt_fast)

        # CHANGE 2
        p3 = T(self.cfg, self.s, self.cfg.prompt_change2_en, self.cfg.prompt_change2_ar, scale=0.56)
        p3 = self.banner(p3).shift(DOWN * 0.9)
        self.play(Transform(self.title, p3), run_time=self.s.rt_fast)

        sign2 = "+" if prob.kind2 == "increase" else "-"
        c2 = change_bar(prob.change2, self.s, label=f"Change 2: {sign2}{prob.change2}", opacity=self.s.change_opacity)
        c2.move_to(np.array([0, self.s.y_final, 0]))
        c2.shift(np.array([self.s.left_anchor_x, 0, 0]) - c2[0].get_left())
        self.play(Create(c2[0]), FadeIn(c2[1]), FadeIn(c2[2], shift=UP * 0.05), run_time=self.s.rt_norm)

        # FINAL
        p4 = T(self.cfg, self.s, self.cfg.prompt_final_en, self.cfg.prompt_final_ar, scale=0.56)
        p4 = self.banner(p4).shift(DOWN * 0.9)
        self.play(Transform(self.title, p4), run_time=self.s.rt_fast)

        final_value = s2 if prob.unknown != "final" else ans
        label2 = ("Final" if self.cfg.language == "en" else "النهاية") + f": {final_value} {prob.item}"
        b2 = state_bar(final_value, self.s, label2, opacity=self.s.state_opacity)
        b2.move_to(np.array([0, self.s.y_final, 0]))
        b2.shift(np.array([self.s.left_anchor_x, 0, 0]) - b2[0].get_left())
        self.play(Create(b2[0]), FadeIn(b2[1]), FadeIn(b2[2], shift=UP * 0.05), run_time=self.s.rt_norm)

        # highlight target
        target = b2 if prob.unknown == "final" else (b0 if prob.unknown == "initial" else b1)
        hi = SurroundingRectangle(target[0], buff=0.15).set_stroke(width=6)
        self.play(Create(hi), run_time=self.s.rt_fast)

        # reveal combined operations (after modeling)
        ops = VGroup()
        if self.s.show_model_to_operations and prob.unknown == "final":
            p5 = T(self.cfg, self.s, self.cfg.prompt_link_en, self.cfg.prompt_link_ar, scale=0.56)
            p5 = self.banner(p5).shift(DOWN * 0.9)
            self.play(Transform(self.title, p5), run_time=self.s.rt_fast)

            expr = op_chain_tex(s0, prob.change1, prob.kind1, prob.change2, prob.kind2, final_value).to_edge(DOWN)
            self.play(Write(expr), run_time=self.s.rt_norm)
            ops.add(expr)

        # context answer
        ctx = VGroup()
        if self.s.show_context_answer:
            if prob.unknown == "final":
                msg = f"Answer: {final_value} {prob.item}"
            elif prob.unknown == "initial":
                msg = f"Answer: {initial_value} {prob.item} at the start"
            else:
                msg = f"Answer: {intermediate_value} {prob.item} after step 1"
            t = Text(msg, font_size=self.s.font_size_small).scale(0.7)
            if len(ops):
                t.next_to(ops[0], UP, buff=0.2)
            else:
                t.to_edge(DOWN)
            self.play(FadeIn(t, shift=UP * 0.05), run_time=self.s.rt_fast)
            ctx.add(t)

        if self.s.show_verify and len(ops):
            check = Text("✓", font_size=self.s.font_size_main).scale(0.7).next_to(ops[0], LEFT, buff=0.25)
            self.play(FadeIn(check, shift=UP * 0.05), run_time=self.s.rt_fast)
            ctx.add(check)

        return VGroup(pb, tl, b0, c1, b1, c2, b2, hi, ops, ctx)


# ============================================================
# RUN:
#   manim -pqh your_file.py M3_L24_TwoStepChangeProblems
#
# CUSTOMIZE EXAMPLE:
#   cfg = LessonConfigM3_L24(
#       problems=[TwoStepChangeProblem(pid="X", initial=25, change1=10, kind1="decrease", change2=3, kind2="decrease",
#                                      item="dirhams", question="...")],
#       language="en"
#   )
# ============================================================

