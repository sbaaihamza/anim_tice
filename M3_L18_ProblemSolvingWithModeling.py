from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Dict, Literal

import numpy as np
from manim import *


# ============================================================
# CONFIG / STYLES
# ============================================================

@dataclass
class ModelStyle:
    stroke_width: float = 4.0
    fill_opacity: float = 0.16

    # bar model visuals
    unit_width: float = 0.55  # visual width per 1 unit
    bar_height: float = 0.6
    bar_corner_radius: float = 0.16

    # text
    font_size_title: int = 38
    font_size_main: int = 34
    font_size_small: int = 28
    font_size_problem: int = 28

    # pacing
    pause: float = 0.45
    rt_fast: float = 0.7
    rt_norm: float = 1.0
    rt_slow: float = 1.25

    # toggles
    show_arabic: bool = False  # enable only if Arabic fonts render correctly
    show_problem_text: bool = True
    show_relation_arrows: bool = True
    show_reasoning_pause: bool = True
    show_operation_reveal: bool = True
    show_verify_step: bool = True

    # layout
    text_box_width: float = 11.4
    text_box_height: float = 2.3
    bar_left_x: float = -5.2


@dataclass
class ModelProblem:
    """
    A "modeling-friendly" word problem.

    Supported types:
      - "difference": unknown = bigger - smaller
      - "total": unknown = part1 + part2
      - "missing_part": unknown = total - known_part
      - "compare_add": unknown = smaller + difference
    """
    pid: str
    kind: Literal["difference", "total", "missing_part", "compare_add"]

    # labels
    subject_a: str
    subject_b: str
    item: str

    # quantities
    a_value: int
    b_value: int
    # optional total or difference depending on kind
    total: Optional[int] = None
    difference: Optional[int] = None

    # what is asked
    question: str = ""
    # expected answer
    answer: int = 0


@dataclass
class LessonConfigM3_L18:
    title_en: str = "Solving problems using modeling"
    title_ar: str = "حل مسائل باستعمال النمذجة"
    language: str = "en"  # "en" | "ar"

    # prompts (strategy steps)
    prompt_read_en: str = "Step 1: Read and extract quantities."
    prompt_read_ar: str = "الخطوة 1: نقرأ ونستخرج المعطيات."

    prompt_model_en: str = "Step 2: Build a bar model."
    prompt_model_ar: str = "الخطوة 2: نبني نموذجاً (أشرطة)."

    prompt_reason_en: str = "Step 3: Reason on the model BEFORE calculating."
    prompt_reason_ar: str = "الخطوة 3: نفكر في النموذج قبل الحساب."

    prompt_calc_en: str = "Step 4: Choose the operation and calculate."
    prompt_calc_ar: str = "الخطوة 4: نختار العملية ونحسب."

    prompt_verify_en: str = "Step 5: Verify by mapping back to the model."
    prompt_verify_ar: str = "الخطوة 5: نتحقق بالرجوع إلى النموذج."

    # default problems
    problems: List[ModelProblem] = field(default_factory=lambda: [
        ModelProblem(
            pid="P1",
            kind="missing_part",
            subject_a="Sara",
            subject_b="",
            item="cards",
            a_value=0, b_value=0,
            total=18,
            difference=None,
            question="Sara has 18 cards. She gave 7 cards away. How many cards does she have now?",
            answer=11
        ),
        ModelProblem(
            pid="P2",
            kind="difference",
            subject_a="Omar",
            subject_b="Rania",
            item="books",
            a_value=14,
            b_value=9,
            question="Omar has 14 books and Rania has 9 books. How many more books does Omar have?",
            answer=5
        ),
        ModelProblem(
            pid="P3",
            kind="total",
            subject_a="Amina",
            subject_b="Youssef",
            item="marbles",
            a_value=6,
            b_value=8,
            question="Amina has 6 marbles and Youssef has 8 marbles. How many marbles do they have altogether?",
            answer=14
        ),
    ])


# ============================================================
# REUSABLE PRIMITIVES
# ============================================================

