# Proposed Base Class API: `AnimTiceScene`

This document proposes the API for a new Python superclass designed to unify shared behavior, reduce duplication, and provide a consistent structure for all `manim` animations in this repository.

## 1. Class Name and Location

- **Class Name:** `AnimTiceScene`
- **Location:** `src/anim_tice/core.py`

This introduces a `src` layout to separate reusable library code from the individual lesson scripts, which will remain in the root directory.

## 2. Responsibilities

### Base Class (`AnimTiceScene`)

The base class will be responsible for all **cross-cutting concerns and orchestration**:

- **Configuration & Styling:**
  - Provides default `StyleConfig` and `LessonConfig` dataclasses.
  - Subclasses can override defaults by passing their own instances to the constructor.
- **Scene Lifecycle:**
  - Manages the main animation loop in the `construct` method.
  - Automatically displays a title banner.
  - Calls a sequence of `step_` methods defined by the subclass.
  - Handles scene cleanup.
- **Helper Methods:**
  - Provides a centralized `t` method for bilingual text rendering.
  - Provides a `banner` method for consistent title placement.
- **Error Handling & Logging:** (Future) Can be extended to include centralized logging and error handling.

### Subclasses (e.g., `M3_G05_Ruler_Scene`)

Subclasses will be responsible for **lesson-specific logic and content**:

- **Defining Steps:**
  - Must implement an abstract `build_steps` method that returns a list of step functions.
- **Implementing Steps:**
  - Each step function (e.g., `step_intro`, `step_explore`) contains the `manim` animations for that part of the lesson.
- **Custom Configuration:**
  - Can define their own `LessonConfig` and `StyleConfig` dataclasses to override the defaults.
- **Lesson-Specific Helpers:**
  - Can implement any additional helper methods required for the lesson.

## 3. API Definition

```python
# Location: src/anim_tice/core.py

from dataclasses import dataclass
from typing import List, Tuple, Callable
from manim import Scene, Mobject

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

```

## 4. Migration Strategy

The refactoring can be done incrementally in small, safe PRs.

-   **PR 1: Introduce the Base Class (This PR)**
    -   Create `src/anim_tice/core.py` with the `AnimTiceScene` and shared dataclasses.
    -   Do **not** modify any existing lesson scripts yet.

-   **PR 2: Refactor a Single Lesson**
    -   Choose one simple lesson (e.g., `M3_L14_MeterUnitMeasurement.py`).
    -   Modify it to inherit from `AnimTiceScene`.
    -   Remove the duplicated dataclasses and helper methods from the lesson file.
    -   Ensure the animation still renders correctly.

-   **PR 3, 4, ...: Refactor Remaining Lessons**
    -   Refactor the remaining lessons one by one or in small batches.
    -   This iterative process minimizes risk and makes reviews easier.

-   **PR N: Final Cleanup**
    -   Once all lessons are migrated, remove any remaining duplicated code.
    -   Update the documentation to explain how to create new lessons using the base class.

## 5. Next PR Checklist

-   [x] Create `docs/ARCHITECTURE_MAP.md`.
-   [x] Create `docs/REFACTOR_PLAN.md`.
-   [x] Propose `AnimTiceScene` API in `docs/BASECLASS_API.md`.
-   [ ] **Next:** Submit a PR with these documentation files for review.
