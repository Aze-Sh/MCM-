# CUMCM 2026 Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a source-traceable CUMCM 2026 repository containing recent-problem and award-feature analysis, a method library, Python/MATLAB implementations, competition workflows, templates, checkers, validation steps, and an installable `cumcm-assistant` Skill.

**Architecture:** Treat research notes and method cards as canonical human-readable knowledge. Put deterministic Python code in `code/python/cumcm_py`, MATLAB code in `code/matlab/+cumcm`, and compare both languages with shared fixtures. Generate the self-contained Skill bundle from canonical repository content and reject drift with hash-based validation.

**Tech Stack:** Markdown, YAML, JSON Schema, BibTeX, Python 3.10+, pytest, NumPy, pandas, SciPy, statsmodels, scikit-learn, NetworkX, OR-Tools, SimPy, SALib, Matplotlib, seaborn, PyYAML, Pydantic, pypdf, Pillow, MATLAB with available Optimization/Statistics/Curve Fitting/Econometrics toolboxes, XeLaTeX.

## Global Constraints

- Read and audit every source in Appendix A to the legally accessible depth; record `full-read`, `partial-read`, `metadata-only`, `blocked`, or `dead-link` truthfully.
- Analyze every publicly available 2021—2025 CUMCM problem; give 2023—2025 deeper per-problem treatment.
- Separate official evaluation, directly observable paper features, and analytical inference; never state inferred award causality as official fact.
- Do not perform complete historical-problem reproduction and do not run mock contests.
- Keep copyrighted or login-restricted originals out of Git; store only metadata, lawful excerpts within quotation limits, paraphrases, and private-path references.
- Rules and format requirements must come from official A-level sources and record the source ID and effective date.
- Method descriptions are canonical; Python and MATLAB implementations share fixtures and must agree on key properties within declared tolerances.
- Every deterministic script must have positive and negative tests. Every checker must emit machine-readable JSON plus a concise human summary.
- Preserve AI-use transparency, citations, source provenance, and code-license records.
- Keep `skill/cumcm-assistant/SKILL.md` below 500 lines and load references progressively.
- Do not add a web application, database server, notebook platform, automatic full-paper writer, or similarity-evasion feature.

---

## Target File Map

```text
README.md
pyproject.toml
environment/compatibility.md
schemas/{source,reading-note,problem-card,evidence,method-card}.schema.json
sources/{catalog.yaml,references.bib,reading-notes/}
rules/{2026-rules.md,2026-paper-format.md,2026-ai-use.md,submission-checklist.md}
cases/2021-2025/<year>/<problem>.{yaml,md}
knowledge/{award-patterns.md,model-selection.md,problem-types/,methods/}
code/fixtures/
code/python/cumcm_py/{types,preprocess,fit,forecast,optimization,graph,simulation,dynamics,decision,ml,sensitivity,plotting}.py
code/matlab/+cumcm/*.m
workflows/*.md
templates/{project,paper,figures,citations,ai-usage}/
checkers/rules/*.yaml
code/python/cumcm_checkers/*.py
validation/*.md
tools/{audit_sources,validate_content,compare_outputs,build_skill_bundle,verify_repository}.py
tests/{content,python,matlab,checkers,skill,fixtures}/
skill/cumcm-assistant/{SKILL.md,agents/openai.yaml,references,scripts,assets}
```

## Shared Interfaces

These names are fixed across tasks.

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, Sequence

ReadStatus = Literal[
    "full-read", "partial-read", "metadata-only", "blocked", "dead-link"
]
EvidenceKind = Literal["official", "observable", "inference"]

@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: Literal["error", "warning", "info"]
    message: str
    path: str | None = None
    source_ids: tuple[str, ...] = ()

@dataclass(frozen=True)
class CheckReport:
    checker: str
    passed: bool
    issues: tuple[ValidationIssue, ...]
    metadata: Mapping[str, Any]

@dataclass(frozen=True)
class ModelResult:
    method: str
    values: Mapping[str, Any]
    diagnostics: Mapping[str, Any]
    assumptions: tuple[str, ...]
```

All checkers implement:

```python
def run_check(target: Path, config: Mapping[str, Any]) -> CheckReport: ...
```

All command-line tools exit `0` when no error-level issue exists, and `1` otherwise.

---

### Task 1: Establish the repository contract and executable skeleton

**Files:**
- Create: `README.md`
- Create: `pyproject.toml`
- Create: `.editorconfig`
- Create: `environment/compatibility.md`
- Create: `code/python/cumcm_py/__init__.py`
- Create: `code/python/cumcm_py/types.py`
- Create: `tools/__init__.py`
- Create: `tests/python/test_imports.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces: the shared dataclasses shown above and a repository-local editable Python package.
- Produces: documented commands `python -m pytest`, `matlab -batch "results=runtests('tests/matlab'); assertSuccess(results)"`, and `xelatex`.

- [ ] **Step 1: Write the package import test**

```python
from cumcm_py.types import CheckReport, ModelResult, ValidationIssue

def test_shared_types_are_importable() -> None:
    assert CheckReport.__name__ == "CheckReport"
    assert ModelResult.__name__ == "ModelResult"
    assert ValidationIssue.__name__ == "ValidationIssue"
```

- [ ] **Step 2: Run the isolated import test**

Run: `python -m pytest tests/python/test_imports.py -v`

Expected: FAIL because `cumcm_py` does not exist.

- [ ] **Step 3: Create the package and root configuration**

Use the fixed dataclasses from “Shared Interfaces” in `types.py`. Configure `pyproject.toml` with `package-dir = {"" = "code/python"}`, pytest paths, UTF-8, and explicit dependencies. Put optional heavy dependencies and MATLAB toolboxes in documented extras rather than silently requiring them.

- [ ] **Step 4: Record the actual local environment**

Run:

```powershell
python --version
python -m pip --version
matlab -batch "disp(version); ver"
xelatex --version
```

Record command, detected version, availability, and date in `environment/compatibility.md`. If a program is absent, record `unavailable` and keep its tests explicitly skipped with the reason.

- [ ] **Step 5: Install editable Python dependencies and rerun the test**

Run: `python -m pip install -e ".[test]"`

Run: `python -m pytest tests/python/test_imports.py -v`

Expected: PASS.

- [ ] **Step 6: Commit the repository contract**

```powershell
git add README.md pyproject.toml .editorconfig .gitignore environment code/python tests/python/test_imports.py
git commit -m "build: establish CUMCM repository contract"
```

---

### Task 2: Define source, reading-note, evidence, problem-card, and method-card schemas

**Files:**
- Create: `schemas/source.schema.json`
- Create: `schemas/reading-note.schema.json`
- Create: `schemas/evidence.schema.json`
- Create: `schemas/problem-card.schema.json`
- Create: `schemas/method-card.schema.json`
- Create: `sources/catalog.yaml`
- Create: `sources/references.bib`
- Create: `code/python/cumcm_py/content.py`
- Create: `tests/content/test_schemas.py`
- Create: `tests/fixtures/content/invalid-source.yaml`

**Interfaces:**
- Produces: `load_yaml(path: Path) -> Any`.
- Produces: `validate_document(path: Path, schema_path: Path) -> tuple[ValidationIssue, ...]`.
- Consumes: Appendix A source IDs and URLs.

