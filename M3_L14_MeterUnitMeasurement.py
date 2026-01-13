from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Dict

import numpy as np
from manim import *


# ============================================================
# CONFIG / STYLES
# ============================================================

@dataclass
class MeterStyle:
    # Visual sizes
    stroke_width: float = 4.0
    fill_opacity: float = 0.18

    # "Meter segment" visual
    meter_length: float = 2.6          # how long 1 m looks on screen
    meter_height: float = 0.35
    meter_corner_radius: float = 0.12

    # "Object" visuals (we simulate real objects with bars/boards/ropes)
    obj_height: float = 0.55
    obj_corner_radius: float = 0.18

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
    show_nonstandard_units_demo: bool = True
    show_snap_guides: bool = True

    # iteration style
    show_iteration_counter: bool = True
    counter_scale: float = 0.75


@dataclass
class ObjectSpec:
    """
    Simulated real-world object as a rounded rectangle bar.
    length_units are in "meter segments" multiples.
    """
    name: str
    length_m: float  # real length in meters for labeling
    # visual width is computed as length_m * meter_length
    y: float = 0.0


@dataclass
class LessonConfigM3_L14:
    title_en: str = "Units of length measurement: the meter (m)"
    title_ar: str = "وحدات قياس الأطوال: المتر (m)"
    language: str = "en"  # "en" | "ar"

    # prompts
    prompt_compare_en: str = "Can we decide which is longer just by looking?"
    prompt_compare_ar: str = "هل يمكن أن نعرف الأطول فقط بالنظر؟"

    prompt_need_unit_en: str = "We need a common unit to measure."
    prompt_need_unit_ar: str = "نحتاج إلى وحدة مشتركة للقياس."

    prompt_meter_en: str = "This is 1 meter (m). We place it at the start."
    prompt_meter_ar: str = "هذا متر واحد (m). نضعه عند البداية."

    prompt_repeat_en: str = "Repeat the meter unit until we reach the end."
    prompt_repeat_ar: str = "نكرر وحدة المتر حتى نصل إلى النهاية."

    prompt_count_en: str = "Count how many meters fit."
    prompt_count_ar: str = "نعد كم متراً نحتاج."

    prompt_label_en: str = "We write the measurement with the symbol m:"
    prompt_label_ar: str = "نكتب القياس مع الرمز m:"

    prompt_validate_en: str = "Alignment matters: start point and end point."
    prompt_validate_ar: str = "المحاذاة مهمة: نقطة البداية ونقطة النهاية."

    # lesson examples: two objects side-by-side (ambiguous), then measure one
    objects: List[ObjectSpec] = field(default_factory=lambda: [
        ObjectSpec(name="desk", length_m=2.0, y=0.7),
        ObjectSpec(name="rope", length_m=2.0, y=-0.7),  # same length -> ambiguous visually if positioned differently
    ])

    # measurement target object (index)
    measure_object_index: int = 0


# ============================================================
# REUSABLE PRIMITIVES
# ============================================================

