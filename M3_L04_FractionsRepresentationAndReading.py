from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Dict

import numpy as np
from manim import *


# ============================================================
# CONFIG / STYLES
# ============================================================

@dataclass
class FractionStyle:
    # Visual sizing
    shape_scale: float = 1.15
    stroke_width: float = 4.0
    fill_opacity: float = 0.20

    # Text
    font_size_title: int = 38
    font_size_main: int = 34
    font_size_small: int = 28

    # Animation pacing
    pause: float = 0.45
    rt_fast: float = 0.7
    rt_norm: float = 1.0
    rt_slow: float = 1.25

    # Layout toggles
    show_number_line: bool = False  # optional extension
    show_arabic: bool = False       # enable only if Arabic renders correctly

    # Colors (keep defaults unless you want custom palette)
    whole_color = WHITE
    part_edge_opacity: float = 0.75


@dataclass
class FractionExample:
    """
    One example: a whole object, partition, choose k parts, then show fraction k/n.
    """
    name: str = "cake"
    denominator: int = 4
    numerator: int = 1
    # shape type: "circle" or "rect" or "bar"
    shape_type: str = "circle"
    # optional: for rect/bar, orientation
    orientation: str = "horizontal"  # "horizontal" | "vertical"


@dataclass
class LessonConfigM3_L04:
    title_en: str = "Fractions: representation and reading"
    title_ar: str = "الأعداد الكسرية: تمثيل وقراءة"
    language: str = "en"  # "en" | "ar"

    # Guided prompts (verbal layer)
    prompt_observe_en: str = "Observe: Is the whole divided into equal parts?"
    prompt_observe_ar: str = "لاحظ: هل قُسِّم الكل إلى أجزاء متساوية؟"

    prompt_name_en: str = "How many equal parts in total?"
    prompt_name_ar: str = "كم عدد الأجزاء المتساوية كلها؟"

    prompt_taken_en: str = "How many parts are taken?"
    prompt_taken_ar: str = "كم جزءاً أخذنا؟"

    prompt_symbol_en: str = "Now we write it as a fraction:"
    prompt_symbol_ar: str = "الآن نكتبها على شكل كسر:"

    # Examples flow (everyday sharing situations)
    examples: List[FractionExample] = field(default_factory=lambda: [
        FractionExample(name="pizza", denominator=4, numerator=1, shape_type="circle"),
        FractionExample(name="chocolate bar", denominator=6, numerator=2, shape_type="rect", orientation="vertical"),
        FractionExample(name="segment", denominator=5, numerator=3, shape_type="bar", orientation="horizontal"),
    ])


# ============================================================
# REUSABLE PRIMITIVES
# ============================================================

