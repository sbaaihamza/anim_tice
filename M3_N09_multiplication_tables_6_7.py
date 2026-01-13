from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Literal, Dict

import numpy as np
from manim import *


# ============================================================
# STYLE / CONFIG
# ============================================================

@dataclass
class MultTableStyle:
    # visuals
    stroke_width: float = 4.0
    fill_opacity: float = 0.12
    dot_radius: float = 0.08
    cell_size: float = 0.44
    array_corner_radius: float = 0.12

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
    show_repeated_addition: bool = True
    show_array_model: bool = True
    show_patterns: bool = True
    stop_at_10: bool = True   # build up to 10 × 6 and 10 × 7 by default
    show_predictions: bool = True

    # layout
    title_y_shift: float = -0.9
    left_x: float = -5.5
    right_x: float = 5.5
    center_y: float = 0.0
    bottom_y: float = -3.0


@dataclass
class TableBuildSpec:
    base: int                    # 6 or 7
    up_to: int = 10              # 10 by default
    label: Optional[str] = None  # "6-times table"
    show_to: int = 10            # used for partial builds


@dataclass
class LessonConfigM3_N09:
    title_en: str = "Constructing the multiplication tables of 6 and 7"
    title_ar: str = "إنشاء جدولي ضرب العددين 6 و7"
    domain_en: str = "Numbers and Operations"
    domain_ar: str = "الأعداد والحساب"
    language: str = "en"

    # guidance prompts
    p_group_en: str = "Start with 1 group, then duplicate groups."
    p_group_ar: str = "نبدأ بمجموعة واحدة ثم نكرر المجموعات."

    p_count_en: str = "Count the total (repeated addition)."
    p_count_ar: str = "نعد المجموع (جمع متكرر)."

    p_pattern_en: str = "Look for patterns in the results."
    p_pattern_ar: str = "نبحث عن نمط في النتائج."

    tables: List[TableBuildSpec] = field(default_factory=lambda: [
        TableBuildSpec(base=6, up_to=10, label="×6"),
        TableBuildSpec(base=7, up_to=10, label="×7"),
    ])


# ============================================================
# HELPERS
# ============================================================

def T(cfg: LessonConfigM3_N09, s: MultTableStyle, en: str, ar: Optional[str] = None, scale: float = 0.6) -> Mobject:
    txt = en if cfg.language == "en" else (ar or en)
    return Text(txt, font_size=s.font_size_main).scale(scale)


def make_group_of_n(n: int, s: MultTableStyle) -> VGroup:
    """
    Visual 'group' model: n dots arranged in 2 rows for compactness.
    """
    cols = int(np.ceil(n / 2))
    dots = VGroup()
    for i in range(n):
        d = Dot(radius=s.dot_radius)
        dots.add(d)
    dots.arrange_in_grid(rows=2, cols=cols, buff=0.18)
    return dots


def array_model(rows: int, cols: int, s: MultTableStyle) -> VGroup:
    """
    Array representation: rows × cols grid of small rounded squares.
    """
    cells = VGroup()
    for r in range(rows):
        for c in range(cols):
            cell = RoundedRectangle(
                width=s.cell_size,
                height=s.cell_size,
                corner_radius=s.array_corner_radius
            )
            cell.set_stroke(width=2).set_fill(opacity=s.fill_opacity)
            cells.add(cell)
    cells.arrange_in_grid(rows=rows, cols=cols, buff=0.08)
    return cells


def make_result_row(k: int, base: int, s: MultTableStyle) -> VGroup:
    """
    Builds a text row: k × base = result
    """
    expr = Text(f"{k} × {base} = {k*base}", font_size=s.font_size_small).scale(0.62)
    return expr


