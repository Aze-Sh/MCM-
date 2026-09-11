# 2026-09-10 赛前复核报告

## 结论

仓库的 Python、MATLAB 方法库、跨语言夹具、检查器和 Skill 已完成本次复核。正式目录已初始化到外层 `contest/2026`。XeLaTeX 可执行文件可以定位，文件元数据显示 XeTeX 4.16 / MiKTeX 25.12；但本次受限环境在 MiKTeX 首次用户设置阶段拒绝访问，因此模板需要在普通 Windows 用户环境再编译一次。

## 实测证据

- 仓库专用环境：`.venv\Scripts\python.exe`，Python 3.12.10，`pip check` 无损坏依赖。
- 完整 Python 测试：`86 passed`。
- 分阶段检查器测试：`57 passed`，包含 2026 AI 声明/PDF/冲突/占位符/润色例外测试。
- Skill 资源包：106 个资源文件，资源哈希校验通过；Skill 测试 `4 passed`。
- MATLAB R2024a：`TestCore.m` 实测 `13 Passed / 0 Failed / 0 Incomplete`，日志在 `matlab.log`；13 个输出重新导出。
- Python/MATLAB 比较：13 个夹具、21 个声明属性通过，机器可读结果在 `cross-language.json`。
- 一键仓库验证（`--matlab no --latex no`）：sources、cases、methods、python、checkers、skill、coverage、git-policy 全部通过；MATLAB/LaTeX 以 skipped 记录，因为前者已经有单独实测证据，后者受 MiKTeX 设置阻塞。
- XeLaTeX 可执行文件元数据：XeTeX 4.16 / MiKTeX 25.12；但当前用户配置仍停在 MiKTeX 首次设置，`xelatex --version` 和论文、AI 详情新编译均被拒绝访问，原因分别见 `latex-attempt.log` 与 `ai-details-latex-attempt.log`。

## 使用入口

从外层打开 [README.md](../../README.md)，实际仓库入口为 `.worktrees/cumcm-build/README.md`。正式比赛目录是 `contest/2026`；先把题面和附件放入 `data/raw`，比赛中用 `--stage draft`，提交前用 `--stage submission`。

## 仍需队伍完成

1. 在普通 Windows 用户环境安装/完成 MiKTeX 首次设置，双遍编译论文模板与 AI 详情模板，并检查 PDF 页面。
2. 比赛开始后选择题目、填写 AI 声明二选一；使用 AI 时持续填写真实的工具版本、目的环节、提示方式、过程、采纳、修改和人工核验，最终导出 `AI工具使用详情.pdf`。
3. 三名队员逐问复核题意、单位、数据来源、模型假设、代码运行结果、图表、引用、匿名性和压缩包内容；检查器通过不等于数学结论正确。
4. 依据官网临时通知确认实际下载、MD5 和上传截止时间；仓库中的日期和规则记录不能替代比赛系统提示。