- [ ] **Step 1: Write schema-validation tests**

```python
from pathlib import Path
from cumcm_py.content import validate_document

def test_catalog_matches_source_schema() -> None:
    issues = validate_document(
        Path("sources/catalog.yaml"), Path("schemas/source.schema.json")
    )
    assert issues == ()

def test_invalid_source_reports_missing_read_status() -> None:
    issues = validate_document(
        Path("tests/fixtures/content/invalid-source.yaml"),
        Path("schemas/source.schema.json"),
    )
    assert any(issue.code == "schema.required" for issue in issues)
```

- [ ] **Step 2: Run tests and observe the missing implementation**

Run: `python -m pytest tests/content/test_schemas.py -v`

Expected: FAIL because schemas and `cumcm_py.content` do not exist.

- [ ] **Step 3: Implement strict schemas**

Require source IDs, locator, authority level, read status, access status, license status, access date, coverage statement, repository targets, and evidence locations. Require `url` for web sources; allow a bibliographic citation or local identifier as the locator for non-web leads. Set `additionalProperties: false` so spelling errors cannot silently pass.

- [ ] **Step 4: Seed the catalog with every Appendix A source**

Create one entry per source ID. Initial read status must reflect evidence already held: use `full-read` only for a complete page or document actually read; use `partial-read` for broad documentation where only relevant sections were audited; use `metadata-only`, `blocked`, or `dead-link` when appropriate.

- [ ] **Step 5: Implement `load_yaml` and `validate_document`**

Map JSON Schema validation paths into `ValidationIssue.path`; use `schema.required`, `schema.enum`, and `schema.type` codes.

- [ ] **Step 6: Run content tests**

Run: `python -m pytest tests/content/test_schemas.py -v`

Expected: both tests PASS.

- [ ] **Step 7: Commit schemas and seed inventory**

```powershell
git add schemas sources/catalog.yaml sources/references.bib code/python/cumcm_py/content.py tests/content tests/fixtures/content
git commit -m "feat: add source and knowledge schemas"
```

---

### Task 3: Audit official competition rules and create compliance notes

**Files:**
- Create: `sources/reading-notes/OFF-CUMCM-HOME.md`
- Create: `sources/reading-notes/OFF-CUMCM-CHARTER.md`
- Create: `sources/reading-notes/OFF-CUMCM-2026-NOTICE.md`
- Create: `sources/reading-notes/OFF-CUMCM-2026-RULES.md`
- Create: `sources/reading-notes/OFF-CUMCM-2026-FORMAT.md`
- Create: `sources/reading-notes/OFF-CUMCM-2026-FORMAT-MIRROR.md`
- Create: `sources/reading-notes/OFF-CUMCM-AI-RULES.md`
- Create: `sources/reading-notes/OFF-CUMCM-AI-RULES-EN.md`
- Create: `sources/reading-notes/OFF-CUMCM-AI-RULES-OLD-DEAD.md`
- Create: `sources/reading-notes/OFF-CUMCM-NATIONAL-JUDGING.md`
- Create: `sources/reading-notes/OFF-CUMCM-REGIONAL-JUDGING.md`
- Create: `rules/2026-rules.md`
- Create: `rules/2026-paper-format.md`
- Create: `rules/2026-ai-use.md`
- Create: `rules/submission-checklist.md`
- Create: `tests/content/test_rules_provenance.py`

**Interfaces:**
- Consumes: source catalog entries prefixed `OFF-CUMCM`.
- Produces: rule statements ending with one or more source IDs and an effective date.

- [ ] **Step 1: Write the provenance test**

```python
from pathlib import Path
import re

RULE_FILES = sorted(Path("rules").glob("*.md"))

def test_every_normative_rule_has_source_id() -> None:
    assert RULE_FILES
    for path in RULE_FILES:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("- 必须") or line.startswith("- 禁止"):
                assert re.search(r"\[OFF-CUMCM-[A-Z0-9-]+\]$", line), (path, line)
```

- [ ] **Step 2: Read every accessible official rules source completely**

For each source, record publication date, access date, exact relevant section, paraphrased requirement, direct-quotation snippets within copyright limits, conflicts, and confidence. Cross-check the accessible Chinese mirror and English AI-rules page; record the old dead Chinese URL without treating it as active.

- [ ] **Step 3: Write four normalized compliance documents**

Keep official requirements separate from team recommendations. Express page count, anonymity, source-code attachment, file-size, AI disclosure, during-contest communication, and external-source citation requirements with source IDs.

- [ ] **Step 4: Run rule provenance tests**

Run: `python -m pytest tests/content/test_rules_provenance.py -v`

Expected: PASS, with every normative bullet traceable.

- [ ] **Step 5: Update catalog read states and commit**

```powershell
git add sources/catalog.yaml sources/reading-notes/OFF-CUMCM-* rules tests/content/test_rules_provenance.py
git commit -m "docs: audit 2026 competition rules"
```

---

### Task 4: Audit courses, books, technical documentation, data sources, and literature tools

**Files:**
- Create: one `sources/reading-notes/<SOURCE-ID>.md` for every exact `COURSE`, `BOOK`, `PYDOC`, `MATLABDOC`, `DATA`, `LITERATURE`, and `PAPER` ID in Appendix A
- Create: `sources/learning-map.md`
- Create: `sources/data-source-guide.md`
- Create: `tests/content/test_catalog_notes.py`

**Interfaces:**
- Consumes: Appendix A source groups `COURSE`, `BOOK`, `PYDOC`, `MATLABDOC`, `DATA`, and `LITERATURE`.
- Produces: one reading note per catalog entry and a method-family-to-source map.

- [ ] **Step 1: Write the catalog-note coverage test**

```python
from pathlib import Path
import yaml

def test_every_learning_or_data_source_has_a_note() -> None:
    entries = yaml.safe_load(Path("sources/catalog.yaml").read_text(encoding="utf-8"))["sources"]
    for entry in entries:
        audited_group = entry["id"].split("-", 1)[0] in {
            "COURSE", "BOOK", "PYDOC", "MATLABDOC", "DATA", "LITERATURE", "PAPER"
        }
        if audited_group and entry["read_status"] not in {"blocked", "dead-link"}:
            note = Path("sources/reading-notes") / f'{entry["id"]}.md'
            assert note.exists(), entry["id"]
```

- [ ] **Step 2: Audit course and book material**

Read public course descriptions, syllabi, visible lessons, textbook metadata, preview material, and companion-resource descriptions. Do not mark a paid book `full-read` unless its complete lawful text was available and read. Extract only what changes repository coverage or method priorities.

- [ ] **Step 3: Audit official Python and MATLAB documentation**

For broad documentation sites, inspect the relevant APIs and examples for the selected method library and mark `partial-read` with exact section coverage. Record stable APIs, version sensitivity, solver/toolbox requirements, and official examples that can seed fixtures.

- [ ] **Step 4: Audit data and literature sources**

Record access method, authentication, license/attribution, geographic and temporal coverage, rate limits, export format, and reliability caveats. Separate authoritative data providers from community-hosted datasets.

- [ ] **Step 5: Build the learning and data-source maps**

