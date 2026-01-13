from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Literal

import numpy as np
from manim import *


# ============================================================
# CONFIG / STYLES
# ============================================================

@dataclass
class DivPSStyle:
    stroke_width: float = 4.0
    fill_opacity: float = 0.14

    # objects & groups
    dot_radius: float = 0.09
    dot_spacing: float = 0.18
    group_box_w: float = 2.2
    group_box_h: float = 1.2
    group_corner_radius: float = 0.18
    group_cols: int = 3  # layout columns for group boxes

    # bars (optional alternative model)
    unit_width: float = 0.45
    bar_height: float = 0.55
    bar_corner_radius: float = 0.16

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
    show_model_switch: bool = True           # show both sharing and grouping styles
    show_symbolic_link: bool = True          # show ÷ expression after the model
    show_context_answer: bool = True         # “... per group” / “... groups”
    show_verify: bool = True

    # layout
    left_anchor_x: float = -5.2
    top_y: float = 0.85
    bottom_y: float = -0.85


@dataclass
class DivisionProblemPS:
    """
    Two main division-problem flavors:
      - "sharing": total and n_groups known -> unknown is per_group (quotient)
      - "grouping": total and group_size known -> unknown is n_groups (quotient)

    Example:
      sharing: 12 apples shared among 3 kids -> 12 ÷ 3 = 4 apples per kid
      grouping: 12 apples, 3 per bag -> 12 ÷ 3 = 4 bags
    """
    pid: str
    kind: Literal["sharing", "grouping"]

    total: int
    n_groups: Optional[int] = None
    group_size: Optional[int] = None

    subject_groups: str = "kids"    # groups name for context
    item: str = "apples"

    question: str = ""
    answer: Optional[int] = None  # computed if None


@dataclass
class LessonConfigM3_L20:
    title_en: str = "Solving division problems"
    title_ar: str = "حل مسائل قسمة"
    language: str = "en"  # keep class bilingual-ready; Arabic text optional

    prompt_total_en: str = "Start: identify the TOTAL."
    prompt_total_ar: str = "البداية: نحدد المجموع."

    prompt_groups_en: str = "Build the model: groups or group size."
    prompt_groups_ar: str = "نبني النموذج: مجموعات أو حجم المجموعة."

    prompt_distribute_en: str = "Use the model to find the quotient."
    prompt_distribute_ar: str = "نستعمل النموذج لإيجاد خارج القسمة."

    prompt_link_en: str = "Now link it to the division expression."
    prompt_link_ar: str = "نربط الآن بالعملية (القسمة)."

    prompt_answer_en: str = "State the answer in words."
    prompt_answer_ar: str = "نكتب الجواب بالكلمات."

    problems: List[DivisionProblemPS] = field(default_factory=lambda: [
        DivisionProblemPS(
            pid="D1",
            kind="sharing",
            total=12,
            n_groups=3,
            subject_groups="kids",
            item="apples",
            question="12 apples are shared equally among 3 kids. How many apples does each kid get?"
        ),
        DivisionProblemPS(
            pid="D2",
            kind="grouping",
            total=15,
            group_size=5,
            subject_groups="bags",
            item="marbles",
            question="15 marbles are packed with 5 marbles per bag. How many bags are needed?"
        ),
    ])


# ============================================================
# REUSABLE PRIMITIVES
# ============================================================

