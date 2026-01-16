# Lesson Template

This document provides a template for creating new lessons using the `AnimTiceScene` base class.

## 1. File Naming

-   Use a descriptive file name that follows the existing convention (e.g., `M1_L01_Topic.py`).
-   Place the file in the root directory of the repository.

## 2. Lesson Structure

Your lesson script should follow this structure:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Callable

import numpy as np
from manim import *

from anim_tice.core import AnimTiceScene, LessonConfig, StyleConfig


# ============================================================
# 1. CONFIGURATION & STYLING
# ============================================================

@dataclass
class YourLessonStyle(StyleConfig):
    # Add any lesson-specific style overrides here
    pass


@dataclass
class YourLessonConfig(LessonConfig):
    title_en: str = "Your Lesson Title"
    title_ar: str = "عنوان الدرس"

    # Add any lesson-specific configuration here
    pass


# ============================================================
# 2. REUSABLE PRIMITIVES (OPTIONAL)
# ============================================================

# Define any reusable classes or functions specific to this lesson
# (e.g., a custom Mobject)


# ============================================================
# 3. LESSON SCENE
# ============================================================

class YourLessonScene(AnimTiceScene):
    """
    A brief description of your lesson.
    """

    def __init__(
        self,
        lesson_config: YourLessonConfig = YourLessonConfig(),
        style_config: YourLessonStyle = YourLessonStyle(),
        **kwargs
    ):
        super().__init__(
            lesson_config=lesson_config,
            style_config=style_config,
            **kwargs
        )

    def build_steps(self):
        """
        Define the sequence of steps for your animation.
        """
        self.steps = [
            ("intro", self.step_intro),
            ("explore", self.step_explore),
            # Add more steps as needed...
            ("outro", self.step_outro),
        ]

    # --- Step Implementations ---

    def step_intro(self):
        # The base class automatically displays the title.
        # You can add a subtitle or other intro animations here.
        pass

    def step_explore(self):
        # Your main animation logic goes here.
        # Use self.t("English", "Arabic") for bilingual text.
        prompt = self.t("Let's explore!", "هيا نستكشف!")
        self.play(Write(prompt))
        self.wait()
        self.play(FadeOut(prompt))

    def step_outro(self):
        # A concluding summary or recap.
        recap = self.t("Well done!", "أحسنت!")
        self.play(Write(recap))
        self.wait()
        self.play(FadeOut(recap))

```

## 4. Running the Lesson

To render your lesson, use the following command, replacing `YourLessonScene` with the name of your scene class:

```bash
manim -pqh YOUR_FILE_NAME.py YourLessonScene
```
