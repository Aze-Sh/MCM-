# CUMCM 2026 可验证竞赛工具仓库

仓库根目录包含可复用的建模工具、检查器、规则、模板和工作流；2026 年 B 题实战资料集中在 [`contest/2026`](contest/2026)。

克隆后从仓库根目录运行下面的 PowerShell 命令：

```powershell
# 1. 安装
python -m pip install -e ".[test]"

# 2. 初始化竞赛项目（可只选 python 或 matlab）
$project = (Resolve-Path contest\2026).Path
python tools/init_project.py $project --languages python matlab --force

# 3. 运行一个方法示例
python -c "from cumcm_py.decision import entropy_topsis; print(entropy_topsis([[8,3],[7,5],[9,4]],[True,False]).values)"

# 4. 检查待提交项目
python -m cumcm_checkers.cli check $project --rules checkers/rules/cumcm-2026.yaml --stage draft --json (Join-Path $project check-report.json)
```

本仓库把资料证据、近五年真题分析、13 个方法卡、Python/MATLAB 代码、工作流、论文与图表模板、检查器和 Codex Skill 连接成一条可复核链路。它不承诺奖项；它帮助队伍减少不可复现、无验证、无来源和格式违规。

## 2026 B 题赛前入口

- [题目任务分解](contest/2026/B题任务分解.md)：问题 3、4 的建模和接口任务表。
- [模拟器接入说明](contest/2026/模拟器接入说明.md)：演练、日志备份和故障处理。
- [正式测试前检查清单](contest/2026/正式测试前检查清单.md)：逐轮放行证据与人工核对项。
- [正式候选代码冻结版](contest/2026/releases/formal-v3-20260911/)：策略 v3、入口命令和 SHA-256 清单。

运行 B 题本地模拟或练习入口时，使用 `contest/2026/python/main.py`；正式测试必须明确传入题号、轮次和 `--confirm-formal`，并按清单确认模拟器状态。

## 建议使用顺序

1. 按 [问题读入工作流](workflows/problem-intake.md) 拆解每一问。
2. 从 [问题类型](knowledge/problem-types) 和 [方法索引](knowledge/methods/index.yaml) 选择少量候选模型。
3. 先完成 [数据审计](workflows/data-audit.md)，再实现和比较模型。
4. 按 [结果验证](workflows/result-validation.md) 做留出/回测、诊断、敏感性和极端情景检查。
5. 使用 [论文模板](templates/paper/main.tex) 和 [图形风格](templates/figures) 写作。
6. 运行提交检查器并逐项完成 [官方要求映射清单](rules/submission-checklist.md)。

## Python 与 MATLAB

- Python 是本环境中完整执行的主验证路径，函数位于 `code/python/cumcm_py`。
- MATLAB 提供对应接口和共享夹具，位于 `code/matlab/+cumcm`。R2024a 已实际运行 13 项单元测试；环境与恢复记录见 [兼容性记录](environment/compatibility.md)。
- 跨语言验证已导出 13 个 MATLAB 夹具并比较 21 个声明属性；比较器、容差和证据见 [跨语言验证](validation/cross-language.md)。

## 资料与证据

[资料目录](sources/catalog.yaml) 为每个来源记录 `full-read`、`partial-read`、`metadata-only`、`blocked` 或 `dead-link` 状态。仓库严格区分官方事实、论文可观察特征和分析推断；[获奖特征综合](knowledge/award-patterns.md) 是复核框架，不是因果保证。

## CUMCM Assistant Skill

Skill 位于 `skill/cumcm-assistant`，包含按需路由、方法卡、规则、代码和模板。复制该目录到个人 Skills 目录即可离线使用；运行：

```powershell
$env:PYTHONUTF8='1'
python C:\Users\37828\.codex\skills\.system\skill-creator\scripts\quick_validate.py skill/cumcm-assistant
python skill/cumcm-assistant/scripts/route_intent.py select-model --prompt "为配送问题建立混合整数规划"
```

`references/manifest.yaml` 记录每个规范源文件的 SHA-256；执行 `python tools/build_skill_bundle.py` 可检测并重建资源包。

## 一键验证

```powershell
python tools/verify_repository.py --matlab auto --latex auto --json validation/repository-report.json
```

`auto` 只对实际可用的可选运行时执行测试；不可用项写为 `skipped` 并保留环境证据，不伪装成 PASS。完整覆盖关系见 [覆盖矩阵](validation/coverage-matrix.yaml) 和 [最终清单](validation/repository-checklist.md)。

## 两种检查阶段

- `--stage draft`：比赛中检查源文件、Markdown/TeX 论文和编辑版 AI 记录。
- `--stage submission`：提交前检查最终打包目录，只接受最终论文 PDF；使用 AI 时还必须存在并能读取 `AI工具使用详情.pdf`。工作目录的 `paper/main.pdf`、`python/` 和 `matlab/` 先复制到一个扁平的最终打包目录（顶层论文、AI 详情文件和 `code/main.py` 或 `code/main.m`），再运行此阶段。空白初始化项目预期会失败，先填入真实结果和声明再检查。

## 正式比赛目录

`tools/init_project.py` 会复制共享数据目录、Python/MATLAB 入口、论文模板、图形风格和 AI 详情模板，并且不会覆盖已存在文件。原始数据放正式项目目录的 `data/raw/`，处理数据放 `data/processed/`，结果放 `output/`，图片放 `figures/`；比赛题面和附件进入项目后，先把每问拆成任务表，再开始建模。

使用本仓库中的 Codex Skill 时，指定 `skill/cumcm-assistant/SKILL.md`；它会按题型只读取相关方法卡、工作流和检查规则。每次 AI 参与都要保留真实用途、核验和修改记录。

## 边界与安全

- 正式提交规则以 [2026 官方规则记录](rules/2026-rules.md) 和官网最新通知为准。
- AI 使用必须如实记录到 `AI工具使用详情.md`；不得隐瞒或伪造。
- `private-sources/` 与 `tmp/` 不进入版本控制；不要提交付费材料、未授权论文、账号、密码或令牌。
- 检查器 PASS 只说明客观规则未触发，不证明数学结论正确。
