# CUMCM 2026 B 题完赛 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不启动正式测试的前提下，完成问题 1、2 的可复算模型，统一问题 3、4 的演练证据，生成可编译论文草稿和正式测试前合规报告。

**Architecture:** `b_geometry.py` 保存几何原语和第二检测点设计，`q1_q2_analysis.py` 生成结构化数值证据，`b_figures.py` 只负责从已登记结果生成论文图。论文只引用 `result-manifest.yaml` 已登记的输出；正式测试由独立人工放行门控制，结果不得用演练数据替代。

**Tech Stack:** Python 3.10+、NumPy、SciPy、Matplotlib、pytest、XeLaTeX、仓库 CUMCM 检查器。

**Spec:** `contest/2026/B题任务分解.md`

## Global Constraints

- 示向误差为每个地点固定但未知的 `[-1°,1°]` 有界误差；同点重复检测不能平均消除。
- 全向源有效接收半径未知但属于 `[1000,1500]` 米；第二检测点的保证接收条件使用 1000 米下界。
- 问题 1 的纯示向楔形交必须区分空集、有界和无界，不得用人工大矩形把无界区域伪装成有限区域。
- 正式成绩只能来自真实正式测试；问题 3、4 各三次，正式测试启动或中止均消耗机会。
- AI 使用情况必须如实记录，论文声明位于参考文献之前，支撑材料提供 `AI工具使用详情.pdf`。
- 比赛期间当届赛题、策略、日志和论文不得公开发布；远端仓库必须为私有。

---

### Task 1: 问题 1 与问题 2 几何核心

**Files:**
- Modify: `contest/2026/python/b_geometry.py`
- Modify: `contest/2026/tests/test_geometry.py`

**Interfaces:**
- Consumes: `bearing_halfplanes()`、`halfplane_region()`、`diameter()`、`enclosing_circle()`。
- Produces: `first_bearing_sector(sensor, bearing_deg, ...) -> np.ndarray`、`second_detector_candidate(point, centers, radius) -> bool`、`recommended_second_detectors(sensor, bearing_deg, ...) -> np.ndarray`、`intersection_angle_deg(sensor1, sensor2, source) -> float`、`clip_polygon_halfplanes(points, a, b) -> np.ndarray`。

- [x] **Step 1: Write failing tests for the first feasible sector and guaranteed-reception lens**

```python
def test_second_detector_design_guarantees_minimum_receive_radius():
    points = g.recommended_second_detectors((0, 0), 0)
    assert points[0] == pytest.approx([761.429453, 648.247783], abs=1e-6)
    centers, radius = g.second_detector_candidate_disks((0, 0), 0)
    assert max(np.linalg.norm(points[0] - centers, axis=1)) <= radius + 1e-9
```

- [x] **Step 2: Run the targeted test and require the missing-interface failure**

Run: `.worktrees/cumcm-build/.venv/Scripts/python.exe -X utf8 -m pytest contest/2026/tests/test_geometry.py -q`

Expected: FAIL because the new second-detector interfaces do not exist.

- [x] **Step 3: Implement the exact three-disc candidate region and symmetric recommendation**

For first point `S1`, measured bearing `theta`, half-error `eps`, range upper bound `R=1500`, and guaranteed radius `r0=1000`, construct centers `S1`, `S1+R*u(theta-eps)`, `S1+R*u(theta+eps)`. A point is admissible iff it lies in all three radius-`r0` discs. Compute the two recommended points from the equal-radius circle intersections and reject invalid parameters with `R > 2*r0`.

- [x] **Step 4: Add polygon clipping and crossing-angle tests**

Test zero-degree wrap, rigid rotation/translation invariance, a source on each sector boundary, the `near` limit, empty clipping, and the recommended design's sampled minimum crossing angle of at least `39.5°`.

- [x] **Step 5: Run all B geometry tests**

Run: `.worktrees/cumcm-build/.venv/Scripts/python.exe -X utf8 -m pytest contest/2026/tests/test_geometry.py -q`

Expected: PASS.

- [x] **Step 6: Commit the geometry unit**

