# Architecture Map

This document maps the current architecture of the `anim_tice` repository.

## 1. Repository Goal

The repository's goal is to create educational math animations using the `manim` library. Each Python script in the root directory corresponds to a specific math lesson and generates a video file.

## 2. Entrypoints

The primary entrypoints are individual Python scripts in the root directory. Each script is a self-contained `manim` animation that can be executed from the command line.

- **Examples:**
  - `M3_G05_Ruler_Construct_Segments_And_Lines.py`
  - `M3_L04_FractionsRepresentationAndReading.py`
  - `M3_N09_multiplication_tables_6_7.py`

## 3. Core Modules and Packages

The repository does not have a formal package structure. All scripts are standalone and reside in the root directory.

- **Core Library:** `manim` is the core dependency, providing the animation framework.
- **Data Classes:** Each script uses dataclasses for configuration (`LessonConfig`) and styling (`Style`).

## 4. Key Classes and Relationships

- **`manim.Scene`:** The base class for all animations. Each script subclasses `manim.Scene` to create a lesson-specific animation.
- **Custom Classes:** Some scripts define reusable components, such as the `Ruler` class in `M3_G05_Ruler_Construct_Segments_And_Lines.py`.

## 5. Cross-Cutting Concerns

- **Configuration:** Each script defines its own dataclasses for configuration, leading to duplication of fields like `language`, `font_size`, and `pause`.
- **Styling:** Similar to configuration, styling is handled by dedicated dataclasses within each script, resulting in repeated style definitions.
- **Orchestration:** The `construct` method in each `Scene` subclass follows a similar pattern of calling `step_` methods in sequence.
- **Text Management:** Helper functions for language-specific text rendering are defined in multiple scripts.

## 6. Duplication and "Same Logic"

- **`LessonConfig` and `Style` Dataclasses:** These are nearly identical across all scripts, with minor variations.
- **`banner` method:** This helper method for positioning titles is redefined in every script.
- **`construct` method:** The orchestration logic is structurally the same in all animations.
- **Helper Functions:** Functions for creating text and other `manim` objects are duplicated.

## 7. Next PR Checklist

- [ ] Create `docs/REFACTOR_PLAN.md` to identify duplication hotspots and architectural risks.
- [ ] Create `docs/BASECLASS_API.md` to propose a new base class API.
