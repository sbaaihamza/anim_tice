# Location: src/anim_tice/core.py

from dataclasses import dataclass
from typing import List, Tuple, Callable
from manim import Scene, Mobject, Write, FadeOut, Text, UP


# --- 1. Shared Configuration & Styling ---

@dataclass
class StyleConfig:
    """Default styles for all lessons."""
    font_size_title: int = 38
    font_size_main: int = 34
    pause: float = 0.45
    rt_fast: float = 0.7
    rt_norm: float = 1.0

@dataclass
class LessonConfig:
    """Default configuration for all lessons."""
    title_en: str
    title_ar: str
    language: str = "en"

# --- 2. Base Class ---

class AnimTiceScene(Scene):
    """
    A reusable base class for Anim-Tice lessons.
    """
    def __init__(
        self,
        lesson_config: LessonConfig,
        style_config: StyleConfig = StyleConfig(),
        **kwargs
    ):
        super().__init__(**kwargs)
        self.cfg = lesson_config
        self.s = style_config
        self.steps: List[Tuple[str, Callable[[], None]]] = []

    def construct(self):
        """Orchestrates the animation lifecycle."""
        # 1. Setup
        self.build_steps()
        self.show_title()

        # 2. Run steps
        for name, step_func in self.steps:
            self.before_step(name)
            step_func()
            self.after_step(name)

        # 3. Teardown
        self.cleanup()

    def build_steps(self):
        """
        Abstract method for subclasses to define their animation steps.

        Example:
        self.steps = [
            ("intro", self.step_intro),
            ("explore", self.step_explore),
        ]
        """
        raise NotImplementedError("Subclasses must implement build_steps.")

    def show_title(self):
        """Displays the initial lesson title."""
        title = self.t(self.cfg.title_en, self.cfg.title_ar, scale=0.62)
        self.play(Write(title), run_time=self.s.rt_norm)
        self.title = self.banner(title)

    def banner(self, mob: Mobject) -> Mobject:
        """Positions a Mobject at the top of the screen."""
        mob.to_edge(UP)
        return mob

    def t(self, en: str, ar: str, scale: float = 0.6) -> Mobject:
        """Renders text in the configured language."""
        txt = en if self.cfg.language == "en" else ar
        return Text(txt, font_size=self.s.font_size_main).scale(scale)

    def before_step(self, name: str):
        """Hook for logic before each step (e.g., logging)."""
        pass

    def after_step(self, name: str):
        """Hook for logic after each step (e.g., pausing)."""
        self.wait(self.s.pause)

    def cleanup(self):
        """Hook for scene cleanup."""
        self.play(FadeOut(self.title), run_time=self.s.rt_fast)
