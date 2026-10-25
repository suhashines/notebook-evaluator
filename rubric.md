---
assignment: "Lab 2 — Polynomial Interpolation"
total_marks: 8
mark_increment: 0.5
tasks:
  - id: CW1
    phase: classwork
    title: "Polynomial evaluation using a list"
    max_marks: 1.0
    evidence_hints: ["coefficient list", "scalar evaluation", "evaluation for multiple x values"]
  - id: CW2
    phase: classwork
    title: "Polynomial class"
    max_marks: 1.5
    evidence_hints: ["__init__", "__call__", "__repr__", "get_degree", "get_coeffs"]
  - id: CW3
    phase: classwork
    title: "Vandermonde interpolation function"
    max_marks: 1.5
    evidence_hints: ["get_poly", "Vandermonde matrix", "pseudoinverse or equivalent linear solve", "Polynomial object"]
  - id: ST1
    phase: self_task
    title: "Evaluate the three-node interpolating polynomial"
    max_marks: 1.0
    evidence_hints: ["three supplied nodes", "get_poly", "evaluation at the requested x"]
  - id: ST2
    phase: self_task
    title: "Evaluate and plot the five-node interpolating polynomial"
    max_marks: 1.0
    evidence_hints: ["five nodes", "get_poly", "requested evaluation", "blue polynomial curve", "yellow star data markers"]
  - id: ST3
    phase: self_task
    title: "Second five-node interpolation task"
    max_marks: 1.0
    evidence_hints: ["five nodes or clearly assigned variant", "get_poly", "requested evaluation", "plot range includes all data points", "blue polynomial curve", "yellow star data markers"]
  - id: ST4
    phase: self_task
    title: "Compare two interpolating polynomials"
    max_marks: 1.0
    evidence_hints: ["two polynomials", "degree and coefficients", "average absolute coefficient values", "choose polynomial with higher average", "evaluate supplied x list"]
---

# Lab 2 — Polynomial Interpolation: Grading Rubric

**Total: 8 marks** — Classwork: 4 marks; Self-task: 4 marks.

The YAML front matter above is the machine-readable source of task IDs and maximum marks. Keep it synchronized with the criteria below whenever the rubric is edited.

## General grading policy

- Assess code and saved outputs; do not execute student notebooks.
- Correct alternative implementations receive credit even if they differ from the reference.
- Missing output or an unexecuted cell is not a deduction by itself when the code is correct.
- Award partial credit only for a requirement demonstrably satisfied by the code/output.
- Beginner-level syntax or API mistakes may receive partial credit when intent and meaningful progress are evident. A logically incorrect implementation receives no credit for the requirement it fails.
- Do not deduct for harmless style, variable names, comments, or different valid data structures.
- Marks must be between zero and the task maximum and use increments of 0.5.
- If task identity or the expected variant cannot be established, flag for manual review instead of inventing a requirement.

## Classwork (4 marks)

### CW1 — Polynomial evaluation using a list (1 mark)
Assess whether the student uses the coefficient list and polynomial degree to evaluate the polynomial for a scalar x and for multiple x values. Correct accumulation over coefficient powers earns credit. A loop-based or otherwise valid equivalent approach is acceptable.

Suggested partial-credit interpretation:
- 1.0: both scalar and multiple-value evaluation are correct.
- 0.5: one of the two parts is correct, or the approach is mostly correct with a minor implementation issue.
- 0.0: no meaningful correct evaluation logic.

### CW2 — Polynomial class (1.5 marks)
Assess the class components shown in the template:
- 0.25: constructor stores coefficients and initializes degree consistently.
- 0.50: `__call__` evaluates the polynomial for one or more x values correctly.
- 0.25: `__repr__` or equivalent string representation describes the polynomial and its degree.
- 0.25: `get_degree()` returns the degree correctly.
- 0.25: `get_coeffs()` returns the coefficients correctly.

The final mark must still use 0.5 increments. The subcriteria guide the judge; do not output fractional quarter-marks. Combine evidence into the nearest rubric-supported half-mark, never exceeding 1.5.

### CW3 — Vandermonde interpolation function (1.5 marks)
Assess whether `get_poly(data_x, data_y)`:
- constructs a Vandermonde matrix with row i containing powers of `data_x[i]` from zero through the required degree;
- obtains coefficients by a mathematically appropriate solution method (pseudoinverse, inverse when appropriate, or a suitable linear solver);
- returns a usable polynomial object consistent with the student's class.

Equivalent vectorized code is acceptable. Printing the matrix is not required for full credit.

## Self-task (4 marks)

Each task is worth 1 mark. Judge the implementation and any available saved outputs against the task requirements in the solution notebook and any task-specific statement in the student notebook.

### ST1 — Three-node interpolation (1 mark)
Use the three supplied nodes with `get_poly` and print/produce the polynomial value at the requested x (x = 3 in the reference task). Correct method use and correct evaluation are the core criteria.

### ST2 — Five-node interpolation and plot (1 mark)
Use the five-node dataset (or a clearly assigned student-specific variant), evaluate at the requested x, and plot the interpolating polynomial and data points. The reference requests a blue polynomial curve and yellow star markers. Award partial credit when evaluation is correct but plotting is missing or materially incorrect.

### ST3 — Second five-node interpolation task (1 mark)
The reference notebook repeats the wording of ST2. Treat ST3 as a separate required task, using its corresponding student task/variant where available. Assess the interpolation, requested evaluation, and plot. The plot range should include all data points, the polynomial curve should be blue, and data points should be yellow stars. Because the reference prompt is duplicated, flag manual review if the student task variant cannot be determined confidently.

### ST4 — Compare two polynomials (1 mark)
Assess whether the student:
- constructs both polynomials from the two supplied node sets;
- reports each polynomial's degree and coefficients;
- calculates the average of the absolute coefficient values for each polynomial;
- selects the polynomial with the larger average and evaluates it at all supplied x values.

Award partial credit for correct subparts. Do not accept `abs(sum(coefficients))/n` as equivalent to `mean(abs(coefficients))`; the absolute value must be applied to each coefficient before averaging. The denominator must include every coefficient.

## Manual-review triggers

Flag the relevant task if:
- a task is missing or its mapping is ambiguous;
- the student's inputs differ from the reference and there is no clear student-specific prompt to explain the variant;
- judge and verifier materially disagree;
- the notebook is malformed or identity cannot be reliably extracted;
- evidence is insufficient to distinguish an API/syntax issue from a logical error.

Do not flag solely because an output is absent when the code itself provides sufficient evidence.