`sources/learning-map.md` must map each of the 11 method families to primary course/book sections and official technical documentation. `sources/data-source-guide.md` must map common CUMCM data needs to recommended primary sources and fallback sources.

- [ ] **Step 6: Run coverage and schema tests**

Run: `python -m pytest tests/content/test_catalog_notes.py tests/content/test_schemas.py -v`

Expected: PASS for every accessible catalog source.

- [ ] **Step 7: Commit audited learning resources**

```powershell
git add sources/catalog.yaml sources/reading-notes sources/learning-map.md sources/data-source-guide.md tests/content/test_catalog_notes.py
git commit -m "docs: audit learning and data resources"
```

---

### Task 5: Audit third-party Skills, repositories, templates, and licenses

**Files:**
- Create: one `sources/reading-notes/<SOURCE-ID>.md` for every exact `REPO` ID in Appendix A
- Create: `sources/repository-audit.md`
- Create: `sources/license-policy.md`
- Create: `tests/content/test_repository_audit.py`

**Interfaces:**
- Consumes: Appendix A `REPO` entries.
- Produces: `adopt`, `adapt-with-attribution`, `structure-only`, or `reject` disposition for every repository.

- [ ] **Step 1: Write the disposition test**

```python
from pathlib import Path

def test_repository_audit_has_one_disposition_per_repo() -> None:
    text = Path("sources/repository-audit.md").read_text(encoding="utf-8")
    for source_id in (
        "REPO-XIAOMA-SKILL", "REPO-LUPYNOW-SKILLS", "REPO-YOKI-SINGLE",
        "REPO-CUMCMTHESIS", "REPO-CUMCM-LATEX", "REPO-GITEE-CUMCM",
    ):
        assert source_id in text
        block = text.split(source_id, 1)[1].split("## ", 1)[0]
        assert any(value in block for value in (
            "adopt", "adapt-with-attribution", "structure-only", "reject"
        ))
```

- [ ] **Step 2: Inspect each repository**

Read the top-level documentation, directory structure, recent activity, license file, dependencies, tests, and representative code. Record commit or release observed. Do not copy code from a repository whose license is missing or unclear.

- [ ] **Step 3: Compare repository ideas against official rules**

Flag outdated format assumptions, nontransparent AI practices, hard-coded paths, unverified algorithms, missing tests, and current-problem browsing risks. Record useful structural ideas without importing assets until the disposition permits it.

- [ ] **Step 4: Write license and reuse policy**

Define required attribution metadata, vendoring rules, modification notices, and rejection criteria. Make the official 2026 format source authoritative over all community templates.

- [ ] **Step 5: Run the audit test and commit**

Run: `python -m pytest tests/content/test_repository_audit.py -v`

```powershell
git add sources/catalog.yaml sources/reading-notes/REPO-* sources/repository-audit.md sources/license-policy.md tests/content/test_repository_audit.py
git commit -m "docs: audit modeling repositories and licenses"
```

---

### Task 6: Create the 2021—2025 problem-card and award-evidence corpus

**Files:**
- Create: `cases/2021-2025/index.yaml`
- Create: `cases/2021-2025/<year>/<problem>.yaml`
- Create: `cases/2021-2025/<year>/<problem>.md`
- Create: `cases/2021-2025/<year>/award-papers.yaml`
- Create: `sources/reading-notes/OFF-CUMCM-PROBLEM-ARCHIVE.md`
- Create: `sources/reading-notes/OFF-CUMCM-2025-PROBLEMS.md`
- Create: `sources/reading-notes/OFF-CUMCM-2025-REVIEW.md`
- Create: `sources/reading-notes/OFF-CUMCM-COMMENTARY-HUB.md`
- Create: `sources/reading-notes/OFF-CUMCM-2023-COMMENTARY.md`
- Create: `sources/reading-notes/OFF-CUMCM-2023-PAPERS.md`
- Create: `sources/reading-notes/OFF-CUMCM-2023-PAPER-A.md`
- Create: `sources/reading-notes/OFF-CUMCM-2023-PAPER-C050.md`
- Create: `sources/reading-notes/OFF-CUMCM-2023-MULTI-LEARNING.md`
- Create: `sources/reading-notes/SECONDARY-CUMCM-PAPERS-2010-2025.md`
- Create: `code/python/cumcm_py/cases.py`
- Create: `tests/content/test_problem_cards.py`

**Interfaces:**
- Produces: `load_problem_card(path: Path) -> Mapping[str, Any]`.
- Produces: `validate_evidence_links(card: Mapping[str, Any], catalog: Mapping[str, Any]) -> tuple[ValidationIssue, ...]`.
- Requires: one card for every publicly available A—E problem in 2021—2025.

- [ ] **Step 1: Write evidence-link tests**

```python
from pathlib import Path
from cumcm_py.cases import load_problem_card, validate_evidence_links
from cumcm_py.content import load_yaml

def test_all_problem_cards_have_valid_evidence() -> None:
    catalog = load_yaml(Path("sources/catalog.yaml"))
    cards = sorted(Path("cases/2021-2025").glob("20??/[A-E].yaml"))
    assert len(cards) >= 20
    for path in cards:
        issues = validate_evidence_links(load_problem_card(path), catalog)
        assert issues == (), path
```

- [ ] **Step 2: Discover and register primary material**

For each year and problem, register the official problem statement, attachments, official commentary, and official displayed award papers. Record inaccessible or absent material as a gap. Register third-party papers only after award status and provenance are verified.

- [ ] **Step 3: Write machine-readable YAML cards**

Each card must include tasks, deliverables, data risks, external-data needs, candidate method families, hidden difficulty, common failure paths, official emphasis, observed award-paper method chains, validation practices, writing/figure practices, transferable rules, and evidence IDs with `official`, `observable`, or `inference` kind.

- [ ] **Step 4: Write human-readable analysis pages**

Generate no full numerical reproduction. Use the YAML card as the source of truth and expand only the reasoning: why the task is difficult, why certain approaches are appropriate, what strong papers do, and what can be transferred into tools or checklists.

- [ ] **Step 5: Implement evidence validation**

Reject missing catalog IDs, `inference` items without both an observable fact and an official criterion, award papers without provenance, and claims that use causal language without `official` evidence.

- [ ] **Step 6: Run card and schema validation**

Run: `python -m pytest tests/content/test_problem_cards.py tests/content/test_schemas.py -v`

Expected: PASS and at least 20 cards; record public gaps in the index rather than inventing cards.

- [ ] **Step 7: Commit recent-problem analysis**

```powershell
git add cases sources/catalog.yaml sources/reading-notes code/python/cumcm_py/cases.py tests/content/test_problem_cards.py
git commit -m "docs: analyze 2021 to 2025 CUMCM problems"
```

---

### Task 7: Synthesize award patterns, problem types, and model-selection rules

**Files:**
- Create: `knowledge/award-patterns.md`
- Create: `knowledge/model-selection.md`
- Create: `knowledge/problem-types/prediction.md`
- Create: `knowledge/problem-types/optimization.md`
- Create: `knowledge/problem-types/evaluation.md`
- Create: `knowledge/problem-types/mechanistic.md`
- Create: `knowledge/problem-types/data-analysis.md`
- Create: `knowledge/problem-types/network-spatial.md`
- Create: `validation/award-feature-review.md`
- Create: `tests/content/test_knowledge_provenance.py`

