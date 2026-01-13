from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Literal

import numpy as np
from manim import *


# ============================================================
# CONFIG / STYLES
# ============================================================

@dataclass
class BarModelMetaStyle:
    stroke_width: float = 4.0
    fill_opacity: float = 0.10

    bar_height: float = 0.62
    bar_corner_radius: float = 0.18
    segment_gap: float = 0.02

    # "mental scene" (icons) sizes
    icon_size: float = 0.55
    thought_scale: float = 0.9

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
    show_thought_bubble: bool = True
    freeze_before_calculation: bool = True
    show_symbolic_calculation: bool = False  # must remain False for this lesson

    # layout
    left_anchor_x: float = -5.2
    bar_y: float = -0.25
    thought_y: float = 1.05


@dataclass
class BarModelMetaProblem:
    """
    This lesson is meta: we animate the process of:
      imagine → draw bars → label known → place ? → STOP (no calculation).

    We keep it generic by storing:
      - entities (for the imagined scene)
      - bar plan (segments + labels + unknown placement)
    """

    pid: str
    question_text: str

    # imagined scene: icons with captions
    scene_items: List[Tuple[str, str]]  # [(kind, caption), ...], kind in {"bag","person","box","coin","apple",...}

    # bar structure
    # segments are named logical parts (not numbers): e.g. ["A", "B", "UNKNOWN"]
    segments: List[str]

    # labels for some segments (strings only; can be numbers later, but here we treat them as "known labels")
    known_labels: List[Tuple[int, str]]  # [(segment_index, label_text), ...]

    # unknown segment index (where to place "?")
    unknown_index: int


@dataclass
class LessonConfigM3_L25:
    title_en: str = "Problem solving – imagining and writing a bar model"
    title_ar: str = "حل المسائل – تخيل وكتابة شريط مسألة"
    language: str = "en"

    prompt_imagine_en: str = "Step 1: Imagine the situation (no drawing yet)."
    prompt_imagine_ar: str = "الخطوة 1: نتخيل الوضعية (بدون رسم)."

    prompt_bars_en: str = "Step 2: Replace the scene with bars."
    prompt_bars_ar: str = "الخطوة 2: نحول المشهد إلى أشرطة."

    prompt_labels_en: str = "Step 3: Label what we know."
    prompt_labels_ar: str = "الخطوة 3: نكتب ما نعرفه."

    prompt_unknown_en: str = "Step 4: Place the unknown (?) correctly."
    prompt_unknown_ar: str = "الخطوة 4: نضع المجهول (?) في مكانه."

    prompt_stop_en: str = "Stop here: the model is ready (no calculation yet)."
    prompt_stop_ar: str = "نتوقف هنا: النموذج جاهز (بدون حساب بعد)."

    problems: List[BarModelMetaProblem] = field(default_factory=lambda: [
        BarModelMetaProblem(
            pid="BM1",
            question_text="Mariam has 12 stickers. She gives some to her friend and has 7 left. How many did she give?",
            scene_items=[("person", "Mariam"), ("box", "stickers"), ("person", "friend")],
            segments=["GIVEN", "LEFT"],
            known_labels=[(1, "7 left"), (0, " ? given")],  # still label-like; we will place "?" separately
            unknown_index=0
        ),
        BarModelMetaProblem(
            pid="BM2",
            question_text="A rope is cut into 3 equal parts. One part is 4 m. What is the whole length?",
            scene_items=[("rope", "rope"), ("scissors", "cut"), ("box", "3 equal parts")],
            segments=["PART", "PART", "PART"],  # show repetition
            known_labels=[(0, "4 m")],  # label ONE part
            unknown_index=2  # we'll place ? on whole bracket instead (handled specially below)
        ),
    ])


# ============================================================
# PRIMITIVES
# ============================================================

