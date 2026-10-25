# Local Jupyter Notebook Evaluator

A rubric-driven, non-executing notebook grading pipeline. It reads student `.ipynb` files directly, extracts code and saved outputs, asks an LLM for a structured assessment, verifies the assessment, validates marks in Python, and exports CSV/XLSX.

## Project layout

```text
notebook-evaluator/
├── AGENTS.md
├── agent.md
├── notebooks/                 # student notebooks
├── rubric.md                  # authoritative rubric
├── solution.ipynb             # reference solution
├── config/evaluator.yaml
├── src/notebook_evaluator/
├── tests/
├── artifacts/
└── results/
```

## Important safety note

Student notebooks are never executed. Notebook outputs are read only from saved cell outputs. Parsing a notebook does not execute code.

## Setup

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

pip install -e ".[dev]"
cp .env.example .env
```

Edit `.env` and `config/evaluator.yaml`. Keep `.env` private.

### Model connection

The default adapter is OpenAI-compatible HTTP. For an OpenRouter-compatible endpoint, set:
- `LLM_API_KEY` to your API key
- `LLM_BASE_URL` to `https://openrouter.ai/api/v1`
- `LLM_MODEL` to the model identifier your account can access

The configured model default is `nvidia/nemotron-3-ultra-550b-a55b:free`, but model availability, context limits, and free-tier conditions are controlled by the provider and may change.

If Hermes is the layer that must mediate model requests in your setup, use a command/API adapter supported by your installed Hermes version. Do not guess CLI flags: confirm the invocation supported by your installation before changing `llm_client.py`. The evaluator's grading workflow itself is independent of the agent interface.

## Run

From the project root:

```bash
notebook-evaluator inspect
notebook-evaluator evaluate --dry-run
notebook-evaluator evaluate
notebook-evaluator export
```

`inspect` prints discovered notebooks and parsed identity. `evaluate --dry-run` writes normalized notebook JSON but makes no model calls. A full evaluation requires a configured API key and endpoint.

To explicitly choose inputs:

```bash
notebook-evaluator evaluate \
  --notebooks notebooks \
  --rubric rubric.md \
  --solution solution.ipynb \
  --config config/evaluator.yaml
```

## Batch and context behavior

The default batch size is 2. Requests are independent HTTP requests; there is no shared model conversation context to clear between batches. Completed results are checkpointed. A rerun skips validated completed records unless `--force` is supplied. This gives automatic isolation and avoids manual `/new` commands.

If you configure a stateful Hermes conversation adapter instead, that adapter must create an isolated session per judge/verifier call or explicitly reset state using a documented Hermes interface.

## Marking rules

- Classwork: 4 marks total.
- Self-task: 4 marks total, four tasks worth 1 mark each.
- Overall: 8 marks.
- Marks use 0.5 increments.
- No execution of submissions.
- Missing output alone is not penalized.
- Ambiguous task mapping and judge/verifier disagreements are flagged.

## Outputs

- `results/grades.csv`: one row per student, task mark/reason columns, total, review flag.
- `results/grades.xlsx`: `Grades` and `Audit` worksheets.
- `artifacts/normalized/`: parsed notebook JSON.
- `artifacts/grading_records/`: per-student judge/verifier records and checkpoint state.
- `artifacts/logs/`: application logs.

## Rubric note

The reference notebook repeats the same prompt for Self-task 2 and Self-task 3, while student notebooks may use different node sets or target x-values. The evaluator should judge the corresponding task code against the general task requirements and flag ambiguous prompt/data mismatches for manual review rather than silently assume every input value must match the reference.

## Testing

```bash
pytest
```

Before grading all submissions, compare the pilot grades for the supplied sample notebook with instructor-assigned marks.