**Interfaces:**
- Consumes: all problem cards and official judging-rule notes.
- Produces: model-selection entries with `signals`, `baseline`, `candidate_models`, `required_validation`, `failure_modes`, and evidence IDs.

- [ ] **Step 1: Write provenance and vocabulary tests**

```python
from pathlib import Path
import re

def test_inferred_award_patterns_are_labeled() -> None:
    text = Path("knowledge/award-patterns.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("- 结论："):
            assert re.search(r"类型：(官方评价|论文观察|分析推断)", line)
            assert re.search(r"来源：[^]]+", line)
```

- [ ] **Step 2: Build the cross-year award-feature matrix**

Compare problem understanding, baseline use, model progression, domain mechanism, data treatment, validation, sensitivity, explainability, innovation, writing, figures, limitations, and reproducibility across years and problem types.

- [ ] **Step 3: Convert observations into actionable rules**

For every pattern, state the signal, action, validation obligation, misuse warning, evidence kind, and source IDs. Include counterexamples where a popular technique was not justified by the task.

- [ ] **Step 4: Create the six problem-type guides and selection matrix**

Each guide must identify task signals, fast baseline, candidate model families, data requirements, disqualifying assumptions, minimum validation, suitable figures, and linked method-card IDs.

- [ ] **Step 5: Create the manual award-feature review checklist**

Keep subjective checks such as novelty, logical coherence, and domain plausibility in `validation/award-feature-review.md`; do not pretend they can be fully automated.

- [ ] **Step 6: Run content tests and commit**

Run: `python -m pytest tests/content/test_knowledge_provenance.py -v`

```powershell
git add knowledge validation/award-feature-review.md tests/content/test_knowledge_provenance.py
git commit -m "docs: derive award-informed modeling guidance"
```

---

### Task 8: Build the canonical method-card library

**Files:**
- Create: `knowledge/methods/data-audit.md`
- Create: `knowledge/methods/interpolation-fitting.md`
- Create: `knowledge/methods/regression-inference.md`
- Create: `knowledge/methods/time-series.md`
- Create: `knowledge/methods/lp-milp.md`
- Create: `knowledge/methods/nonlinear-multiobjective.md`
- Create: `knowledge/methods/graph-flow-routing.md`
- Create: `knowledge/methods/monte-carlo-des.md`
- Create: `knowledge/methods/ode-difference.md`
- Create: `knowledge/methods/ahp-entropy-topsis.md`
- Create: `knowledge/methods/ml-clustering-pca.md`
- Create: `knowledge/methods/sensitivity-robustness.md`
- Create: `knowledge/methods/scientific-plotting.md`
- Create: `knowledge/methods/index.yaml`
- Create: `tests/content/test_method_cards.py`

**Interfaces:**
- Consumes: official technical documentation, learning map, problem cards, and model-selection rules.
- Produces: stable method IDs consumed by Python, MATLAB, workflows, and Skill references.

- [ ] **Step 1: Write method-card completeness tests**

```python
from pathlib import Path

REQUIRED = {
    "适用条件", "不适用条件", "数学定义", "假设", "输入输出",
    "选模理由", "Python 入口", "MATLAB 入口", "验证方法",
    "失败模式", "复杂度", "论文表达", "来源"
}

def test_method_cards_have_required_sections() -> None:
    cards = sorted(Path("knowledge/methods").glob("*.md"))
    assert len(cards) == 13
    for card in cards:
        text = card.read_text(encoding="utf-8")
        headings = {line.removeprefix("## ") for line in text.splitlines() if line.startswith("## ")}
        assert REQUIRED <= headings, card
```

- [ ] **Step 2: Write 13 canonical method cards**

Use language-neutral definitions and trace claims to official documentation or textbooks. Include common normalization mistakes, data leakage, overfitting, infeasible optimization, unsupported causality, and unjustified weighting where relevant.

- [ ] **Step 3: Link every card to recent problems and code entry names**

`knowledge/methods/index.yaml` must include method ID, file, problem-type IDs, 2021—2025 case IDs, Python callable, MATLAB callable, and validation fixture IDs.

- [ ] **Step 4: Run tests and commit**

Run: `python -m pytest tests/content/test_method_cards.py -v`

```powershell
git add knowledge/methods tests/content/test_method_cards.py
git commit -m "docs: add canonical modeling method cards"
```

---

### Task 9: Implement and test the Python modeling library

**Files:**
- Create: `code/python/cumcm_py/preprocess.py`
- Create: `code/python/cumcm_py/fit.py`
- Create: `code/python/cumcm_py/forecast.py`
- Create: `code/python/cumcm_py/optimization.py`
- Create: `code/python/cumcm_py/graph.py`
- Create: `code/python/cumcm_py/simulation.py`
- Create: `code/python/cumcm_py/dynamics.py`
- Create: `code/python/cumcm_py/decision.py`
- Create: `code/python/cumcm_py/ml.py`
- Create: `code/python/cumcm_py/sensitivity.py`
- Create: `code/python/cumcm_py/plotting.py`
- Create: `tests/python/test_*.py`

**Interfaces:**
- Produces: `audit_dataframe`, `fit_candidates`, `forecast_backtest`, `solve_linear_program`, `shortest_path_report`, `monte_carlo`, `solve_ode`, `entropy_topsis`, `evaluate_models`, `sensitivity_report`, and `save_figure`.
- Returns: `ModelResult` or a documented domain dataclass; never a bare unlabeled tuple.

- [ ] **Step 1: Write failing tests for all public callables**

Representative tests must assert properties, not only snapshots:

```python
import numpy as np
from cumcm_py.decision import entropy_topsis

def test_topsis_prefers_strictly_dominant_alternative() -> None:
    matrix = np.array([[9.0, 2.0], [5.0, 5.0], [2.0, 9.0]])
    result = entropy_topsis(matrix, benefit=np.array([True, False]))
    assert result.values["ranking"][0] == 0
    assert np.isclose(sum(result.values["weights"]), 1.0)
```

Also test invalid shapes, NaNs, infeasible optimization, insufficient time-series length, disconnected graphs, unstable ODE input, fixed random seeds, train/test leakage protection, and figure export.

- [ ] **Step 2: Run the Python suite and verify red state**

Run: `python -m pytest tests/python -v`

Expected: FAIL on missing modules and callables.

- [ ] **Step 3: Implement the minimal correct algorithms module by module**

Use official library APIs. Include assumptions and diagnostic metadata in every result. Do not silently impute, normalize, change objective direction, or relax constraints.

- [ ] **Step 4: Run each module test after implementation**

Run examples:

```powershell
python -m pytest tests/python/test_preprocess.py -v
python -m pytest tests/python/test_optimization.py -v
python -m pytest tests/python/test_decision.py -v
```

Expected: each module passes before moving to the next.

- [ ] **Step 5: Run the complete Python suite**

Run: `python -m pytest tests/python -v`

Expected: PASS with no warnings caused by repository code.

- [ ] **Step 6: Commit the Python library**

```powershell
git add code/python tests/python pyproject.toml
git commit -m "feat: add tested Python modeling library"
```

---

### Task 10: Implement and test the MATLAB modeling library