def T(cfg: LessonConfigM3_L25, s: BarModelMetaStyle, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
    txt = en if cfg.language == "en" else (ar or en)
    return Text(txt, font_size=s.font_size_main).scale(scale)


def problem_box(text: str, s: BarModelMetaStyle) -> VGroup:
    box = RoundedRectangle(width=11.6, height=2.1, corner_radius=0.25).set_stroke(width=3).set_fill(opacity=0.06)
    t = Paragraph(*text.split("\n"), alignment="left", font_size=s.font_size_problem).scale(0.95)
    t.move_to(box.get_center())
    return VGroup(box, t).to_edge(UP).shift(DOWN * 1.25)


def icon(kind: str, s: BarModelMetaStyle) -> Mobject:
    """
    Simple icon library with pure Manim shapes (no external SVG).
    Keep it minimal: silhouettes, boxes, etc.
    """
    if kind == "person":
        head = Circle(radius=0.18).set_stroke(width=3).set_fill(opacity=0.10)
        body = RoundedRectangle(width=0.45, height=0.55, corner_radius=0.18).set_stroke(width=3).set_fill(opacity=0.10)
        body.next_to(head, DOWN, buff=0.05)
        return VGroup(head, body).scale(s.icon_size / 0.55)

    if kind == "box":
        r = RoundedRectangle(width=0.7, height=0.5, corner_radius=0.15).set_stroke(width=3).set_fill(opacity=0.10)
        return r.scale(s.icon_size / 0.55)

    if kind == "bag":
        bag = RoundedRectangle(width=0.55, height=0.6, corner_radius=0.2).set_stroke(width=3).set_fill(opacity=0.10)
        knot = Triangle().scale(0.13).set_stroke(width=3).set_fill(opacity=0.10).next_to(bag, UP, buff=-0.04)
        return VGroup(bag, knot).scale(s.icon_size / 0.55)

    if kind == "coin":
        c = Circle(radius=0.24).set_stroke(width=3).set_fill(opacity=0.10)
        inner = Circle(radius=0.14).set_stroke(width=2).set_fill(opacity=0.0)
        return VGroup(c, inner).scale(s.icon_size / 0.55)

    if kind == "apple":
        a = Circle(radius=0.23).set_stroke(width=3).set_fill(opacity=0.10)
        leaf = Ellipse(width=0.20, height=0.12).set_stroke(width=3).set_fill(opacity=0.10).next_to(a, UP, buff=-0.05).shift(RIGHT*0.12)
        return VGroup(a, leaf).scale(s.icon_size / 0.55)

    if kind == "rope":
        line = Line(LEFT * 0.45, RIGHT * 0.45, stroke_width=10)
        return line.scale(s.icon_size / 0.55)

    if kind == "scissors":
        blade1 = Line(ORIGIN, RIGHT * 0.45, stroke_width=6).rotate(25 * DEGREES)
        blade2 = Line(ORIGIN, RIGHT * 0.45, stroke_width=6).rotate(-25 * DEGREES)
        ring1 = Circle(radius=0.12).set_stroke(width=4).shift(LEFT * 0.12 + UP * 0.12)
        ring2 = Circle(radius=0.12).set_stroke(width=4).shift(LEFT * 0.12 + DOWN * 0.12)
        return VGroup(blade1, blade2, ring1, ring2).scale(s.icon_size / 0.55)

    # default: generic dot
    return Dot(radius=0.08).scale(s.icon_size / 0.55)


def thought_bubble(content: VGroup, s: BarModelMetaStyle) -> VGroup:
    cloud = RoundedRectangle(width=11.2, height=2.0, corner_radius=0.6).set_stroke(width=3).set_fill(opacity=0.06)
    tail1 = Circle(radius=0.09).set_fill(opacity=0.06).set_stroke(width=0).shift(DOWN * 0.85 + LEFT * 3.8)
    tail2 = Circle(radius=0.06).set_fill(opacity=0.06).set_stroke(width=0).shift(DOWN * 1.05 + LEFT * 4.1)
    g = VGroup(cloud, tail1, tail2)
    content.move_to(cloud.get_center())
    return VGroup(g, content).scale(s.thought_scale).move_to(np.array([0, s.thought_y, 0]))


def bar_strip(n_segments: int, s: BarModelMetaStyle) -> VGroup:
    """
    Build an empty bar template with equal segments (no numbers).
    """
    total_w = 10.2
    seg_w = (total_w - (n_segments - 1) * s.segment_gap) / n_segments
    segs = VGroup()
    for i in range(n_segments):
        r = RoundedRectangle(width=seg_w, height=s.bar_height, corner_radius=s.bar_corner_radius)
        r.set_stroke(width=s.stroke_width).set_fill(opacity=s.fill_opacity)
        segs.add(r)
    segs.arrange(RIGHT, buff=s.segment_gap)
    return segs


def label_above(mob: Mobject, txt: str, s: BarModelMetaStyle) -> Mobject:
    t = Text(txt, font_size=s.font_size_small).scale(0.65)
    t.next_to(mob, UP, buff=0.12)
    return t


# ============================================================
# LESSON SCENE
# ============================================================

class M3_L25_ImagineAndWriteBarModel(Scene):
    """
    M3_L25 — Meta-problem lesson:
      imagine → bar emergence → progressive labeling → '?' placeholder → STOP (no calculation)

    IMPORTANT:
      We explicitly DO NOT calculate.
    """

    def __init__(
        self,
        cfg: LessonConfigM3_L25 = LessonConfigM3_L25(),
        style: BarModelMetaStyle = BarModelMetaStyle(),
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
            "Imagine first. Draw bars second. Stop before calculation.",
            "نتخيل أولاً. نرسم الأشرطة ثانياً. نتوقف قبل الحساب.",
            scale=0.46
        ).next_to(title, DOWN, buff=0.18)

        self.play(Write(title), FadeIn(subtitle, shift=DOWN * 0.15), run_time=self.s.rt_norm)
        self.wait(0.2)
        self.play(FadeOut(subtitle, shift=UP * 0.1), run_time=self.s.rt_fast)
        self.title = title

    def step_exploration(self):
        for p in self.cfg.problems:
            g = self.animate_meta_model(p)
            self.wait(0.35)
            self.play(FadeOut(g), run_time=self.s.rt_fast)

    def step_collective_discussion(self):
        prompt = T(
            self.cfg, self.s,
            "Discussion: What must appear in a correct bar model?",
            "نقاش: ماذا يجب أن يظهر في شريط مسألة صحيح؟",
            scale=0.48
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        box = RoundedRectangle(width=11.6, height=2.9, corner_radius=0.25).to_edge(DOWN).shift(UP * 0.2)
        box.set_stroke(width=3).set_fill(opacity=0.06)

        l1 = T(self.cfg, self.s, "• Bars represent quantities (not pictures).", "• الشريط يمثل كميات (ليس رسماً زخرفياً).", scale=0.50)
        l2 = T(self.cfg, self.s, "• Labels show what is known.", "• نضع تسميات لما هو معلوم.", scale=0.50)
        l3 = T(self.cfg, self.s, "• A clear '?' shows what is asked.", "• نضع علامة '?' لما نبحث عنه.", scale=0.50)

        scaff = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(box.get_center())
        self.play(Create(box), FadeIn(scaff, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.5)
        self.play(FadeOut(VGroup(box, scaff)), run_time=self.s.rt_fast)

    def step_institutionalization(self):
        prompt = T(
            self.cfg, self.s,
            "Institutionalization: Imagine → Bars → Labels → ? → STOP",
            "التثبيت: تخيل → أشرطة → تسميات → ? → توقف",
            scale=0.46
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        chain = VGroup(
            Text("Imagine", font_size=self.s.font_size_small).scale(0.75),
            Text("→", font_size=self.s.font_size_small).scale(0.75),
            Text("Bars", font_size=self.s.font_size_small).scale(0.75),
            Text("→", font_size=self.s.font_size_small).scale(0.75),
            Text("Labels", font_size=self.s.font_size_small).scale(0.75),
            Text("→", font_size=self.s.font_size_small).scale(0.75),
            Text("?", font_size=self.s.font_size_small).scale(0.95),
            Text("→", font_size=self.s.font_size_small).scale(0.75),
            Text("STOP", font_size=self.s.font_size_small).scale(0.75),
        ).arrange(RIGHT, buff=0.2).move_to(ORIGIN).shift(DOWN * 0.3)

        self.play(FadeIn(chain, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.5)
        self.play(FadeOut(chain), run_time=self.s.rt_fast)

    def step_mini_assessment(self):
        prompt = T(
            self.cfg, self.s,
            "Mini-check: Can you place '?' correctly before calculating?",
            "تحقق صغير: هل يمكنك وضع '?' في مكانه قبل الحساب؟",
            scale=0.50
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        p = BarModelMetaProblem(
            pid="BM3",
            question_text="There are 9 birds on a tree. Some fly away, and 5 remain. How many flew away?",
            scene_items=[("box", "tree"), ("bird", "birds"), ("scissors", "fly away")],
            segments=["FLEW_AWAY", "REMAIN"],
            known_labels=[(1, "5 remain")],
            unknown_index=0
        )
        # "bird" isn't in icon(); it will fall back to a dot icon -> ok.
        g = self.animate_meta_model(p)
        self.wait(0.35)
        self.play(FadeOut(g), run_time=self.s.rt_fast)

    def step_outro(self):
        recap = VGroup(
            T(self.cfg, self.s, "Recap:", "الخلاصة:", scale=0.6),
            T(self.cfg, self.s, "• First: imagine the story", "• أولاً: نتخيل القصة", scale=0.50),
            T(self.cfg, self.s, "• Then: bars show relationships", "• ثم: الأشرطة تُظهر العلاقات", scale=0.50),
            T(self.cfg, self.s, "• Finally: labels + '?' (still no calculation)", "• أخيراً: تسميات + '?' (بدون حساب)", scale=0.46),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        recap.to_edge(RIGHT).shift(DOWN * 0.15)
        self.play(FadeIn(recap, shift=LEFT * 0.2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(recap, shift=RIGHT * 0.2), FadeOut(self.title), run_time=self.s.rt_fast)

    # ============================================================
    # Core meta-animation
    # ============================================================

    def animate_meta_model(self, prob: BarModelMetaProblem) -> VGroup:
        pb = VGroup()
        if self.s.show_problem_text:
            pb = problem_box(prob.question_text, self.s)
            self.play(FadeIn(pb, shift=DOWN * 0.1), run_time=self.s.rt_norm)

        # Step 1: Imagine
        p1 = T(self.cfg, self.s, self.cfg.prompt_imagine_en, self.cfg.prompt_imagine_ar, scale=0.52)
        p1 = self.banner(p1).shift(DOWN * 0.9)
        self.play(Transform(self.title, p1), run_time=self.s.rt_fast)

        # Build imagined scene (icons + captions)
        icons = VGroup()
        for kind, caption in prob.scene_items:
            ic = icon(kind, self.s)
            cap = Text(caption, font_size=self.s.font_size_small).scale(0.55).next_to(ic, DOWN, buff=0.12)
            icons.add(VGroup(ic, cap))
        icons.arrange(RIGHT, buff=0.8)

        thought = VGroup()
        if self.s.show_thought_bubble:
            thought = thought_bubble(icons, self.s)
            self.play(FadeIn(thought, shift=UP * 0.08), run_time=self.s.rt_norm)
        else:
            icons.move_to(np.array([0, self.s.thought_y, 0]))
            thought = icons
            self.play(FadeIn(thought, shift=UP * 0.08), run_time=self.s.rt_norm)

        # Step 2: Bars emerge
        p2 = T(self.cfg, self.s, self.cfg.prompt_bars_en, self.cfg.prompt_bars_ar, scale=0.56)
        p2 = self.banner(p2).shift(DOWN * 0.9)
        self.play(Transform(self.title, p2), run_time=self.s.rt_fast)

        segs = bar_strip(len(prob.segments), self.s)
        segs.move_to(np.array([0, self.s.bar_y, 0]))
        segs.shift(np.array([self.s.left_anchor_x, 0, 0]) - segs.get_left())

        self.play(
            thought.animate.set_opacity(0.25).scale(0.98),
            Create(segs),
            run_time=self.s.rt_norm
        )

        # Step 3: progressive labeling (NO calculation)
        p3 = T(self.cfg, self.s, self.cfg.prompt_labels_en, self.cfg.prompt_labels_ar, scale=0.56)
        p3 = self.banner(p3).shift(DOWN * 0.9)
        self.play(Transform(self.title, p3), run_time=self.s.rt_fast)

        labels = VGroup()
        for idx, lab_txt in prob.known_labels:
            if 0 <= idx < len(segs):
                lab = label_above(segs[idx], lab_txt, self.s)
                labels.add(lab)
                self.play(FadeIn(lab, shift=UP * 0.05), run_time=self.s.rt_fast)

        # Step 4: unknown placeholder
        p4 = T(self.cfg, self.s, self.cfg.prompt_unknown_en, self.cfg.prompt_unknown_ar, scale=0.56)
        p4 = self.banner(p4).shift(DOWN * 0.9)
        self.play(Transform(self.title, p4), run_time=self.s.rt_fast)

        unknown_marks = VGroup()

        # Default: put ? on a segment
        if 0 <= prob.unknown_index < len(segs):
            q = Text("?", font_size=self.s.font_size_title).scale(0.95)
            q.move_to(segs[prob.unknown_index].get_center())
            box = SurroundingRectangle(segs[prob.unknown_index], buff=0.12).set_stroke(width=6)
            unknown_marks.add(q, box)
            self.play(FadeIn(q, shift=UP * 0.05), Create(box), run_time=self.s.rt_norm)

        # Special handling: if segments are repeated equal parts (BM2),
        # show a bracket for the WHOLE and put ? as the total.
        # Heuristic: all segment names identical.
        if len(set(prob.segments)) == 1 and len(prob.segments) >= 2:
            bracket = Brace(segs, DOWN, buff=0.15)
            qtot = Text("?", font_size=self.s.font_size_title).scale(0.90).next_to(bracket, DOWN, buff=0.12)
            unknown_marks.add(bracket, qtot)
            self.play(GrowFromCenter(bracket), FadeIn(qtot, shift=DOWN * 0.05), run_time=self.s.rt_norm)

        # Step 5: STOP (freeze before calculation)
        p5 = T(self.cfg, self.s, self.cfg.prompt_stop_en, self.cfg.prompt_stop_ar, scale=0.52)
        p5 = self.banner(p5).shift(DOWN * 0.9)
        self.play(Transform(self.title, p5), run_time=self.s.rt_fast)

        if self.s.freeze_before_calculation:
            stamp = Text("MODEL READY", font_size=self.s.font_size_main).scale(0.7)
            stamp.rotate(10 * DEGREES).set_opacity(0.35).to_edge(DOWN).shift(UP * 0.3)
            self.play(FadeIn(stamp, shift=UP * 0.05), run_time=self.s.rt_fast)
            self.wait(0.25)
            self.play(FadeOut(stamp), run_time=self.s.rt_fast)

        # We intentionally DO NOT show operations or results here.
        return VGroup(pb, thought, segs, labels, unknown_marks)


# ============================================================
# RUN:
#   manim -pqh your_file.py M3_L25_ImagineAndWriteBarModel
#
# CUSTOMIZE:
#   - Add new BarModelMetaProblem instances with your own scene_items + segments + labels.
#   - Keep it "labels only" and stop before calculation (as per lesson).
# ============================================================

