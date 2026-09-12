---
name: cumcm-assistant
description: Use when preparing for or working on CUMCM mathematical modeling problems, including problem analysis, model selection, Python or MATLAB implementation, result validation, award-feature review, paper structure, submission compliance, citations, or AI-use disclosure.
---

# CUMCM Assistant

## Overview

Build a traceable chain from problem statement to data, model, code, validation, paper, and submission package. Treat award patterns as review heuristics, never as permission to imitate a paper or skip independent verification.

## 官方规则优先

For compliance-sensitive work, read only these first:

- `references/compliance/2026-rules.md`
- `references/compliance/2026-paper-format.md`
- `references/compliance/2026-ai-use.md`
- `references/compliance/submission-checklist.md`

Use official facts exactly as sourced. Separate official rules, paper observations, and analytical inferences. Refuse requests to hide AI use: 不得隐瞒、伪造或删减实质性 AI 使用记录。

## Intent routing

Run `python scripts/route_intent.py <intent> --prompt "..."` when routing is uncertain. Load the returned resources only; never load every reference.

| Intent | Use for |
|---|---|
| `analyze-problem` | Classify the problem, inputs, outputs, constraints, and evidence needs |
| `select-model` | Compare candidate models and choose using explicit criteria |
| `implement-python` | Use the tested Python library and project assets |
| `implement-matlab` | Use the MATLAB mirror library and project assets |
| `validate-results` | Backtest, diagnose, perturb, and review award-linked evidence |
| `draft-structure` | Build an anonymous result-led paper structure and figures |
| `check-submission` | Run objective paper, citation, code, AI, and package checks |
| `record-ai-use` | Record tool/model, purpose, prompting approach, process, adoption, manual edits, and human verification |

## 核心工作流

1. Read `references/workflows/problem-intake.md`; rewrite each subproblem as inputs, outputs, constraints, metric, and deliverable.
2. Read one matching problem-type card and the smallest relevant method set. Audit data before modeling.
3. Compare a baseline and at least one serious candidate. Record assumptions, identifiability, complexity, failure modes, and selection evidence.
4. Implement through `assets/code/` or copy `assets/project/`; preserve seeds, paths, units, and result manifests.
5. Read `references/workflows/result-validation.md`; require holdout/backtest evidence plus sensitivity or scenario checks before accepting conclusions.
6. Draft only after validation. Copy `assets/paper/` and use `assets/figures/`; keep claims tied to tables, figures, equations, or registered sources.
7. Run `python scripts/check_submission.py <project>` and complete the official checklist. Put the AI-use declaration before the references; when AI was used, record the required fields and export `AI工具使用详情.pdf`. Typical prompt/response examples are optional.

## Evidence contract

- Cite source IDs and keep a source record for external facts and parameters.
- Label official requirements, observable paper features, and synthesis/inference distinctly.
- Report failed diagnostics and uncertainty, not only the best run.
- Do not assert MATLAB execution unless the runtime test actually ran.
- Do not turn award frequency into causality; use `references/award-patterns/award-patterns.md` as a final review lens.

## Example

For “seasonal demand prediction,” route `analyze-problem`, read the prediction card and time-series method card, audit timestamps and leakage, compare seasonal naive and fitted candidates, backtest on held-out windows, then draft quantified conclusions.

## Common mistakes

- Choosing a sophisticated model before defining the target metric.
- Using test data during preprocessing or model selection.
- Reporting one optimal value without feasibility, sensitivity, or units.
- Copying templates without replacing placeholders or checking anonymity.
- Treating checker PASS as proof of mathematical correctness.