```powershell
git add contest/2026/python/b_geometry.py contest/2026/tests/test_geometry.py
git commit -m "feat: complete B problem bearing geometry"
```

### Task 2: 可复算的第一、二问证据包

**Files:**
- Create: `contest/2026/python/q1_q2_analysis.py`
- Create: `contest/2026/tests/test_q1_q2_analysis.py`
- Create: `contest/2026/output/q1-q2-geometry-20260911.json`
- Modify: `contest/2026/result-manifest.yaml`

**Interfaces:**
- Consumes: Task 1 geometry interfaces.
- Produces: `build_report() -> dict` and a JSON report with the triangle counterexample, minimum enclosing circle, second-detector coordinates, maximum source-to-detector distance, minimum crossing angle, and discretization convergence.

- [x] **Step 1: Write a failing report-schema test**

```python
def test_report_contains_reproducible_q1_q2_evidence():
    report = q1_q2_analysis.build_report()
    assert report["q1"]["diameter_m"] == pytest.approx(40.0)
    assert report["q1"]["minimum_enclosing_radius_m"] == pytest.approx(40 / np.sqrt(3))
    assert report["q2"]["guaranteed_max_distance_m"] <= 1000 + 1e-8
    assert report["q2"]["sampled_min_crossing_angle_deg"] >= 39.5
```

- [x] **Step 2: Implement the deterministic analysis command**

Run: `python contest/2026/python/q1_q2_analysis.py --output contest/2026/output/q1-q2-geometry-20260911.json`

The command must use fixed sampling grids, store every parameter, and write no absolute path.

- [x] **Step 3: Add convergence evidence**

Evaluate angular grids of 41, 81, 161 and 321 points and radial grids of 101, 201 and 401 points. Require the reported minimum crossing angle to vary by less than `0.05°` between the final two resolutions.

- [x] **Step 4: Register the output**

Add one `verified-analytic-and-numeric` entry to `result-manifest.yaml` with script, inputs, parameters, output and observed fields.

- [x] **Step 5: Run the report tests and regenerate the JSON**

Run: `.worktrees/cumcm-build/.venv/Scripts/python.exe -X utf8 -m pytest contest/2026/tests/test_q1_q2_analysis.py -q`

Expected: PASS and byte-stable JSON across two runs.

- [x] **Step 6: Commit the evidence unit**

```powershell
git add contest/2026/python/q1_q2_analysis.py contest/2026/tests/test_q1_q2_analysis.py contest/2026/output/q1-q2-geometry-20260911.json contest/2026/result-manifest.yaml
git commit -m "feat: add reproducible B problem geometry evidence"
```

### Task 3: 论文图表

**Files:**
- Create: `contest/2026/python/b_figures.py`
- Create: `contest/2026/tests/test_b_figures.py`
- Create: `contest/2026/figures/final/q1-region-counterexample.{png,pdf,svg}`
- Create: `contest/2026/figures/final/q2-second-detector-region.{png,pdf,svg}`
- Create: `contest/2026/figures/final/q34-practice-summary.{png,pdf,svg}`

**Interfaces:**
- Consumes: Task 2 JSON and six `official-practice-*.json` reports.
- Produces: three vector figures with Chinese labels, SI units, legible legends and deterministic dimensions.

- [x] **Step 1: Write figure smoke tests**

Check that all three PDFs exist, begin with `%PDF`, are each below 2 MB, and their source-data sidecars contain no absolute paths.

- [x] **Step 2: Draw each figure for one evidence task**

Q1 shows three wedges, triangular feasible region, farthest pair and minimum enclosing circle; Q2 shows the first sector, three-disc intersection and two recommended points; Q3/Q4 shows all six practice clear fractions and virtual times without treating them as formal results.

- [x] **Step 3: Render to PNG and visually inspect**

Run `pdftoppm -png -r 180` for every figure and inspect labels, clipping, line weights and grayscale distinction.

- [x] **Step 4: Commit the figure unit**

```powershell
git add contest/2026/python/b_figures.py contest/2026/tests/test_b_figures.py contest/2026/figures
git commit -m "docs: add B problem evidence figures"
```

### Task 4: B 题论文草稿与 AI 记录

