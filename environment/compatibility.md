# 本机兼容性基线

检查日期：2026-08-11  
系统：Windows，PowerShell

| 组件 | 状态 | 证据 |
|---|---|---|
| Python | 可用 | `Python 3.12.10` |
| pip | 可用 | `pip 25.0.1`，Python 3.12 |
| pytest | 可用 | `pytest 9.1.1` |
| XeLaTeX | 可用 | `MiKTeX-XeTeX 4.16 (MiKTeX 25.12)` |
| MATLAB | 可用 | `24.1.0.2537033 (R2024a)`；重建用户偏好目录后，普通 Windows 用户环境中 13 项 `matlab.unittest` 全部通过。 |

## 验证命令

```powershell
python --version
python -m pip --version
python -m pytest --version
matlab -batch "disp(version); ver"
xelatex --version
```

## MATLAB 恢复与验证状态

原用户偏好目录曾在启动阶段报 `failed to load settings errors_warnings plugin`。使用隔离的 `MATLAB_PREFDIR` 成功启动后，将 `%APPDATA%\MathWorks\MATLAB\R2024a` 备份并重建，普通 Windows 用户环境恢复正常。Codex 文件沙箱内仍可能触发该启动错误，因此 MATLAB 验证须在普通用户环境执行。

`code/matlab/+cumcm` 的 13 个方法入口均由 `tests/matlab/TestCore.m` 覆盖。2026-08-11 实测结果为 **13 Passed / 0 Failed / 0 Incomplete**：

```powershell
matlab -batch "addpath('code/matlab'); results=runtests('tests/matlab'); assertSuccess(results); run('tools/export_matlab_results.m')"
```

随后 `tools/compare_outputs.py` 使用 `code/fixtures/manifest.yaml` 比较 13 个 MATLAB 输出中的 21 个声明属性，结果为 0 个问题；机器可读证据位于 `validation/cross-language-test-report.json`。

## 2026-09-10 赛前复核

| 组件 | 本次状态 | 证据 |
|---|---|---|
| 仓库专用 Python | 通过 | `.venv\Scripts\python.exe`，Python 3.12.10；`pip check` 无损坏依赖；完整 pytest **86 passed**。 |
| MATLAB | 通过 | 普通用户环境运行 `TestCore.m`：**13 Passed / 0 Failed / 0 Incomplete**；输出已重新导出。 |
| Python/MATLAB 一致性 | 通过 | 13 个夹具、21 个声明属性比较通过，见 `validation/preflight-2026-09-10/cross-language.json`。 |
| XeLaTeX 可执行文件 | 可定位，运行阻塞 | `xelatex.exe` 文件元数据为 XeTeX 4.16 / MiKTeX 25.12；当前用户配置仍停在 MiKTeX 首次设置，`xelatex --version` 和新编译均被拒绝访问。 |
| XeLaTeX 新编译 | 环境阻塞 | 当前受限环境的 MiKTeX 首次设置在注册表/用户设置阶段返回拒绝访问；论文和 AI 详情模板尝试日志分别见 `validation/preflight-2026-09-10/latex-attempt.log` 与 `validation/preflight-2026-09-10/ai-details-latex-attempt.log`。仓库已有的 2026-08-11 编译产物不能替代本次新编译。 |

XeLaTeX 的剩余动作是在普通 Windows 用户环境完成一次 `templates\paper\main.tex` 和 `templates\ai-usage\AI工具使用详情.tex` 的双遍编译，再用 `pdftoppm` 查看页面；完成前不要把模板 PDF 当作可提交论文。

## 2026-09-12 B 题工作稿复核

| 组件 | 本次状态 | 证据 |
|---|---|---|
| 仓库专用 Python | 通过 | 重新建立 `.venv`：Python 3.11.15、pip 24.0；`pip check` 为 `No broken requirements found`。 |
| B 题单元测试 | 通过 | `python -m pytest contest/2026/tests -q`：**38 passed**。 |
| 仓库完整测试 | 通过 | 重建 `cumcm-assistant` 的 106 文件资源包后，`python -m pytest -q`：**87 passed**。 |
| 本地合成模拟 | 通过 | 固定种子 20260912--20260921，问题三、四各 10 局，共 20 局全部清除；报告位于忽略目录 `tmp/synthetic-paper-regression-20260912.json`。 |
| B 题论文 XeLaTeX | 通过 | 双遍编译为 A4、12 页，交叉引用已解析；12 页以 120 dpi 全部渲染并检查，无裁切、重叠或字体缺失。 |
| AI 详情 XeLaTeX | 通过 | 7 条实际记录编译为 4 页工作稿并逐页渲染；最终人工复核项保持未勾选。 |
| 2026 草稿检查器 | 通过 | `ai_usage`、`citations`、`code_bundle`、`package`、`paper` 五项均为 PASS，0 个问题。 |
| MATLAB | 沿用上次通过证据 | 本轮只修改 Python 绘图与论文，不改 MATLAB；最近一次普通用户环境结果仍为 **13 Passed / 0 Failed / 0 Incomplete**。 |

正式测试在本轮仍为 **0 次**，没有调用模拟器正式入口。