def T(cfg: LessonConfigM3_L14, s: MeterStyle, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
    txt = en if cfg.language == "en" else (ar or en)
    return Text(txt, font_size=s.font_size_main).scale(scale)


class SimObject(VGroup):
    """
    Simulated real-world object as a rounded rectangle + label.
    """
    def __init__(self, name: str, width: float, height: float, style: MeterStyle, **kwargs):
        super().__init__(**kwargs)
        body = RoundedRectangle(width=width, height=height, corner_radius=style.obj_corner_radius)
        body.set_stroke(width=style.stroke_width).set_fill(opacity=style.fill_opacity)

        label = Text(name, font_size=style.font_size_small)
        label.next_to(body, UP, buff=0.12)

        self.body = body
        self.label = label
        self.add(body, label)

    @property
    def start_point(self) -> np.ndarray:
        return self.body.get_left()

    @property
    def end_point(self) -> np.ndarray:
        return self.body.get_right()


class MeterUnit(VGroup):
    """
    Visual 1-meter segment (not a floating ruler; it "touches" the object).
    """
    def __init__(self, style: MeterStyle, **kwargs):
        super().__init__(**kwargs)
        seg = RoundedRectangle(
            width=style.meter_length,
            height=style.meter_height,
            corner_radius=style.meter_corner_radius
        ).set_stroke(width=style.stroke_width).set_fill(opacity=0.10)

        # endpoints
        pL = Dot(seg.get_left(), radius=0.06)
        pR = Dot(seg.get_right(), radius=0.06)

        lab = Text("1 m", font_size=style.font_size_small).next_to(seg, DOWN, buff=0.12)

        self.seg = seg
        self.pL = pL
        self.pR = pR
        self.lab = lab
        self.add(seg, pL, pR, lab)

    def move_left_end_to(self, point: np.ndarray):
        shift = point - self.seg.get_left()
        self.shift(shift)
        return self

    def left_end(self) -> np.ndarray:
        return self.seg.get_left()

    def right_end(self) -> np.ndarray:
        return self.seg.get_right()


def endpoint_markers(obj: SimObject, style: MeterStyle) -> VGroup:
    """
    Highlight start/end of object (snap-to-endpoints affordance).
    """
    s = Dot(obj.start_point, radius=0.07)
    e = Dot(obj.end_point, radius=0.07)
    s_lab = Text("start", font_size=style.font_size_small).scale(0.75).next_to(s, DOWN, buff=0.1)
    e_lab = Text("end", font_size=style.font_size_small).scale(0.75).next_to(e, DOWN, buff=0.1)
    return VGroup(s, e, s_lab, e_lab)


def build_iteration_counter(style: MeterStyle, k: int, at: np.ndarray) -> VGroup:
    if not style.show_iteration_counter:
        return VGroup()
    txt = Text(f"{k}", font_size=style.font_size_title).scale(style.counter_scale)
    txt.move_to(at)
    ring = Circle(radius=0.35).move_to(at)
    ring.set_stroke(width=3)
    return VGroup(ring, txt)


# ============================================================
# LESSON SCENE (Reusable / Adjustable / Extensible)
# ============================================================

class M3_L14_MeterUnitMeasurement(Scene):
    """
    M3_L14 — Units of length measurement: meter (m)

    Animation flow:
      show_two_objects_side_by_side
      attempt_visual_comparison (ambiguous)
      introduce_meter_unit as physical segment
      place_meter_at_start_point
      repeat_meter_along_object until end
      count_iterations
      reveal measurement label (e.g., 3 m)

    Avoids:
      number-first without unit context,
      floating ruler without contact,
      measurement without start/end alignment.
    """

    def __init__(
        self,
        cfg: LessonConfigM3_L14 = LessonConfigM3_L14(),
        style: MeterStyle = MeterStyle(),
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
            ("exploration_compare", self.step_exploration_compare),
            ("collective_discussion_need_unit", self.step_collective_discussion_need_unit),
            ("institutionalization_meter_iteration", self.step_institutionalization_meter_iteration),
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
            "Estimate vs Measure — we need a standard unit",
            "التقدير vs القياس — نحتاج وحدة معيارية",
            scale=0.52
        ).next_to(title, DOWN, buff=0.18)

        self.play(Write(title), FadeIn(subtitle, shift=DOWN * 0.15), run_time=self.s.rt_norm)
        self.wait(0.2)
        self.play(FadeOut(subtitle, shift=UP * 0.1), run_time=self.s.rt_fast)
        self.title = title

    def step_exploration_compare(self):
        """
        Exploration: visual comparison is insufficient → create need for standard unit.
        """
        p = T(self.cfg, self.s, self.cfg.prompt_compare_en, self.cfg.prompt_compare_ar, scale=0.55)
        p = self.banner(p).shift(DOWN * 0.9)
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        # Build two objects; make the situation ambiguous by shifting them and not aligning starts
        self.obj_mobs: List[SimObject] = []
        for spec in self.cfg.objects:
            w = spec.length_m * self.s.meter_length
            mob = SimObject(spec.name, width=w, height=self.s.obj_height, style=self.s)
            mob.move_to([0, spec.y, 0])

            # introduce ambiguity: slight horizontal offset differences
            if spec.y > 0:
                mob.shift(RIGHT * 0.6)
            else:
                mob.shift(LEFT * 0.35)

            self.obj_mobs.append(mob)

        self.play(FadeIn(self.obj_mobs[0], shift=UP * 0.15), FadeIn(self.obj_mobs[1], shift=DOWN * 0.15), run_time=self.s.rt_norm)

        amb = T(
            self.cfg, self.s,
            "Looks confusing… because they are not aligned.",
            "يبدو الأمر محيّراً… لأنهما غير مُحاذيين.",
            scale=0.52
        ).to_edge(DOWN)

        self.play(FadeIn(amb, shift=UP * 0.1), run_time=self.s.rt_fast)
        self.wait(0.4)
        self.play(FadeOut(amb), run_time=self.s.rt_fast)

    def step_collective_discussion_need_unit(self):
        """
        Discussion: non-standard units cause different results → shared unit needed.
        """
        p = T(self.cfg, self.s, self.cfg.prompt_need_unit_en, self.cfg.prompt_need_unit_ar, scale=0.58)
        p = self.banner(p).shift(DOWN * 0.9)
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        box = RoundedRectangle(width=11.6, height=2.8, corner_radius=0.25).to_edge(DOWN).shift(UP * 0.2)
        box.set_fill(opacity=0.06).set_stroke(width=3)

        l1 = T(self.cfg, self.s, "• Different people → different hand spans/steps.", "• أشخاص مختلفون → قياسات مختلفة بالخطوة/الكف.", scale=0.52)
        l2 = T(self.cfg, self.s, "• So results differ.", "• لذلك تختلف النتائج.", scale=0.52)
        l3 = T(self.cfg, self.s, "• We agree on one standard unit.", "• نتفق على وحدة معيارية واحدة.", scale=0.52)
        scaff = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(box.get_center())

        self.play(Create(box), FadeIn(scaff, shift=UP * 0.1), run_time=self.s.rt_norm)

        if self.s.show_nonstandard_units_demo:
            # quick "hand span" demo: two different unit segments
            u1 = RoundedRectangle(width=1.8, height=0.25, corner_radius=0.1).set_stroke(width=3).set_fill(opacity=0.10)
            u2 = RoundedRectangle(width=1.2, height=0.25, corner_radius=0.1).set_stroke(width=3).set_fill(opacity=0.10)
            u1_lab = Text("hand span A", font_size=self.s.font_size_small).scale(0.65).next_to(u1, DOWN, buff=0.1)
            u2_lab = Text("hand span B", font_size=self.s.font_size_small).scale(0.65).next_to(u2, DOWN, buff=0.1)
            demo = VGroup(VGroup(u1, u1_lab), VGroup(u2, u2_lab)).arrange(DOWN, buff=0.25).to_edge(RIGHT).shift(UP * 0.2)

            self.play(FadeIn(demo, shift=LEFT * 0.1), run_time=self.s.rt_norm)
            self.wait(0.4)
            self.play(FadeOut(demo), run_time=self.s.rt_fast)

        self.play(FadeOut(VGroup(box, scaff)), run_time=self.s.rt_fast)

    def step_institutionalization_meter_iteration(self):
        """
        Institutionalization: meter (m) as standard unit; iterate and count.
        """
        p = T(self.cfg, self.s, self.cfg.prompt_meter_en, self.cfg.prompt_meter_ar, scale=0.58)
        p = self.banner(p).shift(DOWN * 0.9)
        self.play(Transform(self.title, p), run_time=self.s.rt_fast)

        # choose target object to measure
        obj = self.obj_mobs[self.cfg.measure_object_index]

        # show start/end markers to enforce alignment
        marks = endpoint_markers(obj, self.s)
        if self.s.show_snap_guides:
            self.play(FadeIn(marks, shift=UP * 0.1), run_time=self.s.rt_norm)

        # create meter unit and snap to start
        meter = MeterUnit(self.s)
        meter.move_left_end_to(obj.start_point + DOWN * 0.8)
        self.play(FadeIn(meter, shift=UP * 0.1), run_time=self.s.rt_norm)

        # Move meter to touch the object line (not floating)
        # We'll align vertically with the object (y)
        meter.shift(UP * 0.8)
        self.play(meter.animate.shift(UP * 0.0), run_time=0.3)

        # Repeat meter along object until end
        p2 = T(self.cfg, self.s, self.cfg.prompt_repeat_en, self.cfg.prompt_repeat_ar, scale=0.58)
        p2 = self.banner(p2).shift(DOWN * 0.9)
        self.play(Transform(self.title, p2), run_time=self.s.rt_fast)

        length_visual = obj.body.width
        unit_visual = self.s.meter_length
        full_meters = int(np.floor(length_visual / unit_visual + 1e-6))

        counters = VGroup()
        meter_copies = VGroup()

        # Place successive meter copies
        start = obj.start_point
        for i in range(full_meters):
            m = MeterUnit(self.s)
            m.move_left_end_to(start + RIGHT * (i * unit_visual))
            # align vertically to object (so it "touches")
            m.shift(UP * (obj.get_center()[1] - m.get_center()[1]))
            m.lab.set_opacity(0.0)  # hide repeated "1 m" labels for cleanliness
            meter_copies.add(m)

        # animate placing them one by one + counter
        p3 = T(self.cfg, self.s, self.cfg.prompt_count_en, self.cfg.prompt_count_ar, scale=0.58)
        p3 = self.banner(p3).shift(DOWN * 0.9)

        for i, m in enumerate(meter_copies, start=1):
            if i == 1:
                # transform original meter into first placed meter for continuity
                self.play(Transform(meter, m), run_time=self.s.rt_norm)
            else:
                self.play(FadeIn(m, shift=UP * 0.05), run_time=self.s.rt_fast)
            self.play(Transform(self.title, p3), run_time=0.15)

            c = build_iteration_counter(self.s, i, at=obj.get_center() + UP * 1.4)
            counters.add(c)
            self.play(FadeIn(c, shift=UP * 0.05), run_time=0.25)
            if i > 1:
                self.play(FadeOut(counters[i - 2]), run_time=0.2)

        if len(counters) > 0:
            self.play(FadeOut(counters[-1]), run_time=0.2)

        # Reveal final measurement label: "X m"
        p4 = T(self.cfg, self.s, self.cfg.prompt_label_en, self.cfg.prompt_label_ar, scale=0.58)
        p4 = self.banner(p4).shift(DOWN * 0.9)
        self.play(Transform(self.title, p4), run_time=self.s.rt_fast)

        label = Text(f"{full_meters} m", font_size=self.s.font_size_title).next_to(obj, DOWN, buff=0.35)
        self.play(Write(label), run_time=self.s.rt_norm)

        # Validate alignment message
        p5 = T(self.cfg, self.s, self.cfg.prompt_validate_en, self.cfg.prompt_validate_ar, scale=0.56)
        p5.to_edge(DOWN)
        self.play(FadeIn(p5, shift=UP * 0.1), run_time=self.s.rt_fast)
        self.wait(0.4)
        self.play(FadeOut(p5), run_time=self.s.rt_fast)

        self.measure_group = VGroup(meter, meter_copies[1:] if len(meter_copies) > 1 else VGroup(), label, marks)
        # Keep objects on screen for next step; do not fade them yet.

    def step_mini_assessment(self):
        """
        Formative: measure another object and pick correct label.
        """
        prompt = T(
            self.cfg, self.s,
            "Mini-check: How many meters long is this object?",
            "تحقق صغير: كم متر طول هذا الشيء؟",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        # Make a new object of 3 m
        target_len_m = 3
        w = target_len_m * self.s.meter_length
        obj = SimObject("board", width=w, height=self.s.obj_height, style=self.s).move_to(DOWN * 0.2)

        self.play(FadeOut(self.obj_mobs[0]), FadeOut(self.obj_mobs[1]), FadeOut(self.measure_group), run_time=self.s.rt_fast)
        self.play(FadeIn(obj, shift=UP * 0.1), run_time=self.s.rt_norm)

        # options
        o1 = Text("2 m", font_size=self.s.font_size_main)
        o2 = Text("3 m", font_size=self.s.font_size_main)
        o3 = Text("4 m", font_size=self.s.font_size_main)
        opts = VGroup(o1, o2, o3).arrange(DOWN, buff=0.25).to_edge(RIGHT).shift(UP * 0.1)

        self.play(FadeIn(opts, shift=LEFT * 0.1), run_time=self.s.rt_norm)

        # quick iteration: place 3 meters (fast)
        m1 = MeterUnit(self.s).move_left_end_to(obj.start_point)
        m1.shift(UP * (obj.get_center()[1] - m1.get_center()[1]))
        self.play(FadeIn(m1, shift=UP * 0.05), run_time=self.s.rt_fast)

        m2 = MeterUnit(self.s).move_left_end_to(obj.start_point + RIGHT * self.s.meter_length)
        m2.shift(UP * (obj.get_center()[1] - m2.get_center()[1]))
        m2.lab.set_opacity(0)
        self.play(FadeIn(m2, shift=UP * 0.05), run_time=self.s.rt_fast)

        m3 = MeterUnit(self.s).move_left_end_to(obj.start_point + RIGHT * 2 * self.s.meter_length)
        m3.shift(UP * (obj.get_center()[1] - m3.get_center()[1]))
        m3.lab.set_opacity(0)
        self.play(FadeIn(m3, shift=UP * 0.05), run_time=self.s.rt_fast)

        # reveal correct option
        box = SurroundingRectangle(o2, buff=0.12)
        ok = T(self.cfg, self.s, "Correct: 3 m", "صحيح: 3 m", scale=0.56).to_edge(DOWN)
        self.play(Create(box), FadeIn(ok, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.4)

        self.play(FadeOut(VGroup(obj, opts, m1, m2, m3, box, ok)), run_time=self.s.rt_fast)

    def step_outro(self):
        recap = VGroup(
            T(self.cfg, self.s, "Recap:", "الخلاصة:", scale=0.6),
            T(self.cfg, self.s, "• Meter (m) is a standard unit of length", "• المتر (m) وحدة معيارية للطول", scale=0.50),
            T(self.cfg, self.s, "• Always align at the start and end", "• دائماً نحاذي البداية والنهاية", scale=0.50),
            T(self.cfg, self.s, "• Repeat the unit and count", "• نكرر الوحدة ونعدّ", scale=0.50),
            T(self.cfg, self.s, "• Write: value + m", "• نكتب: عدد + m", scale=0.50),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        recap.to_edge(RIGHT).shift(DOWN * 0.15)
        self.play(FadeIn(recap, shift=LEFT * 0.2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(recap, shift=RIGHT * 0.2), FadeOut(self.title), run_time=self.s.rt_fast)


# ============================================================
# RUN:
#   manim -pqh your_file.py M3_L14_MeterUnitMeasurement
#
# CUSTOMIZE OBJECTS:
#   cfg = LessonConfigM3_L14(
#       objects=[
#           ObjectSpec("desk", 2.0, y=0.8),
#           ObjectSpec("rope", 3.0, y=-0.8),
#       ],
#       measure_object_index=1,
#       language="ar"
#   )
# ============================================================