from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Literal, Dict

import numpy as np
from manim import *


# ============================================================
# STYLES / CONFIG
# ============================================================

@dataclass
class BarSegmentationStyle:
    stroke_width: float = 4.0
    fill_opacity: float = 0.10

    bar_height: float = 0.62
    bar_corner_radius: float = 0.18
    bar_width: float = 10.4

    ghost_opacity: float = 0.25
    chosen_opacity: float = 0.16

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
    show_options: bool = True
    show_operation_link: bool = True   # after segmentation is validated
    forbid_early_calculation: bool = True

    # layout
    left_anchor_x: float = -5.2
    bar_y: float = -0.10
    options_y: float = -1.25
    title_shift_y: float = -0.9


@dataclass
class SegmentationOption:
    """
    A segmentation option is a partition of the SAME whole bar.
    segments: list of segment "ratios" (sum = 1.0) OR explicit widths.
    labels: list of label strings per segment (same length as segments).
    highlight: index (segment to highlight as the unknown / target), or None.
    """
    oid: str
    segments: List[float]             # ratios that sum to 1.0
    labels: List[str]
    highlight_index: Optional[int] = None
    is_correct: bool = False
    operation_hint: Optional[str] = None  # shown only after correct option is chosen


@dataclass
class BarSegmentationProblem:
    """
    This is meta: we focus on segmentation quality.
    We show: bar -> propose options -> validate correct -> label segments -> highlight unknown -> link to operation.
    """
    pid: str
    question_text: str
    options: List[SegmentationOption]
    # which option is correct (by oid)
    correct_oid: str


@dataclass
class LessonConfigM3_L26:
    title_en: str = "Problem solving – representing parts on bar models"
    title_ar: str = "حل المسائل – تمثيل الأجزاء على نموذج الأشرطة"
    language: str = "en"

    prompt_show_bar_en: str = "Start from one whole bar."
    prompt_show_bar_ar: str = "ننطلق من شريط يمثل الكل."

    prompt_options_en: str = "Propose segmentation options (some are wrong)."
    prompt_options_ar: str = "نقترح تقسيمات مختلفة (بعضها غير صحيح)."

    prompt_validate_en: str = "Validate the segmentation that matches the situation."
    prompt_validate_ar: str = "نثبت التقسيم الذي يطابق الوضعية."

    prompt_label_en: str = "Label each segment (meaning matters)."
    prompt_label_ar: str = "نسمي كل جزء (المعنى هو الأهم)."

    prompt_target_en: str = "Highlight the segment that answers the question."
    prompt_target_ar: str = "نبرز الجزء الذي يجيب عن السؤال."

    prompt_link_en: str = "Only now, connect to the operation."
    prompt_link_ar: str = "بعدها فقط نربط بالعملية."

    problems: List[BarSegmentationProblem] = field(default_factory=lambda: [
        # 1) Comparison: "more than" => common part + extra part
        BarSegmentationProblem(
            pid="S1",
            question_text=(
                "Ali has 8 marbles. Sara has 3 more marbles than Ali.\n"
                "Represent this with a bar model. What part is the 'difference'?"
            ),
            options=[
                SegmentationOption(
                    oid="S1_O1",
                    segments=[0.5, 0.5],  # equal halves (wrong: doesn't encode "3 more")
                    labels=["Ali", "Sara"],
                    highlight_index=None,
                    is_correct=False
                ),
                SegmentationOption(
                    oid="S1_O2",
                    segments=[0.72, 0.28],  # random unequal split (wrong: no semantic structure)
                    labels=["Sara", "Ali"],
                    highlight_index=None,
                    is_correct=False
                ),
                SegmentationOption(
                    oid="S1_O3",
                    segments=[0.72, 0.28],  # common part + extra part (correct conceptually)
                    labels=["same as Ali", "extra (difference)"],
                    highlight_index=1,
                    is_correct=True,
                    operation_hint="difference → subtraction (or addition if asked for total)"
                ),
            ],
            correct_oid="S1_O3"
        ),
        # 2) Equal parts: whole from repeated equal parts (3 equal parts)
        BarSegmentationProblem(
            pid="S2",
            question_text=(
                "A ribbon is cut into 4 equal parts. One part is labeled '5 cm'.\n"
                "Segment the bar to represent the situation. Which segments are equal parts?"
            ),
            options=[
                SegmentationOption(
                    oid="S2_O1",
                    segments=[0.25, 0.25, 0.25, 0.25],
                    labels=["part", "part", "part", "part"],
                    highlight_index=None,
                    is_correct=True,
                    operation_hint="whole = repeated equal parts (repeated addition / multiplication idea)"
                ),
                SegmentationOption(
                    oid="S2_O2",
                    segments=[0.4, 0.2, 0.2, 0.2],
                    labels=["part", "part", "part", "part"],
                    highlight_index=None,
                    is_correct=False
                ),
                SegmentationOption(
                    oid="S2_O3",
                    segments=[0.5, 0.5],
                    labels=["2 parts", "2 parts"],
                    highlight_index=None,
                    is_correct=False
                ),
            ],
            correct_oid="S2_O1"
        ),
        # 3) Missing part: total known, one part known, one part unknown
        BarSegmentationProblem(
            pid="S3",
            question_text=(
                "A box has 20 candies. 12 are strawberry. The rest are lemon.\n"
                "Segment the bar so one segment is known and the other is the unknown remainder."
            ),
            options=[
                SegmentationOption(
                    oid="S3_O1",
                    segments=[0.6, 0.4],
                    labels=["12 strawberry", "? lemon"],
                    highlight_index=1,
                    is_correct=True,
                    operation_hint="remainder → subtraction (total - known part)"
                ),
                SegmentationOption(
                    oid="S3_O2",
                    segments=[0.5, 0.5],
                    labels=["strawberry", "lemon"],
                    highlight_index=None,
                    is_correct=False
                ),
                SegmentationOption(
                    oid="S3_O3",
                    segments=[0.2, 0.8],
                    labels=["? lemon", "12 strawberry"],
                    highlight_index=0,
                    is_correct=False  # wrong ordering/meaning if we want known part explicitly placed
                ),
            ],
            correct_oid="S3_O1"
        ),
    ])