def t(cfg: LessonConfigM3_L04, s: FractionStyle, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
    txt = en if cfg.language == "en" else (ar or en)
    return Text(txt, font_size=s.font_size_main).scale(scale)


def fraction_tex(n: int, d: int, scale: float = 1.2) -> Mobject:
    return MathTex(rf"\frac{{{n}}}{{{d}}}").scale(scale)


class PartitionedCircle(VGroup):
    """
    Circle partitioned into equal sectors (denominator).
    We can fill selected sectors (numerator).
    """
    def __init__(self, denominator: int, style: FractionStyle, radius: float = 1.5, **kwargs):
        super().__init__(**kwargs)
        self.d = denominator
        self.s = style
        self.radius = radius

        circle = Circle(radius=radius).set_stroke(width=style.stroke_width)
        circle.set_fill(opacity=0.0)

        # sector lines
        lines = VGroup()
        for i in range(denominator):
            ang = i * TAU / denominator
            p = np.array([np.cos(ang), np.sin(ang), 0.0]) * radius
            lines.add(Line(ORIGIN, p).set_stroke(width=style.stroke_width * 0.75, opacity=style.part_edge_opacity))

        self.circle = circle
        self.lines = lines
        self.add(circle, lines)

    def sectors(self) -> VGroup:
        """
        Build fillable sectors as VMobjects.
        """
        sectors = VGroup()
        for i in range(self.d):
            start = i * TAU / self.d
            end = (i + 1) * TAU / self.d
            sec = Sector(
                outer_radius=self.radius,
                start_angle=start,
                angle=(end - start),
            ).set_stroke(width=0).set_fill(opacity=0.0)
            sectors.add(sec)
        return sectors


class PartitionedRect(VGroup):
    """
    Rectangle partitioned into equal strips (denominator).
    """
    def __init__(self, denominator: int, style: FractionStyle, width: float = 4.2, height: float = 2.2,
                 orientation: str = "vertical", **kwargs):
        super().__init__(**kwargs)
        self.d = denominator
        self.s = style
        self.orientation = orientation

        rect = RoundedRectangle(width=width, height=height, corner_radius=0.2).set_stroke(width=style.stroke_width)
        rect.set_fill(opacity=0.0)

        lines = VGroup()
        if orientation == "vertical":
            # vertical strips
            x0 = -width / 2
            for i in range(1, denominator):
                x = x0 + i * width / denominator
                lines.add(Line([x, -height/2, 0], [x, height/2, 0]).set_stroke(
                    width=style.stroke_width * 0.75, opacity=style.part_edge_opacity
                ))
        else:
            # horizontal strips
            y0 = -height / 2
            for i in range(1, denominator):
                y = y0 + i * height / denominator
                lines.add(Line([-width/2, y, 0], [width/2, y, 0]).set_stroke(
                    width=style.stroke_width * 0.75, opacity=style.part_edge_opacity
                ))

        self.rect = rect
        self.lines = lines
        self.add(rect, lines)

    def part_boxes(self) -> VGroup:
        boxes = VGroup()
        w = self.rect.width
        h = self.rect.height
        if self.orientation == "vertical":
            part_w = w / self.d
            for i in range(self.d):
                box = Rectangle(width=part_w, height=h).set_stroke(width=0).set_fill(opacity=0.0)
                box.move_to(self.rect.get_center() + LEFT * (w/2) + RIGHT * (part_w*(i+0.5)))
                boxes.add(box)
        else:
            part_h = h / self.d
            for i in range(self.d):
                box = Rectangle(width=w, height=part_h).set_stroke(width=0).set_fill(opacity=0.0)
                box.move_to(self.rect.get_center() + DOWN * (h/2) + UP * (part_h*(i+0.5)))
                boxes.add(box)
        return boxes


class SegmentedBar(VGroup):
    """
    A bar (like a segment) partitioned into equal parts.
    Great for linking fractions to segments.
    """
    def __init__(self, denominator: int, style: FractionStyle, length: float = 6.0, height: float = 0.8, **kwargs):
        super().__init__(**kwargs)
        self.d = denominator
        self.s = style
        self.length = length
        self.height = height

        outer = RoundedRectangle(width=length, height=height, corner_radius=0.18).set_stroke(width=style.stroke_width)
        outer.set_fill(opacity=0.0)

        sep = VGroup()
        x0 = -length / 2
        for i in range(1, denominator):
            x = x0 + i * length / denominator
            sep.add(Line([x, -height/2, 0], [x, height/2, 0]).set_stroke(
                width=style.stroke_width * 0.75, opacity=style.part_edge_opacity
            ))

        self.outer = outer
        self.sep = sep
        self.add(outer, sep)

    def part_boxes(self) -> VGroup:
        boxes = VGroup()
        part_w = self.length / self.d
        for i in range(self.d):
            box = Rectangle(width=part_w, height=self.height).set_stroke(width=0).set_fill(opacity=0.0)
            box.move_to(self.outer.get_center() + LEFT * (self.length/2) + RIGHT * (part_w*(i+0.5)))
            boxes.add(box)
        return boxes


# ============================================================
# LESSON SCENE (Reusable / Adjustable / Extensible)
# ============================================================

class M3_L04_FractionsRepresentationAndReading(Scene):
    """
    M3_L04 — Fractions: representation and reading

    Follows your animation_guidelines:
      show_whole_object
      divide_into_equal_parts
      highlight_selected_parts
      introduce_fraction_symbol_last

    And didactic actions:
      observe partitioned objects
      identify equal parts
      link parts to verbal expression
    """

    def __init__(
        self,
        cfg: LessonConfigM3_L04 = LessonConfigM3_L04(),
        style: FractionStyle = FractionStyle(),
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
            ("collective_discussion_compare", self.step_collective_discussion_compare),
            ("institutionalization_fraction_notation", self.step_institutionalization_fraction_notation),
            ("mini_assessment_match", self.step_mini_assessment_match),
            ("outro", self.step_outro),
        ]

    # ----------------------------
    # Helpers
    # ----------------------------

    def banner(self, mob: Mobject) -> Mobject:
        mob.to_edge(UP)
        return mob

    def step_intro(self):
        title = t(self.cfg, self.s, self.cfg.title_en, self.cfg.title_ar, scale=0.62)
        title = self.banner(title)

        subtitle = t(
            self.cfg, self.s,
            "Whole → equal parts → selected parts → fraction",
            "الكل → أجزاء متساوية → أجزاء مختارة → كسر",
            scale=0.52
        ).next_to(title, DOWN, buff=0.18)

        self.play(Write(title), FadeIn(subtitle, shift=DOWN * 0.15), run_time=self.s.rt_norm)
        self.wait(0.2)
        self.play(FadeOut(subtitle, shift=UP * 0.1), run_time=self.s.rt_fast)

        self.title = title

    def build_visual(self, ex: FractionExample) -> Tuple[Mobject, VGroup, VGroup]:
        """
        Returns: (base_shape_group, part_boxes_or_sectors, outline_group)
        - base_shape_group: includes outline + partition lines
        - part_boxes_or_sectors: fillable parts (same centers)
        - outline_group: for positioning labels
        """
        d = ex.denominator
        if ex.shape_type == "circle":
            pc = PartitionedCircle(d, self.s, radius=1.55)
            sectors = pc.sectors()
            return pc, sectors, VGroup(pc.circle)
        elif ex.shape_type == "rect":
            pr = PartitionedRect(d, self.s, width=4.4, height=2.4, orientation=ex.orientation)
            boxes = pr.part_boxes()
            return pr, boxes, VGroup(pr.rect)
        else:  # "bar"
            sb = SegmentedBar(d, self.s, length=6.2, height=1.0)
            boxes = sb.part_boxes()
            return sb, boxes, VGroup(sb.outer)

    def highlight_parts(self, parts: VGroup, k: int) -> VGroup:
        """
        Highlight first k parts (you can extend to highlight arbitrary indices).
        """
        chosen = VGroup()
        for i in range(min(k, len(parts))):
            p = parts[i].copy()
            p.set_fill(opacity=self.s.fill_opacity)
            chosen.add(p)
        return chosen

    # ============================================================
    # Steps
    # ============================================================

    def step_exploration_examples(self):
        """
        Exploration: everyday sharing situations (pizza, bar, segment)
        """
        prompt = t(self.cfg, self.s, self.cfg.prompt_observe_en, self.cfg.prompt_observe_ar, scale=0.55)
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        # show first example fully
        self.example_mobs = []
        for idx, ex in enumerate(self.cfg.examples):
            base, parts, outline = self.build_visual(ex)
            base.scale(self.s.shape_scale).move_to(ORIGIN + DOWN * 0.1)

            # Step flow: show whole object
            label = t(self.cfg, self.s, ex.name.title(), ex.name, scale=0.55).to_edge(LEFT).shift(UP * 0.3)

            self.play(FadeIn(label, shift=RIGHT * 0.15), run_time=self.s.rt_fast)
            self.play(Create(base), run_time=self.s.rt_norm)

            # Divide into equal parts: already visible by partition lines; we emphasize by briefly flashing them
            flash_lines = base[1] if isinstance(base, VGroup) and len(base) > 1 else None
            # (base is a VGroup-like. For our objects, partition lines exist as attribute)
            self.play(base.animate.set_stroke(width=self.s.stroke_width + 1), run_time=0.35)
            self.play(base.animate.set_stroke(width=self.s.stroke_width), run_time=0.25)

            # Ask: total parts (denominator)
            ask_total = t(self.cfg, self.s, self.cfg.prompt_name_en, self.cfg.prompt_name_ar, scale=0.52).to_edge(DOWN)
            d_label = Text(f"{ex.denominator}", font_size=self.s.font_size_title).next_to(ask_total, UP, buff=0.15)

            self.play(FadeIn(ask_total, shift=UP * 0.1), FadeIn(d_label, shift=UP * 0.1), run_time=self.s.rt_norm)
            self.wait(0.2)
            self.play(FadeOut(ask_total), FadeOut(d_label), run_time=self.s.rt_fast)

            # Highlight selected parts (numerator)
            ask_taken = t(self.cfg, self.s, self.cfg.prompt_taken_en, self.cfg.prompt_taken_ar, scale=0.52).to_edge(DOWN)
            self.play(FadeIn(ask_taken, shift=UP * 0.1), run_time=self.s.rt_fast)

            chosen = self.highlight_parts(parts, ex.numerator)
            for c in chosen:
                c.move_to(parts[chosen.submobjects.index(c)].get_center())
            # animate fill
            self.play(LaggedStartMap(FadeIn, chosen, lag_ratio=0.12), run_time=self.s.rt_norm)
            self.wait(0.2)
            self.play(FadeOut(ask_taken), run_time=self.s.rt_fast)

            # Introduce symbol LAST (but for exploration we can keep it subtle)
            sym_prompt = t(self.cfg, self.s, self.cfg.prompt_symbol_en, self.cfg.prompt_symbol_ar, scale=0.52).to_edge(DOWN)
            frac = fraction_tex(ex.numerator, ex.denominator, scale=1.3).next_to(sym_prompt, UP, buff=0.18)
            self.play(FadeIn(sym_prompt, shift=UP * 0.1), Write(frac), run_time=self.s.rt_norm)
            self.wait(0.2)

            # store and clear for next example (keep only brief compare later)
            group = VGroup(base, chosen, label, sym_prompt, frac)
            self.example_mobs.append((ex, base, chosen, label, frac))

            # clear current example before next (unless last)
            self.play(FadeOut(sym_prompt), FadeOut(frac), FadeOut(label), FadeOut(chosen), FadeOut(base), run_time=self.s.rt_fast)

    def step_collective_discussion_compare(self):
        """
        Compare representations: same fraction concept, different shapes.
        """
        prompt = t(
            self.cfg, self.s,
            "Discussion: Different pictures, same idea (equal parts).",
            "نقاش: صور مختلفة، نفس الفكرة (أجزاء متساوية).",
            scale=0.55
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        # Show 2 mini-thumbnails side by side for comparison
        if len(self.cfg.examples) < 2:
            return

        ex1, ex2 = self.cfg.examples[0], self.cfg.examples[1]
        base1, parts1, _ = self.build_visual(ex1)
        base2, parts2, _ = self.build_visual(ex2)

        base1.scale(0.75).to_edge(LEFT).shift(DOWN * 0.2 + RIGHT * 0.8)
        base2.scale(0.75).to_edge(RIGHT).shift(DOWN * 0.2 + LEFT * 0.8)

        chosen1 = self.highlight_parts(parts1, ex1.numerator)
        for i, c in enumerate(chosen1):
            c.move_to(parts1[i].get_center())
        chosen1.scale(0.75).move_to(base1.get_center())

        chosen2 = self.highlight_parts(parts2, ex2.numerator)
        for i, c in enumerate(chosen2):
            c.move_to(parts2[i].get_center())
        chosen2.scale(0.75).move_to(base2.get_center())

        frac1 = fraction_tex(ex1.numerator, ex1.denominator, scale=1.1).next_to(base1, DOWN, buff=0.25)
        frac2 = fraction_tex(ex2.numerator, ex2.denominator, scale=1.1).next_to(base2, DOWN, buff=0.25)

        self.play(Create(base1), FadeIn(chosen1), Write(frac1), run_time=self.s.rt_norm)
        self.play(Create(base2), FadeIn(chosen2), Write(frac2), run_time=self.s.rt_norm)

        focus = t(
            self.cfg, self.s,
            "What matters: equal parts + how many parts taken.",
            "المهم: أجزاء متساوية + عدد الأجزاء المأخوذة.",
            scale=0.52
        ).to_edge(DOWN)

        self.play(FadeIn(focus, shift=UP * 0.1), run_time=self.s.rt_fast)
        self.wait(0.4)

        self.play(FadeOut(VGroup(base1, chosen1, frac1, base2, chosen2, frac2, focus)), run_time=self.s.rt_fast)

    def step_institutionalization_fraction_notation(self):
        """
        Formalize numerator/denominator meaning with visuals (no abstract rule first).
        """
        prompt = t(
            self.cfg, self.s,
            "Institutionalization: numerator / denominator",
            "التثبيت: البسط / المقام",
            scale=0.58
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        # Use one clean example (circle 3/5)
        ex = FractionExample(name="pizza", denominator=5, numerator=3, shape_type="circle")
        base, parts, _ = self.build_visual(ex)
        base.scale(self.s.shape_scale).move_to(LEFT * 2.7 + DOWN * 0.1)

        chosen = self.highlight_parts(parts, ex.numerator)
        for i, c in enumerate(chosen):
            c.move_to(parts[i].get_center())
        chosen.move_to(base.get_center()).scale(self.s.shape_scale)

        frac = fraction_tex(ex.numerator, ex.denominator, scale=1.5).move_to(RIGHT * 3.2 + UP * 0.3)

        # Labels pointing to numerator/denominator
        num_box = SurroundingRectangle(frac[0][0], buff=0.08)  # numerator glyph group
        den_box = SurroundingRectangle(frac[0][2], buff=0.08)  # denominator glyph group (layout: \frac{a}{b})
        num_lab = t(self.cfg, self.s, "numerator = parts taken", "البسط = الأجزاء المأخوذة", scale=0.50).next_to(num_box, UP, buff=0.15)
        den_lab = t(self.cfg, self.s, "denominator = equal parts in whole", "المقام = عدد الأجزاء المتساوية", scale=0.50).next_to(den_box, DOWN, buff=0.15)

        self.play(Create(base), FadeIn(chosen), run_time=self.s.rt_norm)
        self.play(Write(frac), run_time=self.s.rt_norm)
        self.play(Create(num_box), FadeIn(num_lab, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.play(Create(den_box), FadeIn(den_lab, shift=DOWN * 0.1), run_time=self.s.rt_norm)

        # Freeze on key rule
        rule = t(
            self.cfg, self.s,
            "Fraction = (taken parts) / (equal parts in the whole)",
            "الكسر = (الأجزاء المأخوذة) / (الأجزاء المتساوية في الكل)",
            scale=0.52
        ).to_edge(DOWN)

        self.play(FadeIn(rule, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.4)

        self.play(FadeOut(VGroup(base, chosen, frac, num_box, den_box, num_lab, den_lab, rule)), run_time=self.s.rt_fast)

    def step_mini_assessment_match(self):
        """
        Formative: match picture to fraction (simple).
        """
        prompt = t(
            self.cfg, self.s,
            "Mini-check: Which fraction matches the picture?",
            "تحقق صغير: أي كسر يوافق الصورة؟",
            scale=0.55
        )
        prompt = self.banner(prompt).shift(DOWN * 0.9)
        self.play(Transform(self.title, prompt), run_time=self.s.rt_fast)

        ex = FractionExample(name="bar", denominator=4, numerator=2, shape_type="rect", orientation="horizontal")
        base, parts, _ = self.build_visual(ex)
        base.scale(0.95).move_to(LEFT * 2.7 + DOWN * 0.1)

        chosen = self.highlight_parts(parts, ex.numerator)
        for i, c in enumerate(chosen):
            c.move_to(parts[i].get_center())
        chosen.scale(0.95).move_to(base.get_center())

        # options
        opt1 = fraction_tex(1, 4, scale=1.2)
        opt2 = fraction_tex(2, 4, scale=1.2)  # correct
        opt3 = fraction_tex(3, 4, scale=1.2)
        options = VGroup(opt1, opt2, opt3).arrange(DOWN, buff=0.35).move_to(RIGHT * 3.1)

        self.play(Create(base), FadeIn(chosen), run_time=self.s.rt_norm)
        self.play(FadeIn(options, shift=LEFT * 0.15), run_time=self.s.rt_norm)

        # reveal correct
        box = SurroundingRectangle(opt2, buff=0.12)
        ok = t(self.cfg, self.s, "Correct!", "صحيح!", scale=0.55).next_to(box, DOWN, buff=0.2)
        self.play(Create(box), FadeIn(ok, shift=UP * 0.1), run_time=self.s.rt_norm)
        self.wait(0.3)

        self.play(FadeOut(VGroup(base, chosen, options, box, ok)), run_time=self.s.rt_fast)

    def step_outro(self):
        recap = VGroup(
            t(self.cfg, self.s, "Recap:", "الخلاصة:", scale=0.6),
            t(self.cfg, self.s, "• Fractions mean equal parts of a whole", "• الكسر يعني أجزاء متساوية من كل", scale=0.50),
            t(self.cfg, self.s, "• Denominator: total equal parts", "• المقام: عدد الأجزاء المتساوية", scale=0.50),
            t(self.cfg, self.s, "• Numerator: parts taken", "• البسط: الأجزاء المأخوذة", scale=0.50),
            t(self.cfg, self.s, "• Read the fraction correctly", "• نقرأ الكسر بشكل صحيح", scale=0.50),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        recap.to_edge(RIGHT).shift(DOWN * 0.2)
        self.play(FadeIn(recap, shift=LEFT * 0.2), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(recap, shift=RIGHT * 0.2), FadeOut(self.title), run_time=self.s.rt_fast)


# ============================================================
# RUN:
#   manim -pqh your_file.py M3_L04_FractionsRepresentationAndReading
#
# CUSTOMIZE EXAMPLES:
#   cfg = LessonConfigM3_L04(
#       examples=[
#           FractionExample(name="cake", denominator=3, numerator=1, shape_type="circle"),
#           FractionExample(name="bar", denominator=8, numerator=5, shape_type="rect", orientation="vertical"),
#       ],
#       language="ar"
#   )
# ============================================================