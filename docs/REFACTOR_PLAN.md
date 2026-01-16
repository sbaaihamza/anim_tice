# Refactor Plan: Inventory and Risks

This document provides a high-level inventory of the codebase, identifies duplication hotspots and architectural risks, and justifies the need for refactoring.

## 1. Dependency Graph / Module Map

The repository is a flat collection of Python scripts with no internal modules.

- **Core Dependency:** All scripts depend externally on the `manim` library.
- **Internal Dependencies:** There are **no internal dependencies** between the lesson scripts. Each file is completely standalone.
- **Execution:** Each script is an independent entrypoint, run via the `manim` command-line tool.

This structure is simple but leads to significant code duplication, as common patterns are not shared.

## 2. Top Duplication Hotspots

The "copy-paste" nature of the scripts has created several hotspots where the same logic is repeated.

1.  **Style Configuration (`@dataclass`)**
    - **Description:** Almost every script defines a `@dataclass` for styling (e.g., `RulerLessonStyle`, `FractionStyle`). These classes share numerous common fields like `font_size_title`, `font_size_main`, `pause`, and animation runtimes (`rt_fast`, `rt_norm`).
    - **Evidence:**
        - `M3_G05_Ruler_Construct_Segments_And_Lines.py`
        - `M3_L04_FractionsRepresentationAndReading.py`

2.  **Lesson Configuration (`@dataclass`)**
    - **Description:** Each script has a configuration dataclass (e.g., `LessonConfigM3_G05`) that contains metadata like `title_en`, `title_ar`, and `language`. This is a common requirement for all lessons.
    - **Evidence:**
        - `M3_G05_Ruler_Construct_Segments_And_Lines.py`
        - `M3_L04_FractionsRepresentationAndReading.py`

3.  **Scene Initialization (`__init__`)**
    - **Description:** The `__init__` method for each `Scene` subclass is identical, accepting `cfg` and `style` objects and assigning them to `self`.
    - **Evidence:**
        - `M3_G05_Ruler_Construct_Segments_And_Lines.py`
        - `M3_L04_FractionsRepresentationAndReading.py`

4.  **Title Banner Helper (`banner`)**
    - **Description:** A helper method named `banner` that positions a title `Mobject` at the top of the screen is redefined in every script.
    - **Evidence:**
        - `M3_G05_Ruler_Construct_Segments_And_Lines.py`
        - `M3_L04_FractionsRepresentationAndReading.py`

5.  **Bilingual Text Helpers (`_prompt` or `t`)**
    - **Description:** Logic for selecting text based on the configured language (`en` or `ar`) is implemented in slightly different ways (`_prompt` vs. `t`) but serves the exact same purpose.
    - **Evidence:**
        - `M3_G05_Ruler_Construct_Segments_And_Lines.py` (see `_prompt`)
        - `M3_L04_FractionsRepresentationAndReading.py` (see `t`)

## 3. Top Architectural Risks & Tech Debt

The current architecture poses several risks to maintainability and scalability.

1.  **High Maintenance Overhead**
    - **Description:** A simple change, like adjusting the default font size or animation speed, requires manually editing every single file in the repository. This is time-consuming and prone to human error.
    - **Evidence:** Any shared value in the Style/Config dataclasses across all `.py` files.

2.  **Risk of Inconsistency**
    - **Description:** Without a single source of truth for styles and configurations, new or modified lessons can easily diverge from the established look and feel, leading to an inconsistent user experience.
    - **Evidence:** The presence of separate, duplicated Style dataclasses in each file.

3.  **Poor Reusability and Abstraction**
    - **Description:** Common animation logic (e.g., displaying a title, managing a sequence of steps) is not abstracted. This makes it difficult to reuse patterns or add cross-cutting features like a global progress bar or consistent logging.
    - **Evidence:** The `construct` method in each scene has a nearly identical structure that is implemented via copy-paste.

4.  **No Centralized Control**
    - **Description:** There is no central place to manage lesson-wide settings, themes, or features. For example, adding a new language would require changes to every file.
    - **Evidence:** The `language` attribute is defined independently in each lesson's configuration dataclass.

5.  **Difficult Onboarding**
    - **Description:** To create a new lesson, a developer must find an existing script, copy it, and carefully modify it. There is no clear template or base class to inherit from, increasing the learning curve.
    - **Evidence:** The lack of a shared `src` directory or `core` module.

## 4. Next PR Checklist

- [ ] Create `docs/BASECLASS_API.md` to propose a new base class that will address these issues.
- [ ] Implement the new base class in a separate `src` directory.
- [ ] Refactor one or two existing lessons to use the new base class.