def pattern_box(lines: List[str], s: MultTableStyle) -> VGroup:
    box = RoundedRectangle(width=5.6, height=2.0, corner_radius=0.25).set_stroke(width=3).set_fill(opacity=0.06)
    txt = VGroup(*[Text(l, font_size=s.font_size_small).scale(0.55) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    txt.move_to(box.get_center())
    return VGroup(box, txt)


# ============================================================
# MAIN SCENE
# ============================================================

class M3_N09_MultiplyTables_6_7(Scene):
    """
    M3_N09 — Build tables of 6 and 7 by:
      1) show 1 group of base
      2) duplicate groups step by step (k = 1..10)
      3) count total (repeated addition)
      4) optionally show array (k rows × base columns)
      5) write the table line k×base=result
      6) highlight patterns
    """

    def __init__(
        self,
        cfg: LessonConfigM3_N09 = LessonConfigM3_N09(),
        style: MultTableStyle = MultTableStyle(),
        **kwargs
    ):
        super().__init__(**kwargs)
        self.cfg = cfg
        self.s = style
        self.steps: List[Tuple[str, Callable[[], None]]] = []

    def banner(self, mob: Mobject) -> Mobject:
        mob.to_edge(UP)
        return mob

    def construct(self):
        self.step_intro()
        for t in self.cfg.tables:
            self.build_one_table(t)
        self.step_outro()

    # ============================================================
    # Intro / Outro
    # ============================================================

    def step_intro(self):
        title = T(self.cfg, self.s, self.cfg.title_en, self.cfg.title_ar, scale=0.58)
        title = self.banner(title)

        sub = T(
            self.cfg, self.s,
            "We build results step by step: groups → counting → pattern.",
            "نبني النتائج خطوة بخطوة: مجموعات → عدّ → نمط.",
            scale=0.46
        ).next_to(title, DOWN, buff=0.18)

        self.play(Write(title), FadeIn(sub, shift=DOWN * 0.12), run_time=self.s.rt_norm)
        self.wait(0.2)
        self.play(FadeOut(sub, shift=UP * 0.08), run_time=self.s.rt_fast)
        self.title = title

    def step_outro(self):
        recap = VGroup(
            T(self.cfg, self.s, "Recap:", "الخلاصة:", scale=0.62),
            T(self.cfg, self.s, "• Multiplication = repeated addition", "• الضرب = جمع متكرر", scale=0.52),
            T(self.cfg, self.s, "• Arrays help us see structure", "• المصفوفات تساعدنا على رؤية البنية", scale=0.52),
            T(self.cfg, self.s, "• Patterns help predict next results", "• الأنماط تساعدنا على توقع النتائج", scale=0.52),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        recap.to_edge(RIGHT).shift(DOWN * 0.2)

        self.play(FadeIn(recap, shift=LEFT * 0.15), run_time=self.s.rt_norm)
        self.wait(0.6)
        self.play(FadeOut(recap, shift=RIGHT * 0.15), FadeOut(self.title), run_time=self.s.rt_fast)

    # ============================================================
    # Core: build one table (×6 or ×7)
    # ============================================================

    def build_one_table(self, spec: TableBuildSpec):
        base = spec.base
        up_to = spec.up_to if not self.s.stop_at_10 else min(spec.up_to, 10)

        # header prompt
        header = T(
            self.cfg, self.s,
            f"Build the {spec.label or f'×{base}'} table",
            f"نبني جدول الضرب {spec.label or f'{base}'}",
            scale=0.56
        )
        header = self.banner(header).shift(DOWN * self.s.title_y_shift)
        self.play(Transform(self.title, header), run_time=self.s.rt_fast)

        # left side: groups / repeated addition
        prompt1 = T(self.cfg, self.s, self.cfg.p_group_en, self.cfg.p_group_ar, scale=0.46).to_edge(LEFT).shift(RIGHT * 0.4 + UP * 2.15)
        self.play(FadeIn(prompt1, shift=UP * 0.05), run_time=self.s.rt_fast)

        # right side: table lines
        table_col = VGroup().to_edge(RIGHT).shift(LEFT * 0.5 + UP * 0.35)

        # base group
        group1 = make_group_of_n(base, self.s)
        group1.move_to(np.array([self.s.left_x + 2.2, 0.8, 0]))
        group_label = Text(f"1 group of {base}", font_size=self.s.font_size_small).scale(0.55).next_to(group1, UP, buff=0.2)

        self.play(FadeIn(group1, shift=UP * 0.08), FadeIn(group_label, shift=UP * 0.08), run_time=self.s.rt_norm)

        # optional: array placeholder
        arr = VGroup()
        if self.s.show_array_model:
            arr = array_model(rows=1, cols=base, s=self.s).scale(0.95)
            arr.move_to(np.array([self.s.left_x + 2.2, -1.0, 0]))
            arr_label = Text("array", font_size=self.s.font_size_small).scale(0.52).next_to(arr, DOWN, buff=0.18)
            self.play(FadeIn(arr, shift=UP * 0.08), FadeIn(arr_label, shift=UP * 0.08), run_time=self.s.rt_fast)

        # first table line
        row = make_result_row(1, base, self.s)
        table_col.add(row)
        row.next_to(table_col, DOWN, buff=0.12) if len(table_col) > 1 else row.move_to(table_col.get_center())
        row.move_to(table_col.get_top() + DOWN * 0.15)
        self.play(Write(row), run_time=self.s.rt_fast)

        # repeated addition text
        add_txt = VGroup()
        if self.s.show_repeated_addition:
            add_txt = Text(f"{base}", font_size=self.s.font_size_small).scale(0.6)
            add_txt.next_to(group1, RIGHT, buff=0.55)
            self.play(FadeIn(add_txt, shift=RIGHT * 0.05), run_time=self.s.rt_fast)

        # build up k = 2..up_to
        groups = VGroup(group1)
        for k in range(2, up_to + 1):
            # duplicate a group
            new_group = make_group_of_n(base, self.s)
            new_group.match_height(group1)
            new_group.next_to(groups, RIGHT, buff=0.35)
            groups.add(new_group)

            # keep groups compact: if too wide, arrange in two rows
            if groups.width > 6.3:
                groups.arrange_in_grid(rows=2, cols=int(np.ceil(len(groups) / 2)), buff=0.35)
                groups.move_to(group1.get_center())

            # update label
            new_label = Text(f"{k} groups of {base}", font_size=self.s.font_size_small).scale(0.55).next_to(groups, UP, buff=0.2)

            # animation
            self.play(
                Transform(group_label, new_label),
                FadeIn(new_group, shift=UP * 0.06),
                run_time=self.s.rt_fast
            )

            # update repeated addition display
            if self.s.show_repeated_addition:
                parts = " + ".join([str(base)] * k)
                new_add = Text(parts, font_size=self.s.font_size_small).scale(0.45)
                new_add.next_to(groups, RIGHT, buff=0.45).shift(UP * 0.05)
                if k == 2:
                    self.play(Transform(add_txt, new_add), run_time=self.s.rt_fast)
                else:
                    self.play(Transform(add_txt, new_add), run_time=self.s.rt_fast)

            # optional: expand array to k rows
            if self.s.show_array_model:
                new_arr = array_model(rows=k, cols=base, s=self.s).scale(0.95)
                new_arr.move_to(arr.get_center())
                self.play(Transform(arr, new_arr), run_time=self.s.rt_fast)

            # write table line
            rowk = make_result_row(k, base, self.s)
            # append under previous rows
            if len(table_col) == 1:
                rowk.next_to(table_col[0], DOWN, buff=0.12)
            else:
                rowk.next_to(table_col[-1], DOWN, buff=0.12)
            table_col.add(rowk)
            self.play(Write(rowk), run_time=self.s.rt_fast)

            # small “predict next” beat
            if self.s.show_predictions and k < up_to:
                pred = Text("Next = +{}".format(base), font_size=self.s.font_size_small).scale(0.45)
                pred.set_opacity(0.45).next_to(rowk, RIGHT, buff=0.25)
                self.play(FadeIn(pred), run_time=self.s.rt_fast)
                self.play(FadeOut(pred), run_time=self.s.rt_fast)

        # patterns highlight
        patt = VGroup()
        if self.s.show_patterns:
            prompt2 = T(self.cfg, self.s, self.cfg.p_pattern_en, self.cfg.p_pattern_ar, scale=0.46).to_edge(LEFT).shift(RIGHT * 0.4 + UP * 1.35)
            self.play(Transform(prompt1, prompt2), run_time=self.s.rt_fast)

            # pattern examples:
            # - constant step = base
            # - parity for ×6: always even; ×7 alternates even/odd
            # - last digit cycles (mod 10) (simple observation)
            lines = [
                f"Each step: +{base}",
                "Look at last digits (cycle)",
            ]
            if base == 6:
                lines.append("All results are even")
            if base == 7:
                lines.append("Even / odd alternates")

            patt = pattern_box(lines, self.s).to_edge(DOWN).shift(UP * 0.25)

            # highlight “+base” by flashing consecutive rows
            self.play(FadeIn(patt, shift=UP * 0.08), run_time=self.s.rt_norm)

            if len(table_col) >= 3:
                # glow a couple of transitions
                for i in range(2, min(6, len(table_col))):
                    self.play(table_col[i-1].animate.set_opacity(0.35), run_time=0.2)
                    self.play(table_col[i].animate.set_opacity(1.0), run_time=0.2)
                    self.play(table_col[i-1].animate.set_opacity(1.0), run_time=0.2)

        # cleanup for next table
        to_fade = VGroup(prompt1, group_label, groups, add_txt, arr, table_col, patt)
        self.play(FadeOut(to_fade), run_time=self.s.rt_fast)


# ============================================================
# RUN:
#   manim -pqh your_file.py M3_N09_MultiplyTables_6_7
#
# EXTEND / ADJUST:
#   - Change LessonConfigM3_N09.tables to include different bases.
#   - Set style.show_array_model=False to rely on groups only.
#   - Increase up_to for 12× if needed.
# ============================================================
