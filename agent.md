# Project Agent Guide

Use `AGENTS.md` as the primary project instruction file. This file is included for tools or workflows that look specifically for `agent.md`.

Before running grading:
- Verify `rubric.md` task IDs and maxima.
- Verify the input folder and reference notebook.
- Confirm the model adapter and credentials are configured.
- Run parser tests and a dry run first.
- Review manual-review flags before using final grades.

Never execute student notebooks. Keep each student's grade independent of other students' identities and submissions. The verifier must assess evidence and rubric alignment; it must not simply average a second score with the first.