# ============================================================
# HELPERS
# ============================================================

def T(cfg: LessonConfigM3_L26, s: BarSegmentationStyle, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
    txt = en if cfg.language == "en" else (ar or en)
    return Text(txt, font_size=s.font_size_main).scale(scale)


def problem_box(text: str, s: BarSegmentationStyle) -> VGroup:
    box = RoundedRectangle(width=11.6, height=2.1, corner_radius=0.25).set_stroke(width=3).set_fill(opacity=0.06)
    t = Paragraph(*text.split("\n"), alignment="left", font_size=s.font_size_problem).scale(0.95)
    t.move_to(box.get_center())
    return VGroup(box, t).to_edge(UP).shift(DOWN * 1.25)


def whole_bar(s: BarSegmentationStyle) -> RoundedRectangle:
    r = RoundedRectangle(width=s.bar_width, height=s.bar_height, corner_radius=s.bar_corner_radius)
    r.set_stroke(width=s.stroke_width).set_fill(opacity=s.fill_opacity)
    return r


def segmented_overlay(whole: RoundedRectangle, ratios: List[float], s: BarSegmentationStyle, opacity: float) -> VGroup:
    """
    Build segment rectangles aligned on top of 'whole', using ratios of whole width.
    """
    w = whole.width
    h = whole.height
    x_left = whole.get_left()[0]
    segs = VGroup()
    cursor = x_left
    for r in ratios:
        seg_w = max(0.35, w * r)
        seg = RoundedRectangle(width=seg_w, height=h, corner_radius=s.bar_corner_radius)
        seg.set_stroke(width=s.stroke_width).set_fill(opacity=opacity)
        seg.move_to(np.array([cursor + seg_w / 2, whole.get_center()[1], 0]))
        cursor += seg_w
        segs.add(seg)

    # separators (thin lines) between segments for readability
    seps = VGroup()
    cursor = x_left
    for r in ratios[:-1]:
        cursor += w * r
        line = Line(
            np.array([cursor, whole.get_bottom()[1], 0]),
            np.array([cursor, whole.get_top()[1], 0]),
            stroke_width=3
        )
        line.set_opacity(0.55)
        seps.add(line)

    return VGroup(segs, seps)


def labels_for_segments(segs: VGroup, labels: List[str], s: BarSegmentationStyle) -> VGroup:
    group = VGroup()
    for i, txt in enumerate(labels):
        if i >= len(segs):
            break
        t = Text(txt, font_size=s.font_size_small).scale(0.55)
        t.next_to(segs[i], UP, buff=0.12)
        group.add(t)
    return group


# ============================================================
# LESSON SCENE
# ============================================================

class M3_L26_RepresentPartsOnBarModels(Scene):
    """
    M3_L26 — Meta lesson on bar segmentation:
      bar → options (ghost) → validate correct → label segments → highlight unknown → link to operation
    """

    def __init__(
        self,
        cfg: LessonConfigM3_L26 = LessonConfigM3_L26(),
        style: BarSegmentationStyle = BarSegmentationStyle(),
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

    def banner(self, mob: Mobject) -> Mobject:
        mob.to_edge(UP)
        return mob

    def build_steps(self):
        self.steps = [
            ("intro", self.step_intro),
            ("exploration", self.step_exploration),
            ("collective_discussion", self.step_collective_discussion),
            ("institutionalization", self.step_institutionalization),
            ("mini_assessment", self.step_mini_assessment),
            ("outro", self.step_outro),
        ]

    # ============================================================
    # Steps
    # ============================================================

    def step_intro(self):
        title = T(self.cfg, self.s, self.cfg.title_en, self.cfg.title_ar, scale=0.58)
        title = self.banner(title)

        subtitle = T(
            self.cfg, self.s,
            "Good segmentation = correct reasoning.",
            "تقسيم صحيح = تفكير صحيح.",
            scale=0.52
        ).next_to(title, DOWN, buff=0.18)

        self.play(Write(title), FadeIn(subtitle, shift=DOWN * 0.15), run_time=self.s.rt_norm)
        self.wait(0.2)
        self.play(FadeOut(subtitle, shift=UP * 0.1), run_time=self.s.rt_fast)
        self.title = title

    def step_exploration(self):
        for p in self.cfg.problems:
            g = self.animate_segmentation_meta(p)
            self.wait(0.35)
            self.play(FadeOut(g), run_time=self.s.rt_fast)

    def step_collective_discussion(self):
        prompt = T(
            self.cfg, self.s,
            "Discussion: Which segmentation is faithful to the story?",
            "نقاش: أي تقسيم يطابق القصة فعلاً؟",
            scale=0.50
        )
        prompt = self.banner(prompt).shift(DOWN * self.s.title_shift_y)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        box = RoundedRectangle(width=11.6, height=2.9, corner_radius=0.25).to_edge(DOWN).shift(UP * 0.2)
        box.set_stroke(width=3).set_fill(opacity=0.06)

        l1 = T(self.cfg, self.s, "• Each segment must mean something.", "• كل جزء يجب أن يمثل معنى.", scale=0.50)
        l2 = T(self.cfg, self.s, "• Equal story parts → equal segments.", "• أجزاء متساوية في القصة → أجزاء متساوية في الشريط.", scale=0.44)
        l3 = T(self.cfg, self.s, "• A random split is not a model.", "• تقسيم عشوائي ليس نموذجاً.", scale=0.50)

        scaff = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(box.get_center())
        self.play(Create(box), FadeIn(scaff, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.55)
        self.play(FadeOut(VGroup(box, scaff)), run_time=self.s.rt_fast)

    def step_institutionalization(self):
        prompt = T(
            self.cfg, self.s,
            "Institutionalization: segment → label → target → operation",
            "التثبيت: نقسم → نسمي → نحدد الهدف → نختار العملية",
            scale=0.48
        )
        prompt = self.banner(prompt).shift(DOWN * self.s.title_shift_y)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        chain = VGroup(
            Text("segment", font_size=self.s.font_size_small).scale(0.75),
            Text("→", font_size=self.s.font_size_small).scale(0.75),
            Text("label", font_size=self.s.font_size_small).scale(0.75),
            Text("→", font_size=self.s.font_size_small).scale(0.75),
            Text("target (?)", font_size=self.s.font_size_small).scale(0.75),
            Text("→", font_size=self.s.font_size_small).scale(0.75),
            Text("operation", font_size=self.s.font_size_small).scale(0.75),
        ).arrange(RIGHT, buff=0.22).move_to(ORIGIN).shift(DOWN * 0.3)

        self.play(FadeIn(chain, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.45)
        self.play(FadeOut(chain), run_time=self.s.rt_fast)

    def step_mini_assessment(self):
        prompt = T(
            self.cfg, self.s,
            "Mini-check: choose the correct segmentation (equal parts or extra part).",
            "تحقق صغير: اختر التقسيم الصحيح (أجزاء متساوية أو جزء زائد).",
            scale=0.46
        )
        prompt = self.banner(prompt).shift(DOWN * self.s.title_shift_y)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        p = BarSegmentationProblem(
            pid="S4",
            question_text=(
                "A jar has 15 candies. 5 are eaten. The rest are left.\n"
                "Which segmentation matches this?"
            ),
            options=[
                SegmentationOption(oid="S4_O1", segments=[0.33, 0.67], labels=["5 eaten", "? left"], highlight_index=1, is_correct=True, operation_hint="left = total - eaten"),
                SegmentationOption(oid="S4_O2", segments=[0.5, 0.5], labels=["eaten", "left"], is_correct=False),
                SegmentationOption(oid="S4_O3", segments=[0.2, 0.8], labels=["? left", "5 eaten"], is_correct=False),
            ],
            correct_oid="S4_O1"
        )
        g = self.animate_segmentation_meta(p)
        self.wait(0.35)
        self.play(FadeOut(g), run_time=self.s.rt_fast)

    def step_outro(self):
        recap = VGroup(
            T(self.cfg, self.s, "Recap:", "الخلاصة:", scale=0.6),
            T(self.cfg, self.s, "• Segment with meaning", "• نقسم بمعنى", scale=0.52),
            T(self.cfg, self.s, "• Label what is known", "• نكتب المعلوم", scale=0.52),
            T(self.cfg, self.s, "• Highlight the asked part", "• نبرز المطلوب", scale=0.52),
            T(self.cfg, self.s, "• Then choose the operation", "• ثم نختار العملية", scale=0.52),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)

        recap.to_edge(RIGHT).shift(DOWN * 0.15)
        self.play(FadeIn(recap, shift=LEFT * 0.2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(recap, shift=RIGHT * 0.2), FadeOut(self.title), run_time=self.s.rt_fast)

    # ============================================================
    # Core meta-animation
    # ============================================================

    def animate_segmentation_meta(self, prob: BarSegmentationProblem) -> VGroup:
        pb = VGroup()
        if self.s.show_problem_text:
            pb = problem_box(prob.question_text, self.s)
            self.play(FadeIn(pb, shift=DOWN * 0.1), run_time=self.s.rt_norm)

        # Whole bar
        p0 = T(self.cfg, self.s, self.cfg.prompt_show_bar_en, self.cfg.prompt_show_bar_ar, scale=0.56)
        p0 = self.banner(p0).shift(DOWN * self.s.title_shift_y)
        self.play(Transform(self.title, p0), run_time=self.s.rt_fast)

        whole = whole_bar(self.s)
        whole.move_to(np.array([0, self.s.bar_y, 0]))
        whole.shift(np.array([self.s.left_anchor_x, 0, 0]) - whole.get_left())
        self.play(Create(whole), run_time=self.s.rt_norm)

        # Options (ghost overlays)
        p1 = T(self.cfg, self.s, self.cfg.prompt_options_en, self.cfg.prompt_options_ar, scale=0.54)
        p1 = self.banner(p1).shift(DOWN * self.s.title_shift_y)
        self.play(Transform(self.title, p1), run_time=self.s.rt_fast)

        option_groups: Dict[str, VGroup] = {}
        opts_row = VGroup()

        if self.s.show_options:
            for opt in prob.options:
                base = whole.copy().set_fill(opacity=0.02)
                overlay = segmented_overlay(base, opt.segments, self.s, opacity=self.s.ghost_opacity)
                # Use ONLY the segment rectangles for labels/highlights
                seg_rects = overlay[0]

                lab = Text(opt.oid.replace("_", " "), font_size=self.s.font_size_small).scale(0.5)
                lab.next_to(base, DOWN, buff=0.12)

                g = VGroup(base, overlay, lab)
                option_groups[opt.oid] = VGroup(base, seg_rects, overlay[1], lab)  # base + segs + seps + label
                opts_row.add(g)

            opts_row.arrange(RIGHT, buff=0.6).scale(0.62)
            opts_row.move_to(np.array([0, self.s.options_y, 0]))
            self.play(FadeIn(opts_row, shift=UP * 0.05), run_time=self.s.rt_norm)

        # Validate the correct segmentation
        p2 = T(self.cfg, self.s, self.cfg.prompt_validate_en, self.cfg.prompt_validate_ar, scale=0.54)
        p2 = self.banner(p2).shift(DOWN * self.s.title_shift_y)
        self.play(Transform(self.title, p2), run_time=self.s.rt_fast)

        # Choose correct option
        correct = next(o for o in prob.options if o.oid == prob.correct_oid)
        chosen_overlay = segmented_overlay(whole, correct.segments, self.s, opacity=self.s.chosen_opacity)
        chosen_segs = chosen_overlay[0]
        chosen_seps = chosen_overlay[1]

        # animate "reject" others quickly (fade)
        if len(opts_row):
            self.play(opts_row.animate.set_opacity(0.18), run_time=self.s.rt_fast)

        # bring chosen on top
        self.play(FadeIn(chosen_overlay, shift=UP * 0.05), run_time=self.s.rt_norm)

        check = Text("✓", font_size=self.s.font_size_main).scale(0.7).next_to(whole, RIGHT, buff=0.2)
        self.play(FadeIn(check, shift=UP * 0.05), run_time=self.s.rt_fast)

        # Label segments
        p3 = T(self.cfg, self.s, self.cfg.prompt_label_en, self.cfg.prompt_label_ar, scale=0.54)
        p3 = self.banner(p3).shift(DOWN * self.s.title_shift_y)
        self.play(Transform(self.title, p3), run_time=self.s.rt_fast)

        seg_labels = labels_for_segments(chosen_segs, correct.labels, self.s)
        self.play(FadeIn(seg_labels, shift=UP * 0.05), run_time=self.s.rt_norm)

        # Highlight target segment (unknown)
        p4 = T(self.cfg, self.s, self.cfg.prompt_target_en, self.cfg.prompt_target_ar, scale=0.54)
        p4 = self.banner(p4).shift(DOWN * self.s.title_shift_y)
        self.play(Transform(self.title, p4), run_time=self.s.rt_fast)

        hi = VGroup()
        if correct.highlight_index is not None and 0 <= correct.highlight_index < len(chosen_segs):
            rect = SurroundingRectangle(chosen_segs[correct.highlight_index], buff=0.12).set_stroke(width=6)
            q = Text("?", font_size=self.s.font_size_title).scale(0.9)
            q.move_to(chosen_segs[correct.highlight_index].get_center())
            hi = VGroup(rect, q)
            self.play(Create(rect), FadeIn(q, shift=UP * 0.05), run_time=self.s.rt_norm)

        # Link to operation (ONLY after segmentation)
        op = VGroup()
        if self.s.show_operation_link and correct.operation_hint:
            p5 = T(self.cfg, self.s, self.cfg.prompt_link_en, self.cfg.prompt_link_ar, scale=0.54)
            p5 = self.banner(p5).shift(DOWN * self.s.title_shift_y)
            self.play(Transform(self.title, p5), run_time=self.s.rt_fast)

            hint = Text(f"Operation hint: {correct.operation_hint}", font_size=self.s.font_size_small).scale(0.55)
            hint.to_edge(DOWN)
            self.play(FadeIn(hint, shift=UP * 0.05), run_time=self.s.rt_norm)
            op.add(hint)

            if self.s.forbid_early_calculation:
                stop = Text("No calculation yet", font_size=self.s.font_size_small).scale(0.55)
                stop.set_opacity(0.35).next_to(hint, UP, buff=0.12)
                self.play(FadeIn(stop), run_time=self.s.rt_fast)
                op.add(stop)

        return VGroup(pb, whole, chosen_overlay, check, seg_labels, hi, op, opts_row)


# ============================================================
# RUN:
#   manim -pqh your_file.py M3_L26_RepresentPartsOnBarModels
#
# EXTEND:
#   - Add new BarSegmentationProblem with 2–4 SegmentationOption items.
#   - Correct option should encode meaning (equal parts / extra / missing).
# ============================================================