def T(cfg: LessonConfigM3_L20, s: DivPSStyle, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
    txt = en if cfg.language == "en" else (ar or en)
    return Text(txt, font_size=s.font_size_main).scale(scale)


def problem_box(text: str, s: DivPSStyle) -> VGroup:
    box = RoundedRectangle(width=11.6, height=2.1, corner_radius=0.25).set_stroke(width=3).set_fill(opacity=0.06)
    t = Paragraph(*text.split("\n"), alignment="left", font_size=s.font_size_problem).scale(0.95)
    t.move_to(box.get_center())
    return VGroup(box, t).to_edge(UP).shift(DOWN * 1.25)


def make_items(total: int, s: DivPSStyle) -> VGroup:
    dots = VGroup(*[Dot(radius=s.dot_radius) for _ in range(total)])
    dots.arrange_in_grid(rows=int(np.ceil(total / 10)), cols=min(10, total), buff=s.dot_spacing)
    return dots


class GroupBox(VGroup):
    def __init__(self, label: str, s: DivPSStyle, **kwargs):
        super().__init__(**kwargs)
        rect = RoundedRectangle(width=s.group_box_w, height=s.group_box_h, corner_radius=s.group_corner_radius)
        rect.set_stroke(width=s.stroke_width).set_fill(opacity=s.fill_opacity)
        txt = Text(label, font_size=s.font_size_small).scale(0.65).next_to(rect, UP, buff=0.08)
        self.rect = rect
        self.txt = txt
        self.add(rect, txt)

    def inside_anchor(self) -> np.ndarray:
        # where to place items inside
        return self.rect.get_center() + DOWN * 0.08


def op_div_tex(total: int, divisor: int, quotient: int, scale: float = 1.25) -> Mobject:
    return MathTex(rf"{total} \div {divisor} = {quotient}").scale(scale)


# ============================================================
# LESSON SCENE
# ============================================================

class M3_L20_SolvingDivisionProblems(Scene):
    """
    M3_L20 — Division problem solving

    Visual flow:
      display_total_quantity
      create_empty_groups OR highlight group_size
      distribute_or_group_objects visually
      count_result (per group OR number of groups)
      reveal division expression matching the model
      highlight answer in context

    Covers both meanings:
      - sharing (unknown per group)
      - grouping (unknown number of groups)
    """

    def __init__(
        self,
        cfg: LessonConfigM3_L20 = LessonConfigM3_L20(),
        style: DivPSStyle = DivPSStyle(),
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
            "Division in problems: sharing OR grouping",
            "القسمة في المسائل: توزيع أو تجميع",
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
            "Discussion: What does the quotient mean?",
            "نقاش: ماذا يعني خارج القسمة؟",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        box = RoundedRectangle(width=11.6, height=2.9, corner_radius=0.25).to_edge(DOWN).shift(UP * 0.2)
        box.set_stroke(width=3).set_fill(opacity=0.06)

        l1 = T(self.cfg, self.s, "• In sharing: quotient = in each group.", "• في التوزيع: خارج القسمة = في كل مجموعة.", scale=0.52)
        l2 = T(self.cfg, self.s, "• In grouping: quotient = number of groups.", "• في التجميع: خارج القسمة = عدد المجموعات.", scale=0.52)
        l3 = T(self.cfg, self.s, "• The model tells you which one.", "• النموذج يبين المعنى.", scale=0.52)

        scaff = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(box.get_center())
        self.play(Create(box), FadeIn(scaff, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.5)
        self.play(FadeOut(VGroup(box, scaff)), run_time=self.s.rt_fast)

    def step_institutionalization(self):
        prompt = T(
            self.cfg, self.s,
            "Institutionalization: Model → Division",
            "التثبيت: نموذج → قسمة",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        r1 = MathTex(r"\text{Sharing: } \frac{\text{total}}{\text{number of groups}} = \text{each group}").scale(0.95)
        r2 = MathTex(r"\text{Grouping: } \frac{\text{total}}{\text{group size}} = \text{number of groups}").scale(0.95).next_to(r1, DOWN, buff=0.25)

        self.play(Write(r1), run_time=self.s.rt_norm)
        self.play(Write(r2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(VGroup(r1, r2)), run_time=self.s.rt_fast)

    def step_mini_assessment(self):
        prompt = T(
            self.cfg, self.s,
            "Mini-check: 20 cookies shared among 4 kids. How many each?",
            "تحقق صغير: 20 قطعة حلوى توزع على 4 أطفال. كم لكل واحد؟",
            scale=0.50
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        p = DivisionProblemPS(
            pid="D3",
            kind="sharing",
            total=20,
            n_groups=4,
            subject_groups="kids",
            item="cookies",
            question="20 cookies are shared equally among 4 kids. How many cookies does each kid get?"
        )
        g = self.animate_problem(p)
        self.wait(0.35)
        self.play(FadeOut(g), run_time=self.s.rt_fast)

    def step_outro(self):
        recap = VGroup(
            T(self.cfg, self.s, "Recap:", "الخلاصة:", scale=0.6),
            T(self.cfg, self.s, "• Identify total and what is fixed (groups or size)", "• نحدد المجموع وما هو ثابت (المجموعات أو الحجم)", scale=0.50),
            T(self.cfg, self.s, "• Build a model to see the quotient meaning", "• نبني نموذجاً لفهم معنى الخارج", scale=0.50),
            T(self.cfg, self.s, "• Then write the division expression", "• ثم نكتب عملية القسمة", scale=0.50),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        recap.to_edge(RIGHT).shift(DOWN * 0.15)
        self.play(FadeIn(recap, shift=LEFT * 0.2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(recap, shift=RIGHT * 0.2), FadeOut(self.title), run_time=self.s.rt_fast)

    # ============================================================
    # Core animation for one division problem
    # ============================================================

    def animate_problem(self, prob: DivisionProblemPS) -> VGroup:
        # compute answer if missing
        if prob.kind == "sharing":
            assert prob.n_groups is not None, "sharing needs n_groups"
            ans = prob.answer if prob.answer is not None else (prob.total // prob.n_groups)
            divisor = prob.n_groups
        else:
            assert prob.group_size is not None, "grouping needs group_size"
            ans = prob.answer if prob.answer is not None else (prob.total // prob.group_size)
            divisor = prob.group_size

        pb = VGroup()
        if self.s.show_problem_text:
            pb = problem_box(prob.question, self.s)
            self.play(FadeIn(pb, shift=DOWN * 0.1), run_time=self.s.rt_norm)

        # Step: identify total
        p1 = T(self.cfg, self.s, self.cfg.prompt_total_en, self.cfg.prompt_total_ar, scale=0.56)
        p1 = self.banner(p1).shift(DOWN * 0.9)
        self.play(Transform(self.title, p1), run_time=self.s.rt_fast)

        items = make_items(prob.total, self.s).to_edge(LEFT).shift(RIGHT * 1.2 + UP * 0.3)
        total_lab = Text(f"Total = {prob.total} {prob.item}", font_size=self.s.font_size_small).scale(0.7)
        total_lab.next_to(items, UP, buff=0.25)
        self.play(FadeIn(items, shift=UP * 0.1), FadeIn(total_lab, shift=UP * 0.05), run_time=self.s.rt_norm)

        # Step: build model (groups or group size)
        p2 = T(self.cfg, self.s, self.cfg.prompt_groups_en, self.cfg.prompt_groups_ar, scale=0.56)
        p2 = self.banner(p2).shift(DOWN * 0.9)
        self.play(Transform(self.title, p2), run_time=self.s.rt_fast)

        model_group = VGroup()

        if prob.kind == "sharing":
            model_group = self.animate_sharing_model(prob, items, ans)
        else:
            model_group = self.animate_grouping_model(prob, items, ans)

        # Step: link to division expression
        op_group = VGroup()
        if self.s.show_symbolic_link:
            p3 = T(self.cfg, self.s, self.cfg.prompt_link_en, self.cfg.prompt_link_ar, scale=0.56)
            p3 = self.banner(p3).shift(DOWN * 0.9)
            self.play(Transform(self.title, p3), run_time=self.s.rt_fast)

            op = op_div_tex(prob.total, divisor, ans, scale=1.25).to_edge(DOWN)
            self.play(Write(op), run_time=self.s.rt_norm)
            op_group.add(op)

        # Step: answer in context
        ctx = VGroup()
        if self.s.show_context_answer:
            p4 = T(self.cfg, self.s, self.cfg.prompt_answer_en, self.cfg.prompt_answer_ar, scale=0.56)
            p4 = self.banner(p4).shift(DOWN * 0.9)
            self.play(Transform(self.title, p4), run_time=self.s.rt_fast)

            if prob.kind == "sharing":
                ctx_txt = Text(f"Answer: {ans} {prob.item} per {prob.subject_groups[:-1] if prob.subject_groups.endswith('s') else prob.subject_groups}",
                               font_size=self.s.font_size_small).scale(0.7)
            else:
                ctx_txt = Text(f"Answer: {ans} {prob.subject_groups}", font_size=self.s.font_size_small).scale(0.7)

            ctx_txt.next_to(op_group if len(op_group) else items, DOWN, buff=0.25)
            if len(op_group):
                ctx_txt.next_to(op_group[0], UP, buff=0.2)
            ctx.add(ctx_txt)
            self.play(FadeIn(ctx_txt, shift=UP * 0.05), run_time=self.s.rt_fast)

        # verify
        verify = VGroup()
        if self.s.show_verify and len(op_group):
            check = Text("✓", font_size=self.s.font_size_main).scale(0.7).next_to(op_group[0], LEFT, buff=0.25)
            verify.add(check)
            self.play(FadeIn(check, shift=UP * 0.05), run_time=self.s.rt_fast)

        return VGroup(pb, items, total_lab, model_group, op_group, ctx, verify)

    # ------------------------------------------------------------
    # Sharing model: create empty groups; distribute objects round-robin
    # ------------------------------------------------------------

    def animate_sharing_model(self, prob: DivisionProblemPS, items: VGroup, ans: int) -> VGroup:
        n_groups = prob.n_groups
        assert n_groups is not None

        groups = VGroup()
        for i in range(n_groups):
            gb = GroupBox(f"{prob.subject_groups[:-1] if prob.subject_groups.endswith('s') else prob.subject_groups} {i+1}", self.s)
            groups.add(gb)

        groups.arrange_in_grid(rows=int(np.ceil(n_groups / self.s.group_cols)), cols=min(self.s.group_cols, n_groups), buff=0.55)
        groups.to_edge(RIGHT).shift(LEFT * 0.8 + UP * 0.1)

        self.play(FadeIn(groups, shift=UP * 0.1), run_time=self.s.rt_norm)

        # distribute dots one by one
        dots = list(items.submobjects)
        placed = [[] for _ in range(n_groups)]
        for k, d in enumerate(dots):
            gi = k % n_groups
            placed[gi].append(d)

            # move dot into group box
            target = groups[gi].inside_anchor()
            # layout inside: small grid
            r = len(placed[gi]) - 1
            col = r % 6
            row = r // 6
            offset = np.array([(col - 2.5) * 0.22, 0.25 - row * 0.22, 0])
            self.play(d.animate.move_to(target + offset), run_time=0.12)

        # counting result per group
        count_labels = VGroup()
        for i, gb in enumerate(groups):
            lab = Text(str(len(placed[i])), font_size=self.s.font_size_small).scale(0.8)
            lab.move_to(gb.rect.get_center() + DOWN * 0.42)
            count_labels.add(lab)

        p = T(self.cfg, self.s, self.cfg.prompt_distribute_en, self.cfg.prompt_distribute_ar, scale=0.56)
        p = self.banner(p).shift(DOWN * 0.9)
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        self.play(FadeIn(count_labels, shift=UP * 0.05), run_time=self.s.rt_norm)
        hi = SurroundingRectangle(count_labels, buff=0.15).set_stroke(width=4)
        self.play(Create(hi), run_time=self.s.rt_fast)
        self.wait(0.25)
        self.play(FadeOut(hi), run_time=self.s.rt_fast)

        return VGroup(groups, count_labels)

    # ------------------------------------------------------------
    # Grouping model: highlight group size; build groups until items are exhausted
    # ------------------------------------------------------------

    def animate_grouping_model(self, prob: DivisionProblemPS, items: VGroup, ans: int) -> VGroup:
        group_size = prob.group_size
        assert group_size is not None

        # We'll create groups incrementally; each group collects group_size dots.
        groups = VGroup()
        groups.to_edge(RIGHT).shift(LEFT * 0.8 + UP * 0.1)

        dots = list(items.submobjects)

        p = T(self.cfg, self.s, self.cfg.prompt_distribute_en, self.cfg.prompt_distribute_ar, scale=0.56)
        p = self.banner(p).shift(DOWN * 0.9)

        # show "group size" hint
        gs = Text(f"Group size = {group_size}", font_size=self.s.font_size_small).scale(0.75).to_edge(RIGHT).shift(LEFT * 1.0 + UP * 2.0)
        self.play(FadeIn(gs, shift=UP * 0.05), run_time=self.s.rt_fast)

        for g in range(ans):
            gb = GroupBox(f"{prob.subject_groups[:-1] if prob.subject_groups.endswith('s') else prob.subject_groups} {g+1}", self.s)
            groups.add(gb)

            # re-layout each time
            groups.arrange_in_grid(rows=int(np.ceil(len(groups) / self.s.group_cols)), cols=min(self.s.group_cols, len(groups)), buff=0.55)
            groups.to_edge(RIGHT).shift(LEFT * 0.8 + UP * 0.1)

            if len(groups) == 1:
                self.play(FadeIn(gb, shift=UP * 0.1), run_time=self.s.rt_fast)
            else:
                self.play(Transform(groups, groups), run_time=0.2)  # keep stable

            # fill this group with group_size dots
            start = g * group_size
            end = start + group_size
            for i, d in enumerate(dots[start:end]):
                target = gb.inside_anchor()
                col = i % 6
                row = i // 6
                offset = np.array([(col - 2.5) * 0.22, 0.25 - row * 0.22, 0])
                self.play(d.animate.move_to(target + offset), run_time=0.12)

        # reveal number of groups
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        lab = Text(f"Number of groups = {ans}", font_size=self.s.font_size_small).scale(0.8).to_edge(DOWN).shift(UP * 0.6)
        self.play(FadeIn(lab, shift=UP * 0.05), run_time=self.s.rt_norm)

        return VGroup(gs, groups, lab)


# ============================================================
# RUN:
#   manim -pqh your_file.py M3_L20_SolvingDivisionProblems
#
# CUSTOMIZE:
#   cfg = LessonConfigM3_L20(
#       problems=[DivisionProblemPS(pid="X", kind="sharing", total=24, n_groups=6, subject_groups="teams", item="balls",
#                                   question="24 balls are shared among 6 teams...")],
#       language="en"
#   )
# ============================================================