def T(cfg: LessonConfigM3_L18, s: ModelStyle, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
    txt = en if cfg.language == "en" else (ar or en)
    return Text(txt, font_size=s.font_size_main).scale(scale)


def boxed_text(text: str, style: ModelStyle) -> VGroup:
    box = RoundedRectangle(width=style.text_box_width, height=style.text_box_height, corner_radius=0.25)
    box.set_stroke(width=3).set_fill(opacity=0.06)
    t = Paragraph(*text.split("\n"), alignment="left", font_size=style.font_size_problem)
    t.scale(0.9)
    t.move_to(box.get_center())
    return VGroup(box, t)


class BarBlock(VGroup):
    def __init__(self, units: int, style: ModelStyle, label: str = "", **kwargs):
        super().__init__(**kwargs)
        w = max(0.8, units * style.unit_width)
        rect = RoundedRectangle(width=w, height=style.bar_height, corner_radius=style.bar_corner_radius)
        rect.set_stroke(width=style.stroke_width).set_fill(opacity=style.fill_opacity)
        self.rect = rect
        self.units = units

        lab = Text(label, font_size=style.font_size_small).scale(0.75) if label else VGroup()
        if label:
            lab.next_to(rect, UP, buff=0.12)
        self.lab = lab
        self.add(rect, lab)

    def left(self) -> np.ndarray:
        return self.rect.get_left()

    def right(self) -> np.ndarray:
        return self.rect.get_right()


def question_mark(style: ModelStyle) -> Mobject:
    return Text("?", font_size=style.font_size_title).scale(0.9)


def op_tex(expr: str, scale: float = 1.25) -> Mobject:
    return MathTex(expr).scale(scale)


def arrow_between(a: Mobject, b: Mobject) -> Arrow:
    return Arrow(a.get_right(), b.get_left(), buff=0.2, stroke_width=4)


# ============================================================
# LESSON SCENE (Reusable / Adjustable / Extensible)
# ============================================================

class M3_L18_ProblemSolvingWithModeling(Scene):
    """
    M3_L18 — Modeling strategy

    Visual flow:
      display problem text
      extract and place first quantity as bar
      add second quantity (aligned/segmented)
      mark unknown part with ?
      pause for reasoning
      reveal operation
      show result
      map result back to model (verification)

    Extensible:
      Add more ModelProblem types; implement a builder per kind.
    """

    def __init__(
        self,
        cfg: LessonConfigM3_L18 = LessonConfigM3_L18(),
        style: ModelStyle = ModelStyle(),
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
            ("exploration_problems", self.step_exploration_problems),
            ("collective_discussion_compare_models", self.step_collective_discussion_compare_models),
            ("institutionalization_strategy", self.step_institutionalization_strategy),
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
            "Read → Model → Reason → Calculate → Verify",
            "نقرأ → نمذج → نفكر → نحسب → نتحقق",
            scale=0.55
        ).next_to(title, DOWN, buff=0.18)

        self.play(Write(title), FadeIn(subtitle, shift=DOWN * 0.15), run_time=self.s.rt_norm)
        self.wait(0.2)
        self.play(FadeOut(subtitle, shift=UP * 0.1), run_time=self.s.rt_fast)
        self.title = title

    # ------------------------------------------------------------
    # Core: animate one problem with bar model
    # ------------------------------------------------------------

    def animate_problem(self, prob: ModelProblem) -> VGroup:
        # Step 1: show problem text
        p1 = T(self.cfg, self.s, self.cfg.prompt_read_en, self.cfg.prompt_read_ar, scale=0.56)
        p1 = self.banner(p1).shift(DOWN * 0.9)
        self.play(Transform(self.title, p1), run_time=self.s.rt_fast)

        text_group = VGroup()
        if self.s.show_problem_text:
            text_group = boxed_text(prob.question, self.s).to_edge(UP).shift(DOWN * 1.3)
            self.play(FadeIn(text_group, shift=DOWN * 0.1), run_time=self.s.rt_norm)

        # Step 2: build model progressively
        p2 = T(self.cfg, self.s, self.cfg.prompt_model_en, self.cfg.prompt_model_ar, scale=0.56)
        p2 = self.banner(p2).shift(DOWN * 0.9)
        self.play(Transform(self.title, p2), run_time=self.s.rt_fast)

        model_group = VGroup()

        if prob.kind == "total":
            model_group = self.model_total(prob)
        elif prob.kind == "difference":
            model_group = self.model_difference(prob)
        elif prob.kind == "missing_part":
            model_group = self.model_missing_part(prob)
        elif prob.kind == "compare_add":
            model_group = self.model_compare_add(prob)
        else:
            raise ValueError(f"Unsupported kind: {prob.kind}")

        # Step 3: reasoning pause (no numbers-first)
        if self.s.show_reasoning_pause:
            p3 = T(self.cfg, self.s, self.cfg.prompt_reason_en, self.cfg.prompt_reason_ar, scale=0.54)
            p3 = self.banner(p3).shift(DOWN * 0.9)
            self.play(Transform(self.title, p3), run_time=self.s.rt_fast)

            thought = T(
                self.cfg, self.s,
                "What does the ? represent in the model?",
                "ماذا يمثل ? في النموذج؟",
                scale=0.52
            ).to_edge(DOWN)
            self.play(FadeIn(thought, shift=UP * 0.05), run_time=self.s.rt_fast)
            self.wait(0.5)
            self.play(FadeOut(thought), run_time=self.s.rt_fast)

        # Step 4: reveal operation and calculate
        op_group = VGroup()
        if self.s.show_operation_reveal:
            p4 = T(self.cfg, self.s, self.cfg.prompt_calc_en, self.cfg.prompt_calc_ar, scale=0.56)
            p4 = self.banner(p4).shift(DOWN * 0.9)
            self.play(Transform(self.title, p4), run_time=self.s.rt_fast)

            op_group = self.operation_reveal(prob)
            self.play(FadeIn(op_group, shift=UP * 0.05), run_time=self.s.rt_norm)

        # Step 5: verification
        verify_group = VGroup()
        if self.s.show_verify_step:
            p5 = T(self.cfg, self.s, self.cfg.prompt_verify_en, self.cfg.prompt_verify_ar, scale=0.56)
            p5 = self.banner(p5).shift(DOWN * 0.9)
            self.play(Transform(self.title, p5), run_time=self.s.rt_fast)

            verify_group = self.verify_mapping(prob, model_group)
            self.play(FadeIn(verify_group, shift=UP * 0.05), run_time=self.s.rt_fast)
            self.wait(0.4)

        return VGroup(text_group, model_group, op_group, verify_group)

    # ------------------------------------------------------------
    # Model builders (bar diagrams)
    # ------------------------------------------------------------

    def anchor_left(self, bar: Mobject):
        bar.shift(np.array([self.s.bar_left_x, 0, 0]) - bar.get_left())

    def model_total(self, prob: ModelProblem) -> VGroup:
        # two parts combine -> total unknown or known; here we ask total
        a = BarBlock(prob.a_value, self.s, label=f"{prob.subject_a}: {prob.a_value}")
        b = BarBlock(prob.b_value, self.s, label=f"{prob.subject_b}: {prob.b_value}")

        a.move_to(LEFT * 2.8 + UP * 0.3)
        b.next_to(a, DOWN, buff=0.65)
        self.anchor_left(a)
        self.anchor_left(b)

        brace = Brace(VGroup(a.rect, b.rect), direction=RIGHT)
        q = question_mark(self.s).next_to(brace, RIGHT, buff=0.2)

        if prob.subject_b == "":
            b.lab.set_opacity(0.0)

        self.play(Create(a.rect), FadeIn(a.lab, shift=UP * 0.05), run_time=self.s.rt_norm)
        self.play(Create(b.rect), FadeIn(b.lab, shift=UP * 0.05), run_time=self.s.rt_norm)
        self.play(GrowFromCenter(brace), FadeIn(q, shift=UP * 0.05), run_time=self.s.rt_norm)

        return VGroup(a, b, brace, q)

    def model_difference(self, prob: ModelProblem) -> VGroup:
        # align bars; extra part is unknown difference
        big = max(prob.a_value, prob.b_value)
        small = min(prob.a_value, prob.b_value)
        big_name = prob.subject_a if prob.a_value >= prob.b_value else prob.subject_b
        small_name = prob.subject_b if prob.a_value >= prob.b_value else prob.subject_a

        top = BarBlock(big, self.s, label=f"{big_name}: {big}")
        bottom = BarBlock(small, self.s, label=f"{small_name}: {small}")

        top.move_to(LEFT * 2.8 + UP * 0.3)
        bottom.next_to(top, DOWN, buff=0.75)
        self.anchor_left(top)
        self.anchor_left(bottom)

        self.play(Create(top.rect), FadeIn(top.lab, shift=UP * 0.05), run_time=self.s.rt_norm)
        self.play(Create(bottom.rect), FadeIn(bottom.lab, shift=UP * 0.05), run_time=self.s.rt_norm)

        # common part highlight
        common_w = small * self.s.unit_width
        common = Rectangle(width=common_w, height=self.s.bar_height).set_stroke(width=0).set_fill(opacity=0.22)
        common.move_to(top.rect.get_left() + np.array([common_w / 2, 0, 0]))
        common2 = common.copy().move_to(bottom.rect.get_left() + np.array([common_w / 2, 0, 0]))

        self.play(FadeIn(common), FadeIn(common2), run_time=self.s.rt_norm)

        # extra part with question mark
        extra_units = big - small
        extra = BarBlock(extra_units, self.s, label="")
        extra.rect.set_fill(opacity=0.22)
        extra.shift((top.rect.get_left() + np.array([common_w, 0, 0])) - extra.left())
        extra.move_to(extra.get_center() + np.array([0, top.get_center()[1] - extra.get_center()[1], 0]))

        q = question_mark(self.s).scale(0.8).move_to(extra.rect.get_center())

        if self.s.show_relation_arrows:
            arr = Arrow(bottom.rect.get_right(), top.rect.get_right(), buff=0.2, stroke_width=4)
            arr_lab = Text("difference", font_size=self.s.font_size_small).scale(0.65).next_to(arr, RIGHT, buff=0.15)
            self.play(Create(arr), FadeIn(arr_lab, shift=UP * 0.05), run_time=self.s.rt_norm)
        else:
            arr, arr_lab = VGroup(), VGroup()

        self.play(FadeIn(extra.rect), FadeIn(q, shift=UP * 0.05), run_time=self.s.rt_norm)

        return VGroup(top, bottom, common, common2, extra.rect, q, arr, arr_lab)

    def model_missing_part(self, prob: ModelProblem) -> VGroup:
        # total known, one part known, other part unknown
        assert prob.total is not None, "missing_part needs total"
        total = prob.total

        total_bar = BarBlock(total, self.s, label=f"Total: {total}")
        total_bar.move_to(LEFT * 2.8 + UP * 0.3)
        self.anchor_left(total_bar)

        known = BarBlock(7, self.s, label="Given: 7")  # will be overwritten
        # Parse known from text by using answer relationship if possible; user can set explicitly via a_value
        known_units = prob.a_value if prob.a_value > 0 else (total - prob.answer)
        known = BarBlock(known_units, self.s, label=f"Given: {known_units}")
        known.shift(total_bar.left() - known.left())
        known.move_to(known.get_center() + np.array([0, total_bar.get_center()[1] - known.get_center()[1], 0]))

        unknown_units = total - known_units
        unknown = BarBlock(unknown_units, self.s, label="")
        unknown.rect.set_fill(opacity=0.22)
        unknown.shift((known.right() - unknown.left()))
        unknown.move_to(unknown.get_center() + np.array([0, total_bar.get_center()[1] - unknown.get_center()[1], 0]))
        q = question_mark(self.s).scale(0.85).move_to(unknown.rect.get_center())

        # show stacked: total bar above, partition below (known + unknown)
        part_row = VGroup(known.rect.copy(), unknown.rect.copy()).arrange(RIGHT, buff=0)
        part_row.move_to(total_bar.get_center() + DOWN * 1.2)
        part_row.shift(total_bar.left() - part_row.get_left())

        self.play(Create(total_bar.rect), FadeIn(total_bar.lab, shift=UP * 0.05), run_time=self.s.rt_norm)
        self.play(FadeIn(part_row, shift=UP * 0.05), run_time=self.s.rt_norm)

        # mark known/unknown on the partition row
        known_lab = Text(str(known_units), font_size=self.s.font_size_small).scale(0.75).move_to(part_row[0].get_center())
        self.play(FadeIn(known_lab, shift=UP * 0.05), run_time=self.s.rt_fast)
        self.play(FadeIn(q, shift=UP * 0.05), run_time=self.s.rt_fast)

        if self.s.show_relation_arrows:
            br = Brace(part_row, direction=UP)
            br_lab = Text(f"{total}", font_size=self.s.font_size_small).scale(0.75).next_to(br, UP, buff=0.1)
            self.play(GrowFromCenter(br), FadeIn(br_lab, shift=UP * 0.05), run_time=self.s.rt_fast)
        else:
            br, br_lab = VGroup(), VGroup()

        return VGroup(total_bar, part_row, known_lab, q, br, br_lab)

    def model_compare_add(self, prob: ModelProblem) -> VGroup:
        # smaller known + difference known -> bigger unknown
        assert prob.difference is not None, "compare_add needs difference"
        small = prob.a_value
        diff = prob.difference

        base = BarBlock(small, self.s, label=f"{prob.subject_a}: {small}")
        extra = BarBlock(diff, self.s, label="difference")
        base.move_to(LEFT * 2.8 + UP * 0.2)
        self.anchor_left(base)
        extra.next_to(base.rect, RIGHT, buff=0)

        whole = VGroup(base.rect.copy(), extra.rect.copy()).arrange(RIGHT, buff=0)
        whole.move_to(base.rect.get_center())
        whole.shift(base.left() - whole.get_left())

        brace = Brace(whole, direction=UP)
        q = question_mark(self.s).next_to(brace, UP, buff=0.15)

        self.play(Create(base.rect), FadeIn(base.lab, shift=UP * 0.05), run_time=self.s.rt_norm)
        self.play(FadeIn(extra.rect, shift=UP * 0.05), run_time=self.s.rt_norm)
        self.play(GrowFromCenter(brace), FadeIn(q, shift=UP * 0.05), run_time=self.s.rt_norm)

        return VGroup(base, extra, whole, brace, q)

    # ------------------------------------------------------------
    # Operation reveal and verification
    # ------------------------------------------------------------

    def operation_reveal(self, prob: ModelProblem) -> VGroup:
        if prob.kind == "total":
            expr = rf"{prob.a_value} + {prob.b_value} = {prob.answer}"
            return op_tex(expr, scale=1.25).to_edge(DOWN)

        if prob.kind == "difference":
            big = max(prob.a_value, prob.b_value)
            small = min(prob.a_value, prob.b_value)
            expr = rf"{big} - {small} = {prob.answer}"
            return op_tex(expr, scale=1.25).to_edge(DOWN)

        if prob.kind == "missing_part":
            assert prob.total is not None
            known_units = prob.a_value if prob.a_value > 0 else (prob.total - prob.answer)
            expr = rf"{prob.total} - {known_units} = {prob.answer}"
            return op_tex(expr, scale=1.25).to_edge(DOWN)

        if prob.kind == "compare_add":
            assert prob.difference is not None
            expr = rf"{prob.a_value} + {prob.difference} = {prob.answer}"
            return op_tex(expr, scale=1.25).to_edge(DOWN)

        return VGroup()

    def verify_mapping(self, prob: ModelProblem, model_group: VGroup) -> VGroup:
        # simple verification label that “fills” the question mark with the answer
        ans = Text(str(prob.answer), font_size=self.s.font_size_title).scale(0.75)
        # find a question mark in the model_group (Text("?"))
        qm = None
        for m in model_group.submobjects:
            if isinstance(m, Text) and m.text == "?":
                qm = m
                break
        # sometimes nested
        if qm is None:
            for m in model_group.family_members_with_points():
                if isinstance(m, Text) and getattr(m, "text", "") == "?":
                    qm = m
                    break

        if qm is not None:
            ans.move_to(qm.get_center())
            self.play(Transform(qm, ans), run_time=self.s.rt_fast)
            return VGroup(Text("✓", font_size=self.s.font_size_title).scale(0.7).to_edge(DOWN))
        else:
            return VGroup(Text("✓", font_size=self.s.font_size_title).scale(0.7).to_edge(DOWN))

    # ============================================================
    # Steps
    # ============================================================

    def step_exploration_problems(self):
        for prob in self.cfg.problems:
            g = self.animate_problem(prob)
            self.wait(0.4)
            self.play(FadeOut(g), run_time=self.s.rt_fast)

    def step_collective_discussion_compare_models(self):
        prompt = T(
            self.cfg, self.s,
            "Discussion: Different models, same goal",
            "نقاش: نماذج مختلفة، نفس الهدف",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        box = RoundedRectangle(width=11.6, height=2.9, corner_radius=0.25).to_edge(DOWN).shift(UP * 0.2)
        box.set_stroke(width=3).set_fill(opacity=0.06)

        l1 = T(self.cfg, self.s, "• The model shows relationships.", "• النموذج يوضح العلاقات.", scale=0.52)
        l2 = T(self.cfg, self.s, "• It makes the unknown visible.", "• يجعل المجهول واضحاً.", scale=0.52)
        l3 = T(self.cfg, self.s, "• Then the operation becomes obvious.", "• ثم تصبح العملية واضحة.", scale=0.52)

        scaff = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(box.get_center())
        self.play(Create(box), FadeIn(scaff, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.5)
        self.play(FadeOut(VGroup(box, scaff)), run_time=self.s.rt_fast)

    def step_institutionalization_strategy(self):
        prompt = T(
            self.cfg, self.s,
            "Institutionalization: The modeling routine",
            "التثبيت: روتين النمذجة",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        routine = VGroup(
            Text("1) Read", font_size=self.s.font_size_main).scale(0.6),
            Text("2) Model", font_size=self.s.font_size_main).scale(0.6),
            Text("3) Reason", font_size=self.s.font_size_main).scale(0.6),
            Text("4) Calculate", font_size=self.s.font_size_main).scale(0.6),
            Text("5) Verify", font_size=self.s.font_size_main).scale(0.6),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(ORIGIN)

        self.play(FadeIn(routine, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(routine), run_time=self.s.rt_fast)

    def step_mini_assessment(self):
        prompt = T(
            self.cfg, self.s,
            "Mini-check: Use a model first, then compute.",
            "تحقق صغير: نمذج أولاً ثم احسب.",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        prob = ModelProblem(
            pid="P4",
            kind="difference",
            subject_a="Hiba",
            subject_b="Nabil",
            item="coins",
            a_value=13,
            b_value=8,
            question="Hiba has 13 coins and Nabil has 8 coins. How many more coins does Hiba have?",
            answer=5
        )
        g = self.animate_problem(prob)
        self.wait(0.4)
        self.play(FadeOut(g), run_time=self.s.rt_fast)

    def step_outro(self):
        recap = VGroup(
            T(self.cfg, self.s, "Recap:", "الخلاصة:", scale=0.6),
            T(self.cfg, self.s, "• Don’t jump to numbers.", "• لا تقفز مباشرة إلى الحساب.", scale=0.50),
            T(self.cfg, self.s, "• Build a model to show relationships.", "• ابنِ نموذجاً لإظهار العلاقات.", scale=0.50),
            T(self.cfg, self.s, "• The model tells you the operation.", "• النموذج يرشدك إلى العملية.", scale=0.50),
            T(self.cfg, self.s, "• Verify by returning to the model.", "• تحقّق بالرجوع إلى النموذج.", scale=0.50),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        recap.to_edge(RIGHT).shift(DOWN * 0.15)
        self.play(FadeIn(recap, shift=LEFT * 0.2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(recap, shift=RIGHT * 0.2), FadeOut(self.title), run_time=self.s.rt_fast)


# ============================================================
# RUN:
#   manim -pqh your_file.py M3_L18_ProblemSolvingWithModeling
#
# CUSTOMIZE:
#   cfg = LessonConfigM3_L18(
#       problems=[
#           ModelProblem(pid="X", kind="total", subject_a="Ali", subject_b="Mona", item="pens",
#                        a_value=9, b_value=7, question="Ali has 9 pens and Mona has 7 pens. How many pens in total?", answer=16)
#       ],
#       language="ar"
#   )
# ============================================================