**Files:**
- Create: `code/matlab/+cumcm/auditData.m`
- Create: `code/matlab/+cumcm/fitCandidates.m`
- Create: `code/matlab/+cumcm/forecastBacktest.m`
- Create: `code/matlab/+cumcm/solveLinearProgram.m`
- Create: `code/matlab/+cumcm/shortestPathReport.m`
- Create: `code/matlab/+cumcm/monteCarlo.m`
- Create: `code/matlab/+cumcm/solveOde.m`
- Create: `code/matlab/+cumcm/entropyTopsis.m`
- Create: `code/matlab/+cumcm/evaluateModels.m`
- Create: `code/matlab/+cumcm/sensitivityReport.m`
- Create: `code/matlab/+cumcm/saveFigure.m`
- Create: `tests/matlab/Test*.m`

**Interfaces:**
- MATLAB functions mirror Task 9 names in camelCase and return structs with fields `method`, `values`, `diagnostics`, and `assumptions`.
- Optional-toolbox absence produces a named skipped test or an actionable error identifier such as `cumcm:MissingToolbox`.

- [ ] **Step 1: Write MATLAB unit tests**

```matlab
classdef TestDecision < matlab.unittest.TestCase
    methods (Test)
        function dominantAlternativeRanksFirst(testCase)
            X = [9 2; 5 5; 2 9];
            result = cumcm.entropyTopsis(X, [true false]);
            testCase.verifyEqual(result.values.ranking(1), 1);
            testCase.verifyEqual(sum(result.values.weights), 1, "AbsTol", 1e-10);
        end
    end
end
```

- [ ] **Step 2: Run tests and verify red state**

Run: `matlab -batch "results=runtests('tests/matlab'); assertSuccess(results)"`

Expected: FAIL because functions are missing. If MATLAB is unavailable, record the blocked command in `environment/compatibility.md`; do not claim MATLAB validation.

- [ ] **Step 3: Implement functions using documented MATLAB APIs**

Validate dimensions, missing values, objective direction, feasibility, and random seeds explicitly. Keep field names compatible with the Python result normalization used in Task 11.

- [ ] **Step 4: Run the complete MATLAB suite**

Run: `matlab -batch "addpath('code/matlab'); results=runtests('tests/matlab'); assertSuccess(results)"`

Expected: PASS when MATLAB and required toolboxes are available; otherwise only explicitly documented optional tests may skip.

- [ ] **Step 5: Commit the MATLAB library**

```powershell
git add code/matlab tests/matlab environment/compatibility.md
git commit -m "feat: add tested MATLAB modeling library"
```

---

### Task 11: Add shared fixtures and cross-language validation

**Files:**
- Create: `code/fixtures/manifest.yaml`
- Create: `code/fixtures/*.csv`
- Create: `code/fixtures/expected/*.json`
- Create: `tools/export_matlab_results.m`
- Create: `tools/compare_outputs.py`
- Create: `tests/python/test_cross_language.py`
- Create: `validation/cross-language.md`

**Interfaces:**
- Produces: `compare_result_files(python_json: Path, matlab_json: Path, manifest: Path) -> CheckReport`.
- Fixture manifest fields: `id`, `method_id`, `input`, `properties`, `absolute_tolerance`, `relative_tolerance`, `seed`.

- [ ] **Step 1: Write comparison tests with pass and fail fixtures**

```python
from pathlib import Path
from tools.compare_outputs import compare_result_files

def test_cross_language_comparison_accepts_tolerance() -> None:
    report = compare_result_files(
        Path("tests/fixtures/cross-language/python.json"),
        Path("tests/fixtures/cross-language/matlab-close.json"),
        Path("tests/fixtures/cross-language/manifest.yaml"),
    )
    assert report.passed

def test_cross_language_comparison_rejects_wrong_ranking() -> None:
    report = compare_result_files(
        Path("tests/fixtures/cross-language/python.json"),
        Path("tests/fixtures/cross-language/matlab-wrong.json"),
        Path("tests/fixtures/cross-language/manifest.yaml"),
    )
    assert not report.passed
```

- [ ] **Step 2: Implement normalized JSON export and comparison**

Compare exact categorical properties, ranking, feasibility, monotonicity, and declared numerical tolerances. Never compare only a single scalar when the method produces constraints or diagnostics.

- [ ] **Step 3: Add one fixture for every public core method**

Use small transparent datasets that can be checked by hand. Record the derivation or official example source in the fixture manifest.

- [ ] **Step 4: Generate Python and MATLAB outputs and compare**

Run:

```powershell
python tools/compare_outputs.py --generate-python --manifest code/fixtures/manifest.yaml
matlab -batch "addpath('code/matlab'); run('tools/export_matlab_results.m')"
python tools/compare_outputs.py --python-dir validation/output/python --matlab-dir validation/output/matlab --manifest code/fixtures/manifest.yaml
```

Expected: exit `0` and a JSON report with zero error-level issues.

- [ ] **Step 5: Commit shared fixtures and validator**

```powershell
git add code/fixtures tools/compare_outputs.py tools/export_matlab_results.m tests/python/test_cross_language.py tests/fixtures/cross-language validation/cross-language.md
git commit -m "test: add cross-language model validation"
```

---

### Task 12: Build competition workflows and reusable project templates

**Files:**
- Create: `workflows/problem-intake.md`
- Create: `workflows/data-audit.md`
- Create: `workflows/model-selection.md`
- Create: `workflows/implementation.md`
- Create: `workflows/result-validation.md`
- Create: `workflows/writing-and-figures.md`
- Create: `workflows/compliance.md`
- Create: `workflows/final-packaging.md`
- Create: `templates/project/python/`
- Create: `templates/project/matlab/`
- Create: `templates/project/shared/`
- Create: `tools/init_project.py`
- Create: `tests/python/test_init_project.py`
- Create: `tests/content/test_workflows.py`

**Interfaces:**
- Produces: `initialize_project(destination: Path, languages: Sequence[str]) -> CheckReport`.
- Every workflow exposes headings `输入`, `输出`, `步骤`, `停止条件`, `失败处理`, `人工检查点`, `来源`.

- [ ] **Step 1: Write workflow-structure and project-initializer tests**

```python
from pathlib import Path
from tools.init_project import initialize_project

def test_initializer_creates_both_language_entries(tmp_path: Path) -> None:
    report = initialize_project(tmp_path / "contest", ["python", "matlab"])
    assert report.passed
    assert (tmp_path / "contest" / "python" / "main.py").exists()
    assert (tmp_path / "contest" / "matlab" / "main.m").exists()
    assert (tmp_path / "contest" / "AI工具使用详情.md").exists()
```

- [ ] **Step 2: Write eight workflow documents**

Integrate award-pattern evidence at the relevant decision points. Require a baseline before an advanced model, explicit model-choice rationale, data-leakage review, and result-validation evidence before writing conclusions.

- [ ] **Step 3: Build minimal project templates**

Provide data, source, output, figure, paper, log, Python, and MATLAB directories; relative paths only; one command per language; source manifest; AI-use log; and result manifest.

- [ ] **Step 4: Implement project initialization**