**Files:**
- Modify: `contest/2026/paper/main.tex`
- Modify: `contest/2026/paper/sections/abstract.tex`
- Modify: `contest/2026/paper/sections/problem.tex`
- Modify: `contest/2026/paper/sections/assumptions.tex`
- Modify: `contest/2026/paper/sections/symbols.tex`
- Modify: `contest/2026/paper/sections/model.tex`
- Modify: `contest/2026/paper/sections/results.tex`
- Modify: `contest/2026/paper/sections/validation.tex`
- Modify: `contest/2026/paper/sections/conclusion.tex`
- Modify: `contest/2026/paper/sections/ai-declaration.tex`
- Modify: `contest/2026/AI工具使用详情.md`

**Interfaces:**
- Consumes: Task 2 report, Task 3 figures, `result-manifest.yaml`, official practice logs and frozen strategy ID.
- Produces: a draft paper in which every number points to a registered result and formal-test cells are explicitly marked as awaiting real formal runs.

- [x] **Step 1: Replace all generic template text with B-specific content**

Write the half-plane model, boundedness classification, diameter algorithm, equilateral-triangle counterexample, three-disc candidate region, robust second-point recommendation, 600 m coverage proof, adaptive localization, stop-at-16 proof and protocol state machine.

- [x] **Step 2: Insert verified results only**

Include Q1/Q2 values from the JSON and six official practice rows labelled “演练”. Keep the three Q3 and three Q4 formal rows empty until real formal tests finish.

- [x] **Step 3: Complete the AI-use working record truthfully**

Record Codex assistance for repository preparation,题面整理、几何推导、代码与测试、模拟器演练复盘、图表和论文草拟；leave team adoption, manual edits and human verification as unchecked statements requiring team completion rather than inventing them.

- [x] **Step 4: Compile and inspect the paper**

Run `xelatex` twice from `contest/2026/paper`, render every page, and fix overflow, unreadable figures, page breaks, anonymity and declaration placement.

- [x] **Step 5: Commit the draft unit**

```powershell
git add contest/2026/paper contest/2026/AI工具使用详情.md
git commit -m "docs: draft complete CUMCM B problem paper"
```

### Task 5: 正式测试前放行

**Files:**
- Modify: `contest/2026/正式测试前检查清单.md`
- Create: `contest/2026/output/preformal-verification-20260911.json`
- Modify: `contest/2026/result-manifest.yaml`

**Interfaces:**
- Consumes: all tests, compiled paper, frozen release hashes and repository checkers.
- Produces: one machine-readable preformal report with pass/fail/skip status and an explicit list of human-only gates.

- [x] **Step 1: Run all automated tests and repository checks**

Run the 86 repository tests, all B-specific tests, frozen SHA-256 verification, draft checker and LaTeX compilation.

- [x] **Step 2: Confirm formal code identity**

Require the six files in `releases/formal-v3-20260911/code/` to match `SHA256SUMS.txt`; any code change requires a new release directory and full revalidation.

- [x] **Step 3: Record human-only gates**

List simulator login/time sync, exact formal problem page, run number, remaining attempt count, interface-ready state, team authorization and post-run upload confirmation.

- [x] **Step 4: Stop before `/enter`**

Do not start a formal run until the team explicitly authorizes that exact problem number and run number after seeing the completed checklist.

### Task 6: 正式测试结果与最终提交

**Files:**
- Modify after each authorized run: `contest/2026/result-manifest.yaml`
- Modify after six runs: `contest/2026/paper/sections/results.tex`
- Create after six runs: `contest/2026/final-submission/`

**Interfaces:**
- Consumes: three authorized Q3 runs, three authorized Q4 runs, original simulator filenames, final paper and AI details PDF.
- Produces: six formal rows, six untouched original logs, final PDF, support ZIP, SHA-256/MD5 records and upload checklist.

- [ ] **Step 1: Run one formally authorized test at a time**
- [ ] **Step 2: Preserve original simulator files and calculate SHA-256 immediately**
- [ ] **Step 3: Replace empty formal rows only from verified result files**
- [ ] **Step 4: Recompile, rerun submission-stage checks, package under 20 MB, and freeze MD5 before the official deadline**