Refuse a nonempty destination unless `--force` is explicitly passed. Never overwrite private data. Return created paths and warnings in `CheckReport`.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/python/test_init_project.py tests/content/test_workflows.py -v`

```powershell
git add workflows templates/project tools/init_project.py tests/python/test_init_project.py tests/content/test_workflows.py
git commit -m "feat: add competition workflows and project templates"
```

---

### Task 13: Build and visually verify the 2026 paper, figure, citation, and AI-use templates

**Files:**
- Create: `templates/paper/main.tex`
- Create: `templates/paper/cumcm2026.sty`
- Create: `templates/paper/sections/*.tex`
- Create: `templates/paper/references.bib`
- Create: `templates/figures/python_style.py`
- Create: `templates/figures/matlabStyle.m`
- Create: `templates/citations/source-record.yaml`
- Create: `templates/ai-usage/AI工具使用详情.md`
- Create: `tests/fixtures/paper/sample-data.csv`
- Create: `tests/content/test_paper_template.py`
- Create: `validation/paper-template.md`

**Interfaces:**
- Paper template compiles with XeLaTeX and contains no table of contents.
- Figure helpers export vector PDF/SVG where appropriate and 300-DPI PNG fallback.

- [ ] **Step 1: Write structural paper-template tests**

```python
from pathlib import Path

def test_paper_template_has_no_toc_and_has_required_sections() -> None:
    text = Path("templates/paper/main.tex").read_text(encoding="utf-8")
    assert "\\tableofcontents" not in text
    for section in ("摘要", "问题重述", "模型假设", "符号说明", "模型建立", "模型检验", "参考文献"):
        assert section in text
```

- [ ] **Step 2: Implement the paper and disclosure templates**

Translate only official 2026 mechanical requirements into style code. Put writing guidance in comments and section prompts, not fabricated conclusions. Include AI tool/model, purpose, key prompts/responses, adoption, and manual changes.

- [ ] **Step 3: Implement Python and MATLAB figure styles**

Use consistent Chinese-capable fonts discovered on the local machine, colorblind-safe colors, explicit units, vector export, and reproducible size presets.

- [ ] **Step 4: Compile and render the sample paper**

Run:

```powershell
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

Workdir: `templates/paper`

Render the resulting PDF to page images and visually inspect cover, abstract, equations, tables, figures, references, page breaks, anonymity, and absence of a contents page. Record results in `validation/paper-template.md`.

- [ ] **Step 5: Run template tests and commit**

Run: `python -m pytest tests/content/test_paper_template.py -v`

```powershell
git add templates tests/fixtures/paper tests/content/test_paper_template.py validation/paper-template.md
git commit -m "feat: add verified CUMCM paper and disclosure templates"
```

---

### Task 14: Implement format, citation, AI-use, code, and package checkers

**Files:**
- Create: `code/python/cumcm_checkers/__init__.py`
- Create: `code/python/cumcm_checkers/cli.py`
- Create: `code/python/cumcm_checkers/paper.py`
- Create: `code/python/cumcm_checkers/citations.py`
- Create: `code/python/cumcm_checkers/ai_usage.py`
- Create: `code/python/cumcm_checkers/code_bundle.py`
- Create: `code/python/cumcm_checkers/package.py`
- Create: `code/python/cumcm_checkers/reporting.py`
- Create: `checkers/rules/cumcm-2026.yaml`
- Create: `tests/checkers/test_*.py`
- Create: `tests/fixtures/checkers/valid/`
- Create: `tests/fixtures/checkers/invalid/`

**Interfaces:**
- Each module implements `run_check(target, config) -> CheckReport`.
- CLI: `python -m cumcm_checkers.cli check <target> --rules checkers/rules/cumcm-2026.yaml --json report.json`.

- [ ] **Step 1: Write paired positive and negative tests**

```python
from pathlib import Path
from cumcm_checkers.ai_usage import run_check

def test_complete_ai_log_passes() -> None:
    report = run_check(Path("tests/fixtures/checkers/valid"), {})
    assert report.passed

def test_missing_ai_fields_fail() -> None:
    report = run_check(Path("tests/fixtures/checkers/invalid/missing-ai-fields"), {})
    assert not report.passed
    assert any(issue.code == "ai.missing_field" for issue in report.issues)
```

Write equivalent paired tests for anonymity, page limit, file size, contents page, citations, source registration, absolute paths, missing run entry, temporary files, and invalid archive structure.

- [ ] **Step 2: Run checker tests and verify red state**

Run: `python -m pytest tests/checkers -v`

Expected: FAIL because checker modules are absent.

- [ ] **Step 3: Implement checkers and JSON reporting**

Use `pypdf` for PDF metadata/page/text checks and Pillow for raster metadata. Keep subjective judgment out of automated pass/fail. Every rule in `cumcm-2026.yaml` must include its official source ID.

- [ ] **Step 4: Implement the aggregate CLI**

Print checker name, pass/fail, severity, file, message, and source IDs. Write deterministic JSON sorted by checker and issue code.

- [ ] **Step 5: Run checker tests and inspect both fixture classes**

Run: `python -m pytest tests/checkers -v`

Run:

```powershell
python -m cumcm_checkers.cli check tests/fixtures/checkers/valid --rules checkers/rules/cumcm-2026.yaml --json validation/valid-report.json
python -m cumcm_checkers.cli check tests/fixtures/checkers/invalid --rules checkers/rules/cumcm-2026.yaml --json validation/invalid-report.json
```

Expected: valid exits `0`; invalid exits `1` and reports each seeded defect.

- [ ] **Step 6: Commit checkers**

```powershell
git add code/python/cumcm_checkers checkers/rules tests/checkers tests/fixtures/checkers validation/valid-report.json validation/invalid-report.json
git commit -m "feat: add CUMCM compliance and package checkers"
```

---

### Task 15: Build and validate the self-contained `cumcm-assistant` Skill

**Files:**
- Create: `skill/cumcm-assistant/SKILL.md`
- Create: `skill/cumcm-assistant/agents/openai.yaml`
- Create: `skill/cumcm-assistant/references/manifest.yaml`
- Create: `skill/cumcm-assistant/references/problem-types/*.md`
- Create: `skill/cumcm-assistant/references/methods/*.md`
- Create: `skill/cumcm-assistant/references/award-patterns/*.md`
- Create: `skill/cumcm-assistant/references/writing/*.md`
- Create: `skill/cumcm-assistant/references/compliance/*.md`
- Create: `skill/cumcm-assistant/scripts/*.py`
- Create: `skill/cumcm-assistant/assets/`
- Create: `tools/build_skill_bundle.py`
- Create: `tests/skill/test_skill_bundle.py`
- Create: `tests/skill/prompts.yaml`

**Interfaces:**
- Produces: `build_skill_bundle(repo_root: Path, skill_root: Path) -> CheckReport`.
- Skill routes `analyze-problem`, `select-model`, `implement-python`, `implement-matlab`, `validate-results`, `draft-structure`, `check-submission`, and `record-ai-use` intents.

- [ ] **Step 1: Initialize the Skill with the official scaffold tool**

Run the installed Skill Creator initializer with name `cumcm-assistant`, resources `scripts,references,assets`, and interface values derived from the approved design. Remove generated example files immediately.

- [ ] **Step 2: Write bundle-drift tests**

```python
from pathlib import Path
from tools.build_skill_bundle import build_skill_bundle

def test_checked_in_skill_bundle_matches_canonical_sources(tmp_path: Path) -> None:
    report = build_skill_bundle(Path.cwd(), tmp_path / "cumcm-assistant")
    assert report.passed
    assert (tmp_path / "cumcm-assistant" / "references" / "manifest.yaml").exists()
```

- [ ] **Step 3: Implement deterministic bundle generation**

Copy only approved canonical documents and templates. Record source path and SHA-256 in the Skill manifest. Rewrite repository-relative links so the installed Skill remains self-contained. Fail if a source is missing or a generated copy differs unexpectedly.

- [ ] **Step 4: Write concise Skill routing instructions**

Make official rules load first for compliance-sensitive tasks. Route by problem type and requested action. Require candidate-model comparison and validation before paper conclusions. Never load all references at once.

- [ ] **Step 5: Add representative prompt expectations**

`tests/skill/prompts.yaml` must cover prediction, optimization, evaluation, mechanistic modeling, Python implementation, MATLAB implementation, award-feature review, paper checking, AI disclosure, and refusal to hide AI use. Store expected resources and workflow IDs, not exact prose answers.

- [ ] **Step 6: Generate metadata and validate the Skill**

Run:

```powershell
python tools/build_skill_bundle.py
python C:\Users\37828\.codex\skills\.system\skill-creator\scripts\quick_validate.py skill/cumcm-assistant
python -m pytest tests/skill -v
```

Expected: scaffold validation PASS, bundle drift test PASS, all prompt routes resolve to existing resources.

- [ ] **Step 7: Commit the Skill**

```powershell
git add skill tools/build_skill_bundle.py tests/skill
git commit -m "feat: add CUMCM assistant Skill"
```

---

### Task 16: Add one-command repository verification and perform final evidence audit

**Files:**
- Create: `tools/verify_repository.py`
- Create: `validation/repository-checklist.md`
- Create: `validation/coverage-matrix.yaml`
- Create: `tests/python/test_verify_repository.py`
- Modify: `README.md`

**Interfaces:**
- Produces: `verify_repository(root: Path, include_matlab: bool, include_latex: bool) -> CheckReport`.
- CLI: `python tools/verify_repository.py --matlab auto --latex auto --json validation/repository-report.json`.

- [ ] **Step 1: Write orchestration tests**

```python
from pathlib import Path
from tools.verify_repository import verify_repository

def test_repository_verifier_runs_all_required_groups(monkeypatch) -> None:
    report = verify_repository(Path.cwd(), include_matlab=False, include_latex=False)
    groups = set(report.metadata["groups"])
    assert {"sources", "cases", "methods", "python", "checkers", "skill"} <= groups
```

- [ ] **Step 2: Implement the verification orchestrator**

Run source schemas and note coverage, problem-card evidence, award-pattern provenance, method-card completeness, Python tests, optional MATLAB tests, cross-language comparisons, optional XeLaTeX build, checker fixtures, Skill validation, bundle drift, and Git tracked-file policy. Preserve each subprocess exit code and output path.

- [ ] **Step 3: Build the coverage matrix**

Map every approved design requirement to files, tests, commands, evidence, and current status. A missing requirement is an error, not a prose caveat.

- [ ] **Step 4: Update the human README**

Lead with four commands: install, initialize a contest project, run a method example, and verify a submission. Document Python/MATLAB choice, source-reading states, Skill installation, and offline use. Link to rules and evidence instead of duplicating them.

- [ ] **Step 5: Run the complete verification command**

Run: `python tools/verify_repository.py --matlab auto --latex auto --json validation/repository-report.json`

Expected: exit `0`; unavailable optional runtimes are recorded as `skipped` with environment evidence, not reported as passed.

- [ ] **Step 6: Inspect Git policy and source completeness**

Run:

```powershell
git status --short
git ls-files private-sources tmp
python -m pytest -v
```

Expected: `git status` lists only the intended Task 16 files; no tracked private or temporary sources; all available-runtime tests pass.

- [ ] **Step 7: Commit final verification and documentation**

```powershell
git add README.md tools/verify_repository.py validation tests/python/test_verify_repository.py
git commit -m "test: add full repository verification"
```

- [ ] **Step 8: Confirm the final commit left a clean worktree**

Run: `git status --short`

Expected: no output.

---

## Appendix A: Seed Source Inventory

The catalog must contain at least these source IDs. Discovery during implementation may add sources, but may not silently remove these entries.

### Official CUMCM sources

- `OFF-CUMCM-HOME` — https://www.mcm.edu.cn/
- `OFF-CUMCM-CHARTER` — https://www.mcm.edu.cn/html_cn/block/44e92058f537729c6b6a62a3662ee417.html
- `OFF-CUMCM-2026-NOTICE` — https://www.mcm.edu.cn/html_cn/node/d6fd7a0ee8f3a3d525e30af1c365fcec.html
- `OFF-CUMCM-2026-RULES` — https://www.mcm.edu.cn/html_cn/node/9d8e511fe7a1447b35f53a82c908e2e0.html
- `OFF-CUMCM-2026-FORMAT` — https://www.mcm.edu.cn/html_cn/node/4cd596519c9eb9fbd866398f6df0caa3.html
- `OFF-CUMCM-2026-FORMAT-MIRROR` — https://dxs.moe.gov.cn/zx/a/hd_sxjm_gsyw/260702/2046411.shtml
- `OFF-CUMCM-AI-RULES` — https://dxs.moe.gov.cn/zx/a/hd_sxjm_gsyw/250904/2017973.shtml
- `OFF-CUMCM-AI-RULES-EN` — https://en.mcm.edu.cn/html_en/node/b87f1a9b1dbbd987f56513609f416722.html
- `OFF-CUMCM-AI-RULES-OLD-DEAD` — https://www.mcm.edu.cn/html_cn/node/eebcfb6dc37fd2de9603dc16026fdf01.html
- `OFF-CUMCM-NATIONAL-JUDGING` — https://www.mcm.edu.cn/html_cn/node/b1f48689659f0660e80a2d6279d7b37d.html
- `OFF-CUMCM-REGIONAL-JUDGING` — https://www.mcm.edu.cn/html_cn/node/011a3fefdb4951a8cb595400f44ec3df.html
- `OFF-CUMCM-PROBLEM-ARCHIVE` — https://www.mcm.edu.cn/html_cn/block/8579f5fce999cdc896f78bca5d4f8237.html
- `OFF-CUMCM-2025-PROBLEMS` — https://www.mcm.edu.cn/html_cn/node/03c91a444e62eee81a3740fa97a461a6.html
- `OFF-CUMCM-2025-REVIEW` — https://dxs.moe.gov.cn/zx/a/hd_sxjm_gsyw/251118/2024336.shtml
- `OFF-CUMCM-COMMENTARY-HUB` — https://dxs.moe.gov.cn/zx/hd/sxjm/sxjmstjp/
- `OFF-CUMCM-2023-COMMENTARY` — https://dxs.moe.gov.cn/zx/hd/sxjm/sxjmstjp/2023sxjmstjp/2023qgdxssxjmjsstjp.shtml
- `OFF-CUMCM-2023-PAPERS` — https://dxs.moe.gov.cn/zx/hd/sxjm/sxjmlw/2023qgdxssxjmjslwzs/2023gjsbqgdxssxjmjslwzs.shtml
- `OFF-CUMCM-2023-PAPER-A` — https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2023qgdxssxjmjslwzs_2023atlw/231104/1865114.shtml
- `OFF-CUMCM-2023-PAPER-C050` — https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2023qgdxssxjmjslwzs_2023ctlw/231104/1865124.shtml
- `OFF-CUMCM-2023-MULTI-LEARNING` — https://dxs.moe.gov.cn/zx/hd/sxjm/dwdxxsxjm/dwdxxsxjm-2023.shtml
- `SECONDARY-CUMCM-PAPERS-2010-2025` — https://www.cmathc.org.cn/mcm/lw/530.html

### Courses and books

- `COURSE-UESTC-MODELING` — https://higher.smartedu.cn/course/6317cbb7325d39c27c419044
- `COURSE-CQUPT-MODELING` — https://higher.smartedu.cn/course/67b26c59225d72705e2f77f1
- `COURSE-HDU-MODELING` — https://www.chinaooc.com.cn/course/68b220d9d5f9b8b6cf833ce6
- `COURSE-TSINGHUA-INTRO` — https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmjcxzs/210413/1614853.shtml
- `COURSE-SCIENTIFIC-COMPUTING` — https://www.cmooc.com/course/22435.html
- `COURSE-MODELING-INDEX` — https://www.cmooc.com/course/22663.html
- `BOOK-MATHEMATICAL-MODELS-6` — https://dxs.moe.gov.cn/zx/a/hd_sxjm_smts/241212/1830809.shtml
- `BOOK-MATLAB-MODELING-PRACTICE` — bibliographic lead: 卓金武、萨和雅、王鸿钧《MATLAB数学建模方法与实践》
- `BOOK-MATLAB-AND-MODELING` — bibliographic lead: 谢中华《MATLAB与数学建模》

### Python and algorithm documentation

- `PYDOC-NUMPY` — https://numpy.org/doc/stable/
- `PYDOC-PANDAS` — https://pandas.pydata.org/docs/
- `PYDOC-SCIPY` — https://docs.scipy.org/doc/scipy/reference/
- `PYDOC-MATPLOTLIB` — https://matplotlib.org/stable/
- `PYDOC-SEABORN` — https://seaborn.pydata.org/
- `PYDOC-SYMPY` — https://docs.sympy.org/latest/index.html
- `PYDOC-STATSMODELS` — https://www.statsmodels.org/stable/user-guide.html
- `PYDOC-SKLEARN` — https://scikit-learn.org/stable/user_guide.html
- `PYDOC-SKLEARN-MODEL-SELECTION` — https://scikit-learn.org/stable/model_selection.html
- `PYDOC-NETWORKX-ALGORITHMS` — https://networkx.org/documentation/stable/reference/algorithms/index.html
- `PYDOC-NETWORKX-SHORTEST-PATH` — https://networkx.org/documentation/stable/reference/algorithms/shortest_paths.html
- `PYDOC-NETWORKX-FLOW` — https://networkx.org/documentation/stable/reference/algorithms/flow.html
- `PYDOC-ORTOOLS` — https://developers.google.com/optimization
- `PYDOC-ORTOOLS-VRP` — https://developers.google.com/optimization/routing/vrp
- `PYDOC-ORTOOLS-MIP` — https://developers.google.com/optimization/mip/mip_example
- `PYDOC-PYOMO` — https://pyomo.readthedocs.io/en/stable/getting_started/
- `PYDOC-SIMPY` — https://simpy.readthedocs.io/en/stable/
- `PYDOC-SALIB` — https://salib.readthedocs.io/en/latest/
- `PYDOC-GEOPANDAS` — https://geopandas.org/en/stable/
- `PYDOC-OSMNX` — https://osmnx.readthedocs.io/en/stable/
- `PYDOC-PYMCDM` — https://pymcdm.readthedocs.io/en/master/
- `PAPER-PYDECISION` — https://arxiv.org/abs/2404.06370

### MATLAB documentation

- `MATLABDOC-MATLAB` — https://www.mathworks.com/help/matlab/
- `MATLABDOC-OPTIMIZATION` — https://www.mathworks.com/help/optim/
- `MATLABDOC-STATISTICS-ML` — https://www.mathworks.com/help/stats/
- `MATLABDOC-CURVE-FITTING` — https://www.mathworks.com/help/curvefit/
- `MATLABDOC-ECONOMETRICS` — https://www.mathworks.com/help/econ/

### Data and literature sources

- `DATA-NBS-CHINA` — https://data.stats.gov.cn/
- `DATA-WORLD-BANK-API` — https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation
- `DATA-WORLD-BANK-CALLS` — https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures
- `DATA-WORLD-BANK-INDICATORS` — https://datahelpdesk.worldbank.org/knowledgebase/articles/898599-indicator-api-queries
- `DATA-NASA` — https://data.nasa.gov/
- `DATA-OSM-APIS` — https://wiki.openstreetmap.org/wiki/APIs
- `DATA-OSM-OVERPASS` — https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL
- `DATA-KAGGLE` — https://www.kaggle.com/datasets
- `LITERATURE-OPENALEX` — https://developers.openalex.org/api-reference/works
- `LITERATURE-CROSSREF` — https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- `LITERATURE-CNKI` — https://www.cnki.net/

### Existing Skills, repositories, and templates

- `REPO-XIAOMA-SKILL` — https://github.com/XiaoMaColtAI/math-modeling-skill
- `REPO-XIAOMA-INDEX` — https://github.com/XiaoMaColtAI/math-modeling-skill/blob/main/references/%E7%AE%97%E6%B3%95%E7%B4%A2%E5%BC%95.md
- `REPO-LUPYNOW-SKILLS` — https://github.com/Lupynow/math-modeling-skills
- `REPO-YOKI-SINGLE` — https://github.com/Yoki-cmd/math-modeling-single
- `REPO-CUMCMTHESIS` — https://github.com/latexstudio/CUMCMThesis
- `REPO-CUMCM-LATEX` — https://github.com/Sustainable-Enjoyment/CUMCM-LaTeX-Template
- `REPO-GITEE-CUMCM` — https://gitee.com/cumcm
- `REPO-GITHUB-CUMCM-TOPIC` — https://github.com/topics/cumcm

---

## Execution Checkpoints

- **Checkpoint A — after Task 5:** source catalog, reading states, official rules, learning map, and repository/license audit are complete.
- **Checkpoint B — after Task 8:** 2021—2025 problem corpus, award-feature synthesis, model selection, and method cards are complete before code expansion.
- **Checkpoint C — after Task 11:** Python, MATLAB, and cross-language fixtures are validated on available local runtimes.
- **Checkpoint D — after Task 14:** workflows, templates, paper rendering, and positive/negative checker fixtures are validated.
- **Checkpoint E — after Task 16:** Skill bundle and whole-repository verification pass, with unavailable optional runtimes reported honestly.

## Execution Handoff

Execute this plan with `superpowers:executing-plans` in the current repository, task by task, stopping at each checkpoint for evidence review. Do not start a later checkpoint while an earlier checkpoint has unresolved error-level findings.
